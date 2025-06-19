# 南昌新东方凭证打印系统 v2.2.0

这是一个基于Flask的Web应用程序，用于管理用户权限和打印各种学员凭证。

> 🎉 **最新版本 v2.2.0** 新增Excel批量导入功能、优化用户管理体验！查看 [更新日志](CHANGELOG.md) 了解详情。

> 🚀 **新用户？** 查看 [快速开始指南](QUICK_START.md) 快速上手！

## 功能特性

### 🆕 v2.2.0 新增功能
- 📊 **Excel批量导入**：全新的用户批量导入系统，支持Excel文件导入
- 📋 **智能模板系统**：提供带说明的Excel模板，包含示例数据和详细填写指南
- ✅ **数据验证增强**：自动验证用户名唯一性、邮箱格式、角色权限等
- 🎨 **界面优化**：重新设计用户创建页面，突出推荐Excel导入功能

### 🔥 v2.1.0 核心功能
- 📬 **消息盒子系统**：实时消息通知，支持打印成功、审批结果等多种消息类型
- 📝 **审批备注功能**：管理员审批时可添加详细备注说明
- 🔔 **实时通知**：未读消息数量实时更新，自动刷新
- 👤 **智能操作员显示**：根据用户姓名和用户名智能显示操作员信息

### 🔥 核心功能
- 🔐 **用户权限管理**：支持超级管理员和普通用户两种角色
- 👥 **用户账号管理**：支持批量创建用户、启用/禁用账号、姓名邮箱管理
- 📊 **Excel批量导入**：支持Excel文件批量导入用户，包含详细模板和说明
- 🖨️ **凭证打印功能**：支持多种类型的凭证打印预览
- 📋 **操作日志记录**：完整记录所有打印操作
- 🔍 **学员信息查询**：根据学员编码查询可打印的凭证
- 🔄 **用户信息变更审批**：分级权限管理，普通用户变更需审批
- 📱 **响应式设计**：支持桌面和移动设备访问

## 支持的凭证类型

### 🎯 核心凭证处理器（新架构）

1. **学员账户充值提现凭证** - `student_account_certificate.py`
   - 支持充值和提现业务
   - 自动货币格式化（¥15,000.00）
   - 智能余额计算

2. **班级凭证（报班凭证）** - `enrollment_certificate.py`
   - 完整的班级信息管理
   - 费用计算和优惠处理
   - 支持23个模板字段

3. **退费凭证** - `refund_fee_certificate.py`
   - 退费金额自动格式化
   - 余额更新和记录
   - 支持多种退费方式

### 📋 传统凭证类型（兼容模式）

4. 报班凭证
5. 转班凭证
6. 退班凭证
7. 调课凭证
8. 优惠重算凭证
9. 高端报班凭证

## 系统要求

- Python 3.7+
- Windows 10+ (需要中文字体支持)
- 至少 2GB 内存
- 100MB 可用磁盘空间
- MySQL 5.7+

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

### 2. 配置MySQL数据库

1. 确保MySQL服务已启动
2. 复制环境变量模板：
```bash
copy env.example .env
```
3. 编辑 `.env` 文件，配置MySQL连接：
```bash
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

```bash
# 初始化MySQL数据库
python database_setup.py

