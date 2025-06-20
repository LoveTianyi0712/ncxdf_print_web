#!/bin/bash

# 南昌新东方凭证打印系统 - 生产环境启动脚本
# 生产模式：不启用热部署

echo "=================================="
echo "  凭证打印系统 - 生产模式启动"
echo "=================================="

# 停止已有的进程
echo "正在停止已有进程..."
pkill -f "python3.*run.py" 2>/dev/null
pkill -f "python3.*app.py" 2>/dev/null

# 等待进程完全停止
sleep 2

# 设置环境变量
export FLASK_DEBUG=false
export PORT=8080

# 启动应用
echo "正在启动应用..."
echo "端口: 8080"
echo "模式: 生产环境"
echo "热部署: 已关闭"
echo "=================================="

python3 run.py 