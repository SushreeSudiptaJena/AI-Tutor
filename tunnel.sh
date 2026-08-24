#!/usr/bin/env bash
# infra-005 -- expose the local backend to the team, and print the one line
# everyone else has to paste.
#
#     ./tunnel.sh
#
# The quick-tunnel URL is regenerated every time cloudflared starts, so it has
# to be reposted to the team channel on every restart. That is the whole reason
# this script exists: it waits for the URL, prints it in the exact form a
# teammate pastes into frontend/.env.local, and then stays in the foreground.
#
# Run the backend in another terminal first:
#     .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000 --app-dir backend

set -uo pipefail

PORT="${PORT:-8000}"
BOLD=$'\033[1m'; RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; OFF=$'\033[0m'

if ! command -v cloudflared >/dev/null 2>&1; then
  printf '%scloudflared is not on PATH.%s\n' "$RED" "$OFF"
  printf 'Windows, no admin rights needed:\n'
  printf '  curl -sL -o ~/bin/cloudflared.exe \\\n'
  printf '    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe\n'
  exit 1
fi

# Fail early with a useful message rather than tunnelling to nothing. A tunnel
# pointing at a dead port returns 502 to the whole team, which looks like the
# tunnel is broken when it is the backend that is down.
if ! curl -sf -o /dev/null --max-time 3 "http://localhost:$PORT/health"; then
  printf '%sNothing is answering on localhost:%s.%s\n' "$RED" "$PORT" "$OFF"
  printf 'Start the backend first, in another terminal:\n'
  printf '  .venv/Scripts/python.exe -m uvicorn app.main:app --port %s --app-dir backend\n' "$PORT"
  exit 1
fi

LOG="$(mktemp -t tunnel-XXXXXX.log)"
trap 'rm -f "$LOG"' EXIT

printf '%s==> Starting tunnel to localhost:%s%s\n' "$BOLD" "$PORT" "$OFF"
cloudflared tunnel --url "http://localhost:$PORT" > "$LOG" 2>&1 &
TUNNEL_PID=$!
trap 'kill $TUNNEL_PID 2>/dev/null; rm -f "$LOG"' EXIT INT TERM

URL=""
for _ in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1)
  [ -n "$URL" ] && break
  kill -0 $TUNNEL_PID 2>/dev/null || { printf '%scloudflared exited:%s\n' "$RED" "$OFF"; tail -20 "$LOG"; exit 1; }
  sleep 1
done

if [ -z "$URL" ]; then
  printf '%sNo tunnel URL after 30s.%s Last lines:\n' "$RED" "$OFF"
  tail -20 "$LOG"
  exit 1
fi

# cloudflared prints the URL as soon as it is assigned, which is a few seconds
# before the edge will actually route to it. Checking once here reported 000 on
# a tunnel that was fine -- so retry, and only complain if it stays down.
CODE=000
for _ in $(seq 1 10); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL/health")
  [ "$CODE" = "200" ] && break
  sleep 2
done

if [ "$CODE" = "200" ]; then
  printf '%s==> Tunnel is live and /health answered 200 through it.%s\n' "$GREEN" "$OFF"
else
  printf '%s==> Tunnel is up but /health returned %s through it.%s\n' "$YELLOW" "$CODE" "$OFF"
  if [ "$CODE" = "000" ]; then
    # Seen in practice: cloudflared connects happily and the hostname it was
    # given never resolves. It is not worth debugging -- Ctrl-C and rerun, and
    # the next hostname works. Do not post a 000 URL to the team.
    printf '    000 means the hostname did not resolve, not that your backend is down.\n'
    printf '    Ctrl-C and run this again; you will get a different hostname.\n'
  else
    printf '    The URL below is still worth trying; the edge can take a moment.\n'
  fi
fi

cat <<EOF

  ${BOLD}Post this to the team channel:${OFF}

    Backend is up. Put this in frontend/.env.local and restart \`npm run dev\`:

    VITE_API_BASE=$URL

  Vite only reads .env.local at startup -- an already-running dev server will
  keep using the previous URL until it is restarted.

  This URL dies when this process does. Ctrl-C stops the tunnel.

EOF

wait $TUNNEL_PID
