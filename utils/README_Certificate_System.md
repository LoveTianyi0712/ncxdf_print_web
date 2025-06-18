# 凭证打印系统设计文档

## 概述

本系统已从原有的单一充值提现凭证设计扩展为支持多种类型凭证的通用打印系统。系统支持 11 种不同的凭证类型，并为不同类型的凭证提供专门的处理方法。

## 系统架构

### 1. 凭证分类系统

凭证按业务类型分为 5 大类：

- **报班类** - 处理学员报名相关凭证
- **退费类** - 处理退费、退班相关凭证  
- **调整类** - 处理转班、调课、优惠重算凭证
- **财务类** - 处理充值提现凭证
- **管理类** - 处理班级管理凭证

### 2. 模板映射表

| BizType | 模板文件 | 凭证类别 |
|---------|----------|----------|
| 1 | 报班凭证.mrt | 报班类 |
| 2 | 转班凭证.mrt | 调整类 |
| 3 | 退班凭证.mrt | 退费类 |
| 4 | 调课凭证.mrt | 调整类 |
| 5 | 班级凭证.mrt | 管理类 |
| 6 | 学员账户充值提现凭证.mrt | 财务类 |
| 7 | 优惠重算凭证.mrt | 调整类 |
| 8 | 退费凭证.mrt | 退费类 |
| 9 | 高端报班凭证.mrt | 报班类 |
| 10 | 高端报名凭证.mrt | 报班类 |
| 11 | 高端退费凭证.mrt | 退费类 |

### 3. 处理器系统

每个凭证类别都有专门的处理器，用于处理特定类型凭证的业务逻辑：

- `enrollment_processor` - 报班类凭证处理器
- `refund_processor` - 退费类凭证处理器  
- `adjustment_processor` - 调整类凭证处理器
- `financial_processor` - 财务类凭证处理器
- `management_processor` - 管理类凭证处理器

## API 接口

### 1. 主要入口函数

#### `create_certificate_printer()`
创建凭证打印器实例
```python
printer = create_certificate_printer()
```

#### `print_certificate_by_type(cert_type, data, currency_symbol="¥")`
根据模板名称打印凭证
```python
# 打印报班凭证
result = print_certificate_by_type("报班凭证.mrt", enrollment_data)
```

#### `print_certificate_by_biz_type(biz_type, data, currency_symbol="¥")`  
根据 BizType 打印凭证
```python
# 打印退费凭证 (BizType=8)
result = print_certificate_by_biz_type(8, refund_data)
```

#### `simulate_print_request(message)`
处理传统格式的打印消息（异步）
```python
# 传统方式
result = await simulate_print_request(message)
```

### 2. 辅助函数

#### `get_available_certificates()`
获取所有可用的凭证类型信息
```python
certs = get_available_certificates()
```

#### `print_certificate_info()`
打印系统支持的所有凭证类型信息
```python
print_certificate_info()
```

## 使用示例

### 1. 报班类凭证

```python
# 普通报班凭证
enrollment_data = {
    "nSchoolId": 35,
    "sSchoolName": "南昌学校",
    "sOperator": "李老师",
    "sStudentName": "张三",
    "sPay": "学费：¥2000.00",
    "sPayType": "支付方式：微信支付"
    # ... 其他字段
}

# 方式1：使用模板名称
result = print_certificate_by_type("报班凭证.mrt", enrollment_data)

# 方式2：使用BizType  
result = print_certificate_by_biz_type(1, enrollment_data)
```

### 2. 退费类凭证

```python
# 退费凭证
refund_data = {
    "nSchoolId": 35,
    "sSchoolName": "南昌学校", 
    "sOperator": "王老师",
    "sStudentName": "李四",
    "sPay": "退费金额：¥1000.00",
    "sPayType": "退费方式：原路返回"
    # ... 其他字段
}

# 打印退费凭证
result = print_certificate_by_type("退费凭证.mrt", refund_data)
```

### 3. 财务类凭证

