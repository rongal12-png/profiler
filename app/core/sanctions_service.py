"""
Sanctions screening service.

Downloads and parses sanctions lists (OFAC SDN, EU Consolidated, Israel NBCTF),
stores addresses in the DB for fast lookup, and checks individual wallet addresses
against the combined list.
"""

import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from .config import SessionLocal
from .models import SanctionsList, SanctionsAddress

logger = logging.getLogger(__name__)

# Source URLs
SANCTIONS_SOURCES = {
    "ofac_sdn": "https://www.treasury.gov/ofac/downloads/sdn_advanced.xml",
    "eu_consolidated": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=n002ofgv",
    "israel_nbctf": "https://nbctf.mod.gov.il/he/Sanctions/SanctionsList.json",
}


def _normalize_address(address: str) -> str:
    """Normalize address for comparison: lowercase, strip whitespace."""
    return address.strip().lower()


def check_address(address: str, db: Session | None = None) -> dict | None:
    """
    Check if an address appears on any sanctions list.
    Returns {list_name, entity_name, entity_type} or None.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        normalized = _normalize_address(address)
        hit = (
            db.query(SanctionsAddress)
            .join(SanctionsList)
            .filter(
                SanctionsAddress.address == normalized,
                SanctionsList.status == "active",
            )
            .first()
        )
        if hit:
            return {
                "list_name": hit.sanctions_list.list_name,
                "entity_name": hit.entity_name,
                "entity_type": hit.entity_type,
            }
        return None
    finally:
        if close_db:
            db.close()


def update_all_lists(db: Session | None = None, settings: dict | None = None) -> list[dict]:
    """Update all enabled sanctions lists. Returns status for each list."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        enabled_lists = {}
        if settings:
            enabled_lists = settings.get("sanctions", {}).get("lists", {})
        else:
            enabled_lists = {"ofac_sdn": True, "eu_consolidated": True, "israel_nbctf": True}

        results = []
        for list_name, enabled in enabled_lists.items():
            if not enabled:
                results.append({"list_name": list_name, "status": "skipped", "reason": "disabled"})
                continue
            try:
                count = update_sanctions_list(list_name, db=db)
                results.append({"list_name": list_name, "status": "ok", "record_count": count})
            except Exception as e:
                logger.error(f"Failed to update {list_name}: {e}", exc_info=True)
                results.append({"list_name": list_name, "status": "error", "error": str(e)})

        return results
    finally:
        if close_db:
            db.close()


def update_sanctions_list(list_name: str, db: Session | None = None) -> int:
    """
    Download, parse, and store a single sanctions list.
    Returns the number of addresses stored.
    """
    if list_name not in SANCTIONS_SOURCES:
        raise ValueError(f"Unknown sanctions list: {list_name}")

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    source_url = SANCTIONS_SOURCES[list_name]

    try:
        # Get or create the list record
        sl = db.query(SanctionsList).filter(SanctionsList.list_name == list_name).first()
        if not sl:
            sl = SanctionsList(list_name=list_name, source_url=source_url, status="updating")
            db.add(sl)
            db.flush()
        else:
            sl.status = "updating"
            db.flush()

        # Download the list
        logger.info(f"Downloading sanctions list: {list_name} from {source_url}")
        resp = requests.get(source_url, timeout=120)
        resp.raise_for_status()
        content = resp.content
        file_hash = hashlib.sha256(content).hexdigest()

        # Skip if content hasn't changed
        if sl.file_hash == file_hash:
            sl.status = "active"
            db.commit()
            logger.info(f"Sanctions list {list_name} unchanged (hash match), skipping parse")
            return sl.record_count or 0

        # Parse addresses based on list type
        if list_name == "ofac_sdn":
            addresses = _parse_ofac_sdn(content)
        elif list_name == "eu_consolidated":
            addresses = _parse_eu_consolidated(content)
        elif list_name == "israel_nbctf":
            addresses = _parse_israel_nbctf(content)
        else:
            addresses = []

        # Replace old addresses with new ones (atomic swap)
        db.query(SanctionsAddress).filter(SanctionsAddress.list_id == sl.id).delete()

        now = datetime.now(timezone.utc)
        for addr_entry in addresses:
            db.add(SanctionsAddress(
                list_id=sl.id,
                address=_normalize_address(addr_entry["address"]),
                entity_name=addr_entry.get("entity_name", "Unknown"),
                entity_type=addr_entry.get("entity_type"),
                source_entry_id=addr_entry.get("source_entry_id"),
                added_at=now,
            ))

        sl.last_updated = now
        sl.record_count = len(addresses)
        sl.file_hash = file_hash
        sl.source_url = source_url
        sl.status = "active"

        db.commit()
        logger.info(f"Sanctions list {list_name} updated: {len(addresses)} addresses")
        return len(addresses)

    except Exception as e:
        if sl:
            sl.status = "error"
            try:
                db.commit()
            except Exception:
                db.rollback()
        raise
    finally:
        if close_db:
            db.close()


