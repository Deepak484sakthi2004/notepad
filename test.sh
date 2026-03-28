#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  NoteSpace — test runner
#  Usage:  ./test.sh          (all tests)
#          ./test.sh unit     (unit tests only)
#          ./test.sh int      (integration tests only)
#          ./test.sh -k name  (filter by test name)
# ─────────────────────────────────────────────────────────────────────────────
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"

cd "$BACKEND"
[[ -d .venv ]] || { echo "No .venv found. Run setup.sh first."; exit 1; }
source .venv/bin/activate

case "${1:-all}" in
    unit)  python -m pytest tests/unit/ -v --tb=short ;;
    int)   python -m pytest tests/integration/ -v --tb=short ;;
    all|-k|*)
        python -m pytest tests/ -v --tb=short "$@"
        ;;
esac
