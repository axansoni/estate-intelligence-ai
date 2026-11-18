"""Data preprocessing and semantic chunking pipeline for scraped DarGlobal and Wasalt records."""
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from backend.config import settings
from backend.models.schemas import PropertyRecord

logger = logging.getLogger("estate_intelligence.ingestion.preprocess")


def clean_and_normalize_text(text: str) -> str:
    """Clean HTML artifacts, normalize Unicode whitespace, and remove boilerplate noise."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def create_chunks_from_record(record: PropertyRecord) -> List[Dict[str, Any]]:
    """Split a PropertyRecord into structured, self-contained semantic chunks with full metadata attribution."""
    chunks: List[Dict[str, Any]] = []
    base_meta = {
        "record_id": record.id,
        "project_name": record.project_name,
        "source_website": record.source_website,
        "page_url": record.page_url,
        "location": record.location,
        "country": record.country,
        "city": record.city,
        "developer": record.developer,
        "brand_partner": record.brand_partner or "None",
        "pricing": record.pricing,
        "payment_plan": record.payment_plan,
        "completion_info": record.completion_info,
        "status": record.status,
        "last_scraped_timestamp": record.last_scraped_timestamp,
    }

    # Format property details string
    details_str = "; ".join(
        f"{k.replace('_', ' ').title()}: {v}"
        for k, v in record.property_details.items()
        if v is not None and v != ""
    )

    # Chunk 1: Overview, Location, Developer & Property Specifications
    overview_text = clean_and_normalize_text(
        f"[{record.source_website}] Project: {record.project_name} | "
        f"Location: {record.location} ({record.city}, {record.country}) | "
        f"Developer: {record.developer} | Brand Partner: {record.brand_partner or 'N/A'} | "
        f"Status: {record.status} | Completion: {record.completion_info} | "
        f"Pricing: {record.pricing} | "
        f"Property Specifications: {details_str} | "
        f"Description: {record.description} | "
        f"Source URL: {record.page_url}"
    )
    chunks.append(
        {
            "chunk_id": f"{record.id}::overview",
            "section_type": "overview_and_specs",
            "text": overview_text,
            "metadata": {**base_meta, "section_type": "overview_and_specs"},
        }
    )

    # Chunk 2: Pricing, Payment Plan, Completion Timeline & Investment Attributes
    other_attrs_str = "; ".join(
        f"{k.replace('_', ' ').title()}: {v}"
        for k, v in record.other_attributes.items()
        if v is not None and v != ""
    )
    financial_text = clean_and_normalize_text(
        f"[{record.source_website}] Project Pricing, Payment Plan & Timeline for {record.project_name} "
        f"in {record.location}: "
        f"Starting Price / Pricing: {record.pricing}. "
        f"Payment Plan: {record.payment_plan}. "
        f"Completion & Handover Timeline: {record.completion_info}. "
        f"Current Status: {record.status}. "
        f"Developer: {record.developer}. "
        f"Property Details: {details_str}. "
        f"Additional Investment Info: {other_attrs_str or 'Standard regional terms apply'}. "
        f"Source URL: {record.page_url}"
    )
    chunks.append(
        {
            "chunk_id": f"{record.id}::pricing_and_timeline",
            "section_type": "pricing_and_timeline",
            "text": financial_text,
            "metadata": {**base_meta, "section_type": "pricing_and_timeline"},
        }
    )

    # Chunk 3: Amenities, Facilities & FAQs
    amenities_str = ", ".join(record.amenities) if record.amenities else "Not publicly specified"
    faqs_str = " | ".join(
        f"Q: {faq.get('question', '')} A: {faq.get('answer', '')}"
        for faq in record.faqs
    )
    amenities_faq_text = clean_and_normalize_text(
        f"[{record.source_website}] Amenities, Facilities & FAQs for {record.project_name} "
        f"({record.location}): "
        f"Available Amenities & Lifestyle Facilities: {amenities_str}. "
        f"Frequently Asked Questions: {faqs_str or 'See project description for full details.'} "
        f"Source URL: {record.page_url}"
    )
    chunks.append(
        {
            "chunk_id": f"{record.id}::amenities_and_faqs",
            "section_type": "amenities_and_faqs",
            "text": amenities_faq_text,
            "metadata": {**base_meta, "section_type": "amenities_and_faqs"},
        }
    )

    return chunks


def preprocess_all_records(records: List[PropertyRecord]) -> List[Dict[str, Any]]:
    """Convert all scraped PropertyRecord items into deduplicated chunks and save to disk."""
    settings.ensure_dirs()
    all_chunks: List[Dict[str, Any]] = []
    seen_hashes = set()

    for rec in records:
        rec_chunks = create_chunks_from_record(rec)
        for ch in rec_chunks:
            text_hash = hashlib.sha256(ch["text"].encode("utf-8")).hexdigest()
            if text_hash in seen_hashes:
                continue
            seen_hashes.add(text_hash)
            all_chunks.append(ch)

    chunks_json_path = settings.PROCESSED_DATA_DIR / "chunks.json"
    chunks_jsonl_path = settings.PROCESSED_DATA_DIR / "chunks.jsonl"

    with open(chunks_json_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    with open(chunks_jsonl_path, "w", encoding="utf-8") as f:
        for ch in all_chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")

    logger.info(
        "Preprocessed %d records into %d semantic chunks at %s",
        len(records),
        len(all_chunks),
        chunks_json_path,
    )
    return all_chunks
