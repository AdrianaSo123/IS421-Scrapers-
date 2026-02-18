#!/bin/bash

# Load environment variables if needed (though Python handles .env)
# export OPENAI_API_KEY=...

echo "Starting Daily Ingestion Job..."
date

# 1. Run TechCrunch Ingestion
echo "Running TechCrunch Ingestion..."
ai-techcrunch --limit 20 --output ./data/ingestion_output

# 2. Run Hacker News Ingestion
# We fetch more here because we filter for AI content
echo "Running Hacker News Ingestion..."
ai-hn --limit 60 --output ./data/ingestion_output

echo "Ingestion Job Complete."
