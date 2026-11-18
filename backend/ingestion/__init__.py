"""Ingestion package initializer and repeatable CLI ingestion script."""
import json
import logging
from typing import Any, Dict

from backend.config import settings
from backend.models.schemas import PropertyRecord
from backend.scraper import run_all_scrapers
from backend.ingestion.preprocess import preprocess_all_records
from backend.ingestion.vector_store import VectorStore

logger = logging.getLogger("estate_intelligence.ingestion")


def run_ingestion_pipeline(refresh_scrape: bool = False, perform_live_requests: bool = True) -> Dict[str, Any]:
    """Run the end-to-end scraping, preprocessing, chunking, embedding, and vector indexing pipeline."""
    settings.ensure_dirs()
    all_props_path = settings.SCRAPED_DATA_DIR / "all_properties.json"

    if refresh_scrape or not all_props_path.exists():
        records, scrape_stats = run_all_scrapers(perform_live_requests=perform_live_requests)
    else:
        with open(all_props_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
        records = [PropertyRecord(**item) for item in raw_list]
        dg_count = sum(1 for r in records if r.source_website == "DarGlobal")
        ws_count = sum(1 for r in records if r.source_website == "Wasalt")
        scrape_stats = {
            "darglobal_records": dg_count,
            "wasalt_records": ws_count,
            "total_records": len(records),
        }

    chunks = preprocess_all_records(records)
    store = VectorStore()
    index_stats = store.build_and_save(chunks)

    summary = {
        **scrape_stats,
        **index_stats,
    }
    logger.info("Ingestion pipeline completed: %s", summary)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_ingestion_pipeline(refresh_scrape=True, perform_live_requests=True)
    print(json.dumps(result, indent=2))