```python
# 充值提现凭证
financial_data = {
    "nSchoolId": 35,
    "sSchoolName": "南昌学校",
    "sOperator": "张会计", 
    "sStudentName": "王五",
    "sPay": "提现金额：¥1500.00",
    "dSumBalance": "余额：¥500.00",
    "sPayType": "提现方式：银行卡"
    # ... 其他字段
}

# 打印充值提现凭证
result = print_certificate_by_biz_type(6, financial_data)
```

### 4. 传统方式兼容

```python
# 传统消息格式（完全兼容）
message = {
    "PrintType": "proofprintnew",
    "Info": {
        "Params": {
            "BizType": 6,
            "JsonString": json.dumps(data),
            "CurrencySymbol": "¥",
            "SchoolId": 35
        }
    }
}

result = await simulate_print_request(message)
```

## 数据格式

### 标准数据字段

每个凭证数据应包含以下基本字段：

```python
data = {
    "nSchoolId": 35,                    # 学校ID
    "sSchoolName": "南昌学校",           # 学校名称
    "sTelePhone": "400-175-9898",       # 联系电话
    "sOperator": "操作员姓名",           # 操作员
    "dtCreate": "2024-12-23 10:30:00",  # 创建时间
    "Title": "凭证标题",                # 凭证标题
    "sStudentCode": "NC6080119756",     # 学员编码
    "sStudentName": "学员姓名",          # 学员姓名
    "sGender": "性别",                  # 性别
    "sPay": "金额信息",                 # 金额信息
    "sPayType": "支付方式",             # 支付方式
    "dtCreateDate": "2024-12-23 10:30:00", # 凭证日期
    "sProofName": "凭证名称",           # 凭证名称
    "sBizType": "业务类型",             # 业务类型
    "nBizId": 126560051,               # 业务ID
    "sRegZoneName": "部门名称"          # 部门名称
}
```

### 特殊字段

不同类型的凭证可能需要额外的特殊字段：

- **财务类凭证**：`dSumBalance` (余额信息)
- **班级凭证**：`sClassName`, `sTeacherName`, `nStudentCount` 等
- **调整类凭证**：根据具体业务需求添加

## 输出文件

系统会在 `image/` 目录下生成两种文件：

1. **PNG图像文件** - 凭证的可视化输出
   - 格式：`{凭证名称}_{时间戳}.png`
   - 例如：`报班凭证_20241223142203.png`

2. **JSON数据文件** - 原始数据备份
   - 格式：`{凭证名称}_{时间戳}.json`  
   - 例如：`报班凭证_20241223142203.json`

## 扩展指南

### 添加新的凭证类型

1. 在 `TEMPLATE_MAPPING` 中添加新的 BizType 映射
2. 在 `CERTIFICATE_TYPES` 中添加到相应类别或创建新类别
3. 在 `TEMPLATE_NAME_TO_BIZTYPE` 中添加反向映射
4. 如需要，创建专门的处理器方法

### 自定义处理器

```python
def my_custom_processor(self, data, biz_type):
    """自定义凭证处理器"""
    processed_data = data.copy()
    
    # 添加自定义逻辑
    processed_data['custom_field'] = "custom_value"
    
    return processed_data
```

## 注意事项

1. **向后兼容** - 原有的异步调用方式完全保持兼容
2. **模板文件** - 确保 `properties/` 目录下有对应的 .mrt 模板文件
3. **字体支持** - 系统会自动查找中文字体，优先使用宋体
4. **错误处理** - 系统包含完善的错误处理和日志输出
5. **输出质量** - 图像输出使用 200 DPI 高分辨率

## 示例文件

运行 `python utils/certificate_examples.py` 可以查看完整的使用示例，包括：

- 各种类型凭证的打印示例
- 不同调用方式的对比
- 数据格式的标准用法
- 错误处理的最佳实践

## 总结

新的凭证打印系统提供了：

✅ **多类型支持** - 支持 11 种不同类型的凭证  
✅ **灵活调用** - 提供多种调用方式  
✅ **专门处理** - 每种类型有对应的处理器  
✅ **向后兼容** - 完全兼容原有系统  
✅ **易于扩展** - 可轻松添加新的凭证类型  
✅ **完善文档** - 提供详细的使用说明和示例 