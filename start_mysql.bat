@echo off
chcp 65001 >nul
echo.
echo ========================================
echo     南昌新东方凭证打印系统 (MySQL版)
echo ========================================
echo.

REM 检查是否存在.env文件
if not exist ".env" (
    echo 警告: 未找到.env文件，正在复制示例配置...
    copy "env.example" ".env"
    echo.
    echo 请编辑.env文件配置MySQL连接参数后重新运行此脚本
    echo.
    pause
    exit
)

echo 正在初始化数据库...
python database_setup.py
if errorlevel 1 (
    echo.
    echo 数据库初始化失败，请检查MySQL连接配置
    pause
    exit
)

echo.
echo 正在启动应用程序...
python run.py
pause 