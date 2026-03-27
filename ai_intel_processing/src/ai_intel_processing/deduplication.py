import hashlib
import json
import os
import logging
from typing import Set, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from .utils import setup_logger, log_struct

logger = setup_logger("ai_intel_processing.deduplication")

class DeduplicationStore:
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join(os.environ.get("DATA_DIR", "./data"), "processed_urls.json")
        self.storage_path = storage_path
        self.seen_hashes: Set[str] = set()
        self._load_store()

    def _normalize_url(self, url: str) -> str:
        """
        Normalizes a URL for consistent hashing.
        - Lowercases scheme and netloc
        - Removes tracking parameters (utm_*, etc.)
        - Removes trailing slashes
        - Drops fragment
        """
        parsed = urlparse(url)
        
        # Strip utm_ params from query
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = [(k, v) for k, v in query_params if not k.lower().startswith('utm_')]
        new_query = urlencode(filtered_query)
        
        # Strip trailing slash from path
        new_path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path
        
        normalized = urlunparse((
            parsed.scheme.lower(), 
            parsed.netloc.lower(), 
            new_path, 
            parsed.params, 
            new_query, 
            "" # Drop fragment
        ))
        return normalized

    def _compute_hash(self, url: str) -> str:
        """Computes SHA-256 hash of normalized URL."""
        normalized = self._normalize_url(url)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _load_store(self):
        """Loads seen hashes from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.seen_hashes = set(data.get("hashes", []))
                log_struct(logger, logging.INFO, "Loaded deduplication store", count=len(self.seen_hashes))
            except Exception as e:
                log_struct(logger, logging.ERROR, "Failed to load deduplication store", error=str(e))
                # Start fresh if corrupted
                self.seen_hashes = set()
        else:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def _save_store(self):
        """Saves seen hashes to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump({"hashes": list(self.seen_hashes)}, f)
        except Exception as e:
            log_struct(logger, logging.ERROR, "Failed to save deduplication store", error=str(e))

    def is_processed(self, url: str) -> bool:
        """Checks if a URL has already been processed."""
        url_hash = self._compute_hash(url)
        return url_hash in self.seen_hashes

    def mark_processed(self, url: str):
        """Marks a URL as processed and persists to disk."""
        url_hash = self._compute_hash(url)
        if url_hash not in self.seen_hashes:
            self.seen_hashes.add(url_hash)
            self._save_store()
            log_struct(logger, logging.DEBUG, "Marked URL as processed", url=url, hash=url_hash)
