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

# Fix 9: Explicit Trend Thresholds
HIGH_FUNDING_THRESHOLD = 10
CONSOLIDATION_THRESHOLD = 5
VALID_EVENT_TYPES = {"funding", "acquisition", "partnership", "contract", "restructuring", "other"}

# Initialize the FastMCP server
mcp = FastMCP("Capital Intelligence Engine")

mcp_cache = TTLCache(maxsize=100, ttl=300)

def _get_db() -> sqlite3.Connection:
    db_path = os.environ.get("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/scrapers.db")))
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn

@cached(cache=mcp_cache)
def _fetch_capital_events_cached(limit: int, event_type: Optional[str] = None) -> List[CapitalEvent]:
    query = "SELECT raw_data FROM articles WHERE 1=1"
    params = []
    
    if event_type:
        query += " AND json_extract(raw_data, '$.event_type') = ?"
        params.append(event_type)
        
    query += " ORDER BY inserted_at DESC LIMIT ?"
    params.append(limit)
    
    with _get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
    results = []
    for row in rows:
        raw = json.loads(row["raw_data"])
        
        # Fix 2: Explicit EventType normalization and fallback
        e_type = raw.get("event_type")
        if e_type not in VALID_EVENT_TYPES:
            e_type = "other"
            
        # Fix 8: ISO 8601 formatting guarantees
        published_at = raw.get("published_at", "")
        if not published_at:
            published_at = "1970-01-01T00:00:00Z"
            
        results.append(CapitalEvent(
            title=raw.get("title", "Unknown"),
            company=raw.get("company", "Unknown") or "Unknown",
            event_type=e_type,
            funding_amount=raw.get("funding_amount", "Undisclosed") or "Undisclosed",
            summary=raw.get("summary", ""),
            published_at=published_at
        ))
    return results

@mcp.tool()
@mcp_tool_wrapper
def get_capital_events(limit: int = 10, event_type: Optional[EventTypeEnum] = None) -> ToolResponse[List[CapitalEvent]]:
    """
    Returns a list of structured capital events ordered by recency.
    Use this tool when you need up-to-date funding, acquisition, or general market event data.
    """
    if limit > 100: limit = 100
    if limit < 1: limit = 1
        
    try:
        events = _fetch_capital_events_cached(limit, event_type)
        # Fix 1: Ensure success data invariant
        return ToolResponse(success=True, data=events, error=None)
        
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            # Fix 1: explicitly fail with None data
            return ToolResponse(
                success=False, 
                data=None, 
                error="Database locked by an active ingestion process. Please retry your query in 1-2 seconds."
            )
        raise e

@mcp.tool()
@mcp_tool_wrapper
def search_companies(company_name: str, limit: int = 10) -> ToolResponse[List[CapitalEvent]]:
    """
    Searches exclusively for capital intelligence mentioning a specific company.
    Use this tool when you need to research a target company's historical funding or M&A activity.
    """
    if limit > 50: limit = 50
    if limit < 1: limit = 1
        
    try:
        company_name = company_name.strip()
        if not company_name or len(company_name) < 2:
            return ToolResponse(success=False, data=None, error="company_name must be at least 2 characters long.")
            
        # Fix 4: Higher precision company hits
        with _get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT raw_data FROM articles WHERE json_extract(raw_data, '$.company') LIKE ? ORDER BY inserted_at DESC LIMIT ?",
                (f"%{company_name}%", limit)
            )
            rows = cursor.fetchall()
            
            # If no direct hits, slightly fuzzy fallback
            if not rows:
                cursor.execute(
                    "SELECT raw_data FROM articles WHERE raw_data LIKE ? ORDER BY inserted_at DESC LIMIT ?",
                    (f"%{company_name}%", limit)
                )
                rows = cursor.fetchall()

        results = []
        for row in rows:
            raw = json.loads(row["raw_data"])
            e_type = raw.get("event_type") if raw.get("event_type") in VALID_EVENT_TYPES else "other"
            pub_at = raw.get("published_at", "") or "1970-01-01T00:00:00Z"

            results.append(CapitalEvent(
                title=raw.get("title", "Unknown"),
                company=raw.get("company", "Unknown") or "Unknown",
                event_type=e_type,
                funding_amount=raw.get("funding_amount", "Undisclosed") or "Undisclosed",
                summary=raw.get("summary", ""),
                published_at=pub_at
            ))
            
        return ToolResponse(success=True, data=results, error=None)
        
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            return ToolResponse(success=False, data=None, error="Database locked by an active ingestion process. Please retry your query in 1-2 seconds.")
        raise e

