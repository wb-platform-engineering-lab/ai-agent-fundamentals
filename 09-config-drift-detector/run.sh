#!/bin/bash
# config-drift-detector — run script
# Shows how to run this agent manually and how to schedule it.

set -e

echo "=== config-drift-detector ==="
echo ""

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

# Run the drift check
python3 agent.py

echo ""
echo "=== To schedule this as a cron job ==="
echo "Run: crontab -e"
echo "Add: 0 * * * * cd $(pwd) && python3 agent.py >> drift.log 2>&1"
echo "(runs every hour)"