def _parse_ofac_sdn(xml_bytes: bytes) -> list[dict]:
    """
    Parse OFAC SDN Advanced XML for crypto addresses.
    Crypto addresses are in <Feature> elements with FeatureTypeID matching crypto types.
    """
    addresses = []
    try:
        root = ET.fromstring(xml_bytes)
        ns = {"ns": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADVANCED_XML"}

        # Build lookup of crypto FeatureTypeIDs from ReferenceValueSets
        crypto_type_ids = set()
        for feature_type in root.findall(".//ns:FeatureType", ns):
            if feature_type.text and "Digital Currency Address" in feature_type.text:
                type_id = feature_type.get("ID")
                if type_id:
                    crypto_type_ids.add(type_id)

        logger.info(f"OFAC SDN: found {len(crypto_type_ids)} crypto FeatureType IDs")

        # Iterate through all DistinctParty elements
        for party in root.findall(".//ns:DistinctParty", ns):
            party_id = party.get("FixedRef", "")

            # Get entity name from primary Identity
            entity_name = "Unknown"
            for profile in party.findall(".//ns:Profile", ns):
                for identity in profile.findall(".//ns:Identity[@Primary='true']", ns):
                    for name_part_value in identity.findall(".//ns:NamePartValue", ns):
                        if name_part_value.text:
                            entity_name = name_part_value.text.strip()
                            break
                    if entity_name != "Unknown":
                        break
                if entity_name != "Unknown":
                    break

            # If no primary identity name, use first NamePartValue found
            if entity_name == "Unknown":
                for name_part_value in party.findall(".//ns:NamePartValue", ns):
                    if name_part_value.text:
                        entity_name = name_part_value.text.strip()
                        break

            # Find all Feature elements with crypto FeatureTypeID
            for feature in party.findall(".//ns:Feature", ns):
                feature_type_id = feature.get("FeatureTypeID", "")
                if feature_type_id in crypto_type_ids:
                    # Extract address from VersionDetail with DetailTypeID="1432"
                    for version_detail in feature.findall(".//ns:VersionDetail[@DetailTypeID='1432']", ns):
                        if version_detail.text:
                            addr = version_detail.text.strip()
                            # Basic validation: min length 26 chars
                            if len(addr) >= 26:
                                addresses.append({
                                    "address": addr,
                                    "entity_name": entity_name,
                                    "entity_type": "OFAC_SDN",
                                    "source_entry_id": party_id,
                                })

    except ET.ParseError as e:
        logger.error(f"Failed to parse OFAC SDN XML: {e}")

    logger.info(f"OFAC SDN: parsed {len(addresses)} crypto addresses")
    return addresses


def _parse_eu_consolidated(xml_bytes: bytes) -> list[dict]:
    """
    Parse EU Consolidated Sanctions List XML for crypto addresses.
    Crypto addresses are embedded in <remark> free-text fields, not in <identification>.
    """
    addresses = []
    import re

    try:
        root = ET.fromstring(xml_bytes)
        # Namespace: http://eu.europa.ec/fpi/fsd/export
        ns = {"ns": "http://eu.europa.ec/fpi/fsd/export"}

        # Iterate over all sanctionEntity elements
        for entity in root.findall(".//ns:sanctionEntity", ns):
            entity_name = "Unknown"

            # Get canonical English name from nameAlias with strong="true"
            for name_alias in entity.findall(".//ns:nameAlias[@strong='true']", ns):
                whole_name = name_alias.get("wholeName")
                if whole_name:
                    entity_name = whole_name.strip()
                    break

            # If no strong name, fall back to first wholeName
            if entity_name == "Unknown":
                for name_alias in entity.findall(".//ns:nameAlias", ns):
                    whole_name = name_alias.get("wholeName")
                    if whole_name:
                        entity_name = whole_name.strip()
                        break

            # Extract all <remark> text (from nameAlias and address elements)
            remark_texts = []
            for remark in entity.findall(".//ns:remark", ns):
                if remark.text:
                    remark_texts.append(remark.text)

            # Parse all remark texts for crypto addresses using regex
            combined_text = "\n".join(remark_texts)

            # ETH/BSC addresses (0x + 40 hex chars)
            for match in re.finditer(r'\b(0x[0-9a-fA-F]{40})\b', combined_text):
                addresses.append({
                    "address": match.group(1),
                    "entity_name": entity_name,
                    "entity_type": "EU_CONSOLIDATED",
                })

            # Bitcoin bech32 (bc1...)
            for match in re.finditer(r'\b(bc1[a-zA-HJ-NP-Z0-9]{25,62})\b', combined_text):
                addresses.append({
                    "address": match.group(1),
                    "entity_name": entity_name,
                    "entity_type": "EU_CONSOLIDATED",
                })

            # Bitcoin legacy (1... or 3...)
            for match in re.finditer(r'\b([13][a-km-zA-HJ-NP-Z1-9]{25,34})\b', combined_text):
                addresses.append({
                    "address": match.group(1),
                    "entity_name": entity_name,
                    "entity_type": "EU_CONSOLIDATED",
                })

            # Tron (T...)
            for match in re.finditer(r'\b(T[1-9A-HJ-NP-Za-km-z]{33})\b', combined_text):
                addresses.append({
                    "address": match.group(1),
                    "entity_name": entity_name,
                    "entity_type": "EU_CONSOLIDATED",
                })

    except ET.ParseError as e:
        logger.error(f"Failed to parse EU Consolidated XML: {e}")

    logger.info(f"EU Consolidated: parsed {len(addresses)} crypto addresses")
    return addresses


def _parse_israel_nbctf(content: bytes) -> list[dict]:
    """
    Parse Israel NBCTF sanctions list.
    Attempts JSON format first, falls back to text parsing.
    """
    import json

    addresses = []
    try:
        data = json.loads(content)

        # Handle various JSON structures
        entries = data if isinstance(data, list) else data.get("entries", data.get("items", []))

        for entry in entries:
            entity_name = entry.get("name", entry.get("entity_name", "Unknown"))

            # Look for crypto addresses in various fields
            for field in ["crypto_addresses", "addresses", "wallets", "digital_currency"]:
                if field in entry:
                    addrs = entry[field]
                    if isinstance(addrs, str):
                        addrs = [addrs]
                    for addr in addrs:
                        if isinstance(addr, str) and len(addr) >= 26:
                            addresses.append({
                                "address": addr,
                                "entity_name": entity_name,
                                "entity_type": "ISRAEL_NBCTF",
                                "source_entry_id": str(entry.get("id", "")),
                            })

            # Also check identification documents
            for ident in entry.get("identifications", entry.get("ids", [])):
                if isinstance(ident, dict):
                    ident_type = ident.get("type", "").lower()
                    ident_value = ident.get("value", ident.get("number", ""))
                    if "crypto" in ident_type or "wallet" in ident_type or "digital" in ident_type:
                        if isinstance(ident_value, str) and len(ident_value) >= 26:
                            addresses.append({
                                "address": ident_value,
                                "entity_name": entity_name,
                                "entity_type": "ISRAEL_NBCTF",
                            })

    except (json.JSONDecodeError, TypeError):
        # Not JSON; try to extract addresses from text
        text = content.decode("utf-8", errors="ignore")
        logger.warning("Israel NBCTF: could not parse as JSON, attempting text extraction")
        import re
        # Match Ethereum-style addresses
        for match in re.finditer(r'\b(0x[a-fA-F0-9]{40})\b', text):
            addresses.append({
                "address": match.group(1),
                "entity_name": "NBCTF Listed Entity",
                "entity_type": "ISRAEL_NBCTF",
            })
        # Match Bitcoin addresses
        for match in re.finditer(r'\b([13][a-km-zA-HJ-NP-Z1-9]{25,34})\b', text):
            addresses.append({
                "address": match.group(1),
                "entity_name": "NBCTF Listed Entity",
                "entity_type": "ISRAEL_NBCTF",
            })
        for match in re.finditer(r'\b(bc1[a-zA-HJ-NP-Z0-9]{25,87})\b', text):
            addresses.append({
                "address": match.group(1),
                "entity_name": "NBCTF Listed Entity",
                "entity_type": "ISRAEL_NBCTF",
            })

    logger.info(f"Israel NBCTF: parsed {len(addresses)} crypto addresses")
    return addresses
