import click
import json
import os
import time
from datetime import datetime
from .client import fetch_top_stories, fetch_story_details
from .filter import is_ai_story
from .scraper import fetch_content_generic
from ai_intel_processing.schema import NewsArticle
from ai_intel_processing.processing import IntelProcessor
from ai_intel_processing.deduplication import DeduplicationStore
from ai_intel_processing.utils import setup_logger, log_struct
import logging

logger = setup_logger("ai_hackernews_ingest.cli")

@click.command()
@click.option('--limit', default=20, help='Number of stories to check (not necessarily output).')
@click.option('--output', default='./output', help='Output directory for JSONL files.')
@click.option('--raw', is_flag=True, help='Output raw ingestion data without LLM processing.')
def main(limit, output, raw):
    """
    Hacker News AI Ingestion CLI.
    """
    log_struct(logger, logging.INFO, "Starting Hacker News ingestion", limit=limit, output_dir=output, raw_mode=raw)
    
    os.makedirs(output, exist_ok=True)
    output_file = os.path.join(output, "hackernews_data.jsonl")
    
    top_ids = fetch_top_stories(limit=limit * 2) # Fetch more to allow for filtering
    dedup = DeduplicationStore()
    processor = IntelProcessor()
    
    count = 0
    with open(output_file, 'a') as f:
        for story_id in top_ids:
            if count >= limit:
                break
                
            story = fetch_story_details(story_id)
            if not story:
                continue
                
            title = story.get("title", "")
            if is_ai_story(title):
                log_struct(logger, logging.INFO, "Found AI story", title=title, id=story_id)
                
                url = story.get("url")
                
                # Deduplication check
                check_url = url if url else f"https://news.ycombinator.com/item?id={story_id}"
                if dedup.is_processed(check_url):
                    log_struct(logger, logging.DEBUG, "Skipping processed URL", url=check_url)
                    continue

                content = ""
                raw_text = ""
                status_code = 200 # Default for non-fetched internal stories
                
                if url:
                    content, raw_text, status_code = fetch_content_generic(url)
                elif "text" in story:
                    content = story["text"] # HN internal discussion
                    raw_text = content
                    status_code = 200
                
                if not content:
                    log_struct(logger, logging.WARNING, "No content found for story", id=story_id, title=title)
                    continue

                if raw:
                    from ai_intel_processing.schema import RawIngestionOutput
                    
                    raw_length = len(raw_text)
                    raw_preview = raw_text[:500] if raw_text else ""
                    
                    output_data = RawIngestionOutput(
                        source="hackernews",
                        title=title,
                        url=check_url,
                        published_at=datetime.utcfromtimestamp(story.get("time", time.time())).isoformat(),
                        raw_text_length=raw_length,
                        raw_text_preview=raw_preview,
                        http_status=status_code
                    )
                    f.write(output_data.model_dump_json() + '\n')
                    dedup.mark_processed(check_url)
                    count += 1
                else:
                    # Create NewsArticle
                    try:
                        article = NewsArticle(
                            source="hackernews",
                            title=title,
                            url=check_url,
                            published_at=datetime.utcfromtimestamp(story.get("time", time.time())),
                            content=content,
                            raw_metadata={
                                "hn_score": story.get("score"),
                                "comment_count": story.get("descendants"),
                                "by": story.get("by"),
                                "id": story_id
                            }
                        )
                        
                        output_data = processor.process_article(article)
                        f.write(output_data.model_dump_json() + '\n')
                        dedup.mark_processed(check_url)
                        count += 1
                        
                    except Exception as e:
                        log_struct(logger, logging.ERROR, "Failed to process story", id=story_id, error=str(e))
            else:
                log_struct(logger, logging.DEBUG, "Skipping non-AI story", title=title)

    log_struct(logger, logging.INFO, "Ingestion complete", total_processed=count)

if __name__ == "__main__":
    main()
