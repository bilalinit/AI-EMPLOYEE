#!/bin/bash
# PM2 Stop Script for AI Employee
# This script stops AI Employee processes managed by PM2
#
# Usage:
#   ./stop_pm2.sh          # Stop local environment (default)
#   ./stop_pm2.sh local    # Stop local environment
#   ./stop_pm2.sh cloud    # Stop cloud environment
#   ./stop_pm2.sh all      # Stop all environments

set -e

# Get environment (default: local)
ENVIRONMENT="${1:-local}"

echo "========================================="
echo "AI Employee - PM2 Stop ($ENVIRONMENT)"
echo "========================================="
echo ""

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 is not installed!"
    exit 1
fi

# Stop based on environment
if [[ "$ENVIRONMENT" == "all" ]]; then
    echo "🛑 Stopping ALL AI Employee processes..."
    pm2 stop ai-employee-local ai-employee-cloud ai-employee-dedup-api 2>/dev/null || true
elif [[ "$ENVIRONMENT" == "cloud" ]]; then
    echo "🛑 Stopping AI Employee Cloud (orchestrator + dedup API)..."
    pm2 stop ai-employee-cloud ai-employee-dedup-api 2>/dev/null || true
elif [[ "$ENVIRONMENT" == "local" ]]; then
    echo "🛑 Stopping AI Employee Local (watchdog + dedup API)..."
    pm2 stop ai-employee-local ai-employee-dedup-api 2>/dev/null || true
else
    echo "🛑 Stopping AI Employee ($ENVIRONMENT)..."
    pm2 stop "ai-employee-${ENVIRONMENT}" 2>/dev/null || true
fi

echo ""
echo "✅ AI Employee processes stopped!"
echo ""
echo "Process status:"
pm2 list
echo ""

if [[ "$ENVIRONMENT" != "all" ]]; then
    echo "To restart: ./start_pm2.sh $ENVIRONMENT"
else
    echo "To restart: ./start_pm2.sh [local|cloud]"
fi
echo ""