@mcp.tool()
@mcp_tool_wrapper
def summarize_market_activity(days: int = 7) -> ToolResponse[MarketSummary]:
    """
    Synthesizes massive datasets of capital events into a high-level briefing.
    Use this tool when you need to understand broad market trends, funding acceleration, or consolidation phases over a time window.
    """
    if days > 30: days = 30
    if days < 1: days = 1
    
    try:
        with _get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT raw_data FROM articles WHERE inserted_at >= date('now', ?)",
                (f"-{days} days",)
            )
            rows = cursor.fetchall()
            
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            return ToolResponse(success=False, data=None, error="Database locked. Please retry in 1-2 seconds.")
        raise e

    if not rows:
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
    
    for row in rows:
        raw = json.loads(row["raw_data"])
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
        f"Analysis of {len(rows)} recent articles implies a {trend.replace('_', ' ').lower()}. "
        f"We observed {total_funding_rounds} funding rounds and {total_acquisitions} M&A events. "
        f"Entities commanding the most focus include: {', '.join(top_companies) if top_companies else 'various players'}."
    )
     
    return ToolResponse(
        success=True, 
        data=MarketSummary(
            timeframe_days=days,
            total_events_analyzed=len(rows),
            top_companies_mentioned=top_companies,
            event_type_distribution=event_types,
            trend_signal=trend,
            high_level_summary=summary_text
        ),
        error=None
    )


# --- INGESTION BACKGROUND ENGINE ---

job_status = {}

def clean_stale_jobs():
    """Fix 3: Cleanup expired jobs older than 15 minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    stale_keys = [k for k, v in job_status.items() if datetime.fromisoformat(v["updated_at"]) < cutoff]
    for k in stale_keys:
        del job_status[k]

def run_ingestion_job(job_id: str, source: str, limit: int):
    try:
        job_status[job_id]["status"] = "processing"
        
        # Safe isolation & logging
        cmd = ["ai-techcrunch"] if source == "techcrunch" else ["ai-hn"]
        cmd.extend(["--limit", str(limit)])
        
        logger.info(f"Running background ingestion: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["result_text"] = "Successfully extracted all documents."
            if result.stdout:
                logger.info(f"Job {job_id} output: {result.stdout[:200]}")
            mcp_cache.clear()
            logger.info(f"Job {job_id} finished successfully. Cache cleared.")
        else:
            err_msg = result.stderr[:200] if result.stderr else "Unknown CLI error."
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["error"] = f"Exit {result.returncode}: {err_msg}"
            logger.error(f"Job {job_id} failed with exit {result.returncode}: {err_msg}")
            
    except subprocess.TimeoutExpired:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["error"] = "Subprocess timed out after 120 seconds."
        logger.error(f"Job {job_id} timed out.")
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["error"] = f"Catastrophic exception: {str(e)}"
        logger.error(f"Job {job_id} exception: {str(e)}", exc_info=True)
        
    if job_id in job_status: # thread safety check if cleaned up
        job_status[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

@mcp.tool()
@mcp_tool_wrapper
def trigger_ingestion(source: SourceEnum, limit: int = 10) -> ToolResponse[str]:
    """
    Triggers an async scraping job. Does NOT block. Returns job_id to monitor via get_ingestion_status.
    Use this tool to command the system to actively fetch the newest articles from TechCrunch or HackerNews if data looks stale.
    """
    clean_stale_jobs()
    
    if limit > 50: limit = 50
    if limit < 1: limit = 1
        
    job_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    job_status[job_id] = {
        "status": "pending",
        "source": source,
        "created_at": now_iso,
        "updated_at": now_iso
    }
    
    t = threading.Thread(target=run_ingestion_job, args=(job_id, source, limit), daemon=True)
    t.start()
    
    return ToolResponse(success=True, data=job_id, error=None)

@mcp.tool()
@mcp_tool_wrapper
def get_ingestion_status(job_id: str) -> ToolResponse[dict]:
    """
    Looks up real-time status of trigger_ingestion job.
    Use this immediately after trigger_ingestion to monitor completion. Once status is 'completed', query for events.
    """
    clean_stale_jobs()
    
    status_dict = job_status.get(job_id)
    if not status_dict:
        return ToolResponse(success=False, data=None, error=f"Job {job_id} not found or expired (jobs prune after 15m).")
        
    return ToolResponse(success=True, data=status_dict, error=None)


def main():
    mcp.run()

if __name__ == "__main__":
    main()
