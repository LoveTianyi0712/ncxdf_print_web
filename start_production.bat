@echo off
chcp 65001 >nul
title 南昌新东方凭证打印系统 - 生产环境

echo.
echo ===============================================
echo    南昌新东方凭证打印系统 - 生产环境启动器
echo ===============================================
echo.

REM 设置生产环境变量
set FLASK_ENV=production

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo [警告] 建议以管理员身份运行此脚本以获得最佳权限
    echo [信息] 继续以当前用户身份运行...
    echo.
)

REM 检查Python是否安装
echo [检查] 验证Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 获取Python版本信息
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] Python版本: %PYTHON_VERSION%

REM 检查pip是否可用
echo [检查] 验证pip包管理器...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] pip不可用，请检查Python安装
    pause
    exit /b 1
)
echo [成功] pip可用

REM 检查MySQL连接（如果可用）
echo [检查] 验证MySQL连接...
python -c "import pymysql; print('PyMySQL模块可用')" >nul 2>&1
if errorlevel 1 (
    echo [警告] PyMySQL模块不可用，稍后将安装
)

REM 创建生产环境配置文件
echo [配置] 检查环境配置...
if not exist ".env" (
    if exist "env.example" (
        echo [信息] 正在创建生产环境配置文件...
        copy "env.example" ".env"
        echo [重要] 请编辑 .env 文件，配置生产环境参数:
        echo   - MYSQL_HOST: MySQL服务器地址
        echo   - MYSQL_PASSWORD: MySQL密码
        echo   - SECRET_KEY: 应用密钥（请使用强密码）
        echo   - FLASK_ENV: 已设置为production
        echo.
        
        REM 自动设置生产环境标识
        echo FLASK_ENV=production >> .env
        
        echo [暂停] 请现在编辑.env文件，配置完成后按任意键继续...
        pause
    ) else (
        echo [错误] 找不到env.example文件，无法创建配置
        pause
        exit /b 1
    )
) else (
    echo [成功] 环境配置文件已存在
)

REM 创建生产环境虚拟环境
echo [环境] 设置Python虚拟环境...
if not exist "venv_prod" (
    echo [信息] 创建生产环境虚拟环境...
    python -m venv venv_prod
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [成功] 生产环境虚拟环境创建完成
)

REM 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv_prod\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)

REM 升级pip
echo [更新] 升级pip到最新版本...
python -m pip install --upgrade pip

REM 安装生产环境依赖
echo [依赖] 安装Python依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖包安装失败，请检查网络连接和requirements.txt文件
    pause
    exit /b 1
)

REM 安装生产环境额外依赖
echo [依赖] 安装生产环境额外组件...
pip install gunicorn
pip install gevent
if errorlevel 1 (
    echo [警告] 生产环境组件安装失败，将使用开发服务器
)

echo [成功] 所有依赖包安装完成

REM 初始化数据库
echo [数据库] 初始化数据库...
python database_setup.py
if errorlevel 1 (
    echo [错误] 数据库初始化失败，请检查MySQL服务和配置
    echo 常见问题解决方案:
    echo 1. 确保MySQL服务已启动
    echo 2. 检查.env文件中的数据库连接参数
    echo 3. 确保数据库用户有足够权限
    echo.
    pause
    exit /b 1
)
echo [成功] 数据库初始化完成

REM 创建日志目录
if not exist "logs" mkdir logs
echo [信息] 日志目录已准备完成

REM 创建生产环境启动选项
echo.
echo [启动选项] 请选择启动方式:
echo 1. 使用Gunicorn生产服务器 (推荐)
echo 2. 使用Flask开发服务器
echo 3. 后台服务模式启动
echo.
choice /c 123 /n /m "请输入选项 (1-3): "

if errorlevel 3 goto background_mode
if errorlevel 2 goto dev_server
if errorlevel 1 goto gunicorn_server

:gunicorn_server
echo.
echo [启动] 使用Gunicorn生产服务器启动...
echo [信息] 服务器配置: 4工作进程, 绑定0.0.0.0:5000
echo [访问] http://localhost:5000
echo [管理] 按Ctrl+C停止服务器
echo.
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --keep-alive 30 --max-requests 5000 --max-requests-jitter 100 run:app
goto end

:dev_server
echo.
echo [启动] 使用Flask开发服务器启动...
echo [访问] http://localhost:5000
echo [管理] 按Ctrl+C停止服务器
echo.
python run.py
goto end

:background_mode
echo.
echo [启动] 后台服务模式启动...
echo [信息] 服务将在后台运行
start /b gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --keep-alive 30 --max-requests 5000 --max-requests-jitter 100 --pid gunicorn.pid run:app
echo [成功] 服务已在后台启动
echo [访问] http://localhost:5000
echo [停止] 运行: taskkill /f /pid [进程ID]
echo [日志] 查看logs目录下的日志文件
goto end

:end
echo.
echo [信息] 生产环境启动脚本执行完成
pause 