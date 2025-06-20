#!/bin/bash
# -*- coding: utf-8 -*-

# 南昌新东方凭证打印系统 - Linux生产环境启动脚本
# 支持CentOS, Ubuntu, Debian等主流Linux发行版

set -e  # 遇到错误立即退出

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

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户运行应用"
        echo -n "是否继续？(y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "退出脚本"
            exit 1
        fi
    fi
}

# 检测Linux发行版
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    log_info "操作系统: $OS $VER"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PIP_CMD="pip"
    else
        log_error "未找到Python，请先安装Python 3.7+"
        echo "安装命令示例:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
        echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
        echo "  Fedora:        sudo dnf install python3 python3-pip"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log_success "Python版本: $PYTHON_VERSION"
    
    # 检查Python版本是否满足要求
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" 2>/dev/null; then
        log_error "Python版本过低，需要3.7或更高版本"
        exit 1
    fi
}

# 检查pip
check_pip() {
    log_info "检查pip包管理器..."
    
    if ! command -v $PIP_CMD &> /dev/null; then
        log_error "pip不可用，请先安装pip"
        echo "安装命令示例:"
        echo "  Ubuntu/Debian: sudo apt install python3-pip"
        echo "  CentOS/RHEL:   sudo yum install python3-pip"
        exit 1
    fi
    
    log_success "pip可用"
}

# 安装系统依赖
install_system_deps() {
    log_info "检查系统依赖..."
    
    # 检查是否安装了开发工具
    if ! command -v gcc &> /dev/null; then
        log_warning "未检测到gcc，可能需要安装开发工具"
        echo "请根据您的系统安装开发工具:"
        echo "  Ubuntu/Debian: sudo apt install build-essential python3-dev libmysqlclient-dev"
        echo "  CentOS/RHEL:   sudo yum groupinstall 'Development Tools' && sudo yum install python3-devel mysql-devel"
        echo "  Fedora:        sudo dnf groupinstall 'Development Tools' && sudo dnf install python3-devel mysql-devel"
        echo -n "继续安装？某些包可能编译失败 (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "退出脚本"
            exit 1
        fi
    fi
}

# 创建和激活虚拟环境
setup_venv() {
    log_info "设置Python虚拟环境..."
    
    VENV_DIR="venv_prod"
    
    if [ ! -d "$VENV_DIR" ]; then
        log_info "创建生产环境虚拟环境..."
        $PYTHON_CMD -m venv $VENV_DIR
        if [ $? -ne 0 ]; then
            log_error "虚拟环境创建失败"
            exit 1
        fi
        log_success "生产环境虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source $VENV_DIR/bin/activate
    
    # 更新pip
    log_info "升级pip到最新版本..."
    pip install --upgrade pip
}

# 检查环境配置
setup_config() {
    log_info "检查环境配置..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_info "创建生产环境配置文件..."
            cp env.example .env
            
            # 设置生产环境标识
            echo "FLASK_ENV=production" >> .env
            
            log_warning "请编辑 .env 文件，配置生产环境参数:"
            echo "  - MYSQL_HOST: MySQL服务器地址"
            echo "  - MYSQL_PASSWORD: MySQL密码"
            echo "  - SECRET_KEY: 应用密钥（请使用强密码）"
            echo "  - FLASK_ENV: 已设置为production"
            echo ""
            echo -n "是否现在编辑配置文件？(y/N): "
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                ${EDITOR:-nano} .env
            fi
        else
            log_error "找不到env.example文件，无法创建配置"
            exit 1
        fi
    else
        log_success "环境配置文件已存在"
    fi
    
    # 设置环境变量
    export FLASK_ENV=production
}

