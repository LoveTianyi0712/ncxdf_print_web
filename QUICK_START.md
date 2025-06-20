# 🚀 快速开始指南

## 新用户快速上手

### 1️⃣ 安装依赖
```bash
pip install -r requirements.txt
```

### 2️⃣ 配置数据库
```bash
# 复制环境变量模板
copy env.example .env

# 编辑 .env 文件，配置MySQL连接信息
# 然后初始化数据库
python database_setup.py
```

### 3️⃣ 生成测试数据
```bash
# 生成三个核心凭证处理器的测试数据
python scripts/generate_test_certificates.py
```

### 4️⃣ 启动应用
```bash
python run.py
```

### 5️⃣ 访问系统
浏览器打开：http://localhost:5000

## 🎯 学员编码格式

### 学员编码示例格式
- **NC12345678** - 标准学员编码格式参考

## 🔧 开发者指南

### 使用新的凭证处理器
```python
# 学员账户凭证
from utils.certificate_processors.student_account_certificate import generate_student_account_certificate

# 班级凭证  
from utils.certificate_processors.enrollment_certificate import generate_enrollment_certificate

# 退费凭证
from utils.certificate_processors.refund_fee_certificate import generate_refund_fee_certificate
```

### 项目结构
```
├── scripts/generate_test_certificates.py  # 测试数据生成器
├── utils/certificate_processors/          # 核心凭证处理器
│   ├── student_account_certificate.py    # 学员账户凭证
│   ├── enrollment_certificate.py         # 班级凭证
│   └── refund_fee_certificate.py         # 退费凭证
└── image/                                # 生成的凭证文件
```

## 🎉 完成！

现在你可以：
- 登录系统管理用户
- 输入测试学员编码查看凭证
- 生成和下载凭证图片
- 查看操作日志

详细信息请参考 [README.md](README.md) 