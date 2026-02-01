#!/bin/bash
# Simple watchdog for Telegram forwarder
# Checks every 2 minutes and restarts if needed

FORWARDER_DIR="/home/aka/telegram-forwarder-py"
LOG="$FORWARDER_DIR/watchdog.log"

cd "$FORWARDER_DIR"

# Load environment
if [ -f config.env ]; then
    export $(grep -v '^#' config.env | xargs)
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
    
    # Sleep for 2 minutes
    sleep 120
done
