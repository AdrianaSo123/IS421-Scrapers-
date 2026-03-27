from mcp.server.fastmcp import FastMCP
from typing import Optional, List
from .schema import ToolResponse, EventTypeEnum, CapitalEvent, MarketSummary, SourceEnum
from .logger import mcp_tool_wrapper, logger
from cachetools import cached, TTLCache
import sqlite3
import json
import os
import uuid
import threading
import subprocess
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Auto-load the root environment variables so Claude config doesn't need naked API keys
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env")))

import sys
if not os.environ.get("OPENAI_API_KEY"):
    sys.stderr.write("FATAL ERROR: OPENAI_API_KEY environment variable is required.\n")
    sys.exit(1)
if not os.environ.get("DB_PATH"):
    sys.stderr.write("FATAL ERROR: DB_PATH environment variable is required.\n")
    sys.exit(1)

# Fix 9: Explicit Trend Thresholds
HIGH_FUNDING_THRESHOLD = 10
CONSOLIDATION_THRESHOLD = 5
VALID_EVENT_TYPES = {"funding", "acquisition", "partnership", "contract", "restructuring", "other"}

# Initialize the FastMCP server
mcp = FastMCP("Capital Intelligence Engine")

mcp_cache = TTLCache(maxsize=100, ttl=300)

from ai_intel_processing.database import DatabaseStore

def _parse_event_row(raw: dict) -> CapitalEvent:
    e_type = raw.get("event_type")
    if e_type not in VALID_EVENT_TYPES:
        e_type = "other"
        
    published_at = raw.get("published_at", "")
    if not published_at:
        published_at = "1970-01-01T00:00:00Z"
        
    return CapitalEvent(
        title=raw.get("title", "Unknown"),
        company=raw.get("company", "Unknown") or "Unknown",
        event_type=e_type,
        funding_amount=raw.get("funding_amount", "Undisclosed") or "Undisclosed",
        summary=raw.get("summary", ""),
        published_at=published_at
    )

@cached(cache=mcp_cache)
def _fetch_capital_events_cached(limit: int, event_type: Optional[str] = None) -> List[CapitalEvent]:
    db = DatabaseStore()
    raw_events = db.get_events(limit, event_type)
    return [_parse_event_row(raw) for raw in raw_events]

@mcp.tool()
@mcp_tool_wrapper
def get_capital_events(limit: int = 10, event_type: Optional[EventTypeEnum] = None) -> ToolResponse[List[CapitalEvent]]:
    """
    Returns a list of structured capital events ordered by recency.
    Use this tool when you need up-to-date funding, acquisition, or general market event data.
    """
    if not isinstance(limit, int):
        return ToolResponse(success=False, data=None, error="limit must be an integer")
    if event_type is not None and not isinstance(event_type, (str, EventTypeEnum)):
        return ToolResponse(success=False, data=None, error="event_type must be a valid string or enum")
        
    if limit > 100: limit = 100
    if limit < 1: limit = 1
        
    try:
        events = _fetch_capital_events_cached(limit, event_type)
        return ToolResponse(success=True, data=events, error=None)
    except Exception as e:
        logger.error(f"Internal error in get_capital_events: {e}", exc_info=True)
        return ToolResponse(success=False, data=None, error="Internal server error occurred")

@mcp.tool()
@mcp_tool_wrapper
def search_companies(company_name: str, limit: int = 10) -> ToolResponse[List[CapitalEvent]]:
    """
    Searches exclusively for capital intelligence mentioning a specific company.
    Use this tool when you need to research a target company's historical funding or M&A activity.
    """
    if not isinstance(company_name, str):
        return ToolResponse(success=False, data=None, error="company_name must be a string")
    if not isinstance(limit, int):
        return ToolResponse(success=False, data=None, error="limit must be an integer")
        
    if limit > 50: limit = 50
    if limit < 1: limit = 1
        
    try:
        company_name = company_name.strip()
        if not company_name or len(company_name) < 2:
            return ToolResponse(success=False, data=None, error="company_name must be at least 2 characters long.")
            
        db = DatabaseStore()
        raw_events = db.search_events(company_name, limit)
        results = [_parse_event_row(raw) for raw in raw_events]
            
        return ToolResponse(success=True, data=results, error=None)
    except Exception as e:
        logger.error(f"Internal error in search_companies: {e}", exc_info=True)
        return ToolResponse(success=False, data=None, error="Internal server error occurred")

