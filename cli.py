import click
import requests
import time
import os
import pandas as pd
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

@click.group()
def cli():
    """Company Wallet Intelligence CLI"""
    pass

@cli.command()
@click.option('--input', 'input_file', required=True, type=click.Path(exists=True), help='Path to the input CSV file with user wallets.')
@click.option('--out', 'output_dir', required=True, type=click.Path(), help='Directory to save the output reports.')
def profile(input_file, output_dir):
    """Submits a new wallet analysis batch job."""
    click.echo(f"Submitting job for file: {input_file}")

    try:
        with open(input_file, 'rb') as f:
            response = requests.post(f"{API_BASE_URL}/jobs/submit", files={'file': f})

        if response.status_code != 200:
            click.echo(f"Error submitting job: {response.status_code} - {response.text}", err=True)
            return

        job_data = response.json()
        job_id = job_data['job_id']
        click.echo(f"Successfully submitted job with ID: {job_id}")
        click.echo("Polling for job completion...")

        while True:
            status_response = requests.get(f"{API_BASE_URL}/jobs/{job_id}/status")
            if status_response.status_code != 200:
                click.echo(f"Error fetching status: {status_response.text}", err=True)
                break

            status_data = status_response.json()
            click.echo(f"Job Status: {status_data['status']} | Wallets Processed: {status_data['wallets_processed']}/{status_data['total_wallets']}")

            if status_data['status'] == 'COMPLETED':
                click.echo("Job completed. Fetching reports...")
                fetch_and_save_reports(job_id, output_dir)
                break
            elif status_data['status'] == 'FAILED':
                click.echo(f"Job failed: {status_data.get('result', 'Unknown error')}", err=True)
                break

            time.sleep(10)

    except requests.exceptions.ConnectionError:
        click.echo("Error: Could not connect to the API. Is the 'api' service running?", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)

def fetch_and_save_reports(job_id, output_dir):
    """Fetches all reports for a completed job and saves them."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    report_formats = {
        "json": "report.json",
        "csv": "report.csv",
        "markdown": "report.md",
        "html": "report.html"
    }

    for format_key, filename in report_formats.items():
        try:
            url = f"{API_BASE_URL}/jobs/{job_id}/report?format={format_key}"
            res = requests.get(url)
            res.raise_for_status()

            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(res.text)
            click.echo(f"Successfully saved {output_path}")

        except requests.exceptions.RequestException as e:
            click.echo(f"Failed to download {format_key} report: {e}", err=True)


if __name__ == '__main__':
    cli()
