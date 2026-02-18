from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class InvestmentRelevant(BaseModel):
    is_relevant: bool = Field(..., description="Whether the article is relevant for investment analysis")
    reasoning: Optional[str] = Field(None, description="Reasoning for relevance or irrelevance")

class NewsArticle(BaseModel):
    """
    Represents a normalized news article from any source.
    """
    source: str = Field(..., description="Source of the article (e.g., 'techcrunch', 'hackernews')")
    title: str = Field(..., description="Title of the article")
    url: str = Field(..., description="URL of the article") # kept as str to avoid Pydantic URL complexity for now, but validated
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    content: str = Field(..., description="Full text content of the article")
    
    # Raw metadata from source
    raw_metadata: Dict[str, Any] = Field(default_factory=dict, description="Original metadata from source")

class RawIngestionOutput(BaseModel):
    """
    Schema for raw verification mode output.
    """
    schema_version: Literal["1.0"] = "1.0"
    source: str
    title: str
    url: str
    published_at: Optional[str]
    raw_text_length: int
    raw_text_preview: str = Field(..., description="First 500 characters of raw text")
    http_status: int = 200
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class OutputSchema(BaseModel):
    """
    Final output schema for the ingestion system.
    """
    schema_version: Literal["2.0"] = "2.0"
    source: str
    title: str
    url: str
    published_at: Optional[str] # ISO format string for serialization
    company: Optional[str] = None
    funding_amount: Optional[str] = None
    funding_stage: Optional[str] = None
    investors: List[str] = Field(default_factory=list)
    summary: str
    investment_relevant: bool
    event_type: Literal["funding", "acquisition", "partnership", "contract", "restructuring", "other"] = Field(..., description="Classification of the event")
    
    # Traceability
    model_used: str = Field(..., description="LLM model used for analysis")
    prompt_version: str = Field(..., description="Version of the prompt used")
    processing_timestamp: str = Field(..., description="When the processing occurred")
    article_hash: str = Field(..., description="SHA-256 hash of the article content")
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http or https')
        return v

class InvestmentAnalysis(BaseModel):
    """
    Structured output from LLM analysis.
    """
    company: Optional[str] = Field(None, description="Name of the main company involved")
    funding_amount: Optional[str] = Field(None, description="Funding amount if applicable (e.g. '$10M')")
    funding_stage: Optional[str] = Field(None, description="Funding stage if applicable (e.g. 'Series A')")
    investors: List[str] = Field(default_factory=list, description="List of investors mentioned")
    summary: str = Field(..., description="Concise summary of the article")
    investment_relevant: bool = Field(..., description="Whether the article is relevant to AI investment")
    event_type: Literal["funding", "acquisition", "partnership", "contract", "restructuring", "other"] = Field(..., description="Classification of the event")
