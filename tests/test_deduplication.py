import pytest
import os
import json
from ai_intel_processing.deduplication import DeduplicationStore

TEST_STORE_PATH = "./tests/data/test_dedup.json"

@pytest.fixture
def dedup_store():
    if os.path.exists(TEST_STORE_PATH):
        os.remove(TEST_STORE_PATH)
    store = DeduplicationStore(storage_path=TEST_STORE_PATH)
    yield store
    if os.path.exists(TEST_STORE_PATH):
        os.remove(TEST_STORE_PATH)

def test_url_normalization(dedup_store):
    url1 = "https://Example.com/Foo?utm_source=bar"
    url2 = "https://example.com/foo?utm_source=bar"
    
    norm1 = dedup_store._normalize_url(url1)
    norm2 = dedup_store._normalize_url(url2)
    
    assert norm1 == "https://example.com/Foo"
    assert norm2 == "https://example.com/foo"

def test_hashing_consistency(dedup_store):
    url = "https://techcrunch.com/article"
    hash1 = dedup_store._compute_hash(url)
    hash2 = dedup_store._compute_hash(url)
    assert hash1 == hash2

def test_persistence(dedup_store):
    url = "https://example.com/persistent"
    assert not dedup_store.is_processed(url)
    
    dedup_store.mark_processed(url)
    assert dedup_store.is_processed(url)
    
    # Reload from disk
    new_store = DeduplicationStore(storage_path=TEST_STORE_PATH)
    assert new_store.is_processed(url)
