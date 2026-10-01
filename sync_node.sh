#!/bin/sh
echo "=== SINHRONIZACIJA IPHONE ČVORA ==="
git stash -u >/dev/null 2>&1
git pull --rebase origin dev
git stash pop >/dev/null 2>&1
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
PYTHONPATH=. pytest tests/
echo "=== STATUS: SPREMAN ==="