# 安装Python依赖
install_dependencies() {
    log_info "安装Python依赖包..."
    
    if [ ! -f "requirements.txt" ]; then
        log_error "找不到requirements.txt文件"
        exit 1
    fi
    
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        log_error "依赖包安装失败"
        exit 1
    fi
    
    # 安装生产环境额外依赖
    log_info "安装生产环境组件..."
    pip install gunicorn gevent || log_warning "生产环境组件安装失败，将使用开发服务器"
    
    log_success "所有依赖包安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    if [ ! -f "database_setup.py" ]; then
        log_error "找不到database_setup.py文件"
        exit 1
    fi
    
    $PYTHON_CMD database_setup.py
    if [ $? -ne 0 ]; then
        log_error "数据库初始化失败，请检查MySQL服务和配置"
        echo "常见问题解决方案:"
        echo "1. 确保MySQL服务已启动: sudo systemctl start mysql"
        echo "2. 检查.env文件中的数据库连接参数"
        echo "3. 确保数据库用户有足够权限"
        exit 1
    fi
    
    log_success "数据库初始化完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p logs
    mkdir -p tmp
    
    log_success "目录创建完成"
}

# 设置权限
set_permissions() {
    log_info "设置文件权限..."
    
    # 设置日志目录权限
    chmod 755 logs
    chmod 755 tmp
    
    # 设置执行权限
    chmod +x *.sh 2>/dev/null || true
    
    log_success "权限设置完成"
}

# 启动选择菜单
show_startup_menu() {
    echo ""
    echo "======================================"
    echo "请选择启动方式:"
    echo "1. Gunicorn生产服务器 (推荐)"
    echo "2. Flask开发服务器"
    echo "3. 后台守护进程模式"
    echo "4. 系统服务模式"
    echo "======================================"
    echo -n "请输入选项 (1-4): "
    read -r choice
    
    case $choice in
        1)
            start_gunicorn
            ;;
        2)
            start_flask_dev
            ;;
        3)
            start_daemon
            ;;
        4)
            start_systemd_service
            ;;
        *)
            log_error "无效选项"
            show_startup_menu
            ;;
    esac
}

# Gunicorn生产服务器启动
start_gunicorn() {
    log_info "使用Gunicorn生产服务器启动..."
    
    if ! command -v gunicorn &> /dev/null; then
        log_error "Gunicorn未安装，请先安装: pip install gunicorn"
        exit 1
    fi
    
    # 创建Gunicorn配置文件
    cat > gunicorn.conf.py << EOF
# Gunicorn配置文件
bind = "0.0.0.0:5000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 30
max_requests = 5000
max_requests_jitter = 100
preload_app = True
pidfile = "gunicorn.pid"
logfile = "logs/gunicorn.log"
loglevel = "info"
access_logfile = "logs/access.log"
error_logfile = "logs/error.log"
EOF
    
    log_success "Gunicorn配置创建完成"
    echo "服务器信息:"
    echo "  - 地址: http://0.0.0.0:5000"
    echo "  - 工作进程: 4"
    echo "  - 日志: logs/gunicorn.log"
    echo "  - 停止: Ctrl+C 或 kill -TERM \$(cat gunicorn.pid)"
    echo ""
    
    # 启动Gunicorn
    gunicorn -c gunicorn.conf.py run:app
}

# Flask开发服务器启动
start_flask_dev() {
    log_info "使用Flask开发服务器启动..."
    log_warning "注意: 开发服务器不适合生产环境使用"
    
    echo "服务器信息:"
    echo "  - 地址: http://localhost:5000"
    echo "  - 停止: Ctrl+C"
    echo ""
    
    $PYTHON_CMD run.py
}

