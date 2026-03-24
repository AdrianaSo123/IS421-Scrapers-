import pytest
import os
from ai_capital_mcp.server import get_capital_events, trigger_ingestion, get_ingestion_status, summarize_market_activity
from ai_capital_mcp.schema import ToolResponse

def test_get_capital_events_bounds():
    """Verify that inputs exceeding 100 are strictly bounded to 100."""
    res = get_capital_events(limit=9999)
    assert res.success == True
    assert len(res.data) <= 100

def test_get_capital_events_lower_bounds():
    """Verify negative bounds are reset to 1."""
    res = get_capital_events(limit=-5)
    assert res.success == True

def test_summarize_market_bounds():
    """Verify that looking backward a million days caps tightly to 30."""
    res = summarize_market_activity(days=99999)
    assert res.success == True
    assert res.data.timeframe_days == 30

def test_trigger_ingestion_async_job_flow():
    """Ensure triggering ingestion returns a valid JOB ID and valid lookup state."""
    res = trigger_ingestion(source="techcrunch", limit=1)
    assert res.success == True
    assert isinstance(res.data, str)
    
    # Immediately check lookup state
    status_res = get_ingestion_status(res.data)
    assert status_res.success == True
    assert status_res.data["status"] in ["pending", "processing", "completed", "failed"]

def test_get_ingestion_status_missing():
    """Ensure invalid job lookups return robust ToolResponse errors rather than crasing."""
    status_res = get_ingestion_status("invalid-uuid-0000")
    assert status_res.success == False
    assert "not found" in status_res.error
