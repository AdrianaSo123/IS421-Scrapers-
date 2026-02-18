#!/bin/bash
set -e

# Setup
OUTPUT_DIR="verification_data"
DEDUP_FILE="verification_data/processed_urls.json"
rm -rf $OUTPUT_DIR
mkdir -p $OUTPUT_DIR

echo "--- 1. Running Unit Tests ---"
pytest tests

echo "--- 2. TechCrunch Raw Ingestion (Run 1) ---"
# We need to point dedup store to a temp location or just accept default. 
# Default is ./data/processed_urls.json.
# I'll let it use default but clear it first.
rm -f ./data/processed_urls.json

# Run 1 (Normal Mode for Determinism)
ai-techcrunch --limit 3 --output $OUTPUT_DIR/run1_norm
mv $OUTPUT_DIR/run1_norm/techcrunch_data.jsonl $OUTPUT_DIR/tc_run1.jsonl

echo "--- 3. TechCrunch Ingestion (Run 2 - Cleanup State) ---"
rm -f ./data/processed_urls.json
ai-techcrunch --limit 3 --output $OUTPUT_DIR/run2_norm
mv $OUTPUT_DIR/run2_norm/techcrunch_data.jsonl $OUTPUT_DIR/tc_run2.jsonl

echo "--- 4. Verify Determinism (TechCrunch - Processed) ---"
python3 verify_determinism.py $OUTPUT_DIR/tc_run1.jsonl $OUTPUT_DIR/tc_run2.jsonl

echo "--- 5. Deduplication Verification ---"
# Start with fresh state
rm -f ./data/processed_urls.json
# Run 1
ai-techcrunch --limit 2 --output $OUTPUT_DIR/dedup_test --raw
# Run 2 (Should skip processed and fetch next 2 unique)
ai-techcrunch --limit 2 --output $OUTPUT_DIR/dedup_test --raw
# Verify no duplicates in the file
python3 audit_output.py $OUTPUT_DIR/dedup_test/techcrunch_data.jsonl

echo "--- 6. Hacker News Raw Ingestion & Audit ---"
rm -f ./data/processed_urls.json
ai-hn --limit 20 --output $OUTPUT_DIR/hn --raw
python3 audit_output.py $OUTPUT_DIR/hn/hackernews_data.jsonl

echo "--- All Verification Checks Passed ---"
