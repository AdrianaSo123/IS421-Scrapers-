import pytest
from ai_intel_processing.schema import NewsArticle, OutputSchema, RawIngestionOutput
from pydantic import ValidationError
from datetime import datetime

def test_news_article_validation():
    # Valid
    article = NewsArticle(
        source="test",
        title="Test Article",
        url="https://example.com",
        content="Some content"
    )
    assert article.title == "Test Article"
    
    # Invalid URL (Pydantic might not validate strictly logic unless we added validator, 
    # but I added one to OutputSchema)
    # NewsArticle has: url: str.
    
    # Missing required field
    with pytest.raises(ValidationError):
        NewsArticle(source="test")

def test_output_schema_validation():
    # Valid
    output = OutputSchema(
        schema_version="2.0",
        source="test",
        title="Test",
        url="https://example.com",
        summary="Summary",
        investment_relevant=True,
        published_at="2023-01-01T00:00:00",
        event_type="other",
        model_used="gpt-4",
        prompt_version="1.0",
        processing_timestamp="2023-01-01T00:00:00",
        article_hash="abc"
    )
    assert output.schema_version == "2.0"
    
    # Invalid URL
    with pytest.raises(ValidationError):
        OutputSchema(
            source="test",
            title="Test",
            url="ftp://example.com", # Schema requires http/https
            summary="Summary",
            investment_relevant=True
        )

def test_raw_ingestion_output():
    raw = RawIngestionOutput(
        source="test",
        title="Test",
        url="https://example.com",
        published_at=None,
        raw_text_length=100,
        raw_text_preview="Preview",
        http_status=200
    )
    assert raw.http_status == 200
