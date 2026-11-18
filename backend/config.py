"""Configuration module for Estate Intelligence AI backend."""
import os
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(dotenv_path=None):  # type: ignore
        if dotenv_path and Path(dotenv_path).exists():
            for line in Path(dotenv_path).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Application settings loaded from environment variables with sensible defaults."""

    APP_NAME: str = "Estate Intelligence AI"
    APP_VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # OpenRouter configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    ).rstrip("/")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
    OPENROUTER_FALLBACK_MODELS: List[str] = [
        m.strip()
        for m in os.getenv(
            "OPENROUTER_FALLBACK_MODELS",
            "openrouter/free,nvidia/nemotron-3-ultra:free,baidu/ernie-5.5-flash-preview:free,google/gemma-4-31b-it:free,google/gemma-4-26b-a4b-it:free,meta-llama/llama-3.3-70b-instruct:free",
        ).split(",")
        if m.strip()
    ]

    # Data directories
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
    SCRAPED_DATA_DIR: Path = Path(
        os.getenv("SCRAPED_DATA_DIR", str(DATA_DIR / "scraped"))
    )
    PROCESSED_DATA_DIR: Path = Path(
        os.getenv("PROCESSED_DATA_DIR", str(DATA_DIR / "processed"))
    )
    VECTOR_DB_DIR: Path = Path(
        os.getenv("VECTOR_DB_DIR", str(DATA_DIR / "vector_db"))
    )

    # Embedding model configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Scraper configuration
    SCRAPER_USER_AGENT: str = os.getenv(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    SCRAPER_RATE_LIMIT_SECONDS: float = float(
        os.getenv("SCRAPER_RATE_LIMIT_SECONDS", "0.5")
    )
    SCRAPER_TIMEOUT_SECONDS: int = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "15"))

    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    def ensure_dirs(self) -> None:
        """Ensure all data directories exist."""
        self.SCRAPED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
