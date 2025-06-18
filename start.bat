@echo off
chcp 65001 >nul
title 南昌新东方凭证打印系统

echo.
echo ===============================================
echo           南昌新东方凭证打印系统
echo ===============================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] Python环境检查通过
echo.

REM 检查是否需要安装依赖
if not exist venv (
    echo [信息] 首次运行，正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖包安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [成功] 依赖包安装完成
    echo.
)

echo [信息] 正在启动Web应用程序...
echo.
echo 访问地址: http://localhost:5000
echo 如需登录账号请联系管理员
echo.
echo [提示] 要停止服务器，请按 Ctrl+C
echo.

REM 启动应用程序
python run.py

echo.
echo [信息] 应用程序已停止
pause 