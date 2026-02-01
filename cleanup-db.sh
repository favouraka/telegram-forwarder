#!/bin/bash
# Cleanup SQLite locks before starting forwarder

FORWARDER_DIR="/home/aka/telegram-forwarder-py"
cd "$FORWARDER_DIR"

# Kill any existing forwarder processes
pkill -9 -f "forwarder.py forward" 2>/dev/null

# Remove SQLite journal files (these cause "database is locked" errors)
find . -name "*.session-journal" -delete 2>/dev/null
find . -name "*.session-wal" -delete 2>/dev/null
find . -name "*.session-shm" -delete 2>/dev/null

# Wait a moment for file system to settle
sleep 1

exit 0