@mcp.tool()
@mcp_tool_wrapper
def summarize_market_activity(days: int = 7) -> ToolResponse[MarketSummary]:
    """
    Synthesizes massive datasets of capital events into a high-level briefing.
    Use this tool when you need to understand broad market trends, funding acceleration, or consolidation phases over a time window.
    """
    if not isinstance(days, int):
        return ToolResponse(success=False, data=None, error="days must be an integer")
        
    if days > 30: days = 30
    if days < 1: days = 1
    
    try:
        db = DatabaseStore()
        raw_events = db.get_events_since(days)
        
        if not raw_events:
            return ToolResponse(
                success=True, 
                data=MarketSummary(
                    timeframe_days=days, 
                    total_events_analyzed=0, 
                    top_companies_mentioned=[],
                    event_type_distribution={},
                    trend_signal="STAGNANT",
                    high_level_summary="No activity detected in the specified timeframe."
                ),
                error=None
            )
            
        companies_count = {}
        event_types = {}
        total_funding_rounds = 0
        total_acquisitions = 0
        
        for raw in raw_events:
            c = raw.get("company")
            if c and c != "Unknown":
                companies_count[c] = companies_count.get(c, 0) + 1
                
            e_type = raw.get("event_type", "other")
            event_types[e_type] = event_types.get(e_type, 0) + 1
            
            if e_type == "funding": total_funding_rounds += 1
            if e_type == "acquisition": total_acquisitions += 1
                
        top_companies = sorted(companies_count, key=companies_count.get, reverse=True)[:5]
         
        # Fix 9: Deterministic Signals
        if total_funding_rounds >= HIGH_FUNDING_THRESHOLD:
            trend = "HIGH_FUNDING_ACTIVITY"
        elif total_acquisitions >= CONSOLIDATION_THRESHOLD:
            trend = "CONSOLIDATION_PHASE"
        else:
            trend = "MODERATE_ACTIVITY"
            
        summary_text = (
            f"Analysis of {len(raw_events)} recent articles implies a {trend.replace('_', ' ').lower()}. "
            f"We observed {total_funding_rounds} funding rounds and {total_acquisitions} M&A events. "
            f"Entities commanding the most focus include: {', '.join(top_companies) if top_companies else 'various players'}."
        )
         
        return ToolResponse(
            success=True, 
            data=MarketSummary(
                timeframe_days=days,
                total_events_analyzed=len(raw_events),
                top_companies_mentioned=top_companies,
                event_type_distribution=event_types,
                trend_signal=trend,
                high_level_summary=summary_text
            ),
            error=None
        )
    except Exception as e:
        logger.error(f"Internal error in summarize_market_activity: {e}", exc_info=True)
        return ToolResponse(success=False, data=None, error="Internal server error occurred")


# --- INGESTION BACKGROUND ENGINE ---

job_status = {}
job_status_lock = threading.Lock()

def clean_stale_jobs():
    """Fix 3: Cleanup expired jobs older than 15 minutes."""
    with job_status_lock:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        stale_keys = [k for k, v in job_status.items() if datetime.fromisoformat(v["updated_at"]) < cutoff]
        for k in stale_keys:
            del job_status[k]

