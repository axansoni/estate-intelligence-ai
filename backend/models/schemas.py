"""Data models and schemas for Estate Intelligence AI (supports Pydantic v2 with stdlib dataclass compatibility)."""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field  # type: ignore

    class PropertyRecord(BaseModel):
        id: str = Field(...)
        source_website: str = Field(...)
        project_name: str = Field(...)
        page_url: str = Field(...)
        description: str = Field(...)
        location: str = Field(...)
        country: str = Field(default="")
        city: str = Field(default="")
        developer: str = Field(default="Not publicly specified")
        brand_partner: Optional[str] = Field(default=None)
        property_details: Dict[str, Any] = Field(default_factory=dict)
        amenities: List[str] = Field(default_factory=list)
        pricing: str = Field(default="Available on request (not publicly listed on page)")
        payment_plan: str = Field(default="Available on request from sales team")
        completion_info: str = Field(default="Not publicly specified")
        status: str = Field(default="Under Development")
        image_urls: List[str] = Field(default_factory=list)
        faqs: List[Dict[str, str]] = Field(default_factory=list)
        other_attributes: Dict[str, Any] = Field(default_factory=dict)
        last_scraped_timestamp: str = Field(...)

    class ChatMessage(BaseModel):
        role: str
        content: str

    class ChatRequest(BaseModel):
        message: str
        history: List[ChatMessage] = Field(default_factory=list)
        source_filter: Optional[str] = Field(default=None)
        top_k: int = Field(default=8)

    class SourceCitation(BaseModel):
        project_name: str
        source_website: str
        page_url: str
        location: str
        pricing: Optional[str] = None
        completion_info: Optional[str] = None
        relevance_score: float = 0.0
        snippet: str = ""

    class ChatResponse(BaseModel):
        answer: str
        sources: List[SourceCitation]
        model_used: str
        llm_mode: str
        retrieved_chunks_count: int
        latency_ms: int
        notice: Optional[str] = None

except ImportError:

    @dataclass
    class PropertyRecord:  # type: ignore
        id: str
        source_website: str
        project_name: str
        page_url: str
        description: str
        location: str
        last_scraped_timestamp: str
        country: str = ""
        city: str = ""
        developer: str = "Not publicly specified"
        brand_partner: Optional[str] = None
        property_details: Dict[str, Any] = field(default_factory=dict)
        amenities: List[str] = field(default_factory=list)
        pricing: str = "Available on request (not publicly listed on page)"
        payment_plan: str = "Available on request from sales team"
        completion_info: str = "Not publicly specified"
        status: str = "Under Development"
        image_urls: List[str] = field(default_factory=list)
        faqs: List[Dict[str, str]] = field(default_factory=list)
        other_attributes: Dict[str, Any] = field(default_factory=dict)

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class ChatMessage:  # type: ignore
        role: str
        content: str

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class ChatRequest:  # type: ignore
        message: str
        history: List[ChatMessage] = field(default_factory=list)
        source_filter: Optional[str] = None
        top_k: int = 8

        def __post_init__(self):
            normalized = []
            for h in self.history:
                if isinstance(h, dict):
                    normalized.append(ChatMessage(role=h.get("role", "user"), content=h.get("content", "")))
                else:
                    normalized.append(h)
            self.history = normalized

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class SourceCitation:  # type: ignore
        project_name: str
        source_website: str
        page_url: str
        location: str
        pricing: Optional[str] = None
        completion_info: Optional[str] = None
        relevance_score: float = 0.0
        snippet: str = ""

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class ChatResponse:  # type: ignore
        answer: str
        sources: List[SourceCitation]
        model_used: str
        llm_mode: str
        retrieved_chunks_count: int
        latency_ms: int
        notice: Optional[str] = None

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)
