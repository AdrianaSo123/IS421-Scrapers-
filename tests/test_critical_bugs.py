import pytest
from ai_intel_processing.schema import OutputSchema
from pydantic import ValidationError

def test_output_schema_url_validator_returns_value():
    """
    Verifies that the URL validator returns the value and doesn't swallow it (returning None).
    """
    url = "https://techcrunch.com/article"
    data = {
        "source": "techcrunch",
        "title": "Test Title",
        "url": url,
        "content": "Content",
        "published_at": None,
        "summary": "Summary",
        "investment_relevant": True,
        "event_type": "other",
        "model_used": "test",
        "prompt_version": "0.0",
        "processing_timestamp": "2023-01-01",
        "article_hash": "hash"
    }
    # If validator returns None, this will likely fail validation or result in None url if allowed
    model = OutputSchema(**data)
    assert model.url == url
    assert model.url is not None

def test_output_schema_url_validator_rejects_invalid():
    data = {
        "source": "techcrunch",
        "title": "Test Title",
        "url": "ftp://bad-url.com",
        "summary": "Summary",
        "investment_relevant": True
    }
    with pytest.raises(ValidationError):
        OutputSchema(**data)
