import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional
from ai_intel_processing.utils import setup_logger, log_struct

logger = setup_logger("ai_hackernews_ingest.scraper")

DEFAULT_TIMEOUT = 10

from typing import Optional, Tuple

def fetch_content_generic(url: str) -> Tuple[str, str, int]:
    """
    Fetches content from a generic URL. 
    Returns (clean_text, raw_html, status_code).
    """
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={"User-Agent": "AI_Ingest_Bot/1.0"})
        response.raise_for_status()
        
        raw_text = response.text
        soup = BeautifulSoup(raw_text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text(separator='\n')
        
        # Simple cleanup
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text, raw_text, response.status_code
    
    except Exception as e:
        status = getattr(e, 'response', None) and getattr(e.response, 'status_code', 0)
        log_struct(logger, logging.WARNING, "Failed to fetch generic content", url=url, error=str(e), status=status or 0)
        return "", "", status or 0
