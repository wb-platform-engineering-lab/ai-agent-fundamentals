#!/bin/bash
set -e

echo "=== doc-oracle demo ==="
echo ""

# Install chromadb if not present
pip install chromadb -q

# Ingest the sample docs
echo "Step 1: Ingesting sample docs..."
python memory.py --ingest docs/
echo ""

# Ask a question
echo "Step 2: Asking a question..."
echo ""
python agent.py "how do we rollback a failed deployment?"
echo ""
echo "=== demo complete ==="
echo ""
echo "Try your own questions:"
echo "  python agent.py 'what are the severity levels for incidents?'"
echo "  python agent.py 'what happens during a freeze window?'"
echo "  python agent.py  # interactive mode"
