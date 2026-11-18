"""Vector database storage and hybrid semantic retrieval engine.

Persists embeddings and chunk metadata to disk in data/vector_db/ (supporting FAISS, NumPy .npy,
and JSON vector storage), with source filtering, project deduplication, and cross-platform
comparison retrieval between DarGlobal and Wasalt.
"""
import json
import logging
import re
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings
from backend.ingestion.embeddings import EmbeddingEngine

logger = logging.getLogger("estate_intelligence.ingestion.vector_store")

STOPWORDS = {
    "what", "which", "where", "when", "who", "how", "are", "is", "the", "in", "on", "at",
    "of", "for", "to", "and", "or", "from", "with", "both", "between", "available",
    "does", "do", "can", "you", "tell", "me", "about", "list", "show", "have", "has",
    "mention", "mentioned", "publicly", "listed", "platforms", "platform", "website",
    "websites", "properties", "property", "projects", "project", "real", "estate",
}


def _save_npy_float32(path: Path, matrix: List[List[float]]) -> None:
    """Write a standard NumPy v1.0 .npy float32 file without requiring numpy if unavailable."""
    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0
    header_dict = f"{{'descr': '<f4', 'fortran_order': False, 'shape': ({rows}, {cols}), }}"
    header_bytes = header_dict.encode("latin1")
    padding_len = (64 - ((10 + len(header_bytes) + 1) % 64)) % 64
    header_bytes = header_bytes + (b" " * padding_len) + b"\n"
    magic = b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header_bytes))

    with open(path, "wb") as f:
        f.write(magic)
        f.write(header_bytes)
        for row in matrix:
            f.write(struct.pack(f"<{cols}f", *row))


