# 南昌新东方凭证打印系统 - 生产环境部署指南

## 📋 概述

本文档详细说明如何在生产环境中部署和运行南昌新东方凭证打印系统。提供了Windows和Linux两个平台的一键启动脚本，支持多种部署方式。

## 🔧 系统要求

### 基础要求
- **Python**: 3.7 或更高版本
- **MySQL**: 5.7 或更高版本
- **内存**: 至少 2GB RAM
- **磁盘**: 至少 5GB 可用空间
- **网络**: 支持HTTP/HTTPS访问

### Windows环境
- Windows 10/11 或 Windows Server 2016+
- PowerShell 5.0+
- Visual C++ 构建工具 (可选，用于编译某些Python包)

### Linux环境
- Ubuntu 18.04+ / CentOS 7+ / Debian 9+ / Fedora 30+
- 开发工具包 (build-essential, gcc, python3-dev)
- MySQL开发库 (libmysqlclient-dev)

## 🚀 快速部署

### Windows环境

#### 1. 下载并准备项目
```bash
# 克隆或下载项目到本地
cd /path/to/ncxdf_print_web
```

#### 2. 运行生产环境启动脚本
```bash
# 以管理员身份运行PowerShell或命令提示符
.\start_production.bat
```

#### 3. 按照脚本提示完成配置
脚本会自动完成以下步骤：
- 检查Python环境
- 创建虚拟环境
- 安装依赖包
- 配置环境变量
- 初始化数据库
- 启动服务

### Linux环境

#### 1. 下载并准备项目
```bash
cd /path/to/ncxdf_print_web
chmod +x start_production.sh
```

#### 2. 运行生产环境启动脚本
```bash
./start_production.sh
```

#### 3. 选择启动方式
脚本提供4种启动方式：
1. **Gunicorn生产服务器** (推荐)
2. **Flask开发服务器**
3. **后台守护进程模式**
4. **系统服务模式**

## ⚙️ 配置说明

### 环境变量配置 (.env文件)

脚本会自动创建`.env`文件，请根据实际情况修改以下配置：

```bash
# MySQL数据库配置
MYSQL_HOST=localhost                    # 数据库主机地址
MYSQL_PORT=3306                        # 数据库端口
MYSQL_DATABASE=print_system            # 数据库名称
MYSQL_USERNAME=root                    # 数据库用户名
MYSQL_PASSWORD=your_secure_password    # 数据库密码(请设置强密码)

# Flask应用配置
SECRET_KEY=your-very-secure-secret-key-here  # 应用密钥(请设置强密码)
FLASK_ENV=production                    # 环境模式
```

### 安全配置建议

1. **数据库安全**
   - 使用强密码
   - 限制数据库访问IP
   - 定期备份数据

2. **应用安全**
   - 使用复杂的SECRET_KEY
   - 配置防火墙规则
   - 启用HTTPS (生产环境必须)

3. **系统安全**
   - 使用非root用户运行应用
   - 定期更新系统补丁
   - 监控系统日志

## 🛠️ 部署方式详解

### 1. Gunicorn生产服务器 (推荐)

**特点**：
- 高性能WSGI HTTP服务器
- 支持多工作进程
- 内置负载均衡
- 生产环境稳定可靠

**配置**：
```python
# 自动生成的gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 30
max_requests = 5000
max_requests_jitter = 100
```

**启动命令**：
```bash
gunicorn -c gunicorn.conf.py run:app
```

### 2. 后台守护进程模式

**特点**：
- 服务在后台运行
- 自动管理PID文件
- 支持优雅重启
- 适合服务器环境

**管理命令**：
```bash
# 启动
./start_production.sh (选择选项3)

# 停止
kill -TERM $(cat gunicorn.pid)

# 重启
kill -HUP $(cat gunicorn.pid)

# 查看状态
ps -p $(cat gunicorn.pid)
```

### 3. 系统服务模式 (Linux)

**特点**：
- 集成系统服务管理
- 开机自启动
- 系统级别的进程管理
- 标准化的服务操作

