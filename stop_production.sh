#!/bin/bash
# -*- coding: utf-8 -*-

# 南昌新东方凭证打印系统 - Linux生产环境停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1"
}

echo "==============================================="
echo "  南昌新东方凭证打印系统 - 停止服务"
echo "==============================================="
echo ""

# 停止Gunicorn服务
stop_gunicorn() {
    log_info "查找Gunicorn进程..."
    
    # 检查PID文件
    if [ -f "gunicorn.pid" ]; then
        PID=$(cat gunicorn.pid)
        log_info "发现Gunicorn PID文件: $PID"
        
        # 检查进程是否存在
        if ps -p $PID > /dev/null 2>&1; then
            log_info "正在优雅停止Gunicorn服务..."
            
            # 发送TERM信号优雅停止
            kill -TERM $PID
            
            # 等待进程结束
            for i in {1..10}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    log_success "Gunicorn服务已优雅停止"
                    break
                fi
                sleep 1
            done
            
            # 如果进程仍在运行，强制终止
            if ps -p $PID > /dev/null 2>&1; then
                log_warning "优雅停止超时，强制终止..."
                kill -KILL $PID
                if [ $? -eq 0 ]; then
                    log_success "Gunicorn服务已强制停止"
                else
                    log_error "无法停止Gunicorn服务"
                fi
            fi
        else
            log_warning "PID文件存在但进程不存在"
        fi
        
        # 删除PID文件
        rm -f gunicorn.pid
    else
        log_info "未找到Gunicorn PID文件"
    fi
}

# 停止Flask开发服务器
stop_flask_dev() {
    log_info "查找Flask开发服务器进程..."
    
    # 查找run.py相关进程
    FLASK_PIDS=$(pgrep -f "python.*run.py" 2>/dev/null)
    if [ -n "$FLASK_PIDS" ]; then
        log_info "发现Flask开发服务器进程: $FLASK_PIDS"
        for pid in $FLASK_PIDS; do
            log_info "停止Flask进程: $pid"
            kill -TERM $pid 2>/dev/null
            sleep 2
            
            # 检查是否还在运行
            if ps -p $pid > /dev/null 2>&1; then
                log_warning "强制终止Flask进程: $pid"
                kill -KILL $pid 2>/dev/null
            fi
            
            if [ $? -eq 0 ]; then
                log_success "Flask进程已停止: $pid"
            fi
        done
    else
        log_info "未找到Flask开发服务器进程"
    fi
}

# 停止系统服务
stop_systemd_service() {
    SERVICE_NAME="ncxdf-print-web"
    
    if command -v systemctl &> /dev/null; then
        log_info "检查系统服务状态..."
        
        if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
            log_info "停止系统服务: $SERVICE_NAME"
            sudo systemctl stop $SERVICE_NAME
            
            if [ $? -eq 0 ]; then
                log_success "系统服务已停止"
                
                # 询问是否禁用自启动
                echo -n "是否禁用服务自启动？(y/N): "
                read -r response
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    sudo systemctl disable $SERVICE_NAME
                    log_success "服务自启动已禁用"
                fi
            else
                log_error "停止系统服务失败"
            fi
        else
            log_info "系统服务未运行"
        fi
    else
        log_info "系统不支持systemctl，跳过系统服务检查"
    fi
}

# 检查端口使用情况
check_port() {
    log_info "检查端口5000使用情况..."
    
    PORT_PIDS=$(lsof -ti:5000 2>/dev/null)
    if [ -n "$PORT_PIDS" ]; then
        log_warning "端口5000仍在使用中，相关进程:"
        lsof -i:5000 2>/dev/null
        
        echo -n "是否强制终止这些进程？(y/N): "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            for pid in $PORT_PIDS; do
                log_info "终止进程: $pid"
                kill -KILL $pid 2>/dev/null
            done
            log_success "端口5000已释放"
        fi
    else
        log_success "端口5000已释放"
    fi
}

# 清理临时文件
cleanup_files() {
    log_info "清理临时文件..."
    
    # 删除配置文件
    rm -f gunicorn.conf.py gunicorn_daemon.conf.py
    
    # 删除PID文件
    rm -f gunicorn.pid
    
    # 清理临时systemd服务文件
    rm -f /tmp/ncxdf-print-web.service 2>/dev/null
    
    log_success "临时文件清理完成"
}

# 显示停止选项
show_stop_menu() {
    echo "选择停止方式:"
    echo "1. 停止所有服务 (推荐)"
    echo "2. 仅停止Gunicorn服务"
    echo "3. 仅停止Flask开发服务器"
    echo "4. 仅停止系统服务"
    echo "5. 强制清理所有相关进程"
    echo ""
    echo -n "请输入选项 (1-5): "
    read -r choice
    
    case $choice in
        1)
            stop_gunicorn
            stop_flask_dev
            stop_systemd_service
            check_port
            cleanup_files
            ;;
        2)
            stop_gunicorn
            check_port
            ;;
        3)
            stop_flask_dev
            check_port
            ;;
        4)
            stop_systemd_service
            ;;
        5)
            force_cleanup
            ;;
        *)
            log_error "无效选项"
            show_stop_menu
            ;;
    esac
}

# 强制清理所有相关进程
force_cleanup() {
    log_warning "强制清理所有相关进程..."
    
    # 杀死所有相关Python进程
    pkill -f "python.*run.py" 2>/dev/null
    pkill -f "gunicorn.*run:app" 2>/dev/null
    
    # 强制释放端口
    PORT_PIDS=$(lsof -ti:5000 2>/dev/null)
    if [ -n "$PORT_PIDS" ]; then
        kill -KILL $PORT_PIDS 2>/dev/null
    fi
    
    # 停止系统服务
    if command -v systemctl &> /dev/null; then
        sudo systemctl stop ncxdf-print-web 2>/dev/null
    fi
    
    # 清理文件
    cleanup_files
    
    log_success "强制清理完成"
}

# 检查是否在正确的目录中
if [ ! -f "app.py" ] || [ ! -f "run.py" ]; then
    log_error "请在项目根目录中运行此脚本"
    exit 1
fi

# 设置脚本可执行权限
chmod +x "$0" 2>/dev/null

# 显示菜单并执行
show_stop_menu

echo ""
log_success "停止脚本执行完成"
echo "如果仍有问题，请检查系统进程并手动处理" 