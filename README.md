# Capital Intelligence Engine

A robust, modular, and deterministic AI news ingestion system designed to extract high-value capital event data and expose it securely to AI Agents via the Model Context Protocol (MCP).

## Architecture

The system consists of **two distinct operational halves**, powered by four modular Python packages:

### 1. The Background Scrapers
Automated background Docker containers that run continuously on a schedule. They fetch, process, and store AI-focused market events into a centralized local database (`scrapers.db`).

1.  **`ai_techcrunch_ingest`**: Fetches and extracts AI news from TechCrunch via RSS and HTML scraping.
2.  **`ai_hackernews_ingest`**: Monitors Hacker News for AI-related stories using the Firebase API and keyword filtering.
3.  **`ai_intel_processing`**: The shared intelligence core that handles strict Pydantic schema validation, data normalization, database structuring, and LLM-based analysis (via OpenAI).

### 2. The MCP Tool Server
The bridge that allows LLMs to interact with your data:

4. **`ai_capital_mcp`**: A native Model Context Protocol (MCP) server built with FastMCP. It securely exposes your `scrapers.db` data as explicitly defined tools to AI assistants like Claude Desktop. It provides tools to read the latest events, search companies, summarize broad market trends, and even command the scrapers to fetch fresh data on-demand.

---

## Installation & Setup

We recommend running the entire system via Docker to ensure environments remain predictable and isolated.

### Local Development (Python)
If developing locally, install the packages in editable mode:

```bash
pip install -e ./ai_intel_processing
pip install -e ./ai_techcrunch_ingest
pip install -e ./ai_hackernews_ingest
pip install -e ./ai_capital_mcp
```

### Background Scrapers (Docker)
The scrapers are orchestrated using Docker Compose (or standalone `docker run` commands) that mount a persistent `./data` volume for the `scrapers.db` database.

### Claude Desktop Integration (MCP)
To give Claude Desktop access to your Capital Intelligence database, you can use our automated setup script:

```bash
# Automatically detects paths and updates your Claude configuration
./setup_mcp.sh
```

Alternatively, you can manually edit your `claude_desktop_config.json` (Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "capital-intelligence": {
      "command": "/usr/local/bin/docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "OPENAI_API_KEY=your_key_here",
        "-v",
        "/absolute/path/to/your/data:/app/data",
        "ai-capital-mcp:latest"
      ]
    }
  }
}
```

## Principles

-   **Determinism**: LLM output uses `temperature=0` and `seed=42` to minimize variance.
-   **Capital Focus**: Optimized to selectively identify **Funding, Acquisitions, Partnerships, Contracts**, and **Restructuring** events, filtering out generic noise.
-   **Explicit Schemas**: Enforces Pydantic Schema v2.0 for all LLM extraction boundaries.
-   **Thread Safety**: Robust SQLite connection handling allows the scrapers to write to `scrapers.db` seamlessly while the MCP server reads from it concurrently.
