from typing import TypeVar, Generic, Optional, Literal, List
from pydantic import BaseModel, Field

T = TypeVar('T')

class ToolResponse(BaseModel, Generic[T]):
    """Standardized wrapper for all MCP tool returns."""
    success: bool = Field(..., description="True if the operation succeeded.")
    data: Optional[T] = Field(None, description="The strongly-typed payload. Must be None if success=False.")
    error: Optional[str] = Field(None, description="Explicit error message if success is False.")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds.")
    source: Optional[str] = Field(None, description="The MCP underlying tool source.")

EventTypeEnum = Literal["funding", "acquisition", "partnership", "contract", "restructuring", "other"]
SourceEnum = Literal["techcrunch", "hackernews"]

class CapitalEvent(BaseModel):
    title: str = Field(..., description="The title of the capital event.")
    company: str = Field(default="Unknown", description="The company involved. Normalized to 'Unknown' if missing.")
    event_type: EventTypeEnum = Field(default="other", description="The classification of the event.")
    funding_amount: str = Field(default="Undisclosed", description="Funding amount if applicable.")
    summary: str = Field(default="", description="Summary of the event.")
    published_at: str = Field(default="1970-01-01T00:00:00Z", description="Publication date string.")

class MarketSummary(BaseModel):
    timeframe_days: int = Field(..., description="The number of days aggregated.")
    total_events_analyzed: int = Field(..., description="Total events found in this window.")
    top_companies_mentioned: List[str] = Field(default_factory=list, description="Companies mentioned the most.")
    event_type_distribution: dict[str, int] = Field(default_factory=dict, description="Counts of funding vs acquisition vs others.")
    trend_signal: str = Field(..., description="High-level directional trend indicator.")
    high_level_summary: str = Field(..., description="A synthesized overview of market movement.")
