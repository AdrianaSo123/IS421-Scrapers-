import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from ai_intel_processing.processing import IntelProcessor
from ai_intel_processing.schema import NewsArticle, InvestmentAnalysis

def test_process_article_with_llm():
    # Mock LLM Client
    mock_llm_client = MagicMock()
    mock_llm_client.model = "mock-model"
    
    # Mock analysis result
    mock_analysis = InvestmentAnalysis(
        company="Test Corp",
        funding_amount="$5M",
        funding_stage="Seed",
        investors=["VC A"],
        summary="A test summary",
        investment_relevant=True,
        event_type="funding"
    )
    mock_llm_client.analyze.return_value = mock_analysis

    # Patch the LLMClient import in processing.py or where it's instantiated
    # Since IntelProcessor instantiates it in __init__, we can mock the class
    with patch('ai_intel_processing.llm.LLMClient', return_value=mock_llm_client):
        processor = IntelProcessor(api_key="fake-key")
        
        article = NewsArticle(
            source="techcrunch",
            title="Test Article",
            url="https://example.com/article",
            published_at=datetime.utcnow(),
            content="Some content about Test Corp raising $5M."
        )
        
        output = processor.process_article(article)
        
        # Verify LLM was called
        mock_llm_client.analyze.assert_called_once()
        
        # Verify output structure
        assert output.company == "Test Corp"
        assert output.funding_amount == "$5M"
        assert output.investment_relevant is True
        assert output.summary == "A test summary"

def test_process_article_llm_failure():
    mock_llm_client = MagicMock()
    mock_llm_client.model = "mock-model"
    mock_llm_client.analyze.return_value = None # Simulate failure
    
    with patch('ai_intel_processing.llm.LLMClient', return_value=mock_llm_client):
        processor = IntelProcessor(api_key="fake-key")
        
        article = NewsArticle(
            source="techcrunch",
            title="Fail Article",
            url="https://example.com/fail",
            published_at=datetime.utcnow(),
            content="Content"
        )
        
        output = processor.process_article(article)
        
        assert output.company is None
        assert output.summary == "Analysis failed or content unavailable."
