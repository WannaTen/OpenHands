#!/bin/bash

set -e

echo "Starting graceful shutdown of GUI extension services..."

# Set DISPLAY environment variable
export DISPLAY=:${DISPLAY_NUM}

# 1. First close noVNC (Web client)
echo "Shutting down noVNC..."
pkill -f "novnc_proxy" || echo "noVNC already stopped or not running"

# 2. Close tint2 panel
echo "Shutting down tint2 panel..."
pkill -f "tint2" || echo "tint2 already stopped or not running"

# 3. Close mutter window manager
echo "Shutting down mutter window manager..."
pkill -f "mutter" || echo "mutter already stopped or not running"

# 4. Close x11vnc server
echo "Shutting down x11vnc server..."
pkill -f "x11vnc" || echo "x11vnc already stopped or not running"

# Wait a moment for services to fully stop
sleep 2

# 5. Finally close Xvfb (virtual display server)
echo "Shutting down Xvfb display server..."
pkill -f "Xvfb.*${DISPLAY}" || echo "Xvfb already stopped or not running"

# Clean up lock files
if [ -e "/tmp/.X${DISPLAY_NUM}-lock" ]; then
    echo "Cleaning up X11 lock files..."
    rm -f "/tmp/.X${DISPLAY_NUM}-lock"
fi

# Clean up temporary log files
echo "Cleaning up temporary files..."
rm -f /tmp/x11vnc_stderr.log
rm -f /tmp/mutter_stderr.log
rm -f /tmp/tint2_stderr.log
rm -f /tmp/novnc.log

# Verify if services have stopped
echo "Verifying service status..."
remaining_processes=0

if pgrep -f "novnc_proxy" > /dev/null; then
    echo "Warning: noVNC process is still running"
    remaining_processes=$((remaining_processes + 1))
fi

if pgrep -f "tint2" > /dev/null; then
    echo "Warning: tint2 process is still running"
    remaining_processes=$((remaining_processes + 1))
fi

if pgrep -f "mutter" > /dev/null; then
    echo "Warning: mutter process is still running"
    remaining_processes=$((remaining_processes + 1))
fi

if pgrep -f "x11vnc" > /dev/null; then
    echo "Warning: x11vnc process is still running"
    remaining_processes=$((remaining_processes + 1))
fi

if pgrep -f "Xvfb.*${DISPLAY}" > /dev/null; then
    echo "Warning: Xvfb process is still running"
    remaining_processes=$((remaining_processes + 1))
fi

if [ $remaining_processes -eq 0 ]; then
    echo "✅ All GUI services successfully shut down"
else
    echo "⚠️  $remaining_processes processes still not fully shut down, may require manual handling"
    echo "For force shutdown, run ./force_stop.sh"
fi

echo "GUI extension shutdown complete"