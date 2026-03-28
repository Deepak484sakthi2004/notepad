#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  NoteSpace — development launcher
#  Usage:  ./start.sh            (starts both backend + frontend)
#          ./start.sh backend    (backend only)
#          ./start.sh frontend   (frontend only)
# ─────────────────────────────────────────────────────────────────────────────
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

log()  { echo -e "${CYAN}[notespace]${NC} $*"; }
ok()   { echo -e "${GREEN}[notespace]${NC} $*"; }
warn() { echo -e "${YELLOW}[notespace]${NC} $*"; }
die()  { echo -e "${RED}[notespace] ERROR:${NC} $*"; exit 1; }

# ── pre-flight checks ─────────────────────────────────────────────────────────
check_services() {
    log "Checking PostgreSQL..."
    pg_isready -q 2>/dev/null || die "PostgreSQL is not running. Start it with: brew services start postgresql@14"
    ok "PostgreSQL is up"

    log "Checking Redis..."
    redis-cli ping &>/dev/null || die "Redis is not running. Start it with: brew services start redis"
    ok "Redis is up"
}

# ── backend ───────────────────────────────────────────────────────────────────
start_backend() {
    log "Starting Flask backend on http://localhost:5000 ..."
    cd "$BACKEND"

    [[ -f .env ]] || die ".env not found in backend/. Run setup.sh first."
    [[ -d .venv ]] || die ".venv not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"

    source .venv/bin/activate
    python run.py &
    BACKEND_PID=$!
    ok "Backend started (PID $BACKEND_PID)"
}

# ── frontend ──────────────────────────────────────────────────────────────────
start_frontend() {
    log "Starting Vite frontend on http://localhost:5173 ..."
    cd "$FRONTEND"

    [[ -d node_modules ]] || { log "Installing npm packages..."; npm install; }

    npm run dev &
    FRONTEND_PID=$!
    ok "Frontend started (PID $FRONTEND_PID)"
}

# ── cleanup on exit ───────────────────────────────────────────────────────────
cleanup() {
    echo ""
    log "Shutting down..."
    [[ -n "$BACKEND_PID" ]]  && kill "$BACKEND_PID"  2>/dev/null && ok "Backend stopped"
    [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null && ok "Frontend stopped"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── entry point ───────────────────────────────────────────────────────────────
case "${1:-both}" in
    backend)
        check_services
        start_backend
        wait "$BACKEND_PID"
        ;;
    frontend)
        start_frontend
        wait "$FRONTEND_PID"
        ;;
    both|*)
        check_services
        start_backend
        start_frontend
        echo ""
        ok "═══════════════════════════════════════════════════"
        ok "  Backend  →  http://localhost:5000"
        ok "  Frontend →  http://localhost:5173"
        ok "  API docs  →  http://localhost:5000/api/health"
        ok "═══════════════════════════════════════════════════"
        warn "Press Ctrl+C to stop both servers"
        wait
        ;;
esac