# 后台守护进程模式
start_daemon() {
    log_info "后台守护进程模式启动..."
    
    if ! command -v gunicorn &> /dev/null; then
        log_error "Gunicorn未安装，无法启动守护进程"
        exit 1
    fi
    
    # 检查是否已经在运行
    if [ -f "gunicorn.pid" ]; then
        PID=$(cat gunicorn.pid)
        if ps -p $PID > /dev/null 2>&1; then
            log_warning "服务已在运行 (PID: $PID)"
            echo -n "是否重启服务？(y/N): "
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                log_info "停止现有服务..."
                kill -TERM $PID
                sleep 3
            else
                log_info "保持现有服务运行"
                return
            fi
        fi
    fi
    
    # 创建Gunicorn配置
    cat > gunicorn_daemon.conf.py << EOF
# Gunicorn守护进程配置
bind = "0.0.0.0:5000"
workers = 4
worker_class = "gevent"
daemon = True
pidfile = "gunicorn.pid"
logfile = "logs/gunicorn.log"
loglevel = "info"
access_logfile = "logs/access.log"
error_logfile = "logs/error.log"
user = "$(whoami)"
EOF
    
    log_info "启动后台守护进程..."
    gunicorn -c gunicorn_daemon.conf.py run:app
    
    if [ $? -eq 0 ]; then
        log_success "服务已在后台启动"
        echo "服务信息:"
        echo "  - 地址: http://localhost:5000"
        echo "  - PID文件: gunicorn.pid"
        echo "  - 日志: logs/gunicorn.log"
        echo "  - 停止: kill -TERM \$(cat gunicorn.pid)"
        echo "  - 状态检查: ps -p \$(cat gunicorn.pid)"
    else
        log_error "守护进程启动失败"
        exit 1
    fi
}

# 系统服务模式
start_systemd_service() {
    log_info "创建系统服务..."
    
    # 检查systemd是否可用
    if ! command -v systemctl &> /dev/null; then
        log_error "systemctl不可用，此系统不支持systemd服务"
        exit 1
    fi
    
    SERVICE_NAME="ncxdf-print-web"
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    
    # 创建systemd服务文件
    SERVICE_FILE="/tmp/${SERVICE_NAME}.service"
    cat > $SERVICE_FILE << EOF
[Unit]
Description=南昌新东方凭证打印系统
After=network.target mysql.service

[Service]
Type=notify
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv_prod/bin
ExecStart=$CURRENT_DIR/venv_prod/bin/gunicorn -c gunicorn.conf.py run:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo "系统服务文件已创建: $SERVICE_FILE"
    echo ""
    echo "要安装并启动系统服务，请执行以下命令:"
    echo "  sudo cp $SERVICE_FILE /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable $SERVICE_NAME"
    echo "  sudo systemctl start $SERVICE_NAME"
    echo ""
    echo "服务管理命令:"
    echo "  启动: sudo systemctl start $SERVICE_NAME"
    echo "  停止: sudo systemctl stop $SERVICE_NAME"
    echo "  重启: sudo systemctl restart $SERVICE_NAME"
    echo "  状态: sudo systemctl status $SERVICE_NAME"
    echo "  日志: sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    
    echo -n "是否现在安装并启动系统服务？(y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        sudo cp $SERVICE_FILE /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable $SERVICE_NAME
        sudo systemctl start $SERVICE_NAME
        
        log_success "系统服务已安装并启动"
        sudo systemctl status $SERVICE_NAME
    else
        log_info "系统服务文件已准备就绪，可稍后手动安装"
    fi
}

# 主函数
main() {
    echo "==============================================="
    echo "  南昌新东方凭证打印系统 - Linux生产环境启动器"
    echo "==============================================="
    echo ""
    
    # 环境检查
    check_root
    detect_os
    check_python
    check_pip
    install_system_deps
    
    # 环境设置
    setup_venv
    setup_config
    install_dependencies
    
    # 应用初始化
    init_database
    create_directories
    set_permissions
    
    log_success "环境准备完成"
    
    # 启动选择
    show_startup_menu
}

# 信号处理
trap 'log_info "脚本被中断"; exit 1' INT TERM

# 检查是否在正确的目录中
if [ ! -f "app.py" ] || [ ! -f "run.py" ]; then
    log_error "请在项目根目录中运行此脚本"
    exit 1
fi

# 执行主函数
main "$@" 