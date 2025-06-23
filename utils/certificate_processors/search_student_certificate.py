#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学员凭证搜索模块

该模块提供搜索学员所有类型凭证信息的功能，包括班级凭证、充值提现记录等。

主要功能：
- search_student(): 搜索学员所有类型的凭证记录
- search_class_records(): 搜索班级凭证记录
- search_account_records(): 搜索充值提现记录

使用示例：
    from utils.certificate_processors.search_student_certificate import search_student
    
    # 搜索学员所有凭证
    result = search_student(None, current_user, 'NC12345678')

返回值：
- 成功: 返回包含学员信息和所有凭证数据的字典
- 学员不存在: 返回 0
- 请求失败: 返回 404
"""

import requests
from datetime import datetime
import random
from ..time_utils import get_beijing_time_str


def format_currency(amount):
    """
    格式化金额，添加人民币符号和千分位分隔符
    
    参数:
        amount: 金额，可以是数字、字符串或None
    
    返回:
        格式化后的金额字符串，如 "¥1,234.56"
    """
    if amount is None or amount == '' or amount == 0:
        return '¥0.00'
    
    try:
        # 如果是字符串，先尝试转换为数字
        if isinstance(amount, str):
            # 移除可能存在的货币符号和空格
            amount = amount.replace('¥', '').replace('￥', '').replace(',', '').strip()
        
        # 转换为浮点数
        amount_value = float(amount)
        
        # 格式化为带逗号的货币格式
        formatted = f"¥{amount_value:,.2f}"
        return formatted
    except (ValueError, TypeError):
        # 如果转换失败，返回原始字符串（如果有的话）或默认值
        return f"¥{str(amount)}" if amount else "¥0.00"


# 默认cookies配置（实际使用时应该从用户会话获取）
DEFAULT_COOKIES = {
    'FE_USER_CODE': 'NC24048S6UzC',
    'FE_USER_NAME': '%E5%BC%A0%E8%B0%A6235',
    'rem': 'on',
    'XDFUUID': 'ce6a5a3d-9251-5279-d83a-8f1fc6dcd799',
    'erpSchoolId': '35',
    'gr_user_id': '581a8283-1851-4e73-a092-9075db03f151',
    'a28834c02dcdb241_gr_last_sent_cs1': 'zhangqian235@xdf.cn',
    '964de61476ecd75d_gr_last_sent_cs1': '01027b0e73ba43728dc1e96228e6d606',
    'a28834c02dcdb241_gr_cs1': 'zhangqian235@xdf.cn',
    '964de61476ecd75d_gr_cs1': '01027b0e73ba43728dc1e96228e6d606',
    'jiaowuSchoolId': '35',
    'OA_USER_KEY': 'YjQ2NTBkM2NjNzA0MTUwZTNlMGNmNjQwMDczMGVkNzE7emhhbmdxaWFuMjM1OzE3NDk3ODAwMDM%3D',
    'e2e': 'A2722AEC8CB1725A84385253E3D81D09',
    'casgwusercred': 'NGjz2HfXFFWhcL8Ih_gnED4-mc30XuIwvU7M7bF6wQBciD11s9Pj4GZNsoLFfBhezRZ3fF3uBWh0jJ_MIi9xp56CT6r6-E51i9CfYubbVa-jPmWHuQVTOnsZG0r2miw-F5Z6lkbev2yXITkrUajCbakhU0xK-ZWvarh6jPTzn7U',
    'crosgwusercred': '4qLA-_bkyBtbQspD5OITWCxRI1aviyzNjG-Q-VBq4Gma1hjjUgP2g2yGPmbIjfpQSiiHv2zNTZmJUXEnjbzDUg546d24fe41ac0ff94a449d5f52e6aeba',
    'e2mf': '4c558bdd0e2f4b8893daf159e6a3d4f7',
    'erpUserId': 'zhangqian235',
}


def search_class_records(cookies, headers, student_code, student_info):
    """
    搜索学员班级凭证记录
    
    参数:
        cookies: 认证cookies
        headers: 请求头
        student_code: 学员编码
        student_info: 学员基本信息
    
    返回:
        班级凭证记录列表
    """
    class_records = []
    
    try:
        # 查询学生的班级信息
        json_data = {
            'SchoolId': 35,
            'PageIndex': 1,
            'PageSize': 40,
            'Filters': [
                {
                    'Field': 'StudentCode',
                    'Operation': 0,
                    'Value': student_code,
                    'Logic': 0,
                },
                {
                    'Field': 'CustomizedClassStatus',
                    'Operation': 10,
                    'Value': '0',
                    'Logic': 0,
                },
                {
                    'Field': 'OutType',
                    'Operation': 10,
                    'Value': '0',
                    'Logic': 0,
                },
            ],
            'Sort': [
                {
                    'Field': 'InTime',
                    'Dir': 1,
                },
            ],
        }
        
        response = requests.post(
            'https://erp.xdf.cn/nises/apinises/roster/homePageRosterRecordQuerySign',
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json().get('Data', {}).get('Data', [])
            for record in data:
                certificate_data = {
                    'biz_type': 5,  # 班级凭证
                    'biz_name': '班级凭证',
                    'data': {
                        # 基本信息
                        'sSchoolName': '南昌学校',
                        'sTelePhone': '400-175-9898',
                        'sChannel': '直营',
                        # 学员信息（优先使用传入的学员姓名）
                        'sStudentName': student_info.get('student_name') or record.get('StudentName') or '未知姓名',
                        'sStudentCode': record['StudentCode'],
                        'sGender': student_info.get('gender', '未知'),
                        'sCardCode': record['CardCode'],
                        # 班级信息
                        'sClassName': record['ClassName'],
                        'sClassCode': record['ClassCode'],
                        'sSeatNo': record['CardCode'][-1] if record['CardCode'] and record['CardCode'][-2:][0] == '0' else record['CardCode'][-2:] if record['CardCode'] else '',
                        'dtBeginDate': record['BeginDate'],
                        'dtEndDate': record['EndDate'],
                        'nTryLesson': '是' if record.get('TryLesson') else '否',
                        # 时间信息
                        'sRegisterTime': record['PrintTime'],
                        'sPrintAddress': record['PrintAddress'],
                        'sPrintTime': get_beijing_time_str(),
                        'dtCreate': get_beijing_time_str(),
                        # 费用信息（格式化为带人民币符号的字符串）
                        'dFee': format_currency(record.get('Fee', 0)),  # 商品标准金额
                        'dVoucherFee': format_currency(record.get('Voucher', 0)),  # 商品优惠金额
                        'dShouldFee': format_currency(record.get('Fee', 0)),  # 商品应收金额
                        'dRealFee': format_currency(record.get('UsedPay', 0)),  # 商品实收金额
                        # 操作信息
                        'sOperator': student_info.get('operator', 'system'),
                        # 图像数据（可选）
                        'RWMImage': ''
                    }
                }
                class_records.append(certificate_data)
                
    except Exception as e:
        print(f"搜索班级记录时发生错误: {str(e)}")
    
    return class_records


def search_account_records(cookies, headers, student_code, student_info):
    """
    搜索学员充值提现记录
    
    参数:
        cookies: 认证cookies
        headers: 请求头
        student_code: 学员编码
        student_info: 学员基本信息
    
    返回:
        充值提现记录列表
    """
    account_records = []
    
    try:
        # 查询学员账户充值提现记录（使用正确的API）
        json_data = {
            'SchoolId': 35,
            'PageIndex': 1,
            'PageSize': 40,
            'Filters': [
                {
                    'Field': 'OrderStatus',
                    'Operation': '0',
                    'Value': '1',
                    'Logic': 0,
                },
                {
                    'Field': 'StudentCode',
                    'Logic': 0,
                    'Operation': '0',
                    'Value': student_code,
                },
            ],
            'Sort': [
                {
                    'Field': 'CompleteDate',
                    'Dir': 1,
                },
            ],
        }
        
        response = requests.post(
            'https://erp.xdf.cn/nises/apinises/StuStoreAccount/QueryStoreOrderPage',
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"充值提现API响应状态: {response.status_code}")
            print(f"响应数据结构: {list(response_data.keys()) if response_data else 'None'}")
            
            data = response_data.get('Data', {}).get('Data', [])
            print(f"找到记录数量: {len(data)}")
            
            for record in data:
                order_type = record.get('OrderTypeName', '未知')
                print(f"记录类型: {order_type}")
                
                # 只处理学员账户充值提现类型的记录
                if record.get('OrderTypeName') == '学员账户提现':
                    certificate_data = {
                        'biz_type': 6,  # 学员账户凭证
                        'biz_name': '提现凭证',  # 简化凭证名称
                        'data': {
                            "nSchoolId": 35,
                            "sSchoolName": "南昌学校",
                            "sTelePhone": "400-175-9898",
                            "sOperator": student_info.get('operator', 'system'),
                            "dtCreate": get_beijing_time_str(),
                            "Title": "提现凭证",  # 简化标题
                            "PrintNumber": 1,
                            "YNVIEWPrint": 1,
                            "PrintDocument": "",
                            "sStudentCode": record['StudentCode'],
                            "sStudentName": student_info.get('student_name') or record.get('StudentName') or '未知姓名',
                            "sGender": student_info.get('gender', '未知'),
                            "sPay": f"提现金额：{format_currency(record.get('Pay', 0))}",
                            "dSumBalance": format_currency(record.get('Balance', 0)),
                            "sPayType": f"提现方式：{record.get('PayTypeName', '未知')}",
                            "dtCreateDate": record.get('TransactionTime', get_beijing_time_str()),
                            "sProofName": "提现凭证",  # 简化凭证名称
                            "sBizType": "提现",  # 业务类型标识
                            "sRegZoneName": "客服行政"
                        }
                    }
                    account_records.append(certificate_data)
                elif record.get('OrderTypeName') == '学员账户充值':
                    certificate_data = {
                        'biz_type': 6,  # 学员账户凭证
                        'biz_name': '充值凭证',  # 简化凭证名称
                        'data': {
                            "nSchoolId": 35,
                            "sSchoolName": "南昌学校",
                            "sTelePhone": "400-175-9898",
                            "sOperator": student_info.get('operator', 'system'),
                            "dtCreate": get_beijing_time_str(),
                            "Title": "充值凭证",  # 简化标题
                            "PrintNumber": 1,
                            "YNVIEWPrint": 1,
                            "PrintDocument": "",
                            "sStudentCode": record['StudentCode'],
                            "sStudentName": student_info.get('student_name') or record.get('StudentName') or '未知姓名',
                            "sGender": student_info.get('gender', '未知'),
                            "sPay": f"充值金额：{format_currency(record.get('Pay', 0))}",
                            "dSumBalance": format_currency(record.get('Balance', 0)),
                            "sPayType": f"充值方式：{record.get('PayTypeName', '未知')}",
                            "dtCreateDate": record.get('TransactionTime', get_beijing_time_str()),
                            "sProofName": "充值凭证",  # 简化凭证名称
                            "sBizType": "充值",  # 业务类型标识
                            "sRegZoneName": "客服行政"
                        }
                    }
                    account_records.append(certificate_data)
        else:
            print(f"充值提现API请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
                
    except Exception as e:
        print(f"搜索账户记录时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"最终返回账户记录数量: {len(account_records)}")
    return account_records


def search_student(cookies, current_user, student_code):
    """
    搜索学员所有类型的凭证信息
    
    参数:
        cookies: 认证cookies字典，如果为None或空，将使用DEFAULT_COOKIES
        current_user: 当前用户对象，用于记录操作者信息
        student_code: 学生编号字符串
    
    返回:
        成功: 返回包含学员信息和所有凭证数据的字典
        失败: 返回错误码
               - 0: 未找到该学员
               - 404: 网络请求失败或API调用失败
    """
    # 如果没有提供cookies，使用默认配置
    if not cookies or cookies == 1:
        cookies = DEFAULT_COOKIES
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://erp.xdf.cn',
        'Pragma': 'no-cache',
        'Referer': 'https://erp.xdf.cn/nis/index',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'appSourceKey': 'nis-lm',
        'authorization': 'e2at',
        'school': '35',
        'schoolId': '35',
        'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    try:
        # 第一步：根据学生编号查询学生基本信息
        json_data = {
            'SchoolId': 35,
            'QueryValue': student_code,
            'PageIndex': 1,
            'PageSize': 10,
        }
        
        response = requests.post(
            'https://erp.xdf.cn/apinisbff/Student/QueryStudentWithBound',
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"QueryStudentWithBound API失败，状态码: {response.status_code}")
            return 404
        
        first_response = response.json()
        print(f"QueryStudentWithBound API响应结构: {list(first_response.keys()) if first_response else 'None'}")
            
        if first_response.get('Msg') == '没有找到学员！':
            return 0
        
        # 尝试从第一个API获取学员姓名作为备用
        backup_student_name = None
        if 'Data' in first_response and first_response['Data']:
            first_student = first_response['Data'][0] if isinstance(first_response['Data'], list) else first_response['Data']
            backup_student_name = (first_student.get('StudentName') or 
                                 first_student.get('Name') or 
                                 first_student.get('RealName'))
            print(f"从第一个API获取的备用姓名: '{backup_student_name}'")
        
        # 第二步：获取学生详细信息
        json_data = {
            'SchoolId': 35,
            'StudentCode': student_code,
            'EnType': True,
        }

        response = requests.post(
            'https://erp.xdf.cn/apinisbff/Student/QueryBrief', 
            cookies=cookies,
            headers=headers, 
            json=json_data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"QueryBrief API失败，状态码: {response.status_code}")
            return 404
            
        brief_response = response.json()
        print(f"QueryBrief API响应结构: {list(brief_response.keys()) if brief_response else 'None'}")
        
        if 'Data' not in brief_response:
            print("QueryBrief响应中没有Data字段")
            return 404
            
        query_brief = brief_response['Data']
        print(f"学员详细信息字段: {list(query_brief.keys()) if query_brief else 'None'}")
        
        s_gender = query_brief.get('Gender', 0)
        if s_gender == 1:
            s_gender = '男'
        elif s_gender == 2:
            s_gender = '女'
        else:
            s_gender = '未知'

        # 尝试多个可能的姓名字段，如果都没有则使用备用姓名
        student_name = (query_brief.get('StudentName') or 
                       query_brief.get('Name') or 
                       query_brief.get('RealName') or 
                       query_brief.get('sStudentName') or
                       backup_student_name or
                       '未知姓名')
        
        print(f"最终提取的学员姓名: '{student_name}', 性别: '{s_gender}'")

        # 构建学员基本信息
        # 操作员逻辑：如果姓名为空、None或"未设置"，则使用用户名
        operator_name = 'system'
        if current_user:
            if current_user.name and current_user.name.strip() and current_user.name.strip() != '未设置':
                operator_name = current_user.name.strip()
            else:
                operator_name = current_user.username
        
        student_info = {
            'student_name': student_name,
            'gender': s_gender,
            'operator': operator_name,
            'reports': []
        }

        # 第三步：搜索所有类型的凭证记录
        all_records = []
        
        # 搜索班级凭证记录
        class_records = search_class_records(cookies, headers, student_code, student_info)
        all_records.extend(class_records)
        
        # 搜索充值提现记录
        account_records = search_account_records(cookies, headers, student_code, student_info)
        all_records.extend(account_records)
        
        # 将所有记录添加到学员信息中
        student_info['reports'] = all_records
        
        # 生成报班凭证测试数据
        enrollment_test_data = generate_test_enrollment_registration_data(student_info)
        student_info['enrollment_test_data'] = enrollment_test_data
        
        return student_info
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {str(e)}")
        return 404
    except Exception as e:
        print(f"搜索学生凭证信息时发生错误: {str(e)}")
        return 404


# 为了保持向后兼容，提供别名
def search_student_classes(cookies, current_user, student_code):
    """search_student函数的别名，用于向后兼容"""
    return search_student(cookies, current_user, student_code)


def test_currency_format():
    """测试金额格式化功能"""
    test_cases = [
        (1000, "¥1,000.00"),
        (1234.56, "¥1,234.56"),
        ("2500", "¥2,500.00"),
        (0, "¥0.00"),
        (None, "¥0.00"),
        ("", "¥0.00"),
        ("¥3000", "¥3,000.00"),
        (123456.789, "¥123,456.79")
    ]
    
    print("测试金额格式化功能:")
    for amount, expected in test_cases:
        result = format_currency(amount)
        status = "✓" if result == expected else "✗"
        print(f"{status} format_currency({amount}) = {result} (期望: {expected})")


def generate_test_enrollment_registration_data(student_info):
    """
    生成班级凭证测试数据
    
    参数:
        student_info: 学员基本信息
    
    返回:
        班级凭证测试数据字典
    """
    # 随机生成1-7条班级数据
    class_count = random.randint(1, 7)
    
    # 班级模板数据
    class_templates = [
        {'code': 'MATH001', 'name': '数学基础班', 'subject': '数学'},
        {'code': 'ENG001', 'name': '英语提高班', 'subject': '英语'},
        {'code': 'PHY001', 'name': '物理基础班', 'subject': '物理'},
        {'code': 'CHEM001', 'name': '化学实验班', 'subject': '化学'},
        {'code': 'LANG001', 'name': '语文阅读班', 'subject': '语文'},
        {'code': 'HIST001', 'name': '历史文化班', 'subject': '历史'},
        {'code': 'GEO001', 'name': '地理探索班', 'subject': '地理'},
    ]
    
    # 随机选择班级
    selected_classes = random.sample(class_templates, min(class_count, len(class_templates)))
    
    # 生成订单号
    order_code = f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
    
    # 生成班级数据
    class_array = []
    total_should_fee = 0
    total_fee = 0
    total_discount = 0
    
    for i, class_template in enumerate(selected_classes):
        # 随机生成费用
        standard_fee = random.randint(1200, 2000)
        discount_fee = random.randint(50, 200)
        should_fee = standard_fee
        register_fee = standard_fee - discount_fee
        
        total_should_fee += should_fee
        total_fee += register_fee
        total_discount += discount_fee
        
        class_data = {
            "sSeatNo": f"{chr(65+i)}{str(i+1).zfill(3)}",  # A001, B002, etc.
            "sClassCode": class_template['code'],
            "sClassName": class_template['name'],
            "dtBeginDate": f"2024-{str((i%12)+1).zfill(2)}-15",
            "dtEndDate": f"2024-{str(((i%12)+3)%12+1).zfill(2)}-15",
            "sRegisterTime": f"2024-01-{str(10+i)} 报名成功",
            "sPrintAddress": f"南昌市朝阳区XX路XX号{i+1}01教室",
            "sPrintTime": f"2024-{str((i%12)+1).zfill(2)}-15 {9+(i%6)}:00-{12+(i%6)}:00",
            "nTryLesson": str(i % 3),
            "dVoucherFee": discount_fee,
            "dFee": standard_fee,
            "dRegisterFee": register_fee,
            "dClassVoucherFee": discount_fee,
            "dShouldFee": should_fee
        }
        class_array.append(class_data)
    
    # 构建完整的测试数据
    test_data = {
        # 主订单信息
        "sOrderCode": order_code,
        "sBatchCode": f"BATCH{random.randint(100, 999)}",
        "Discounttype": total_discount,  # 优惠金额
        "BizType": "报班",
        "sChannel": "直营",
        "sPayType": "现金支付",
        "sSchoolName": "南昌新东方培训学校",
        "sTelePhone": "400-175-9898",
        "sOperator": student_info.get('operator', 'system'),
        "dtCreate": get_beijing_time_str(),
        "feedBackTitle": "客服热线：400-175-9898",
        "feedBackImg": "",
        "microServiceTitle": "微信公众号：南昌新东方",
        "microServiceImg": "",
        "RWMImage": "",
        
        # 费用汇总
        "dShouldFee": total_should_fee,  # 应收金额
        "dFee": total_fee,  # 实收金额
        "dReturnFee": 0.0,  # 退费金额
        
        # 学生信息
        "Student": {
            "sStudentName": student_info.get('student_name', '测试学员'),
            "sStudentCode": f"STU{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}",
            "sGender": student_info.get('gender', '未知'),
            "sMobile": f"138{random.randint(10000000, 99999999)}"
        },
        
        # 班级和卡片信息数组
        "ClassAndCardArray": class_array
    }
    
    return test_data


def generate_test_class_certificate_data(student_info, student_code):
    """
    生成班级凭证测试数据 - 用于测试分页和集成打印功能
    
    参数:
        student_info: 学员基本信息
        student_code: 学员编码
    
    返回:
        班级凭证测试数据列表 (随机1-7条记录)
    """
    import random
    from datetime import datetime, timedelta
    
    # 随机生成1-7条班级凭证数据
    record_count = random.randint(1, 7)
    
    # 班级凭证模板数据
    class_templates = [
        {
            'class_code': 'MATH2024001', 
            'class_name': '初中数学培优班', 
            'subject': '数学',
            'teacher': '王老师',
            'room': '数学专用教室A'
        },
        {
            'class_code': 'ENG2024002', 
            'class_name': '高中英语强化班', 
            'subject': '英语',
            'teacher': '李老师',
            'room': '英语听力室B'
        },
        {
            'class_code': 'PHY2024003', 
            'class_name': '物理实验提高班', 
            'subject': '物理',
            'teacher': '张老师',
            'room': '物理实验室C'
        },
        {
            'class_code': 'CHEM2024004', 
            'class_name': '化学综合班', 
            'subject': '化学',
            'teacher': '赵老师',
            'room': '化学实验室D'
        },
        {
            'class_code': 'LANG2024005', 
            'class_name': '语文阅读写作班', 
            'subject': '语文',
            'teacher': '孙老师',
            'room': '文学阅览室E'
        },
        {
            'class_code': 'HIST2024006', 
            'class_name': '历史文化素养班', 
            'subject': '历史',
            'teacher': '周老师',
            'room': '人文教室F'
        },
        {
            'class_code': 'GEO2024007', 
            'class_name': '地理探索班', 
            'subject': '地理',
            'teacher': '吴老师',
            'room': '地理专用室G'
        }
    ]
    
    # 随机选择班级模板
    selected_templates = random.sample(class_templates, min(record_count, len(class_templates)))
    
    # 生成班级凭证数据
    class_certificate_records = []
    base_date = datetime.now()
    
    for i, template in enumerate(selected_templates):
        # 随机生成时间
        start_date = base_date + timedelta(days=random.randint(1, 30))
        end_date = start_date + timedelta(days=random.randint(60, 120))
        
        # 随机生成费用
        standard_fee = random.randint(1500, 2500)
        discount_fee = random.randint(100, 300)
        actual_fee = standard_fee - discount_fee
        
        # 生成卡片编码
        card_code = f"CARD{start_date.strftime('%Y%m')}{random.randint(1000, 9999)}"
        
        # 生成座位号
        seat_no = f"{chr(65 + i)}{str(random.randint(1, 30)).zfill(2)}"
        
        # 构建班级凭证数据
        certificate_data = {
            'biz_type': 5,  # 班级凭证
            'biz_name': '班级凭证',
            'data': {
                # 基本信息
                'sSchoolName': '南昌新东方培训学校',
                'sTelePhone': '400-175-9898',
                'sChannel': '直营',
                
                # 学员信息
                'sStudentName': student_info.get('student_name', '测试学员'),
                'sStudentCode': student_code,
                'sGender': student_info.get('gender', '未知'),
                'sCardCode': card_code,
                
                # 班级信息
                'sClassName': template['class_name'],
                'sClassCode': template['class_code'],
                'sSeatNo': seat_no,
                'sTeacher': template['teacher'],
                'sClassRoom': template['room'],
                'sSubject': template['subject'],
                
                # 时间信息
                'dtBeginDate': start_date.strftime('%Y-%m-%d'),
                'dtEndDate': end_date.strftime('%Y-%m-%d'),
                'sRegisterTime': f"{base_date.strftime('%Y-%m-%d')} 报名成功",
                'sPrintAddress': f"南昌市朝阳区学府路{random.randint(1, 999)}号{template['room']}",
                'sPrintTime': get_beijing_time_str(),
                'dtCreate': get_beijing_time_str(),
                
                # 费用信息（格式化为带人民币符号的字符串）
                'dFee': format_currency(standard_fee),  # 商品标准金额
                'dVoucherFee': format_currency(discount_fee),  # 商品优惠金额
                'dShouldFee': format_currency(standard_fee),  # 商品应收金额
                'dRealFee': format_currency(actual_fee),  # 商品实收金额
                
                # 试听信息
                'nTryLesson': '是' if random.choice([True, False]) else '否',
                'nTryLessonCount': str(random.randint(0, 3)),
                
                # 操作信息
                'sOperator': student_info.get('operator', 'system'),
                
                # 状态信息
                'sStatus': '已报名',
                'sPayStatus': '已缴费',
                
                # 图像数据（可选）
                'RWMImage': ''
            }
        }
        
        class_certificate_records.append(certificate_data)
    
    print(f"生成了 {len(class_certificate_records)} 条班级凭证测试数据")
    
    return class_certificate_records


def generate_test_class_certificate_for_printing(student_info, student_code, count=None):
    """
    专门为打印功能生成班级凭证测试数据
    
    参数:
        student_info: 学员基本信息
        student_code: 学员编码  
        count: 指定生成数量，None表示随机1-7条
    
    返回:
        适用于打印的班级凭证数据列表
    """
    if count is None:
        count = random.randint(1, 7)
    
    # 调用主要的生成函数
    class_records = generate_test_class_certificate_data(student_info, student_code)
    
    # 如果指定了数量，调整记录数
    if count != len(class_records):
        if count > len(class_records):
            # 需要更多记录，复制现有记录并修改
            additional_needed = count - len(class_records)
            for i in range(additional_needed):
                base_record = class_records[i % len(class_records)].copy()
                # 修改一些字段使其不同
                base_record['data']['sClassCode'] += f"_EXT{i+1}"
                base_record['data']['sClassName'] += f" (扩展班{i+1})"
                class_records.append(base_record)
        else:
            # 需要较少记录，截取
            class_records = class_records[:count]
    
    print(f"为打印功能生成了 {len(class_records)} 条班级凭证数据（分页测试用）")
    
    return class_records


if __name__ == "__main__":
    # 运行测试
    test_currency_format()