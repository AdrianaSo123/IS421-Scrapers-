import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional, Dict, Any
from ai_intel_processing.schema import NewsArticle
from ai_intel_processing.utils import setup_logger, log_struct
from datetime import datetime
from dateutil import parser as date_parser

logger = setup_logger("ai_techcrunch_ingest.scraper")

DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1.0 # seconds

from typing import Optional, Dict, Any, Tuple

def fetch_article(url: str, session: Optional[requests.Session] = None) -> Tuple[Optional[str], int]:
    """
    Fetches the HTML content of an article with retries and timeout.
    Returns (html_content, status_code).
    """
    if session is None:
        session = requests.Session()

    for attempt in range(MAX_RETRIES):
        try:
            log_struct(logger, logging.DEBUG, "Fetching article", url=url, attempt=attempt+1)
            response = session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
            return response.text, response.status_code
        except requests.RequestException as e:
            status = getattr(e.response, 'status_code', 0) if e.response else 0
            log_struct(logger, logging.WARNING, "Failed to fetch article", url=url, error=str(e), attempt=attempt+1, status=status)
            if status == 404:
                return None, 404 # Don't retry 404s
            time.sleep(2 ** attempt) # Exponential backoff
    
    log_struct(logger, logging.ERROR, "Max retries exceeded", url=url)
    return None, 0

def extract_article_data(html: str, url: str) -> Optional[NewsArticle]:
    """
    Parses HTML to extract article content and metadata.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # TechCrunch specific selectors (subject to change, hence the need for distinct scraper modules)
        # Title
        title_tag = soup.find('h1', class_='article__title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
        
        # Content
        content_div = soup.find('div', class_='article-content')
        if not content_div:
             # Fallback for some layouts
            content_div = soup.find('div', class_='entry-content')
            
        if content_div:
            paragraphs = content_div.find_all('p')
            content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
        else:
             content = ""
             log_struct(logger, logging.WARNING, "Could not find content div", url=url)

        # Date
        # Trying to find date in meta tags first as it's more reliable
        published_at_str = None
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date:
            published_at_str = meta_date['content']
            
        published_at = date_parser.parse(published_at_str) if published_at_str else datetime.utcnow()

        return NewsArticle(
            source="techcrunch",
            title=title,
            url=url,
            published_at=published_at,
            content=content,
            raw_metadata={"parsed_at": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        log_struct(logger, logging.ERROR, "Error parsing article", url=url, error=str(e))
        return None
