@echo off
chcp 65001 >nul
title 南昌新东方凭证打印系统 - 健康检查

echo.
echo ===============================================
echo    南昌新东方凭证打印系统 - 健康检查
echo ===============================================
echo.

REM 设置服务URL
set SERVICE_URL=http://localhost:5000
set API_URL=%SERVICE_URL%/api/version

REM 检查端口是否开放
:check_port
echo [信息] 检查端口5000是否开放...
netstat -ano | find ":5000" >nul
if errorlevel 1 (
    echo [错误] 端口5000未开放
    set /a failed_checks+=1
    goto :check_process
) else (
    echo [成功] 端口5000已开放
    set /a passed_checks+=1
)

REM 检查进程状态
:check_process
echo.
echo [信息] 检查应用进程状态...

REM 检查Gunicorn PID文件
if exist "gunicorn.pid" (
    set /p GUNICORN_PID=<gunicorn.pid
    tasklist /fi "pid eq !GUNICORN_PID!" 2>nul | find "!GUNICORN_PID!" >nul
    if errorlevel 1 (
        echo [错误] Gunicorn进程不存在 ^(PID: !GUNICORN_PID!^)
        set /a failed_checks+=1
    ) else (
        echo [成功] Gunicorn进程正常运行 ^(PID: !GUNICORN_PID!^)
        set /a passed_checks+=1
    )
) else (
    REM 检查Flask开发服务器
    for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /fo csv /nh 2^>nul') do (
        set "pid=%%~a"
        setlocal enabledelayedexpansion
        for /f "tokens=*" %%b in ('wmic process where "ProcessId=!pid!" get CommandLine /value 2^>nul ^| find "run.py"') do (
            echo [成功] Flask开发服务器正常运行 ^(PID: !pid!^)
            set /a passed_checks+=1
            goto :check_http
        )
        endlocal
    )
    echo [错误] 未发现运行中的应用进程
    set /a failed_checks+=1
)

REM 检查HTTP响应
:check_http
echo.
echo [信息] 检查HTTP服务响应...

REM 使用PowerShell进行HTTP检查
powershell -Command "try { $response = Invoke-WebRequest -Uri '%SERVICE_URL%' -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop; if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 302) { Write-Host '[成功] HTTP服务正常 (状态码: ' $response.StatusCode ')'; exit 0 } else { Write-Host '[错误] HTTP服务异常 (状态码: ' $response.StatusCode ')'; exit 1 } } catch { Write-Host '[错误] HTTP服务异常:' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    set /a failed_checks+=1
) else (
    set /a passed_checks+=1
)

REM 检查API响应
echo.
echo [信息] 检查API服务响应...

powershell -Command "try { $response = Invoke-WebRequest -Uri '%API_URL%' -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop; $content = $response.Content; if ($content -match 'version') { Write-Host '[成功] API服务正常'; Write-Host '  API响应:' $content; exit 0 } else { Write-Host '[错误] API服务异常'; exit 1 } } catch { Write-Host '[警告] API服务检查失败:' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    set /a failed_checks+=1
) else (
    set /a passed_checks+=1
)

REM 检查系统资源
:check_resources
echo.
echo [信息] 检查系统资源使用情况...

REM 检查内存使用
for /f "tokens=4" %%i in ('systeminfo ^| find "可用物理内存"') do set available_memory=%%i
echo   内存信息: 可用物理内存 %available_memory%

REM 检查磁盘使用
for /f "tokens=3" %%i in ('dir /-c ^| find "可用字节"') do set available_disk=%%i
echo   磁盘信息: 可用空间 %available_disk%

echo [成功] 系统资源检查完成

REM 生成健康报告
:generate_report
echo.
echo ==================================
echo        健康检查报告
echo ==================================

set /a total_checks=4
if not defined passed_checks set passed_checks=0
if not defined failed_checks set failed_checks=0

echo 检查项目: %passed_checks%/%total_checks% 通过

if %passed_checks% equ %total_checks% (
    echo [成功] 所有检查项目通过，服务运行正常
    echo 服务访问地址: %SERVICE_URL%
    goto :end_success
) else (
    if %passed_checks% gtr 0 (
        echo [警告] 部分检查项目失败，服务可能存在问题
        goto :end_warning
    ) else (
        echo [错误] 多数检查项目失败，服务可能已停止
        echo.
        echo 建议操作:
        echo 1. 检查服务是否启动: start_production.bat
        echo 2. 查看日志文件: 检查logs目录
        echo 3. 检查配置文件: .env
        goto :end_error
    )
)

:end_success
echo.
echo [提示] 如需持续监控，请使用: health_check.bat --continuous
pause
exit /b 0

:end_warning
echo.
echo [提示] 请检查失败的项目并进行修复
pause
exit /b 1

:end_error
echo.
echo [提示] 请检查服务状态并重新启动
pause
exit /b 2

REM 持续监控模式
:continuous_monitor
echo [信息] 启动持续监控模式 ^(按Ctrl+C退出^)
echo.

:monitor_loop
echo %date% %time% - 执行健康检查...

REM 简化的检查（只检查端口和HTTP）
netstat -ano | find ":5000" >nul
if errorlevel 1 (
    echo ✗ 服务异常
    echo [警告] 检测到服务异常，考虑重启服务
) else (
    powershell -Command "try { Invoke-WebRequest -Uri '%SERVICE_URL%' -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop | Out-Null; Write-Host '✓ 服务正常' } catch { Write-Host '✗ 服务异常' }"
)

echo 下次检查: 30秒后
echo ----------------------------------------

timeout /t 30 /nobreak >nul
goto :monitor_loop

REM 参数处理
if "%1"=="--continuous" goto :continuous_monitor
if "%1"=="-c" goto :continuous_monitor
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

REM 默认执行完整检查
goto :check_port

:show_help
echo 用法: %0 [选项]
echo 选项:
echo   无参数          执行一次完整健康检查
echo   -c, --continuous 持续监控模式
echo   -h, --help      显示帮助信息
pause
exit /b 0 