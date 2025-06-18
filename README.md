# 南昌新东方凭证打印系统

这是一个基于Flask的Web应用程序，用于管理用户权限和打印各种学员凭证。

## 功能特性

- 🔐 **用户权限管理**：支持超级管理员和普通用户两种角色
- 👥 **用户账号管理**：支持批量创建用户、启用/禁用账号
- 🖨️ **凭证打印功能**：支持多种类型的凭证打印预览
- 📋 **操作日志记录**：完整记录所有打印操作
- 🔍 **学员信息查询**：根据学员编码查询可打印的凭证
- 📱 **响应式设计**：支持桌面和移动设备访问

## 支持的凭证类型

1. 报班凭证
2. 转班凭证
3. 退班凭证
4. 调课凭证
5. 班级凭证
6. 学员账户充值提现凭证
7. 优惠重算凭证
8. 退费凭证
9. 高端报班凭证

## 系统要求

- Python 3.7+
- Windows 10+ (需要中文字体支持)
- 至少 2GB 内存
- 100MB 可用磁盘空间
- MySQL 5.7+ 或 SQLite (可选择)

## 安装步骤

### 1. 克隆或下载项目文件

确保所有文件都在同一个目录下：

```
print/
├── app.py                    # 主应用文件
├── run.py                   # 启动脚本
├── requirements.txt         # 依赖列表
├── README.md               # 说明文档
├── utils/                  # 工具模块目录
│   ├── __init__.py
│   └── print_simulator.py # 打印模拟器
├── properties/             # 模板文件目录
│   ├── 报班凭证.mrt
│   ├── 转班凭证.mrt
│   └── ...
└── templates/              # HTML模板目录
    ├── base.html
    ├── login.html
    └── ...
```

### 2. 配置数据库

#### 使用SQLite（默认，无需额外配置）
```bash
# 无需额外操作，直接跳到第3步
```

#### 使用MySQL（可选）
1. 确保MySQL服务已启动
2. 复制环境变量模板：
```bash
copy env.example .env
```
3. 编辑 `.env` 文件，配置MySQL连接：
```bash
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=print_system
MYSQL_USERNAME=your_username
MYSQL_PASSWORD=your_password
```

### 3. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据库

#### SQLite用户
```bash
python run.py
```

#### MySQL用户
```bash
# 先初始化数据库
python database_setup.py

# 然后启动应用
python run.py
```

### 5. 访问系统

在浏览器中打开：http://localhost:5000

## 默认账号

系统会自动创建默认管理员账号，具体信息请联系系统管理员获取。

⚠️ **重要提示**：首次登录后请立即修改默认密码！

## 使用说明

### 管理员功能

1. **用户管理**
   - 创建新用户（支持批量创建）
   - 启用/禁用用户账号
   - 查看用户列表和状态

2. **系统监控**
   - 查看所有用户的打印记录
   - 监控系统使用统计
   - 管理系统权限

3. **账户管理**
   - 修改个人密码
   - 查看账户信息

### 普通用户功能

1. **打印凭证**
   - 输入学员编码查询信息
   - 选择要打印的凭证类型
   - 预览和下载打印图片

2. **查看记录**
   - 查看自己的打印历史
   - 查看操作详情

3. **账户管理**
   - 修改个人密码
   - 查看账户信息

### 操作流程

1. **登录系统**
   - 使用分配的用户名和密码登录

2. **查询学员**
   - 在"打印凭证"页面输入学员编码
   - 系统显示学员信息和可打印凭证列表

3. **选择凭证**
   - 从列表中选择需要打印的凭证类型
   - 点击"生成打印"按钮

4. **预览下载**
   - 系统生成打印预览图片（保存在image文件夹）
   - 可以下载图片文件
   - 操作自动记录到系统日志

## 示例学员编码

系统预置了以下测试数据：

- **NC6080119755**：王淳懿（有多种凭证）
- **NC6080119756**：张三（有报班凭证）

## 技术架构

- **后端框架**：Flask + SQLAlchemy
- **数据库**：SQLite / MySQL (可配置)
- **数据库驱动**：PyMySQL (MySQL), SQLite3 (SQLite)
- **前端框架**：Bootstrap 5 + JavaScript
- **图像处理**：PIL (Pillow)
- **模板引擎**：Jinja2
- **配置管理**：python-dotenv

## 目录结构

```
├── app.py                  # Flask应用主文件
├── run.py                 # 启动脚本
├── config.py              # 配置文件
├── database_setup.py      # 数据库初始化脚本
├── env.example           # 环境变量示例
├── utils/                 # 工具模块目录
│   └── print_simulator.py # 打印处理模块
├── requirements.txt       # Python依赖
├── print_system.db       # SQLite数据库（运行后自动创建）
├── templates/            # HTML模板
├── static/              # 静态资源（CSS/JS）
├── properties/          # 打印模板文件
└── image/               # 生成的图片输出目录（自动创建）
```

## 数据库表结构

### users 表
- id: 用户ID
- username: 用户名
- password_hash: 密码哈希
- role: 用户角色 (admin/user)
- is_enabled: 账号状态
- created_at: 创建时间
- created_by: 创建者ID

### print_logs 表
- id: 记录ID
- user_id: 用户ID
- student_code: 学员编码
- student_name: 学员姓名
- biz_type: 业务类型
- biz_name: 业务名称
- print_time: 打印时间
- print_data: 打印数据(JSON)

## 安全考虑

1. **密码安全**：使用Werkzeug进行密码哈希
2. **会话管理**：使用Flask-Login管理用户会话
3. **权限控制**：基于角色的访问控制
4. **操作审计**：完整的操作日志记录

## 常见问题

### Q: 无法生成打印预览？
A: 检查properties目录是否包含所有.mrt模板文件，确保Windows系统安装了中文字体。

### Q: 如何修改密码？
A: 登录后点击右上角用户名下拉菜单中的"修改密码"，或在侧边栏中选择"修改密码"。

### Q: 忘记密码怎么办？
A: 普通用户请联系管理员重置密码。管理员忘记密码可删除print_system.db文件，重新运行应用程序会重新创建默认管理员账号。

### Q: 如何切换数据库类型？
A: 编辑 `.env` 文件，将 `DATABASE_TYPE` 设置为 `sqlite` 或 `mysql`，并配置相应的连接参数。

### Q: 如何添加新的凭证类型？
A: 需要修改app.py中的TEMPLATE_MAPPING字典，并在properties目录添加对应的.mrt文件。

### Q: MySQL连接失败怎么办？
A: 检查MySQL服务是否启动，连接参数是否正确，数据库是否存在。可运行 `python database_setup.py` 初始化数据库。

### Q: 支持多少并发用户？
A: 基于Flask开发模式，建议同时在线用户不超过50人。生产环境建议使用Gunicorn等WSGI服务器。

## 技术支持

如有技术问题或功能建议，请联系系统管理员。

## 更新日志

### v1.0.0 (2025-06-18)
- 初始版本发布
- 实现基本的用户管理和打印功能
- 支持9种凭证类型
- 完整的操作日志记录

---

© 2025 南昌新东方凭证打印系统 