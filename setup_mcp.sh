#!/bin/bash

# setup_mcp.sh - Automates Claude Desktop MCP configuration for the Capital Intelligence Engine

# Detect OS
OS_TYPE="$(uname)"
if [ "$OS_TYPE" != "Darwin" ]; then
    echo "❌ Error: This script is currently only optimized for macOS (Claude Desktop)."
    exit 1
fi

PROJECT_ROOT="$(pwd)"
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
TEMPLATE_FILE="$PROJECT_ROOT/claude_desktop_config.template.json"

echo "🚀 Starting MCP Setup for: $PROJECT_ROOT"

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "⚠️  Warning: 'docker' command not found in PATH. Make sure Docker Desktop is installed."
fi

# Ensure Claude config directory exists
mkdir -p "$CLAUDE_CONFIG_DIR"

# Backup existing config if it exists
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    echo "📦 Backing up existing Claude configuration to: ${CLAUDE_CONFIG_FILE}.bak"
    cp "$CLAUDE_CONFIG_FILE" "${CLAUDE_CONFIG_FILE}.bak"
fi

# Generate new config from template
echo "📝 Generating new configuration from template..."
# Use sed to replace {{PROJECT_ROOT}} with the actual absolute path
# We use a different delimiter (|) because paths contain slashes
sed "s|{{PROJECT_ROOT}}|$PROJECT_ROOT|g" "$TEMPLATE_FILE" > "$CLAUDE_CONFIG_FILE"

echo "✅ Success! Claude Desktop configuration updated."
echo "💡 Please RESTART Claude Desktop (Cmd+Q and reopen) to apply changes."
echo "🔨 Then look for the Hammer icon in the bottom right of the chat box."
