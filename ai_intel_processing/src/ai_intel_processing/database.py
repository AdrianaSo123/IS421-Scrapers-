import sqlite3
import json
import logging
from typing import List, Optional, Any, Dict
from datetime import datetime
import os

from .schema import OutputSchema
from .utils import setup_logger, log_struct

logger = setup_logger("ai_intel_processing.database")

class DatabaseStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.environ.get("DB_PATH", "./data/scrapers.db")
        self.db_path = db_path
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes the SQLite schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Table for runs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        completed_at TEXT,
                        status TEXT NOT NULL,
                        items_processed INTEGER DEFAULT 0,
                        errors INTEGER DEFAULT 0
                    )
                """)
                
                # Table for processed articles/products
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        canonical_key TEXT UNIQUE NOT NULL,
                        source TEXT NOT NULL,
                        title TEXT NOT NULL,
                        url TEXT NOT NULL,
                        published_at TEXT,
                        company TEXT,
                        investment_relevant BOOLEAN,
                        event_type TEXT,
                        summary TEXT,
                        inserted_at TEXT NOT NULL,
                        raw_data JSON
                    )
                """)
                
                # Index for deduplication lookup
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_canonical_key ON articles(canonical_key)
                """)
                
                conn.commit()
                log_struct(logger, logging.DEBUG, "Initialized SQLite schema", db_path=self.db_path)
        except Exception as e:
            log_struct(logger, logging.ERROR, "Failed to initialize database", error=str(e))
            raise

    def start_run(self, source: str) -> int:
        """Records a new scraper run."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO runs (source, started_at, status) VALUES (?, ?, ?)",
                (source, now, "running")
            )
            conn.commit()
            return cursor.lastrowid

    def finish_run(self, run_id: int, status: str, items_processed: int, errors: int):
        """Marks a run as finished."""
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE runs 
                SET completed_at = ?, status = ?, items_processed = ?, errors = ?
                WHERE id = ?
                """,
                (now, status, items_processed, errors, run_id)
            )
            conn.commit()

    def is_processed(self, canonical_key: str) -> bool:
        """Checks if an article has been processed based on canonical key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM articles WHERE canonical_key = ?", (canonical_key,))
            return cursor.fetchone() is not None

    def save_article(self, canonical_key: str, article: OutputSchema):
        """Saves a processed article to the database. Overwrites if it exists."""
        now = datetime.utcnow().isoformat()
        raw_data = article.model_dump_json()
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO articles 
                (canonical_key, source, title, url, published_at, company, investment_relevant, event_type, summary, inserted_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_key) DO UPDATE SET
                    title=excluded.title,
                    published_at=excluded.published_at,
                    company=excluded.company,
                    investment_relevant=excluded.investment_relevant,
                    event_type=excluded.event_type,
                    summary=excluded.summary,
                    raw_data=excluded.raw_data
                """,
                (
                    canonical_key,
                    article.source,
                    article.title,
                    article.url,
                    article.published_at,
                    article.company,
                    article.investment_relevant,
                    article.event_type,
                    article.summary,
                    now,
                    raw_data
                )
            )
            conn.commit()
