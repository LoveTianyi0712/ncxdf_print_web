#!/bin/bash

# 南昌新东方凭证打印系统 - 开发环境启动脚本
# 支持热部署：代码修改后自动重启

echo "=================================="
echo "  凭证打印系统 - 开发模式启动"
echo "=================================="

# 停止已有的进程
echo "正在停止已有进程..."
pkill -f "python3.*run.py" 2>/dev/null
pkill -f "python3.*app.py" 2>/dev/null

# 等待进程完全停止
sleep 2

# 设置环境变量
export FLASK_DEBUG=true
export PORT=8080

# 启动应用
echo "正在启动应用..."
echo "端口: 8080"
echo "热部署: 已启用 (修改代码后自动重启)"
echo "=================================="

python3 run.py 