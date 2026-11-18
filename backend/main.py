"""FastAPI and standalone HTTP server for Estate Intelligence AI — DarGlobal & Wasalt Research Chatbot."""
import json
import logging
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from backend.config import settings
from backend.models.schemas import ChatMessage, ChatRequest
from backend.ingestion import run_ingestion_pipeline
from backend.chatbot.rag import RAGEngine

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("estate_intelligence.api")

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Lazy-initialize the singleton RAGEngine and ensure the vector store is built."""
    global _rag_engine
    if _rag_engine is None:
        settings.ensure_dirs()
        all_props_file = settings.SCRAPED_DATA_DIR / "all_properties.json"
        vector_meta_file = settings.VECTOR_DB_DIR / "chunks_metadata.json"
        if not all_props_file.exists() or not vector_meta_file.exists():
            run_ingestion_pipeline(
                refresh_scrape=not all_props_file.exists(),
                perform_live_requests=False,
            )
        _rag_engine = RAGEngine()
    return _rag_engine


def handle_health() -> Dict[str, Any]:
    engine = get_rag_engine()
    dg_count = sum(1 for r in engine.all_records if r.source_website == "DarGlobal")
    ws_count = sum(1 for r in engine.all_records if r.source_website == "Wasalt")
    has_key = bool(
        settings.OPENROUTER_API_KEY
        and not settings.OPENROUTER_API_KEY.startswith("your_")
    )
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "knowledge_base": {
            "total_records": len(engine.all_records),
            "darglobal_records": dg_count,
            "wasalt_records": ws_count,
            "total_indexed_chunks": len(engine.vector_store.chunks),
            "embedding_backend": engine.vector_store.embedder.backend_type,
            "vector_db_dir": str(settings.VECTOR_DB_DIR),
        },
        "llm": {
            "provider": "OpenRouter (https://openrouter.ai/api/v1)",
            "configured_model": settings.OPENROUTER_MODEL,
            "fallback_models": settings.OPENROUTER_FALLBACK_MODELS,
            "api_key_configured": has_key,
            "mode": "openrouter_live"
            if has_key
            else "grounded_rag_synthesis (awaiting OPENROUTER_API_KEY)",
        },
    }


def handle_sources(source: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    engine = get_rag_engine()
    records = engine.all_records
    if source and source.lower() in ("darglobal", "wasalt"):
        records = [r for r in records if r.source_website.lower() == source.lower()]
    if search and search.strip():
        q = search.strip().lower()
        records = [
            r
            for r in records
            if q in r.project_name.lower()
            or q in r.location.lower()
            or q in r.description.lower()
            or q in r.country.lower()
        ]
    dg_total = sum(1 for r in engine.all_records if r.source_website == "DarGlobal")
    ws_total = sum(1 for r in engine.all_records if r.source_website == "Wasalt")
    return {
        "summary": {
            "total_indexed_projects": len(engine.all_records),
            "darglobal_projects_count": dg_total,
            "wasalt_projects_count": ws_total,
            "total_vector_chunks": len(engine.vector_store.chunks),
            "filtered_count": len(records),
        },
        "records": [r.model_dump() for r in records],
    }


def handle_models() -> Dict[str, Any]:
    engine = get_rag_engine()
    models = engine.openrouter.discover_free_models()
    return {
        "default_model": settings.OPENROUTER_MODEL,
        "fallback_models": settings.OPENROUTER_FALLBACK_MODELS,
        "available_free_models": models,
    }


def handle_chat(payload: Dict[str, Any], override_key: Optional[str] = None) -> Dict[str, Any]:
    engine = get_rag_engine()
    msg = str(payload.get("message", "")).strip()
    if not msg:
        raise ValueError("Field 'message' is required and cannot be empty.")
    raw_history = payload.get("history") or []
    history = [
        ChatMessage(role=h.get("role", "user"), content=h.get("content", ""))
        if isinstance(h, dict)
        else h
        for h in raw_history
    ]
    req = ChatRequest(
        message=msg,
        history=history,
        source_filter=payload.get("source_filter"),
        top_k=int(payload.get("top_k", 8)),
    )
    resp = engine.answer_question(req, override_api_key=override_key)
    out = resp.model_dump()
    out["sources"] = [
        s.model_dump() if hasattr(s, "model_dump") else s for s in resp.sources
    ]
    return out


# Optional FastAPI mount when fastapi is installed in the environment
try:
    from fastapi import FastAPI, Header, HTTPException, Query  # type: ignore
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore
    from fastapi.responses import FileResponse  # type: ignore
    from fastapi.staticfiles import StaticFiles  # type: ignore

    app = FastAPI(
        title="Estate Intelligence AI — DarGlobal & Wasalt Research API",
        version=settings.APP_VERSION,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    @app.get("/health")
    async def api_health():
        return handle_health()

    @app.get("/api/sources")
    @app.get("/sources")
    async def api_sources(
        source: Optional[str] = Query(default=None),
        search: Optional[str] = Query(default=None),
    ):
        return handle_sources(source=source, search=search)

    @app.get("/api/models")
    async def api_models():
        return handle_models()

    @app.post("/api/chat")
    @app.post("/chat")
    async def api_chat(
        payload: Dict[str, Any],
        x_openrouter_key: Optional[str] = Header(default=None, alias="X-OpenRouter-Key"),
    ):
        import asyncio
        try:
            return await asyncio.to_thread(handle_chat, payload, override_key=x_openrouter_key)
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=str(ve))

    @app.post("/api/ingest")
    async def api_ingest(refresh_scrape: bool = False):
        summary = run_ingestion_pipeline(refresh_scrape=refresh_scrape, perform_live_requests=refresh_scrape)
        get_rag_engine().reload()
        return {"status": "reindexed", "summary": summary}

    if FRONTEND_DIST.exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API route not found")
            candidate = FRONTEND_DIST / full_path
            if candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(FRONTEND_DIST / "index.html"))

except ImportError:
    app = None  # type: ignore


class EstateIntelligenceHTTPHandler(BaseHTTPRequestHandler):
    """Production multi-threaded HTTP handler serving REST API endpoints and static SPA."""

    def _send_json(self, status_code: int, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-OpenRouter-Key")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-OpenRouter-Key")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/api/health", "/health"):
            self._send_json(200, handle_health())
            return
        if path in ("/api/sources", "/sources"):
            src = qs.get("source", [None])[0]
            search = qs.get("search", [None])[0]
            self._send_json(200, handle_sources(source=src, search=search))
            return
        if path == "/api/models":
            self._send_json(200, handle_models())
            return

        # Serve static frontend
        rel_path = path.lstrip("/") or "index.html"
        target_file = FRONTEND_DIST / rel_path
        if not target_file.is_file():
            target_file = FRONTEND_DIST / "index.html"

        if target_file.is_file():
            content = target_file.read_bytes()
            mime_type, _ = mimetypes.guess_type(str(target_file))
            self.send_response(200)
            self.send_header("Content-Type", mime_type or "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self._send_json(404, {"detail": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"

        try:
            payload = json.loads(raw_body) if raw_body else {}
        except Exception:
            self._send_json(400, {"detail": "Invalid JSON body"})
            return

        if path in ("/api/chat", "/chat"):
            override_key = self.headers.get("X-OpenRouter-Key")
            try:
                res = handle_chat(payload, override_key=override_key)
                self._send_json(200, res)
            except ValueError as ve:
                self._send_json(422, {"detail": str(ve)})
            except Exception as exc:
                logger.exception("Chat error: %s", exc)
                self._send_json(500, {"detail": str(exc)})
            return

        if path == "/api/ingest":
            refresh = bool(payload.get("refresh_scrape", False))
            summary = run_ingestion_pipeline(refresh_scrape=refresh, perform_live_requests=refresh)
            get_rag_engine().reload()
            self._send_json(200, {"status": "reindexed", "summary": summary})
            return

        self._send_json(404, {"detail": "Endpoint not found"})


def run_server(host: str = settings.HOST, port: int = settings.PORT) -> None:
    get_rag_engine()
    server = ThreadingHTTPServer((host, port), EstateIntelligenceHTTPHandler)
    logger.info("Estate Intelligence AI Server listening on http://%s:%d", host, port)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
