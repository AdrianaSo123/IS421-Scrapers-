import feedparser
import logging
from typing import List, Dict, Any
from ai_intel_processing.utils import setup_logger, log_struct

logger = setup_logger("ai_techcrunch_ingest.rss")

TC_RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"

def fetch_feed(url: str = TC_RSS_URL) -> List[Dict[str, Any]]:
    """
    Fetches and parses the TechCrunch AI RSS feed.
    Returns a list of raw entry dictionaries.
    """
    log_struct(logger, logging.INFO, "Fetching RSS feed", url=url)
    
    feed = feedparser.parse(url)
    
    if feed.bozo:
        log_struct(logger, logging.WARNING, "Feed parsing encountered an error (bozo)", error=str(feed.bozo_exception))
        # Depending on severity, we might still process partial data, but let's log it clearly.

    entries = feed.entries
    log_struct(logger, logging.INFO, "Feed fetched successfully", count=len(entries))
    
    return entries
