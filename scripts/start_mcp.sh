#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$DIR")"

# Load environment
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Preflight check: binary exists
MCP_BIN="/Library/Frameworks/Python.framework/Versions/3.11/bin/ai-capital-mcp"
if [ ! -x "$MCP_BIN" ]; then
    if command -v ai-capital-mcp &> /dev/null; then
        MCP_BIN="ai-capital-mcp"
    else
        echo "FATAL ERROR: ai-capital-mcp command could not be found." >&2
        echo "Please ensure the virtual environment is active or the package is installed in your python path." >&2
        exit 1
    fi
fi

# Launch
exec "$MCP_BIN"
