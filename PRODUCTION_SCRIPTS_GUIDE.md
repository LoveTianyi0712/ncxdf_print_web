# 生产环境脚本使用指南

## 📁 脚本文件说明

本项目为生产环境部署提供了以下脚本文件：

### Windows 脚本
- **`start_production.bat`** - 生产环境启动脚本
- **`stop_production.bat`** - 生产环境停止脚本  
- **`health_check.bat`** - 健康检查脚本

### Linux 脚本
- **`start_production.sh`** - 生产环境启动脚本
- **`stop_production.sh`** - 生产环境停止脚本
- **`health_check.sh`** - 健康检查脚本

### 文档
- **`PRODUCTION_DEPLOYMENT.md`** - 详细部署文档
- **`PRODUCTION_SCRIPTS_GUIDE.md`** - 本指南

## 🚀 快速开始

### Windows 用户

#### 1. 首次部署
```cmd
# 以管理员身份运行命令提示符或PowerShell
.\start_production.bat
```

#### 2. 停止服务
```cmd
.\stop_production.bat
```

#### 3. 健康检查
```cmd
# 单次检查
.\health_check.bat

# 持续监控
.\health_check.bat --continuous
```

### Linux 用户

#### 1. 首次部署
```bash
# 添加执行权限
chmod +x *.sh

# 启动服务
./start_production.sh
```

#### 2. 停止服务
```bash
./stop_production.sh
```

#### 3. 健康检查
```bash
# 单次检查
./health_check.sh

# 持续监控
./health_check.sh --continuous
```

## ⚙️ 脚本功能详解

### 启动脚本 (`start_production.*`)

**功能：**
- ✅ 自动检查Python和pip环境
- ✅ 创建生产环境虚拟环境 (`venv_prod`)
- ✅ 安装项目依赖
- ✅ 配置生产环境变量
- ✅ 初始化数据库
- ✅ 启动Web服务

**启动方式选择：**
1. **Gunicorn生产服务器** (推荐) - 高性能WSGI服务器
2. **Flask开发服务器** - 简单调试用
3. **后台守护进程** (Linux) - 后台运行
4. **系统服务** (Linux) - 开机自启动

### 停止脚本 (`stop_production.*`)

**功能：**
- 🛑 优雅停止Gunicorn服务
- 🛑 停止Flask开发服务器
- 🛑 停止系统服务 (Linux)
- 🛑 释放端口占用
- 🧹 清理临时文件

### 健康检查脚本 (`health_check.*`)

**检查项目：**
- 🔍 端口5000是否开放
- 🔍 应用进程是否运行
- 🔍 HTTP服务是否响应 
- 🔍 API接口是否正常
- 🔍 数据库连接状态
- 🔍 系统资源使用情况

**使用模式：**
- **单次检查** - 执行一次完整健康检查
- **持续监控** - 每30秒检查一次服务状态

## 📋 使用流程

### 首次部署流程
1. **准备环境** - 确保Python和MySQL已安装
2. **运行启动脚本** - 执行 `start_production.*`
3. **配置环境变量** - 编辑生成的 `.env` 文件
4. **选择启动方式** - 根据需求选择服务器类型
5. **验证部署** - 访问 http://localhost:5000

### 日常维护流程
1. **健康检查** - 定期运行 `health_check.*`
2. **查看日志** - 检查 `logs/` 目录下日志文件
3. **重启服务** - 使用停止和启动脚本
4. **监控资源** - 使用持续监控模式

## 🔧 配置说明

### 环境变量 (.env文件)
```bash
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=print_system
MYSQL_USERNAME=root
MYSQL_PASSWORD=your_secure_password

# 应用配置
SECRET_KEY=your-very-secure-secret-key
FLASK_ENV=production
```

### 重要目录
- `venv_prod/` - 生产环境虚拟环境
- `logs/` - 日志文件目录
- `tmp/` - 临时文件目录

## 🚨 故障排除

### 常见问题

#### 1. 启动失败
```bash
# 检查Python环境
python --version

# 检查MySQL服务
# Windows
net start mysql
# Linux  
sudo systemctl start mysql

# 查看详细错误日志
tail -f logs/*.log  # Linux
type logs\*.log     # Windows
```

#### 2. 端口占用
```bash
# 查找占用进程
# Windows
netstat -ano | findstr :5000
# Linux
lsof -i :5000

# 强制停止进程
# Windows  
taskkill /f /pid <PID>
# Linux
kill -9 <PID>
```

#### 3. 权限问题 (Linux)
```bash
# 设置脚本权限
chmod +x *.sh

# 设置目录权限
chmod 755 logs/ tmp/
```

### 服务异常重启
```bash
# 1. 停止所有服务
./stop_production.sh  # Linux
.\stop_production.bat  # Windows

# 2. 检查进程清理
./health_check.sh     # Linux
.\health_check.bat     # Windows

# 3. 重新启动
./start_production.sh  # Linux
.\start_production.bat  # Windows
```

## 📊 性能调优

### Gunicorn配置优化
- **工作进程数** = CPU核心数 * 2 + 1
- **连接数** = 根据内存大小调整
- **超时时间** = 根据业务需求设置

### 系统优化建议
- 增加文件描述符限制
- 调整TCP连接参数
- 配置日志轮转
- 设置定期备份

## 🔒 安全建议

1. **使用强密码** - 数据库密码和SECRET_KEY
2. **限制访问** - 配置防火墙规则
3. **HTTPS配置** - 生产环境必须启用
4. **定期更新** - 系统和依赖包
5. **权限控制** - 使用非root用户运行

## 📞 技术支持

如遇问题，请：
1. 查看日志文件 (`logs/` 目录)
2. 运行健康检查脚本
3. 参考详细部署文档 (`PRODUCTION_DEPLOYMENT.md`)
4. 检查配置文件设置

---

**版本信息**
- 脚本版本: 1.0.0
- 支持系统: Windows 10+, Linux (Ubuntu/CentOS/Debian)
- 最后更新: 2025-01-20 