**服务管理**：
```bash
# 安装服务后的管理命令
sudo systemctl start ncxdf-print-web      # 启动
sudo systemctl stop ncxdf-print-web       # 停止
sudo systemctl restart ncxdf-print-web    # 重启
sudo systemctl status ncxdf-print-web     # 状态
sudo systemctl enable ncxdf-print-web     # 开机自启
sudo systemctl disable ncxdf-print-web    # 禁用自启

# 查看日志
sudo journalctl -u ncxdf-print-web -f
```

## 🔄 服务管理

### 停止服务

#### Windows
```bash
.\stop_production.bat
```

#### Linux
```bash
./stop_production.sh
```

### 重启服务

#### 优雅重启 (推荐)
```bash
# Linux - Gunicorn支持优雅重启
kill -HUP $(cat gunicorn.pid)

# 或者使用系统服务
sudo systemctl reload ncxdf-print-web
```

#### 完全重启
```bash
# 停止后重新启动
./stop_production.sh
./start_production.sh
```

### 服务状态监控

#### 检查进程状态
```bash
# Linux
ps aux | grep gunicorn
ps -p $(cat gunicorn.pid)

# Windows
tasklist | findstr python
```

#### 检查端口占用
```bash
# Linux
netstat -tlnp | grep :5000
lsof -i :5000

# Windows
netstat -ano | findstr :5000
```

#### 查看日志
```bash
# 应用日志
tail -f logs/gunicorn.log
tail -f logs/access.log
tail -f logs/error.log

# 系统服务日志 (Linux)
sudo journalctl -u ncxdf-print-web -f
```

## 🔍 故障排除

### 常见问题及解决方案

#### 1. 数据库连接失败
```bash
# 检查MySQL服务状态
# Linux
sudo systemctl status mysql
sudo systemctl start mysql

# Windows
net start mysql
```

**解决方案**：
- 确认MySQL服务已启动
- 检查`.env`文件中的数据库配置
- 验证数据库用户权限
- 测试数据库连接

#### 2. 端口占用
```bash
# 查找占用端口5000的进程
# Linux
lsof -i :5000
kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /f /pid <PID>
```

#### 3. 权限问题
```bash
# Linux - 确保文件权限正确
chmod +x *.sh
chmod 755 logs/
chown -R user:user /path/to/project
```

#### 4. 依赖包安装失败
```bash
# 手动安装依赖
pip install -r requirements.txt

# 如果编译失败，安装开发工具
# Ubuntu/Debian
sudo apt install build-essential python3-dev libmysqlclient-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel mysql-devel
```

## 📊 性能优化

### Gunicorn配置优化

根据服务器配置调整工作进程数：
```python
# 工作进程数 = CPU核心数 * 2 + 1
workers = 4  # 双核服务器建议值

# 根据内存调整连接数
worker_connections = 1000  # 单进程最大连接数
```

### 数据库优化

```bash
# MySQL配置优化 (my.cnf)
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
max_connections = 200
```

### 系统优化

```bash
# 增加文件描述符限制
ulimit -n 65535

# 调整TCP参数
echo 'net.core.somaxconn = 1024' >> /etc/sysctl.conf
sysctl -p
```

## 🔒 SSL/HTTPS配置 (可选)

### 使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📝 维护任务

### 定期备份

#### 数据库备份
```bash
# 创建备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root -p print_system > backup_${DATE}.sql
```

#### 应用备份
```bash
# 备份配置和日志
tar -czf backup_${DATE}.tar.gz .env logs/ static/ templates/
```

### 日志轮转
```bash
# 使用logrotate (Linux)
/path/to/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 user group
}
```

### 监控脚本
```bash
#!/bin/bash
# 服务健康检查
curl -f http://localhost:5000/api/version || {
    echo "Service down, restarting..."
    ./stop_production.sh
    ./start_production.sh
}
```

## 📞 技术支持

如果遇到部署问题，请：

1. 查看日志文件 (`logs/` 目录)
2. 检查系统资源使用情况
3. 验证配置文件设置
4. 参考本文档的故障排除部分

## 📄 版本说明

- **脚本版本**: 1.0.0
- **支持的系统**: Windows 10+, Ubuntu 18.04+, CentOS 7+
- **最后更新**: 2025-01-20

---

**注意**: 生产环境部署前请务必测试所有功能，确保配置正确并做好数据备份。 