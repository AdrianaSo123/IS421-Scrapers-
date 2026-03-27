import click
import json
import os
from typing import Optional
from .rss import fetch_feed
from .scraper import fetch_article, extract_article_data
from ai_intel_processing.processing import IntelProcessor
from ai_intel_processing.database import DatabaseStore
from ai_intel_processing.deduplication import DeduplicationStore
from ai_intel_processing.utils import setup_logger, log_struct
import logging

from ai_intel_processing.schema import IngestionResult

logger = setup_logger("ai_techcrunch_ingest.cli")

def run_ingestion(limit: int, output: str, raw: bool, db_session: Optional[DatabaseStore] = None, job_id: Optional[str] = None) -> IngestionResult:
    log_struct(logger, logging.INFO, "Starting TechCrunch ingestion", limit=limit, output_dir=output, raw_mode=raw, job_id=job_id)
    
    # We still ensure output dir exists for raw mode if needed
    os.makedirs(output, exist_ok=True)
    
    entries = fetch_feed()
    db = db_session if db_session else DatabaseStore()
    dedup = DeduplicationStore() # keep for hashing logic
    processor = IntelProcessor() # API key would be passed here via env var or config
    
    run_id = db.start_run("techcrunch")
    count = 0
    errors = 0
    for entry in entries:
        if count >= limit:
            break
        
        url = entry.link
        canonical_key = dedup._compute_hash(url)
        
        if db.is_processed(canonical_key):
            log_struct(logger, logging.DEBUG, "Skipping processed URL", url=url)
            continue

        log_struct(logger, logging.INFO, "Processing entry", title=entry.title, job_id=job_id)
        
        html, status_code = fetch_article(url)
        
        if raw:
            # Raw mode: normalize to cleaned text length (per requirements)
            from ai_intel_processing.schema import RawIngestionOutput
            
            raw_text_length = 0
            raw_preview = ""
            
            if html:
                 # We must extract the text to measure it properly
                article = extract_article_data(html, url)
                if article and article.content:
                    raw_text_length = len(article.content)
                    raw_preview = article.content[:500]
                else:
                    # Fallback if extraction fails
                    raw_text_length = len(html)
                    raw_preview = html[:500]

            output_data = RawIngestionOutput(
                source="techcrunch",
                title=entry.title,
                url=url,
                published_at=entry.published if hasattr(entry, 'published') else None,
                raw_text_length=raw_text_length,
                raw_text_preview=raw_preview,
                http_status=status_code
            )
            output_file = os.path.join(output, "techcrunch_data.jsonl")
            with open(output_file, 'a') as f:
                f.write(output_data.model_dump_json() + '\n')
                
            db.mark_processed_raw(canonical_key, "techcrunch", entry.title, url)
            count += 1
            
        elif html:
            # Normal mode
            article = extract_article_data(html, url)
            if article:
                # Enrich with RSS title if extraction failed
                if entry.title and (not article.title or article.title == "Unknown Title"):
                    article.title = entry.title
                    
                # Enrich with Intel Processor
                try:
                    output_data = processor.process_article(article)
                    db.save_article(canonical_key, output_data)
                    
                    output_file = os.path.join(output, "techcrunch_data.jsonl")
                    with open(output_file, 'a') as f:
                        f.write(output_data.model_dump_json() + '\n')
                        
                    count += 1
                except Exception as e:
                    log_struct(logger, logging.ERROR, "Failed to process article", url=url, error=str(e))
                    errors += 1
            else:
                errors += 1
        else:
            errors += 1

    db.finish_run(run_id, "success", count, errors)
    log_struct(logger, logging.INFO, "Ingestion complete", total_processed=count, job_id=job_id)
    return IngestionResult(status="success", processed=count, errors=errors)

@click.command()
@click.option('--limit', default=10, help='Number of articles to fetch.')
@click.option('--output', default='./output', help='Output directory for JSONL files.')
@click.option('--raw', is_flag=True, help='Output raw ingestion data without LLM processing.')
def main(limit, output, raw):
    """
    TechCrunch AI Ingestion CLI.
    """
    run_ingestion(limit, output, raw)

if __name__ == "__main__":
    main()
