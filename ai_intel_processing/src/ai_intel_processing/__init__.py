"""
ai_intel_processing - Shared intelligence module for AI news ingestion system.
"""

from .schema import NewsArticle, InvestmentRelevant, OutputSchema, RawIngestionOutput
from .processing import IntelProcessor
from .utils import setup_logger
from .deduplication import DeduplicationStore

__all__ = ["NewsArticle", "InvestmentRelevant", "OutputSchema", "RawIngestionOutput", "IntelProcessor", "setup_logger", "DeduplicationStore"]
