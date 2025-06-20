#!/bin/bash
# -*- coding: utf-8 -*-

# 南昌新东方凭证打印系统 - 健康检查脚本

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

# 检查服务URL
SERVICE_URL="http://localhost:5000"
API_URL="$SERVICE_URL/api/version"

echo "==============================================="
echo "  南昌新东方凭证打印系统 - 健康检查"
echo "==============================================="
echo ""

# 检查端口是否开放
check_port() {
    log_info "检查端口5000是否开放..."
    
    if command -v nc &> /dev/null; then
        if nc -z localhost 5000 2>/dev/null; then
            log_success "端口5000已开放"
            return 0
        else
            log_error "端口5000未开放"
            return 1
        fi
    else
        # 使用netstat检查
        if netstat -tln 2>/dev/null | grep ":5000" > /dev/null; then
            log_success "端口5000已开放"
            return 0
        else
            log_error "端口5000未开放"
            return 1
        fi
    fi
}

# 检查HTTP响应
check_http() {
    log_info "检查HTTP服务响应..."
    
    if command -v curl &> /dev/null; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL" --connect-timeout 10)
        if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 302 ]; then
            log_success "HTTP服务正常 (状态码: $HTTP_CODE)"
            return 0
        else
            log_error "HTTP服务异常 (状态码: $HTTP_CODE)"
            return 1
        fi
    elif command -v wget &> /dev/null; then
        if wget -q --spider --timeout=10 "$SERVICE_URL" 2>/dev/null; then
            log_success "HTTP服务正常"
            return 0
        else
            log_error "HTTP服务异常"
            return 1
        fi
    else
        log_warning "未找到curl或wget，跳过HTTP检查"
        return 0
    fi
}

# 检查API响应
check_api() {
    log_info "检查API服务响应..."
    
    if command -v curl &> /dev/null; then
        API_RESPONSE=$(curl -s "$API_URL" --connect-timeout 10 2>/dev/null)
        if [ $? -eq 0 ] && echo "$API_RESPONSE" | grep -q "version"; then
            log_success "API服务正常"
            echo "  API响应: $API_RESPONSE"
            return 0
        else
            log_error "API服务异常"
            return 1
        fi
    else
        log_warning "未找到curl，跳过API检查"
        return 0
    fi
}

# 检查进程状态
check_process() {
    log_info "检查应用进程状态..."
    
    # 检查Gunicorn进程
    if [ -f "gunicorn.pid" ]; then
        PID=$(cat gunicorn.pid)
        if ps -p $PID > /dev/null 2>&1; then
            log_success "Gunicorn进程正常运行 (PID: $PID)"
            
            # 显示进程详情
            PROCESS_INFO=$(ps -p $PID -o pid,ppid,cmd --no-headers 2>/dev/null)
            echo "  进程信息: $PROCESS_INFO"
            return 0
        else
            log_error "Gunicorn进程不存在 (PID: $PID)"
            return 1
        fi
    fi
    
    # 检查Flask开发服务器
    FLASK_PIDS=$(pgrep -f "python.*run.py" 2>/dev/null)
    if [ -n "$FLASK_PIDS" ]; then
        log_success "Flask开发服务器正常运行 (PID: $FLASK_PIDS)"
        for pid in $FLASK_PIDS; do
            PROCESS_INFO=$(ps -p $pid -o cmd --no-headers 2>/dev/null)
            echo "  进程信息: $PROCESS_INFO"
        done
        return 0
    fi
    
    # 检查系统服务
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet ncxdf-print-web 2>/dev/null; then
            log_success "系统服务正常运行"
            systemctl status ncxdf-print-web --no-pager -l
            return 0
        fi
    fi
    
    log_error "未发现运行中的应用进程"
    return 1
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    if [ -f ".env" ]; then
        # 读取数据库配置
        source .env 2>/dev/null
        
        if command -v mysql &> /dev/null; then
            if mysql -h"${MYSQL_HOST:-localhost}" -P"${MYSQL_PORT:-3306}" \
                     -u"${MYSQL_USERNAME:-root}" -p"${MYSQL_PASSWORD}" \
                     -e "SELECT 1;" "${MYSQL_DATABASE:-print_system}" > /dev/null 2>&1; then
                log_success "数据库连接正常"
                return 0
            else
                log_error "数据库连接失败"
                return 1
            fi
        else
            log_warning "未找到mysql客户端，跳过数据库检查"
            return 0
        fi
    else
        log_warning "未找到.env配置文件，跳过数据库检查"
        return 0
    fi
}

