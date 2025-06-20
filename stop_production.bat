@echo off
chcp 65001 >nul
title 南昌新东方凭证打印系统 - 停止服务

echo.
echo ===============================================
echo      南昌新东方凭证打印系统 - 停止服务
echo ===============================================
echo.

echo [信息] 正在查找运行中的服务...

REM 查找Gunicorn进程
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    set PID=%%i
    echo [发现] Python进程: !PID!
)

REM 检查PID文件
if exist "gunicorn.pid" (
    set /p GUNICORN_PID=<gunicorn.pid
    echo [发现] Gunicorn PID文件: !GUNICORN_PID!
    
    REM 尝试优雅停止
    echo [信息] 正在优雅停止Gunicorn服务...
    taskkill /pid !GUNICORN_PID! /t >nul 2>&1
    if errorlevel 1 (
        echo [警告] 优雅停止失败，强制终止...
        taskkill /f /pid !GUNICORN_PID! /t >nul 2>&1
    )
    
    REM 删除PID文件
    del "gunicorn.pid" >nul 2>&1
    echo [成功] Gunicorn服务已停止
) else (
    echo [信息] 未找到Gunicorn PID文件
)

REM 查找并停止所有Python Flask相关进程
echo [信息] 查找Flask相关进程...
for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /fo csv /nh') do (
    set "pid=%%~a"
    setlocal enabledelayedexpansion
    for /f "tokens=*" %%b in ('wmic process where "ProcessId=!pid!" get CommandLine /value 2^>nul ^| find "run.py"') do (
        echo [发现] Flask进程 PID: !pid!
        taskkill /f /pid !pid! >nul 2>&1
        if !errorlevel! equ 0 (
            echo [成功] 已停止Flask进程: !pid!
        )
    )
    endlocal
)

REM 检查端口5000是否还在使用
echo [信息] 检查端口5000使用情况...
netstat -ano | find ":5000" >nul
if errorlevel 1 (
    echo [成功] 端口5000已释放
) else (
    echo [警告] 端口5000仍在使用中
    netstat -ano | find ":5000"
    echo.
    echo [提示] 如需强制释放端口，请手动终止相关进程
)

REM 清理临时文件
echo [信息] 清理临时文件...
if exist "gunicorn.pid" del "gunicorn.pid" >nul 2>&1
if exist "gunicorn.conf.py" del "gunicorn.conf.py" >nul 2>&1
if exist "gunicorn_daemon.conf.py" del "gunicorn_daemon.conf.py" >nul 2>&1

echo.
echo [完成] 服务停止脚本执行完成
echo [提示] 如果仍有进程残留，请检查任务管理器手动结束
echo.
pause 