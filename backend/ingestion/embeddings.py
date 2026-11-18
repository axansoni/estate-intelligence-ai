"""Embedding generation module supporting Sentence-Transformers, NumPy, and pure-Python 384-d semantic vectors."""
import hashlib
import logging
import math
import re
from typing import List

from backend.config import settings

logger = logging.getLogger("estate_intelligence.ingestion.embeddings")

DOMAIN_CONCEPT_CLUSTERS: List[List[str]] = [
    ["price", "pricing", "cost", "starting", "sar", "aed", "qar", "million", "expensive", "cheap", "afford", "budget", "سعر", "أسعار", "ريال"],
    ["payment", "plan", "installment", "down", "handover", "milestone", "financing", "mortgage", "escrow", "دفعات", "تقسيط", "تمويل"],
    ["completion", "delivery", "handover", "timeline", "date", "when", "ready", "under", "construction", "development", "2026", "2027", "2028", "2029", "2030", "2031", "تحت الإنشاء", "جاهز"],
    ["waterfront", "beach", "beachfront", "sea", "ocean", "oceanfront", "canal", "corniche", "marina", "island", "coastal", "shore", "بحر", "واجهة بحرية", "كورنيش"],
    ["golf", "fairway", "course", "club", "clubhouse", "cart", "championship", "jge", "simaisma", "aida", "wadi safar", "جولف"],
    ["amenity", "amenities", "facility", "facilities", "pool", "infinity", "gym", "fitness", "spa", "sauna", "cinema", "padel", "concierge", "security", "مرافق", "مميزات", "مسبح", "نادي"],
    ["villa", "villas", "mansion", "mansions", "townhouse", "duplex", "standalone", "فيلا", "فلل", "قصر", "دوبلكس"],
    ["apartment", "apartments", "flat", "flats", "studio", "penthouse", "tower", "floor", "compound", "شقة", "شقق", "أدوار", "كومباوند", "برج"],
    ["land", "plot", "plots", "masterplan", "square", "sqm", "sqft", "area", "size", "أرض", "أراضي", "مخطط", "مساحة"],
    ["location", "where", "city", "country", "destination", "address", "district", "neighborhood", "موقع", "مدينة", "حي"],
    ["dubai", "uae", "emirates", "rak", "ras al khaimah", "marjan", "downtown", "business bay", "sheikh zayed", "دبي", "الإمارات"],
    ["riyadh", "jeddah", "makkah", "mecca", "madinah", "medina", "khobar", "dammam", "saudi", "ksa", "الرياض", "جدة", "مكة", "المدينة", "الخبر", "الدمام", "السعودية"],
    ["oman", "muscat", "aida", "qatar", "doha", "qetaifan", "simaisma", "spain", "benahavis", "marbella", "cortesin", "london", "uk", "عمان", "مسقط", "قطر", "الدوحة"],
    ["brand", "branded", "partner", "collaboration", "trump", "aston martin", "pagani", "missoni", "lamborghini", "elie saab", "mouawad", "fendi", "marriott", "w hotels"],
    ["developer", "who", "built", "darglobal", "dar al arkan", "wasalt", "christies", "mashayid", "maya", "aurelina", "infath", "rega", "مطور", "دار الأركان", "وصلت"],
    ["available", "availability", "sold", "out", "status", "units", "booking", "register", "auction", "auctions", "متاح", "للبيع", "مزاد"],
    ["visa", "golden", "residency", "tax", "freehold", "foreign", "investor", "investment", "roi", "yield", "استثمار", "تأشيرة", "إقامة"],
]


class EmbeddingEngine:
    """Generates L2-normalized 384-dimensional embeddings for documents and queries."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL, dim: int = 384):
        self.model_name = model_name
        self.dim = dim
        self._st_model = None
        self.backend_type = "hybrid_semantic_384d"
        self._try_load_sentence_transformer()

    def _try_load_sentence_transformer(self) -> None:
        try:
            import os
            if os.getenv("USE_LIGHTWEIGHT_EMBEDDINGS", "1") == "1":
                return
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._st_model = SentenceTransformer(self.model_name)
            self.backend_type = f"sentence-transformers/{self.model_name}"
        except Exception:
            pass

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9\u0600-\u06FF]+", text.lower())

    def encode_single(self, text: str) -> List[float]:
        """Compute a 384-d L2-normalized semantic + lexical feature-hashing vector."""
        vec = [0.0] * self.dim
        if not text:
            return vec

        tokens = self._tokenize(text)
        text_lower = text.lower()

        for idx, cluster in enumerate(DOMAIN_CONCEPT_CLUSTERS):
            if idx >= 64:
                break
            hits = sum(1 for term in cluster if term in text_lower)
            if hits > 0:
                vec[idx] = math.log1p(hits) * 2.2

        hash_space = self.dim - 64
        for i, tok in enumerate(tokens):
            if len(tok) < 2:
                continue
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            bucket = 64 + (h % hash_space)
            sign = 1.0 if ((h >> 16) & 1) == 0 else -1.0
            weight = 1.5 if len(tok) >= 4 else 0.8
            vec[bucket] += sign * weight

            if i + 1 < len(tokens):
                bigram = f"{tok}_{tokens[i + 1]}"
                hb = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
                bbucket = 64 + (hb % hash_space)
                bsign = 1.0 if ((hb >> 16) & 1) == 0 else -1.0
                vec[bbucket] += bsign * 1.8

            if len(tok) >= 5:
                for c_idx in range(len(tok) - 3):
                    trigram = tok[c_idx : c_idx + 4]
                    hc = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
                    cbucket = 64 + (hc % hash_space)
                    csign = 1.0 if ((hc >> 16) & 1) == 0 else -1.0
                    vec[cbucket] += csign * 0.35

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-8:
            vec = [round(v / norm, 6) for v in vec]
        return vec

    def encode(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._st_model is not None:
            embs = self._st_model.encode(texts, normalize_embeddings=True)
            return [list(map(float, row)) for row in embs]
        return [self.encode_single(t) for t in texts]

    def encode_query(self, query: str) -> List[float]:
        return self.encode_single(query)

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        return sum(a * b for a, b in zip(v1, v2))
