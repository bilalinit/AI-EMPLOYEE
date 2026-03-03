#!/bin/bash
# AI Employee Orchestrator Launcher
# Start the orchestrator which runs all watchers and monitors for tasks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  AI Employee Orchestrator Launcher"
echo "=========================================="
echo ""
echo "Vault: ../AI_Employee_Vault"
echo "Scripts: $SCRIPT_DIR"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed"
    echo "Install from: https://github.com/astral-sh/uv"
    exit 1
fi

# Check if claude is installed
if ! command -v claude &> /dev/null; then
    echo "ERROR: claude is not installed"
    echo "Install from: https://claude.com/product/claude-code"
    exit 1
fi

echo "Starting orchestrator..."
echo "Press Ctrl+C to stop"
echo ""

# Run the orchestrator
uv run python orchestrator.py
