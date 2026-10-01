#!/bin/sh
echo "=== SINHRONIZACIJA IPHONE ČVORA ==="
git pull --rebase origin dev
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
PYTHONPATH=. pytest tests/
echo "=== STATUS: SPREMAN ==="
