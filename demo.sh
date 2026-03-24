#!/usr/bin/env bash
set -e

echo "====================================================="
echo "  Capital Intelligence Engine - Live Demo"
echo "====================================================="
echo ""
echo "[1/3] Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "[2/3] Running Live Ingestion (TechCrunch - 1 Article)..."
echo "This will fetch an article, extract the text, and use OpenAI to guarantee a structured output schema."
echo "-----------------------------------------------------"
ai-techcrunch --limit 1

echo ""
echo "[3/3] Inspecting Output in Database..."
echo "Here is the freshly extracted Capital Intelligence data:"
echo "-----------------------------------------------------"
sqlite3 data/scrapers.db "SELECT json_extract(raw_data, '$.title', '$.company', '$.event_type', '$.funding_amount', '$.summary') FROM articles ORDER BY inserted_at DESC LIMIT 1;" | while read -r line; do
    # Format the JSON array output from SQLite securely into readable text
    echo "$line" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    print(f"\n📰 Title:      {data[0]}")
    print(f"🏢 Company:    {data[1] if data[1] else \"N/A\"}")
    print(f"🎯 Event Type: {data[2]}")
    print(f"💰 Funding:    {data[3] if data[3] else \"N/A\"}")
    print(f"📝 Summary:    {data[4]}")
except Exception as e:
    print(line)
'
done

echo ""
echo "====================================================="
echo "  Demo Complete! Data successfully structured."
echo "====================================================="
