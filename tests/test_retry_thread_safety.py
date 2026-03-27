import pytest
from unittest.mock import patch, MagicMock
from ai_capital_mcp.server import run_ingestion_job, job_status
import ai_techcrunch_ingest.cli
import ai_hackernews_ingest.cli
from ai_intel_processing.schema import IngestionResult

def test_ingestion_retry_loop():
    job_id = "test_retry_job_123"
    job_status[job_id] = {"status": "pending"}
    
    mock_run = MagicMock(side_effect=[Exception("Network hiccup"), Exception("Network hiccup 2"), IngestionResult(status="success", processed=2, errors=0)])
    
    with patch("ai_techcrunch_ingest.cli.run_ingestion", mock_run):
        run_ingestion_job(job_id, "techcrunch", 2)
        
    assert mock_run.call_count == 3
    assert job_status[job_id]["status"] == "completed"

def test_ingestion_failure_exhaustion():
    job_id = "test_exhaust_job_456"
    job_status[job_id] = {"status": "pending"}
    
    mock_run = MagicMock(side_effect=Exception("Terminal failure"))
    
    with patch("ai_hackernews_ingest.cli.run_ingestion", mock_run):
        run_ingestion_job(job_id, "hackernews", 2)
        
    assert mock_run.call_count == 3
    assert job_status[job_id]["status"] == "failed"
    assert "Terminal failure" in job_status[job_id]["error"]