class VectorStore:
    """Persistent vector database supporting FAISS/NumPy cosine similarity + BM25 lexical boost."""

    def __init__(self, db_dir: Path = settings.VECTOR_DB_DIR):
        self.db_dir = db_dir
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_path = self.db_dir / "embeddings.npy"
        self.vectors_json_path = self.db_dir / "vectors.json"
        self.faiss_index_path = self.db_dir / "faiss.index"
        self.metadata_path = self.db_dir / "chunks_metadata.json"

        self.embedder = EmbeddingEngine()
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []

    def build_and_save(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate embeddings for all chunks and persist index + metadata to disk."""
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        self.embeddings = self.embedder.encode(texts)

        # Save .npy binary matrix, vectors.json, and metadata JSON
        _save_npy_float32(self.embeddings_path, self.embeddings)
        with open(self.vectors_json_path, "w", encoding="utf-8") as f:
            json.dump(self.embeddings, f)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

        faiss_saved = False
        try:
            import numpy as np  # type: ignore
            import faiss  # type: ignore

            arr = np.asarray(self.embeddings, dtype=np.float32)
            index = faiss.IndexFlatIP(arr.shape[1])
            index.add(arr)
            faiss.write_index(index, str(self.faiss_index_path))
            faiss_saved = True
        except Exception:
            pass

        dim = len(self.embeddings[0]) if self.embeddings else 384
        return {
            "total_chunks_indexed": len(self.chunks),
            "embedding_dimension": dim,
            "embedding_backend": self.embedder.backend_type,
            "faiss_index_saved": faiss_saved,
            "vector_db_dir": str(self.db_dir),
        }

    def load(self) -> bool:
        """Load persisted embeddings and metadata from disk."""
        if not self.metadata_path.exists() or not self.vectors_json_path.exists():
            return False
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
            with open(self.vectors_json_path, "r", encoding="utf-8") as f:
                self.embeddings = json.load(f)
            return len(self.chunks) > 0 and len(self.embeddings) == len(self.chunks)
        except Exception as exc:
            logger.error("Failed to load vector store: %s", exc)
            return False

    @staticmethod
    def _lexical_overlap_score(query: str, chunk: Dict[str, Any]) -> float:
        q_lower = query.lower()
        q_tokens = [
            t for t in re.findall(r"[a-z0-9\u0600-\u06FF]+", q_lower)
            if t not in STOPWORDS and len(t) > 1
        ]
        if not q_tokens:
            return 0.0

        text_lower = chunk["text"].lower()
        meta = chunk.get("metadata", {})
        proj_lower = meta.get("project_name", "").lower()
        loc_lower = meta.get("location", "").lower()

        score = 0.0
        for tok in q_tokens:
            if tok in proj_lower:
                score += 0.35
            if tok in loc_lower:
                score += 0.20
            if tok in text_lower:
                score += 0.12

        section = meta.get("section_type", "")
        if any(w in q_lower for w in ["price", "cost", "payment", "installment", "completion", "handover", "when", "date", "deliver", "sar", "qar", "aed"]):
            if section == "pricing_and_timeline":
                score += 0.22
        if any(w in q_lower for w in ["amenity", "amenities", "facility", "pool", "waterfront", "beach", "golf", "padel", "gym"]):
            if section in ("amenities_and_faqs", "overview_and_specs"):
                score += 0.18

        return min(score, 1.2)

    def search(
        self,
        query: str,
        top_k: int = 8,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid semantic + entity search with optional source filtering and comparison balancing."""
        if not self.embeddings or not self.chunks:
            if not self.load():
                return []

        q_vec = self.embedder.encode_query(query)
        q_lower = query.lower()

        effective_filter = source_filter
        mentions_dg = any(w in q_lower for w in ["darglobal", "dar global", "astera", "les vagues", "tierra viva", "marea", "neptune", "mulliner", "dg1", "pagani", "urban oasis", "aida", "simaisma"])
        mentions_wasalt = any(w in q_lower for w in ["wasalt", "وصلت", "sadeem", "calma", "darwaza", "دروازة", "etoile", "إتوال", "dyari", "shams al riyadh", "shams al arous", "dar al mashaer", "badr 2", "amelia", "mashayid", "مشيد"])
        is_comparison = any(w in q_lower for w in ["compare", "comparison", "both", "versus", "vs", "difference", "across both"]) or (mentions_dg and mentions_wasalt)

        if not effective_filter and not is_comparison:
            if mentions_dg and not mentions_wasalt:
                effective_filter = "DarGlobal"
            elif mentions_wasalt and not mentions_dg:
                effective_filter = "Wasalt"

        scored_candidates: List[Tuple[float, int]] = []
        for idx, chunk in enumerate(self.chunks):
            src = chunk["metadata"].get("source_website", "")
            if effective_filter and src.lower() != effective_filter.lower():
                continue
            dense_score = self.embedder.cosine_similarity(self.embeddings[idx], q_vec)
            lex_score = self._lexical_overlap_score(query, chunk)
            combined_score = dense_score + lex_score
            scored_candidates.append((combined_score, idx))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        if is_comparison or (effective_filter is None and not mentions_dg and not mentions_wasalt):
            dg_results: List[Dict[str, Any]] = []
            ws_results: List[Dict[str, Any]] = []
            half_k = max(top_k // 2, 3)

            for score, idx in scored_candidates:
                ch = self.chunks[idx]
                src = ch["metadata"].get("source_website", "")
                entry = {**ch, "score": round(score, 4)}
                if src == "DarGlobal" and len(dg_results) < half_k:
                    dg_results.append(entry)
                elif src == "Wasalt" and len(ws_results) < half_k:
                    ws_results.append(entry)
                if len(dg_results) >= half_k and len(ws_results) >= half_k:
                    break

            merged = dg_results + ws_results
            merged.sort(key=lambda x: x["score"], reverse=True)
            return merged[:top_k]

        results: List[Dict[str, Any]] = []
        for score, idx in scored_candidates[:top_k]:
            results.append({**self.chunks[idx], "score": round(score, 4)})
        return results
