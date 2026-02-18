"""
ai_techcrunch_ingest - TechCrunch ingestion module.
"""

from .rss import fetch_feed
from .scraper import fetch_article

__all__ = ["fetch_feed", "fetch_article"]
