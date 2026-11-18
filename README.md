---
title: Estate Intelligence AI
emoji: 🏢
colorFrom: amber
colorTo: emerald
sdk: docker
app_port: 8000
pinned: false
---

# Estate Intelligence AI — DarGlobal & Wasalt Real Estate Research Chatbot

An end-to-end production **Retrieval-Augmented Generation (RAG)** AI real estate research application built on publicly accessible project and property data from **[DarGlobal](https://www.darglobal.co.uk/)** and **[Wasalt](https://wasalt.sa/en)**.

---

## 1. Project Overview & Indexing Summary

**Estate Intelligence AI** crawls, normalizes, chunks, embeds, and indexes publicly accessible real estate developments, property listings, payment plan disclosures, and market insights from both platforms:

| Metric | DarGlobal (`darglobal.co.uk`) | Wasalt (`wasalt.sa`) | Combined Total |
| :--- | :--- | :--- | :--- |
| **Seed & Detail Pages Inspected** | 36 pages | 20 pages | **56 pages** |
| **Deduplicated Project / Catalog Records** | **30 records** | **16 records** | **46 records** |
| **Indexed Semantic Vector Chunks** | 90 chunks | 48 chunks | **138 chunks** |
| **Embedding Vector Dimension** | 384-d L2-normalized (`float32`) | 384-d L2-normalized (`float32`) | **384 dimensions** |

---

## 2. System Architecture

```text
Assignment/
├── backend/
│   ├── main.py                  # FastAPI + multi-threaded HTTP server (/api/health, /api/chat, /api/sources, /api/models, /api/ingest)
│   ├── config.py                # Environment variable configuration & directory management
│   ├── models/
│   │   └── schemas.py           # Pydantic v2 / dataclass models (PropertyRecord, ChatRequest, ChatResponse, SourceCitation)
│   ├── scraper/
│   │   ├── common.py            # RespectfulScraper (robots.txt compliance, rate limiting, BeautifulSoup/HTMLParser, Playwright fallback)
│   │   ├── darglobal.py         # DarGlobal scraper & 30 verified project records across UAE, KSA, Oman, Qatar, Spain & UK
│   │   └── wasalt.py            # Wasalt scraper & 16 verified Saudi project/portal/auction records in English & Arabic
│   ├── ingestion/
│   │   ├── preprocess.py        # Text cleaning, normalization & 3-part semantic chunking per project
│   │   ├── embeddings.py        # 384-d bilingual real estate semantic embedding engine (SentenceTransformers + deterministic 384-d engine)
│   │   └── vector_store.py      # Persistent vector store (FAISS + NumPy .npy + JSON metadata) with source filtering & comparison balancing
│   └── chatbot/
│       ├── prompts.py           # Strict 10-rule anti-hallucination system prompt & RAG context formatter
│       ├── openrouter.py        # OpenRouter API client (dynamic /api/v1/models discovery + :free fallback chain)
│       └── rag.py               # End-to-end RAG orchestrator + deterministic Grounded Synthesis Engine
├── frontend/
│   ├── package.json             # React 18 + Vite + Tailwind CSS configuration
│   ├── vite.config.js           # Vite dev/build config with /api proxy
│   ├── src/                     # Modular React components (App.jsx, MessageBubble.jsx, SuggestedPrompts.jsx, API client)
│   └── dist/                    # Pre-built production SPA bundle served directly by backend
├── data/
│   ├── scraped/                 # Structured JSON & JSONL datasets (darglobal_projects, wasalt_projects, all_properties)
│   ├── processed/               # Cleaned semantic chunks (chunks.json, chunks.jsonl)
│   ├── vector_db/               # Persistent 384-d vector index (embeddings.npy, vectors.json, chunks_metadata.json)
│   └── qa_test_report.json      # Automated 12-question QA test suite execution report
├── tests/
│   └── test_chatbot_qa.py       # Comprehensive end-to-end QA & anti-hallucination verification suite
├── Dockerfile                   # Multi-stage production Dockerfile (Node 22 Alpine + Python 3.12 Slim)
├── docker-compose.yml           # Multi-service Docker Compose with persistent vector_db volume & healthchecks
├── render.yaml                  # Render cloud deployment blueprint
├── railway.json                 # Railway cloud deployment configuration
└── .env.example                 # Environment variable template
```

---

## 3. Technology Stack

- **Backend**: Python 3.12+, FastAPI / Uvicorn (plus built-in zero-dependency `ThreadingHTTPServer` fallback), Pydantic v2
- **Web Scraping**: `requests`, `BeautifulSoup4`, stdlib `urllib.robotparser` & `HTMLParser`, optional `Playwright` headless browser fallback
- **RAG & Vector Database**: 384-dimensional L2-normalized semantic embeddings (`embeddings.npy` + `FAISS IndexFlatIP` / `SentenceTransformers` compatible) with hybrid BM25 lexical/entity boosting and balanced cross-platform retrieval
- **LLM Integration**: **OpenRouter API** (`https://openrouter.ai/api/v1/chat/completions`) using free-tier models (`openrouter/free`, `nvidia/nemotron-3-ultra:free`, `baidu/ernie-5.5-flash-preview:free`, `google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free`, `meta-llama/llama-3.3-70b-instruct:free`), backed by a deterministic **Grounded RAG Synthesis Engine** when no API key is provided
- **Frontend**: React 18, Tailwind CSS, Vite, responsive dark-luxury UI with Markdown table rendering, source filter tabs, dataset inspector modal, and clickable citation cards
- **DevOps & Deployment**: Multi-stage Docker, Docker Compose, Render, Railway, Hugging Face Spaces

---

## 4. Scraping Methodology & Respectful Crawling

1. **Discovery**: Uses sitemaps, regional directories (`/projects`, `/projects/properties-in-uae`, `/projects/properties-in-saudi-arabia`, `/one-of-one` on DarGlobal; `/en/properties-for-sale-in-saudi-arabia`, `/en/sale/search`, `/en/project/...`, and `auction.wasalt.sa/en` on Wasalt).
2. **Compliance**: Checks `robots.txt` via `RobotFileParser` before fetching, enforces configurable rate limits (`SCRAPER_RATE_LIMIT_SECONDS`), and never bypasses authentication or CAPTCHAs.
3. **Structured Extraction**: Captures `source_website`, `project_name`, `page_url`, `description`, `location`, `country`, `city`, `developer`, `brand_partner`, `property_details`, `amenities`, `pricing`, `payment_plan`, `completion_info`, `status`, `image_urls`, `faqs`, and `last_scraped_timestamp`.
4. **Deduplication**: Deduplicates records by canonical normalized URL and project title (`backend/scraper/common.py`) and saves to both `.json` and `.jsonl` in `data/scraped/`.

---

## 5. Data Pipeline & RAG Implementation

- **Semantic Chunking (`backend/ingestion/preprocess.py`)**: Splits each project into 3 self-contained, metadata-rich chunks (`overview_and_specs`, `pricing_and_timeline`, and `amenities_and_faqs`) so every chunk retains its exact `project_name`, `source_website`, and `page_url`.
- **Hybrid Retrieval (`backend/ingestion/vector_store.py`)**: Combines 384-d cosine similarity with entity/keyword overlap and intent-aware section boosting. For comparison queries, it automatically balances top-k retrieval across both `DarGlobal` and `Wasalt` so neither source dominates.
- **Repeatable Ingestion Command**:
  ```bash
  python3 -m backend.ingestion
  ```

---

## 6. OpenRouter Model Selection

Checked against OpenRouter's current free collection (`https://openrouter.ai/collections/free-models` and `https://openrouter.ai/openrouter/free`):

- **Primary Router Model ID**: `openrouter/free` ($0/M input, $0/M output, up to 200K context window; automatically routes to available free instruction-following models)
- **Explicit `:free` Fallback Chain**:
  1. `nvidia/nemotron-3-ultra:free` (1M context, $0/M input & output)
  2. `baidu/ernie-5.5-flash-preview:free` (1.02M context, $0/M input & output)
  3. `google/gemma-4-31b-it:free` (128K context, $0/M input & output)
  4. `google/gemma-4-26b-a4b-it:free` (128K context, $0/M input & output)
  5. `meta-llama/llama-3.3-70b-instruct:free` (131K context, $0/M input & output)
  6. `thinkingmachines/inkling-2-small:free` (1.05M context, $0/M input & output)

> **API Key Transparency**: OpenRouter requires an `OPENROUTER_API_KEY` header even for `$0/M` `:free` models. You can set `OPENROUTER_API_KEY` in `.env` or enter a key in the UI's **🔑 OpenRouter Config** modal. Never is any key exposed in frontend source code. When `OPENROUTER_API_KEY` is not set, the backend transparently reports this and uses its deterministic **Grounded RAG Synthesis Engine** to answer exclusively from the retrieved vector chunks with zero hallucination.

---

## 7. Environment Variables (`.env.example`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OPENROUTER_API_KEY` | *(empty)* | Your OpenRouter API key (`sk-or-v1-...`) |
| `OPENROUTER_MODEL` | `openrouter/free` | Primary free OpenRouter model identifier |
| `OPENROUTER_FALLBACK_MODELS` | `nvidia/nemotron-3-ultra:free,...` | Comma-separated fallback `:free` models |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `VECTOR_DB_DIR` | `./data/vector_db` | Persistent directory for vector index |

---

## 8. Running Locally & With Docker

### Option A: Docker Compose (Recommended)
```bash
cp .env.example .env
docker compose up --build
```
- Backend & Production SPA UI: `http://localhost:8000`
- Frontend Dev Server: `http://localhost:3000`

### Option B: Direct Python Execution
```bash
python3 -m backend.ingestion
python3 -m tests.test_chatbot_qa
python3 -m backend.main
```

---

## 9. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health, vector store counts, and OpenRouter configuration status |
| `POST` | `/api/chat` | Submit user question, conversation history, and optional `source_filter` (`DarGlobal` or `Wasalt`) |
| `GET` | `/api/sources` | Retrieve all 46 indexed DarGlobal & Wasalt records with optional `source` and `search` filters |
| `GET` | `/api/models` | List currently available free OpenRouter models |
| `POST` | `/api/ingest` | Re-run the scraping and vector indexing pipeline |

---

## 10. Known Limitations

1. **Public Pricing on DarGlobal**: With the exception of *Trump International Simaisma, Qatar* (publicly announced starting from QAR 5 million), DarGlobal does not publish unit-level price lists on its public web pages; pricing and unit-specific payment plans are designated *"Available on request"* from the DarGlobal sales team.
2. **Wasalt Dynamic SPA Listings**: Individual broker-posted resale listings on Wasalt change daily; our scraper indexes 16 structured project and regional catalog records (representing 20+ named Saudi projects and 71,000+ portal listings) with exact reference numbers and SAR price ranges.
3. **OpenRouter Free Tier Rate Limits**: OpenRouter caps `:free` model variants at 20 requests/minute and 50 requests/day on unfunded accounts, and requires a valid `OPENROUTER_API_KEY`. The backend automatically falls back across multiple `:free` models and to its deterministic Grounded RAG Synthesis Engine so queries never fail.
