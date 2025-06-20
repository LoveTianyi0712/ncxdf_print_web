#!/bin/bash

# 南昌新东方凭证打印系统 - DevBox启动脚本
# 设置环境变量并启动Flask应用

# 导出环境变量
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=print_system
export MYSQL_USERNAME=root
export MYSQL_PASSWORD=Ncxdf2025!
export SECRET_KEY=Ncxdf2025-production-secret-key-change-in-production
export FLASK_ENV=production
export FLASK_DEBUG=false

# 设置应用端口（Sealos平台标准端口）
export PORT=${PORT:-8080}

# 启动应用前确保数据库表已创建
echo "启动南昌新东方凭证打印系统..."
echo "数据库配置: $MYSQL_HOST:$MYSQL_PORT/$MYSQL_DATABASE"
echo "应用将监听端口: $PORT"

# 使用生产环境入口点启动应用
python3 run.py 