# 然后启动应用
python run.py
```

或者直接使用启动脚本：
```bash
start_mysql.bat
```

### 5. 生成测试数据（可选）

```bash
# 生成新架构凭证处理器的测试数据
python scripts/generate_test_certificates.py
```

### 6. 访问系统

在浏览器中打开：http://localhost:5000

## 默认账号

系统会自动创建默认管理员账号，具体信息请联系系统管理员获取。

⚠️ **重要提示**：首次登录后请立即修改默认密码！

## 使用说明

### 管理员功能

1. **用户管理**
   - 创建新用户（支持手动批量创建和Excel批量导入）
   - Excel批量导入：下载模板 → 填写用户信息 → 上传导入
   - 支持导入用户名、密码、姓名、邮箱、角色等完整信息
   - 自动验证数据格式和用户名唯一性
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

学员编码示例格式：

### 🎯 学员编码格式示例
- **NC12345678**：标准学员编码格式参考

## 🏗️ 新架构特性

### 核心凭证处理器
采用全新的模块化设计，每个凭证类型都有独立的处理器：

- **🎯 专业化设计**：每个处理器专门针对特定凭证类型优化
- **💰 智能格式化**：自动处理货币格式（¥15,000.00）
- **🎨 字体优化**：统一的字体放大逻辑（font_size * 2.7）
- **🔧 模板解析**：高效的MRT模板解析器
- **📊 数据验证**：完整的字段验证和默认值处理
- **🖼️ 图像渲染**：支持图像、线条、文本等所有组件类型
- **🔍 统一搜索**：集成学员所有类型凭证的搜索功能

### 处理器架构
```
utils/certificate_processors/
├── student_account_certificate.py  # 学员账户凭证
├── enrollment_certificate.py       # 班级凭证
├── refund_fee_certificate.py       # 退费凭证
├── search_student_certificate.py   # 统一学员凭证搜索
└── print_simulator.py             # 通用模板解析器
```

## 技术架构

- **后端框架**：Flask + SQLAlchemy
- **数据库**：MySQL
- **数据库驱动**：PyMySQL
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
├── start_mysql.bat       # MySQL启动脚本
├── scripts/              # 脚本工具目录
│   ├── generate_test_certificates.py # 测试数据生成脚本
│   └── test_web_integration.py       # Web集成测试脚本
├── utils/                 # 工具模块目录
│   ├── __init__.py       # 模块初始化
│   ├── certificate_manager.py # 凭证管理器
│   └── certificate_processors/ # 凭证处理器目录
│       ├── __init__.py
│       ├── student_account_certificate.py # 学员账户凭证
│       ├── enrollment_certificate.py      # 班级凭证
│       ├── refund_fee_certificate.py      # 退费凭证
│       └── print_simulator.py             # 模板解析器
├── requirements.txt       # Python依赖
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
A: 普通用户请联系管理员重置密码。管理员忘记密码可联系技术支持重置。

### Q: 如何生成测试数据？
A: 运行 `python scripts/generate_test_certificates.py` 生成三个核心凭证处理器的测试数据。

### Q: 如何测试Web应用集成？
A: 运行 `python scripts/test_web_integration.py` 测试所有凭证处理器与Web应用的集成情况。

### Q: 如何在代码中使用新的凭证处理器？
A: 
```python
# 学员账户凭证
from utils.certificate_processors.student_account_certificate import generate_student_account_certificate
result = generate_student_account_certificate(data)

# 班级凭证
from utils.certificate_processors.enrollment_certificate import generate_enrollment_certificate
result = generate_enrollment_certificate(data)

# 退费凭证
from utils.certificate_processors.refund_fee_certificate import generate_refund_fee_certificate
result = generate_refund_fee_certificate(data)

# 统一学员凭证搜索（包含班级凭证和充值提现记录）
from utils.certificate_processors.search_student_certificate import search_student
result = search_student(cookies, current_user, 'NC12345678')
```

### Q: 如何添加新的凭证类型？
A: 需要修改app.py中的TEMPLATE_MAPPING字典，并在properties目录添加对应的.mrt文件。

### Q: MySQL连接失败怎么办？
A: 检查MySQL服务是否启动，连接参数是否正确，数据库是否存在。可运行 `python database_setup.py` 初始化数据库。

### Q: 支持多少并发用户？
A: 基于Flask开发模式，建议同时在线用户不超过50人。生产环境建议使用Gunicorn等WSGI服务器。

## 技术支持

如有技术问题或功能建议，请联系系统管理员。

## 更新日志

### v1.1.0 (2025-06-18)
- ✨ 新增核心凭证处理器架构
- 🎯 实现学员账户充值提现凭证处理器
- 🎯 实现班级凭证（报班凭证）处理器
- 🎯 实现退费凭证处理器
- 💰 自动货币格式化（¥15,000.00）
- 🎨 优化字体渲染和加粗效果
- 🔧 改进模板解析器性能
- 🌈 更新Web界面主题色为绿色(#287042)

### v1.0.0 (2025-06-18)
- 初始版本发布
- 实现基本的用户管理和打印功能
- 支持9种凭证类型
- 完整的操作日志记录

---

© 2025 南昌新东方凭证打印系统 