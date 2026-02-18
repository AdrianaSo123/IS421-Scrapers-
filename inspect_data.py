import json
import sys

def inspect_records(filepath):
    print(f"Inspecting {filepath}...")
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines[:5]): # Inspect first 5
            data = json.loads(line)
            print(f"\n--- Record {i+1} ---")
            print(f"Source: {data.get('source')}")
            print(f"Title: {data.get('title')}")
            print(f"Event Type: {data.get('event_type')}")
            print(f"Company: {data.get('company')}")
            print(f"Funding: {data.get('funding_amount')} ({data.get('funding_stage')})")
            print(f"Summary: {data.get('summary')}")
            print(f"Relevant: {data.get('investment_relevant')}")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

inspect_records("verification_data/run1/techcrunch_data.jsonl")
