import sys
import json
import hashlib
import argparse
from typing import List, Dict, Any

def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    records = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    return records

def get_deterministic_hash(record: Dict[str, Any], mode: str) -> str:
    """ Computes hash of record based on mode. """
    # Deep copy to avoid modifying original
    clean_record = record.copy()
    
    # Always remove timestamps that vary by execution time
    clean_record.pop('collected_at', None)
    clean_record.pop('processing_timestamp', None)
    clean_record.pop('metadata', None) 

    if mode == "ingestion":
        # Ingestion mode: only check source, url, title, content fields
        # Remove LLM outputs to isolate ingestion determinism
        keys_to_keep = {'source', 'url', 'title', 'content', 'published_at', 'raw_text_length', 'raw_text_preview', 'http_status'}
        clean_record = {k: v for k, v in clean_record.items() if k in keys_to_keep}
    
    # Sort keys for consistent JSON serialization
    serialized = json.dumps(clean_record, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def verify_determinism(file1: str, file2: str, mode: str):
    print(f"Comparing {file1} and {file2} in mode: {mode}...")
    
    records1 = load_jsonl(file1)
    records2 = load_jsonl(file2)
    
    if len(records1) != len(records2):
        print(f"❌ Record count mismatch: {len(records1)} vs {len(records2)}")
        sys.exit(1)
        
    hashes1 = [get_deterministic_hash(r, mode) for r in records1]
    hashes2 = [get_deterministic_hash(r, mode) for r in records2]
    
    mismatches = 0
    for i, (h1, h2) in enumerate(zip(hashes1, hashes2)):
        if h1 != h2:
            print(f"❌ Mismatch at index {i}")
            # Show diff
            r1 = records1[i]
            r2 = records2[i]
            # Simple diff
            keys = set(r1.keys()) | set(r2.keys())
            diffs = []
            for k in keys:
                if k in ['collected_at', 'processing_timestamp', 'metadata']: continue
                if r1.get(k) != r2.get(k):
                    diffs.append(f"{k}: {r1.get(k)} != {r2.get(k)}")
            print(f"   Diffs: {diffs}")
            mismatches += 1
            
    if mismatches == 0:
        print(f"✅ SUCCESS: Files are deterministically identical (ignoring timestamps) in {mode} mode.")
        sys.exit(0)
    else:
        print(f"❌ FAILED: {mismatches} mismatches found.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify output determinism.")
    parser.add_argument("file1", help="First output file")
    parser.add_argument("file2", help="Second output file")
    parser.add_argument("--mode", choices=["ingestion", "full"], default="full", help="Check mode: ingestion (raw fields only) or full (strict)")
    args = parser.parse_args()
    
    verify_determinism(args.file1, args.file2, args.mode)
