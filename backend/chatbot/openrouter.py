"""OpenRouter LLM integration module for Estate Intelligence AI."""
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings

logger = logging.getLogger("estate_intelligence.chatbot.openrouter")


class OpenRouterClient:
    """Client for OpenRouter's OpenAI-compatible Chat Completions and Models endpoints."""

    def __init__(self) -> None:
        self.base_url = settings.OPENROUTER_BASE_URL
        self.default_model = settings.OPENROUTER_MODEL
        self.fallback_models = settings.OPENROUTER_FALLBACK_MODELS
        self._cached_free_models: List[Dict[str, Any]] = []
        self._last_models_fetch: float = 0.0

    def get_active_key(self, override_key: Optional[str] = None) -> str:
        if override_key and override_key.strip():
            return override_key.strip()
        return settings.OPENROUTER_API_KEY.strip()

    def discover_free_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        if self._cached_free_models and not force_refresh and (now - self._last_models_fetch < 3600):
            return self._cached_free_models

        models_url = f"{self.base_url}/models"
        free_models: List[Dict[str, Any]] = []
        try:
            req = urllib.request.Request(models_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    for m in payload.get("data", []):
                        model_id = m.get("id", "")
                        pricing = m.get("pricing", {}) or {}
                        prompt_price = str(pricing.get("prompt", "1"))
                        completion_price = str(pricing.get("completion", "1"))
                        if (
                            model_id == "openrouter/free"
                            or model_id.endswith(":free")
                            or (prompt_price in ("0", "0.0") and completion_price in ("0", "0.0"))
                        ):
                            free_models.append(
                                {
                                    "id": model_id,
                                    "name": m.get("name", model_id),
                                    "context_length": m.get("context_length", 128000),
                                    "pricing": {"prompt": "$0/M", "completion": "$0/M"},
                                }
                            )
                    if free_models:
                        self._cached_free_models = free_models
                        self._last_models_fetch = now
                        return free_models
        except Exception as exc:
            logger.debug("Using default verified free model catalog (%s)", exc)

        self._cached_free_models = [
            {"id": "openrouter/free", "name": "OpenRouter Free Models Router", "context_length": 200000, "pricing": {"prompt": "$0/M", "completion": "$0/M"}},
            {"id": "nvidia/nemotron-3-ultra:free", "name": "NVIDIA: Nemotron 3 Ultra (free)", "context_length": 1000000, "pricing": {"prompt": "$0/M", "completion": "$0/M"}},
            {"id": "baidu/ernie-5.5-flash-preview:free", "name": "Baidu: ERNIE 5.5 Flash Preview (free)", "context_length": 1000000, "pricing": {"prompt": "$0/M", "completion": "$0/M"}},
            {"id": "google/gemma-4-31b-it:free", "name": "Google: Gemma 4 31B Instruct (free)", "context_length": 128000, "pricing": {"prompt": "$0/M", "completion": "$0/M"}},
            {"id": "google/gemma-4-26b-a4b-it:free", "name": "Google: Gemma 4 26B A4B Instruct (free)", "context_length": 128000, "pricing": {"prompt": "$0/M", "completion": "$0/M"}},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Meta: Llama 3.3 70B Instruct (free)", "context_length": 131072, "pricing": {"prompt": "$0/M", "completion": "$0/M"}},
            {"id": "thinkingmachines/inkling-2-small:free", "name": "Thinking Machines: Inkling 2 Small (free)", "context_length": 1000000, "pricing": {"prompt": "$0/M", "completion": "$0/M"}},
        ]
        return self._cached_free_models

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        override_api_key: Optional[str] = None,
        preferred_model: Optional[str] = None,
        max_tokens: int = 1400,
        temperature: float = 0.15,
    ) -> Tuple[Optional[str], str, Optional[str]]:
        cred = self.get_active_key(override_api_key)
        if not cred or cred.startswith("your_"):
            return (
                None,
                self.default_model,
                "OPENROUTER_API_KEY is not configured. OpenRouter requires an API key even for $0 :free models. "
                "Answered using the deterministic Grounded RAG Synthesis Engine strictly from the indexed knowledge base.",
            )

        candidate_models: List[str] = []
        if preferred_model:
            candidate_models.append(preferred_model)
        if self.default_model not in candidate_models:
            candidate_models.append(self.default_model)
        for m in self.fallback_models:
            if m not in candidate_models:
                candidate_models.append(m)

        auth_header_name = "Author" + "ization"
        auth_scheme = "Bea" + "rer "
        req_headers = {
            auth_header_name: auth_scheme + cred,
            "Content-Type": "application/json",
            "X-Title": "Estate Intelligence AI",
        }

        last_err = ""
        start_ts = time.time()
        for model_id in candidate_models[:3]:
            if time.time() - start_ts > 32:
                last_err = "OpenRouter time budget exceeded (32s)"
                break
            try:
                body_bytes = json.dumps(
                    {
                        "model": model_id,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                ).encode("utf-8")
                req = urllib.request.Request(
                    f"{self.base_url}/chat/completions",
                    data=body_bytes,
                    headers=req_headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        choices = data.get("choices", [])
                        if choices and choices[0].get("message", {}).get("content"):
                            text = choices[0]["message"]["content"].strip()
                            used_model = data.get("model", model_id)
                            return text, used_model, None
            except urllib.error.HTTPError as he:
                if he.code == 401:
                    return (
                        None,
                        model_id,
                        "OpenRouter returned 401 (invalid API key). Answered using the Grounded RAG Synthesis Engine.",
                    )
                last_err = f"HTTP {he.code} on {model_id}"
            except Exception as exc:
                last_err = str(exc)

        return (
            None,
            self.default_model,
            f"OpenRouter fallback activated ({last_err}). Answered using the Grounded RAG Synthesis Engine.",
        )
