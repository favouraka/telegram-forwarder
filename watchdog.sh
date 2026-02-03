#!/bin/bash
# Robust watchdog for Telegram forwarder
# Checks every 2 minutes and restarts if needed

set -o pipefail  # Catch errors in pipes

FORWARDER_DIR="/home/aka/telegram-forwarder-py"
LOG="$FORWARDER_DIR/watchdog.log"

echo "[$(date)] Watchdog starting (PID: $$)" >> "$LOG"

# Change directory safely
cd "$FORWARDER_DIR" || {
    echo "[$(date)] ERROR: Cannot cd to $FORWARDER_DIR" >> "$LOG"
    exit 1
}

# Handle signals - don't die on SIGHUP, SIGINT, SIGTERM
trap '' HUP INT TERM

# Load environment safely
if [ -f config.env ]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        export "$key=$value"
    done < config.env
fi

while true; do
    # Check if forwarder is running
    if ! pgrep -f "venv/bin/python.*forwarder.py forward" > /dev/null; then
        echo "[$(date)] Forwarder not running, cleaning up and restarting..." >> "$LOG"
        
        # Clean up SQLite locks
        find . -name "*.session-journal" -delete 2>/dev/null
        find . -name "*.session-wal" -delete 2>/dev/null
        find . -name "*.session-shm" -delete 2>/dev/null
        
        # Start forwarder
        nohup ./venv/bin/python forwarder.py forward >> forwarder.log 2>&1 &
        sleep 2
        
        if pgrep -f "venv/bin/python.*forwarder.py forward" > /dev/null; then
            echo "[$(date)] Forwarder restarted successfully (PID: $(pgrep -f 'venv/bin/python.*forwarder.py forward'))" >> "$LOG"
        else
            echo "[$(date)] Failed to restart forwarder!" >> "$LOG"
        fi
    fi
    
    # Sleep for 2 minutes (handle interruption)
    for ((i=0; i<120; i++)); do
        sleep 1 || true  # Continue even if sleep is interrupted
    done
done

# Should never reach here
echo "[$(date)] Watchdog exited unexpectedly!" >> "$LOG"
