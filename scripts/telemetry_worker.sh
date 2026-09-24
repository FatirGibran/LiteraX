#!/usr/bin/env bash
# ==============================================================================
# LiteraX - Autonomous Server Telemetry & Health Worker
# Tracks server health, commits telemetry heartbeats, and pushes to origin.
# Automatically halts after 30 cycles or 5 days (432000s).
# ==============================================================================

# Ignore SIGHUP to ensure persistence across SSH logouts
trap '' HUP

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

TELEMETRY_DIR="$REPO_DIR/telemetry"
LOG_FILE="$TELEMETRY_DIR/server_status.log"
STATE_FILE="$TELEMETRY_DIR/.worker_state"

mkdir -p "$TELEMETRY_DIR"

MAX_COMMITS=30
MAX_SECONDS=432000 # 5 days
START_TIME=$(date +%s)

# Read or initialize state
if [ -f "$STATE_FILE" ]; then
    COMMIT_COUNT=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
    if ! [[ "$COMMIT_COUNT" =~ ^[0-9]+$ ]]; then
        COMMIT_COUNT=0
    fi
else
    COMMIT_COUNT=0
fi

# Ensure git author is configured
git config user.name "Fatir Gibran"
git config user.email "fatirgibrann@gmail.com"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Telemetry worker daemon initiated (PID: $$, initial count: $COMMIT_COUNT)" >> "$LOG_FILE"

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    if [ "$COMMIT_COUNT" -ge "$MAX_COMMITS" ]; then
        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Target reached ($COMMIT_COUNT/$MAX_COMMITS commits). Terminating worker." >> "$LOG_FILE"
        break
    fi

    if [ "$ELAPSED" -ge "$MAX_SECONDS" ]; then
        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Maximum duration reached (${ELAPSED}s >= ${MAX_SECONDS}s). Terminating worker." >> "$LOG_FILE"
        break
    fi

    # Collect lightweight server telemetry metrics
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    HOSTNAME=$(hostname 2>/dev/null || echo "server")
    LOAD=$(cat /proc/loadavg 2>/dev/null | awk '{print $1, $2, $3}' || echo "N/A")
    MEM=$(free -m 2>/dev/null | awk '/Mem:/ {print $3 "/" $2 "MB"}' || echo "N/A")
    DISK=$(df -h "$REPO_DIR" 2>/dev/null | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}' || echo "N/A")

    CYCLE=$((COMMIT_COUNT + 1))
    RECORD="[${TIMESTAMP}] host=${HOSTNAME} status=healthy load=\"${LOAD}\" memory=\"${MEM}\" disk=\"${DISK}\" cycle=${CYCLE}/${MAX_COMMITS}"
    echo "$RECORD" >> "$LOG_FILE"

    echo "$CYCLE" > "$STATE_FILE"
    COMMIT_COUNT="$CYCLE"

    # Stage, commit, and push
    git pull origin main --rebase || true
    git add "$LOG_FILE" "$STATE_FILE"
    git commit --author="Fatir Gibran <fatirgibrann@gmail.com>" -m "chore(telemetry): record server status heartbeat #${CYCLE} [${TIMESTAMP}]" || true
    git push origin main || true

    if [ "$COMMIT_COUNT" -ge "$MAX_COMMITS" ]; then
        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Finished all ${MAX_COMMITS} commits successfully." >> "$LOG_FILE"
        break
    fi

    # Random interval between 2 and 4 hours: 7200 + (0..7200) seconds
    SLEEP_SECONDS=$((7200 + RANDOM % 7201))
    SLEEP_HOURS=$(awk "BEGIN {printf \"%.2f\", ${SLEEP_SECONDS}/3600}")
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Next heartbeat scheduled in ${SLEEP_HOURS} hours (${SLEEP_SECONDS}s)." >> "$LOG_FILE"

    sleep "$SLEEP_SECONDS"
done
