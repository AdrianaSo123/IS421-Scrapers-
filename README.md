# Capital Intelligence Engine

A robust, modular, and deterministic AI news ingestion system designed to extract high-value capital event data.

## Architecture

The system consists of three modular Python packages:

1.  **`ai_techcrunch_ingest`**: Fetches and extracts AI news from TechCrunch via RSS and HTML scraping.
2.  **`ai_hackernews_ingest`**: Monitoring Hacker News for AI-related stories using the Firebase API and keyword filtering.
3.  **`ai_intel_processing`**: The shared intelligence core that handles schema validation, data normalization, and LLM-based analysis (OpenAI).

### Principles

-   **Determinism**: Ingestion is 100% deterministic. LLM output uses `temperature=0` and `seed=42` to minimize variance.
-   **Capital Focus**: Optimized to extract Funding, Acquisitions, Partnerships, and Contracts.
-   **Explicit Schemas**: Enforces Pydantic Schema v2.0 for all outputs.
-   **Traceability**: Every record includes `model_used`, `prompt_version`, and `article_hash`.

## Installation

The system is designed as a monorepo. Install the packages in editable mode:

```bash
pip install -e ai_intel_processing
pip install -e ai_techcrunch_ingest
pip install -e ai_hackernews_ingest
```

## Usage

### TechCrunch Ingestion

Fetch the latest AI articles from TechCrunch:

```bash
ai-techcrunch --limit 10 --output ./data
```

### Hacker News Ingestion

Fetch top AI stories from Hacker News:

```bash
ai-hn --limit 50 --output ./data
```

## Output Schema (v2.0)

All output files (`.jsonl`) conform to the Version 2.0 schema:

```json
{
  "schema_version": "2.0",
  "source": "techcrunch",
  "title": "Example Article",
  "url": "https://example.com/article",
  "published_at": "2026-02-18T10:00:00+00:00",
  "company": "Example AI Corp",
  "funding_amount": "$50M",
  "funding_stage": "Series A",
  "investors": ["VC Firm A"],
  "summary": "...",
  "investment_relevant": true,
  "event_type": "funding",
  "model_used": "gpt-4o-2024-08-06",
  "prompt_version": "2.0.0",
  "processing_timestamp": "2026-02-18T10:00:05.123456",
  "article_hash": "sha256...",
  "metadata": {...},
  "collected_at": "..."
}
```

### Event Types
- `funding`: VC rounds, IPOs, grants.
- `acquisition`: M&A activity.
- `partnership`: Strategic alliances.
- `contract`: Major customer deals.
- `restructuring`: Layoffs, exec changes.
- `other`: Product launches, research, generic news.

## Verification

To verify determinism between two runs:

```bash
python3 verify_determinism.py run1.jsonl run2.jsonl --mode full
```
