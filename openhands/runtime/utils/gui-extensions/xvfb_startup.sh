#!/bin/bash
set -e  # Exit on error

DPI=96
RES_AND_DEPTH=${WIDTH}x${HEIGHT}x24

# Function to check if Xvfb is already running
check_xvfb_running() {
    if [ -e /tmp/.X${DISPLAY_NUM}-lock ]; then
        return 0  # Xvfb is already running
    else
        return 1  # Xvfb is not running
    fi
}

# Function to check if Xvfb is ready
wait_for_xvfb() {
    local timeout=15
    local start_time=$(date +%s)
    echo "Waiting for Xvfb to be ready on display $DISPLAY..."
    while ! DISPLAY=$DISPLAY xdpyinfo >/dev/null 2>&1; do
        if [ $(($(date +%s) - start_time)) -gt $timeout ]; then
            echo "Xvfb failed to start within $timeout seconds" >&2
            return 1
        fi
        sleep 0.5
    done
    echo "Xvfb is now ready on display $DISPLAY"
    return 0
}

# Check if Xvfb is already running
if check_xvfb_running; then
    echo "Xvfb is already running on display ${DISPLAY}"
    # Still wait for it to be accessible
    if wait_for_xvfb; then
        exit 0
    else
        echo "Existing Xvfb is not accessible, attempting restart..."
        # Kill existing Xvfb
        pkill -f "Xvfb.*${DISPLAY}" || true
        rm -f /tmp/.X${DISPLAY_NUM}-lock
        sleep 1
    fi
fi

# Start Xvfb
# 在Xvfb启动命令中添加键盘支持
Xvfb $DISPLAY -ac -screen 0 $RES_AND_DEPTH -retro -dpi $DPI \
    -nolisten tcp -nolisten unix \
    +extension RANDR +extension GLX +extension RENDER \
    -extension XINERAMA &
XVFB_PID=$!

# Wait for Xvfb to start
if wait_for_xvfb; then
    echo "Xvfb started successfully on display ${DISPLAY}"
    echo "Xvfb PID: $XVFB_PID"
else
    echo "Xvfb failed to start"
    kill $XVFB_PID || true
    exit 1
fi
