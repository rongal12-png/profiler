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
    # OFAC SDN Advanced XML — new URL (old treasury.gov URL redirects here)
    "ofac_sdn": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN_ADVANCED.XML",
    "eu_consolidated": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=n002ofgv",
    "israel_nbctf": "https://nbctf.mod.gov.il/he/Sanctions/SanctionsList.json",
}


def _normalize_address(address: str) -> str:
    """Normalize address for comparison: lowercase, strip whitespace."""
    return address.strip().lower()


class SanctionsCheckError(Exception):
    """Raised when sanctions check cannot be completed (DB error, etc.)."""
    pass


def check_address(address: str, db: Session | None = None) -> dict | None:
    """
    Check if an address appears on any sanctions list.
    Returns {list_name, entity_name, entity_type} or None.

    C5: Raises SanctionsCheckError on DB failures instead of silently
    returning None (which would be a false negative on a compliance path).
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        normalized = _normalize_address(address)

        # Warn if no active sanctions lists exist (lists not yet downloaded)
        active_count = db.query(SanctionsList).filter(SanctionsList.status == "active").count()
        if active_count == 0:
            logger.warning("No active sanctions lists found — run POST /admin/sanctions/update or wait for auto-update")
            return None

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
    except Exception as e:
        # C5: Do NOT silently return None on DB errors — that's a false negative
        logger.error(f"Sanctions check failed for {address}: {e}")
        raise SanctionsCheckError(f"Sanctions check failed: {e}") from e
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
        headers = {"User-Agent": "Mozilla/5.0 (Wallet Intelligence System; compliance use)"}
        resp = requests.get(source_url, timeout=120, headers=headers)
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
        # M4: Rollback the entire transaction (including any deletes) on failure,
        # then update status in a fresh transaction
        db.rollback()
        try:
            sl_refresh = db.query(SanctionsList).filter(SanctionsList.list_name == list_name).first()
            if sl_refresh:
                sl_refresh.status = "error"
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
    Auto-detects namespace from root element for resilience.
    """
    import re as _re
    addresses = []
    try:
        root = ET.fromstring(xml_bytes)

        # Auto-detect namespace from root tag (e.g., {http://...}Sanctions)
        root_ns_match = _re.match(r'\{(.+?)\}', root.tag)
        detected_ns = root_ns_match.group(1) if root_ns_match else ""
        ns = {"ns": detected_ns} if detected_ns else {}
        prefix = "ns:" if detected_ns else ""

        logger.info(f"OFAC SDN: detected namespace = {detected_ns or '(none)'}")

        # Build lookup of crypto FeatureTypeIDs from ReferenceValueSets
        crypto_type_ids = set()
        for feature_type in root.findall(f".//{prefix}FeatureType", ns):
            if feature_type.text and "Digital Currency Address" in feature_type.text:
                type_id = feature_type.get("ID")
                if type_id:
                    crypto_type_ids.add(type_id)

        # Fallback: if XPath didn't find any, try raw iteration (handles nested namespaces)
        if not crypto_type_ids:
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag == "FeatureType" and elem.text and "Digital Currency Address" in elem.text:
                    type_id = elem.get("ID")
                    if type_id:
                        crypto_type_ids.add(type_id)

        logger.info(f"OFAC SDN: found {len(crypto_type_ids)} crypto FeatureType IDs")

        if not crypto_type_ids:
            logger.warning("OFAC SDN: no crypto FeatureType IDs found at all — XML structure may have changed")
            return addresses

        # Iterate through all DistinctParty elements using raw iteration for reliability
        for party in root.iter():
            tag = party.tag.split("}")[-1] if "}" in party.tag else party.tag
            if tag != "DistinctParty":
                continue

            party_id = party.get("FixedRef", "")

            # Get entity name
            entity_name = "Unknown"
            for child in party.iter():
                child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if child_tag == "NamePartValue" and child.text:
                    entity_name = child.text.strip()
                    break

            # Find Features with crypto FeatureTypeID
            for child in party.iter():
                child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if child_tag == "Feature":
                    ft_id = child.get("FeatureTypeID", "")
                    if ft_id in crypto_type_ids:
                        for detail in child.iter():
                            detail_tag = detail.tag.split("}")[-1] if "}" in detail.tag else detail.tag
                            if detail_tag == "VersionDetail" and detail.get("DetailTypeID") == "1432":
                                if detail.text and len(detail.text.strip()) >= 26:
                                    addresses.append({
                                        "address": detail.text.strip(),
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
