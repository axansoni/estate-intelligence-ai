"""Common utilities for web scraping: robots.txt checking, rate-limited HTTP fetching, HTML parsing, and JSON/JSONL persistence."""
import hashlib
import json
import logging
import re
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.robotparser import RobotFileParser

try:
    import requests  # type: ignore
except ImportError:
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    BeautifulSoup = None  # type: ignore

from backend.config import settings
from backend.models.schemas import PropertyRecord

logger = logging.getLogger("estate_intelligence.scraper")


class SimpleHTMLInspector(HTMLParser):
    """Fallback HTML parser when BeautifulSoup is not installed."""

    def __init__(self) -> None:
        super().__init__()
        self.in_h1 = False
        self.in_title = False
        self.h1_text: List[str] = []
        self.title_text: List[str] = []
        self.meta_desc = ""
        self.images: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        attr_dict = dict(attrs)
        if tag == "h1":
            self.in_h1 = True
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = (attr_dict.get("name") or attr_dict.get("property") or "").lower()
            if name in ("description", "og:description") and attr_dict.get("content"):
                self.meta_desc = str(attr_dict["content"])
        elif tag == "img":
            src = attr_dict.get("src") or attr_dict.get("data-src")
            if src and src.startswith("http"):
                self.images.append(src)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self.in_h1 = False
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_h1:
            self.h1_text.append(data)
        elif self.in_title:
            self.title_text.append(data)


class RespectfulScraper:
    """Base scraper with robots.txt compliance, rate limiting, retries, and Playwright optional support."""

    def __init__(self, base_url: str, source_name: str):
        self.base_url = base_url.rstrip("/")
        self.source_name = source_name
        self.rate_limit = settings.SCRAPER_RATE_LIMIT_SECONDS
        self.timeout = settings.SCRAPER_TIMEOUT_SECONDS
        self._last_request_ts = 0.0
        self._robot_parser: Optional[RobotFileParser] = None
        self._visited_urls: Set[str] = set()

        self.headers = {
            "User-Agent": settings.SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        }
        self.session = None
        if requests is not None:
            self.session = requests.Session()
            self.session.headers.update(self.headers)

    def _http_get(self, url: str, timeout: int = 10) -> Optional[str]:
        if self.session is not None:
            resp = self.session.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            return None
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return response.read().decode("utf-8", errors="replace")
        return None

    def _init_robots(self) -> None:
        if self._robot_parser is not None:
            return
        self._robot_parser = RobotFileParser()
        robots_url = f"{self.base_url}/robots.txt"
        try:
            txt = self._http_get(robots_url, timeout=6)
            if txt:
                self._robot_parser.parse(txt.splitlines())
                logger.info("[%s] Loaded robots.txt from %s", self.source_name, robots_url)
            else:
                self._robot_parser.allow_all = True
        except Exception as exc:
            logger.debug("[%s] Could not fetch robots.txt (%s); proceeding respectfully.", self.source_name, exc)
            self._robot_parser.allow_all = True

    def can_fetch(self, url: str) -> bool:
        self._init_robots()
        if not self._robot_parser:
            return True
        try:
            return self._robot_parser.can_fetch(settings.SCRAPER_USER_AGENT, url)
        except Exception:
            return True

    def _respect_rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_ts
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_ts = time.time()

    def fetch_html(self, url: str, use_playwright_fallback: bool = False) -> Optional[str]:
        if not self.can_fetch(url):
            logger.warning("[%s] Skipping URL disallowed by robots.txt: %s", self.source_name, url)
            return None

        self._respect_rate_limit()
        try:
            html = self._http_get(url, timeout=self.timeout)
            if html:
                self._visited_urls.add(url)
                return html
        except Exception as exc:
            logger.debug("[%s] Request note for %s: %s", self.source_name, url, exc)

        if use_playwright_fallback:
            return self._fetch_with_playwright(url)
        return None

    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        try:
            from playwright.sync_api import sync_playwright  # type: ignore

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=settings.SCRAPER_USER_AGENT)
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                page.wait_for_timeout(1500)
                content = page.content()
                browser.close()
                self._visited_urls.add(url)
                return content
        except Exception:
            return None

    def parse_html_metadata(self, url: str, html: str) -> Dict[str, Any]:
        """Parse title, meta description, and images using BeautifulSoup or stdlib HTMLParser."""
        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")
            title_el = soup.find("h1") or soup.find("title")
            title = self.clean_text(title_el.get_text()) if title_el else ""
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
                "meta", attrs={"property": "og:description"}
            )
            if meta_tag and meta_tag.get("content"):
                meta_desc = self.clean_text(str(meta_tag.get("content")))
            images = [
                img.get("src") or img.get("data-src")
                for img in soup.find_all("img")
                if (img.get("src") or img.get("data-src") or "").startswith("http")
            ]
            return {
                "url": url,
                "live_title": title,
                "live_meta_description": meta_desc,
                "live_images": images[:6],
            }

        parser = SimpleHTMLInspector()
        parser.feed(html)
        title = self.clean_text(" ".join(parser.h1_text) or " ".join(parser.title_text))
        return {
            "url": url,
            "live_title": title,
            "live_meta_description": self.clean_text(parser.meta_desc),
            "live_images": parser.images[:6],
        }

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def make_record_id(source_website: str, page_url: str, project_name: str) -> str:
        key = f"{source_website.lower().strip()}::{page_url.strip().rstrip('/')}::{project_name.strip().lower()}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")[:32]
        return f"{source_website.lower()}-{slug}-{digest}"

    @staticmethod
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def deduplicate_records(records: List[PropertyRecord]) -> List[PropertyRecord]:
    seen_urls: Set[str] = set()
    seen_names: Set[str] = set()
    unique: List[PropertyRecord] = []

    for rec in records:
        norm_url = rec.page_url.strip().rstrip("/").lower()
        clean_name = re.sub(r"[^a-z0-9\u0600-\u06FF]+", "", rec.project_name.lower())
        norm_name = f"{rec.source_website.lower()}::{clean_name}"
        if norm_url in seen_urls or norm_name in seen_names:
            continue
        seen_urls.add(norm_url)
        seen_names.add(norm_name)
        unique.append(rec)

    return unique


def save_records_json_and_jsonl(
    records: List[PropertyRecord], json_path: Path, jsonl_path: Path
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    serialized = [rec.model_dump() for rec in records]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in serialized:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info("Saved %d records to %s and %s", len(records), json_path, jsonl_path)