def run_ingestion_job(job_id: str, source: str, limit: int):
    with job_status_lock:
        job_status[job_id]["status"] = "processing"
        
    logger.info(f"Running background ingestion natively for source: {source}")
    
    db_session = DatabaseStore(ensure_schema=False)
    
    max_retries = 3
    result = None
    last_error = None
    
    for attempt in range(max_retries):
        try:
            out_dir = os.path.join(os.environ.get("DATA_DIR", "./data"), "output")
            if source == "techcrunch":
                from ai_techcrunch_ingest.cli import run_ingestion
                result = run_ingestion(limit=limit, output=out_dir, raw=False, db_session=db_session, job_id=job_id)
            else:
                from ai_hackernews_ingest.cli import run_ingestion
                result = run_ingestion(limit=limit, output=out_dir, raw=False, db_session=db_session, job_id=job_id)
                
            from ai_intel_processing.schema import IngestionResult
            if not isinstance(result, IngestionResult):
                with job_status_lock:
                    job_status[job_id]["status"] = "failed"
                    job_status[job_id]["error"] = "Internal ingestion contract violation"
                return
                
            break
            
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Transient error during ingestion for {job_id}: {last_error} (attempt {attempt+1}/{max_retries})")
            time.sleep(2 ** attempt)
            
    with job_status_lock:
        if result and result.status == "success":
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["result_text"] = f"Successfully extracted documents. Processed: {result.processed}, Errors: {result.errors}"
            mcp_cache.clear()
            logger.info(f"Job {job_id} finished successfully. Cache cleared.")
        else:
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["error"] = last_error or "Ingestion returned non-success status"
            logger.error(f"Job {job_id} failed: {job_status[job_id]['error']}")
            
        if job_id in job_status: # thread safety check if cleaned up
            job_status[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

@mcp.tool()
@mcp_tool_wrapper
def trigger_ingestion(source: SourceEnum, limit: int = 10) -> ToolResponse[str]:
    """
    Triggers an async scraping job. Does NOT block. Returns job_id to monitor via get_ingestion_status.
    Use this tool to command the system to actively fetch the newest articles from TechCrunch or HackerNews if data looks stale.
    """
    if not isinstance(source, (str, SourceEnum)):
        return ToolResponse(success=False, data=None, error="source must be a valid string or enum")
    if not isinstance(limit, int):
        return ToolResponse(success=False, data=None, error="limit must be an integer")
        
    source_val = getattr(source, 'value', source)
    if source_val not in ["techcrunch", "hackernews"]:
        return ToolResponse(success=False, data=None, error="source must be techcrunch or hackernews")
        
    if limit > 50: limit = 50
    if limit < 1: limit = 1
        
    try:
        clean_stale_jobs()
            
        job_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        
        with job_status_lock:
            job_status[job_id] = {
                "status": "pending",
                "source": source_val,
                "created_at": now_iso,
                "updated_at": now_iso
            }
        
        t = threading.Thread(target=run_ingestion_job, args=(job_id, source_val, limit), daemon=True)
        t.start()
        
        return ToolResponse(success=True, data=job_id, error=None)
    except Exception as e:
        logger.error(f"Internal error in trigger_ingestion: {e}", exc_info=True)
        return ToolResponse(success=False, data=None, error="Internal server error occurred")

@mcp.tool()
@mcp_tool_wrapper
def get_ingestion_status(job_id: str) -> ToolResponse[dict]:
    """
    Looks up real-time status of trigger_ingestion job.
    Use this immediately after trigger_ingestion to monitor completion. Once status is 'completed', query for events.
    """
    if not isinstance(job_id, str):
        return ToolResponse(success=False, data=None, error="job_id must be a string")
        
    try:
        clean_stale_jobs()
        
        with job_status_lock:
            status_dict = job_status.get(job_id)
            if hasattr(status_dict, "copy"):
                status_dict = status_dict.copy()
                
        if not status_dict:
            return ToolResponse(success=False, data=None, error=f"Job {job_id} not found or expired (jobs prune after 15m).")
            
        return ToolResponse(success=True, data=status_dict, error=None)
    except Exception as e:
        logger.error(f"Internal error in get_ingestion_status: {e}", exc_info=True)
        return ToolResponse(success=False, data=None, error="Internal server error occurred")


def main():
    mcp.run()

if __name__ == "__main__":
    main()
