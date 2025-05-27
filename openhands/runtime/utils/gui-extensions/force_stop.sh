 #!/bin/bash

set -e

echo "Starting FORCE shutdown of GUI extension services..."
echo "⚠️  This will forcefully kill all processes!"

# Set DISPLAY environment variable
export DISPLAY=:${DISPLAY_NUM}

# Force kill all GUI-related processes with SIGKILL
echo "Force killing noVNC processes..."
pkill -9 -f "novnc_proxy" || true

echo "Force killing tint2 processes..."
pkill -9 -f "tint2" || true

echo "Force killing mutter processes..."
pkill -9 -f "mutter" || true

echo "Force killing x11vnc processes..."
pkill -9 -f "x11vnc" || true

echo "Force killing Xvfb processes..."
pkill -9 -f "Xvfb.*${DISPLAY}" || true

# Also kill any remaining X11 processes on this display
echo "Force killing any remaining X11 processes on display ${DISPLAY}..."
pkill -9 -f "DISPLAY=${DISPLAY}" || true

# Clean up all lock files and temporary files
echo "Cleaning up all lock files and temporary files..."
rm -f "/tmp/.X${DISPLAY_NUM}-lock"
rm -f "/tmp/.X11-unix/X${DISPLAY_NUM}"
rm -f /tmp/x11vnc_stderr.log
rm -f /tmp/mutter_stderr.log
rm -f /tmp/tint2_stderr.log
rm -f /tmp/novnc.log

# Clean up any remaining socket files
rm -f "/tmp/.X11-unix/X${DISPLAY_NUM}"

# Wait a moment for cleanup
sleep 1

# Final verification
echo "Verifying all processes are terminated..."
remaining=0

if pgrep -f "novnc_proxy" > /dev/null; then
    echo "ERROR: noVNC process still running after force kill!"
    remaining=$((remaining + 1))
fi

if pgrep -f "tint2" > /dev/null; then
    echo "ERROR: tint2 process still running after force kill!"
    remaining=$((remaining + 1))
fi

if pgrep -f "mutter" > /dev/null; then
    echo "ERROR: mutter process still running after force kill!"
    remaining=$((remaining + 1))
fi

if pgrep -f "x11vnc" > /dev/null; then
    echo "ERROR: x11vnc process still running after force kill!"
    remaining=$((remaining + 1))
fi

if pgrep -f "Xvfb.*${DISPLAY}" > /dev/null; then
    echo "ERROR: Xvfb process still running after force kill!"
    remaining=$((remaining + 1))
fi

if [ $remaining -eq 0 ]; then
    echo "✅ All GUI services forcefully terminated"
    echo "System is now clean and ready for restart"
else
    echo "❌ $remaining processes still running after force kill"
    echo "You may need to reboot the system or contact system administrator"
fi

echo "Force shutdown complete"
