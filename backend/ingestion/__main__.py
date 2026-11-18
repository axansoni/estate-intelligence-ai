"""CLI entrypoint for `python -m backend.ingestion`."""
import json
import logging

from backend.ingestion import run_ingestion_pipeline

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_ingestion_pipeline(refresh_scrape=False, perform_live_requests=False)
    print(json.dumps(result, indent=2))
