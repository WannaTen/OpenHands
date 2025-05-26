#!/bin/bash
echo "setting up X11 keyboard"

# 等待X服务器完全启动
sleep 2

# 检查DISPLAY是否可用
if ! xdpyinfo >/dev/null 2>&1; then
    echo "Error: Cannot connect to X display $DISPLAY" >&2
    exit 1
fi

# 设置键盘布局
if ! setxkbmap -layout us; then
    echo "Warning: Failed to set keyboard layout" >&2
fi

# 重置键盘状态
if ! xset r rate 250 30; then
    echo "Warning: Failed to set keyboard repeat rate" >&2
fi

# 启用数字锁定
numlockx on 2>/dev/null || true

echo "X11 keyboard configured"