# 检查系统资源
check_resources() {
    log_info "检查系统资源使用情况..."
    
    # 检查内存使用
    if command -v free &> /dev/null; then
        MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')
        echo "  内存使用率: $MEMORY_USAGE"
    fi
    
    # 检查CPU负载
    if [ -f "/proc/loadavg" ]; then
        LOAD_AVG=$(cat /proc/loadavg | cut -d' ' -f1-3)
        echo "  系统负载: $LOAD_AVG"
    fi
    
    # 检查磁盘使用
    if command -v df &> /dev/null; then
        DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}')
        echo "  磁盘使用率: $DISK_USAGE"
    fi
    
    log_success "系统资源检查完成"
}

# 生成健康报告
generate_report() {
    local total_checks=0
    local passed_checks=0
    
    echo ""
    echo "=================================="
    echo "       健康检查报告"
    echo "=================================="
    
    # 执行所有检查
    total_checks=$((total_checks + 1))
    if check_port; then passed_checks=$((passed_checks + 1)); fi
    echo ""
    
    total_checks=$((total_checks + 1))
    if check_process; then passed_checks=$((passed_checks + 1)); fi
    echo ""
    
    total_checks=$((total_checks + 1))
    if check_http; then passed_checks=$((passed_checks + 1)); fi
    echo ""
    
    total_checks=$((total_checks + 1))
    if check_api; then passed_checks=$((passed_checks + 1)); fi
    echo ""
    
    total_checks=$((total_checks + 1))
    if check_database; then passed_checks=$((passed_checks + 1)); fi
    echo ""
    
    check_resources
    echo ""
    
    # 显示总结
    echo "=================================="
    echo "检查项目: $passed_checks/$total_checks 通过"
    
    if [ $passed_checks -eq $total_checks ]; then
        log_success "所有检查项目通过，服务运行正常"
        echo "服务访问地址: $SERVICE_URL"
        exit 0
    elif [ $passed_checks -gt 0 ]; then
        log_warning "部分检查项目失败，服务可能存在问题"
        exit 1
    else
        log_error "多数检查项目失败，服务可能已停止"
        echo ""
        echo "建议操作:"
        echo "1. 检查服务是否启动: ./start_production.sh"
        echo "2. 查看日志文件: tail -f logs/*.log"
        echo "3. 检查配置文件: .env"
        exit 2
    fi
}

# 持续监控模式
continuous_monitor() {
    log_info "启动持续监控模式 (按Ctrl+C退出)"
    echo ""
    
    while true; do
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 执行健康检查..."
        
        if check_port && check_http; then
            echo "✓ 服务正常"
        else
            echo "✗ 服务异常"
            
            # 发送通知或执行自动恢复
            log_warning "检测到服务异常，考虑重启服务"
        fi
        
        echo "下次检查: $(date -d '+30 seconds' '+%H:%M:%S')"
        echo "----------------------------------------"
        
        sleep 30
    done
}

# 参数处理
case "${1:-}" in
    --continuous|-c)
        continuous_monitor
        ;;
    --help|-h)
        echo "用法: $0 [选项]"
        echo "选项:"
        echo "  无参数          执行一次完整健康检查"
        echo "  -c, --continuous 持续监控模式"
        echo "  -h, --help      显示帮助信息"
        exit 0
        ;;
    *)
        generate_report
        ;;
esac 