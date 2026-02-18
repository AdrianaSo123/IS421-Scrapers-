import requests
import logging
from typing import List, Dict, Any, Optional
from ai_intel_processing.utils import setup_logger, log_struct
import time

logger = setup_logger("ai_hackernews_ingest.client")

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

def fetch_top_stories(limit: int = 50) -> List[int]:
    """
    Fetches the top story IDs from Hacker News.
    """
    url = f"{HN_API_BASE}/topstories.json"
    try:
        log_struct(logger, logging.DEBUG, "Fetching top stories", url=url)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        ids = response.json()
        return ids[:limit]
    except requests.RequestException as e:
        log_struct(logger, logging.ERROR, "Failed to fetch top stories", error=str(e))
        return []

def fetch_story_details(story_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetches details for a specific story ID.
    """
    url = f"{HN_API_BASE}/item/{story_id}.json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log_struct(logger, logging.WARNING, "Failed to fetch story details", story_id=story_id, error=str(e))
        return None
