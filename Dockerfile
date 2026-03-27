FROM python:3.11-slim

WORKDIR /app

# Ensure curl and minimal build tools are available
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace
COPY . /app

# Install all sub-packages in editable mode
RUN pip install --no-cache-dir -e ./ai_intel_processing
RUN pip install --no-cache-dir -e ./ai_techcrunch_ingest
RUN pip install --no-cache-dir -e ./ai_hackernews_ingest
RUN pip install --no-cache-dir -e ./ai_capital_mcp

# Construct Data Directory Mount
RUN mkdir -p /app/data

# Environment overrides configuration
ENV DATA_DIR=/app/data
ENV DB_PATH=/app/data/scrapers.db

# Expose standard port for standard HTTP fallback if used later (FastMCP natively defaults to STDIO anyway)
EXPOSE 8000

# Executable command
CMD ["ai-capital-mcp"]
