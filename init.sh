#!/usr/bin/env bash
# AI Tutor — startup script.
# Installs dependencies, runs verification, prints the start command.
# If verification fails, STOP and fix the baseline before doing anything else.

set -uo pipefail

# ---------------------------------------------------------------------------
# Resolve the project virtualenv. Created on first run; never committed.
# Windows puts binaries in Scripts/, POSIX in bin/.
# ---------------------------------------------------------------------------
VENV=.venv
if [ -x "$VENV/Scripts/python.exe" ]; then PY="$VENV/Scripts/python.exe"
elif [ -x "$VENV/bin/python" ];      then PY="$VENV/bin/python"
else
  printf 'Creating virtualenv in %s ...
' "$VENV"
  python -m venv "$VENV" || python3 -m venv "$VENV"
  if [ -x "$VENV/Scripts/python.exe" ]; then PY="$VENV/Scripts/python.exe"; else PY="$VENV/bin/python"; fi
fi

# ---------------------------------------------------------------------------
# Edit these three when the stack changes.
# ---------------------------------------------------------------------------
INSTALL_CMD='"$PY" -m pip install -q -r backend/requirements.txt && npm --prefix frontend install --no-fund --no-audit'
VERIFY_CMD='"$PY" -m pytest backend/tests -q && npm --prefix frontend run build'
START_CMD="cloudflared tunnel --url http://localhost:8000   # terminal 1 (backend owner only)
$PY -m uvicorn app.main:app --reload --port 8000 --app-dir backend   # terminal 2
npm --prefix frontend run dev                                        # terminal 3"
# ---------------------------------------------------------------------------

BOLD=$'\033[1m'; RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; OFF=$'\033[0m'
step() { printf '\n%s==> %s%s\n' "$BOLD" "$1" "$OFF"; }

step "Working directory"
pwd

step "Environment check"
if [ ! -f .env ]; then
  printf '%s.env is missing.%s Copy .env.example to .env and fill in DATABASE_URL,\n' "$YELLOW" "$OFF"
  printf 'GLM_API_KEY and SARVAM_API_KEY before running the app.\n'
fi

step "Installing dependencies"
if ! eval "$INSTALL_CMD"; then
  printf '\n%sInstall failed.%s Fix this before touching any feature.\n' "$RED" "$OFF"
  exit 1
fi

step "Verifying"
if ! eval "$VERIFY_CMD"; then
  printf '\n%sVERIFICATION FAILED.%s The baseline is broken.\n' "$RED" "$OFF"
  printf 'Do not start a feature. Fix the baseline first, then re-run ./init.sh\n'
  exit 1
fi
printf '\n%sVerification passed.%s\n' "$GREEN" "$OFF"

step "Start command"
printf '%s\n' "$START_CMD"

if [ "${RUN_START_COMMAND:-0}" = "1" ]; then
  step "Starting backend (frontend and tunnel must be started separately)"
  exec "$PY" -m uvicorn app.main:app --reload --port 8000 --app-dir backend
fi
