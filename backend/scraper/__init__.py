"""Scraper package initializer and unified runner."""
import logging
from typing import Dict, List, Tuple

from backend.config import settings
from backend.models.schemas import PropertyRecord
from backend.scraper.common import deduplicate_records, save_records_json_and_jsonl
from backend.scraper.darglobal import DarGlobalScraper, DARGLOBAL_SEED_URLS
from backend.scraper.wasalt import WasaltScraper, WASALT_SEED_URLS

logger = logging.getLogger("estate_intelligence.scraper")


def run_all_scrapers(perform_live_requests: bool = True) -> Tuple[List[PropertyRecord], Dict[str, int]]:
    """Run both DarGlobal and Wasalt scrapers, deduplicate, and persist to JSON and JSONL."""
    settings.ensure_dirs()

    dg_scraper = DarGlobalScraper()
    dg_records = dg_scraper.run(perform_live_requests=perform_live_requests)
    save_records_json_and_jsonl(
        dg_records,
        settings.SCRAPED_DATA_DIR / "darglobal_projects.json",
        settings.SCRAPED_DATA_DIR / "darglobal_projects.jsonl",
    )

    wasalt_scraper = WasaltScraper()
    wasalt_records = wasalt_scraper.run(perform_live_requests=perform_live_requests)
    save_records_json_and_jsonl(
        wasalt_records,
        settings.SCRAPED_DATA_DIR / "wasalt_projects.json",
        settings.SCRAPED_DATA_DIR / "wasalt_projects.jsonl",
    )

    combined = deduplicate_records(dg_records + wasalt_records)
    save_records_json_and_jsonl(
        combined,
        settings.SCRAPED_DATA_DIR / "all_properties.json",
        settings.SCRAPED_DATA_DIR / "all_properties.jsonl",
    )

    stats = {
        "darglobal_seed_urls_inspected": len(DARGLOBAL_SEED_URLS),
        "wasalt_seed_urls_inspected": len(WASALT_SEED_URLS),
        "darglobal_records": len(dg_records),
        "wasalt_records": len(wasalt_records),
        "total_records": len(combined),
    }
    return combined, stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    records, summary = run_all_scrapers(perform_live_requests=True)
    print(f"Scraping completed: {summary}")
