import click
import json
import os
from .rss import fetch_feed
from .scraper import fetch_article, extract_article_data
from ai_intel_processing.processing import IntelProcessor
from ai_intel_processing.deduplication import DeduplicationStore
from ai_intel_processing.utils import setup_logger, log_struct
import logging

logger = setup_logger("ai_techcrunch_ingest.cli")

@click.command()
@click.option('--limit', default=10, help='Number of articles to fetch.')
@click.option('--output', default='./output', help='Output directory for JSONL files.')
@click.option('--raw', is_flag=True, help='Output raw ingestion data without LLM processing.')
def main(limit, output, raw):
    """
    TechCrunch AI Ingestion CLI.
    """
    log_struct(logger, logging.INFO, "Starting TechCrunch ingestion", limit=limit, output_dir=output, raw_mode=raw)
    
    # Ensure output directory exists
    os.makedirs(output, exist_ok=True)
    output_file = os.path.join(output, "techcrunch_data.jsonl")
    
    entries = fetch_feed()
    dedup = DeduplicationStore()
    processor = IntelProcessor() # API key would be passed here via env var or config
    
    count = 0
    with open(output_file, 'a') as f: # Append mode for now
        for entry in entries:
            if count >= limit:
                break
            
            url = entry.link
            
            if dedup.is_processed(url):
                log_struct(logger, logging.DEBUG, "Skipping processed URL", url=url)
                continue

            log_struct(logger, logging.INFO, "Processing entry", title=entry.title)
            
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
                f.write(output_data.model_dump_json() + '\n')
                dedup.mark_processed(url)
                count += 1
                
            elif html:
                # Normal mode
                article = extract_article_data(html, url)
                if article:
                    # Enrich with RSS title if extraction failed
                    if entry.title and (not article.title or article.title == "Unknown Title"):
                        article.title = entry.title
                        
                    # Enrich with Intel Processor
                    output_data = processor.process_article(article)
                    
                    # Write to JSONL
                    f.write(output_data.model_dump_json() + '\n')
                    dedup.mark_processed(url)
                    count += 1
            
    log_struct(logger, logging.INFO, "Ingestion complete", total_processed=count)

if __name__ == "__main__":
    main()
