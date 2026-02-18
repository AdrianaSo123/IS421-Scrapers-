import sys
import json
from collections import Counter
from urllib.parse import urlparse

def audit_output(filepath: str):
    print(f"Auditing {filepath}...")
    
    records = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    total_records = len(records)
    unique_urls = set()
    sources = Counter()
    short_titles = 0
    short_text = 0
    duplicates = 0
    
    for i, record in enumerate(records):
        url = record.get('url')
        if not url:
            print(f"❌ Record {i} missing URL")
            continue
            
        # URL Validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
             print(f"❌ Record {i} invalid URL: {url}")

        if url in unique_urls:
            duplicates += 1
            print(f"⚠️ Duplicate URL found: {url}")
        unique_urls.add(url)
        
        sources[record.get('source', 'unknown')] += 1
        
        # Title Validation
        title = record.get('title', '')
        if len(title) < 10:
            short_titles += 1
            print(f"⚠️ Short title in record {i}: '{title}'")
            
        # Raw Text Validation (if present)
        raw_len = record.get('raw_text_length')
        if raw_len is not None and raw_len < 500:
            short_text += 1
            print(f"⚠️ Short raw text in record {i}: {raw_len} chars")

    # Summary
    print("\n--- Audit Summary ---")
    print(f"Total Records: {total_records}")
    print(f"Unique URLs: {len(unique_urls)}")
    print(f"Duplicates: {duplicates}")
    print(f"Source Distribution: {dict(sources)}")
    print(f"Title Warnings (<10 chars): {short_titles}")
    print(f"Text Warnings (<500 chars): {short_text}")
    
    if duplicates > 0:
        print("❌ FAILED: Duplicates found.")
        sys.exit(1)
        
    print("✅ Audit Complete.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python audit_output.py <output.jsonl>")
        sys.exit(1)
        
    audit_output(sys.argv[1])
