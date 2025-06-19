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
                        'sPrintTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
                if record.get('OrderTypeName') == '学员账户充值提现':
                    certificate_data = {
                        'biz_type': 6,  # 学员账户凭证
                        'biz_name': '学员账户充值提现凭证',
                        'data': {
                            "nSchoolId": 35,
                            "sSchoolName": "南昌学校",
                            "sTelePhone": "400-175-9898",
                            "sOperator": student_info.get('operator', 'system'),
                            "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Title": "充值提现凭证",
                            "PrintNumber": 1,
                            "YNVIEWPrint": 1,
                            "PrintDocument": "",
                            "sStudentCode": record['StudentCode'],
                            "sStudentName": student_info.get('student_name') or record.get('StudentName') or '未知姓名',
                            "sGender": student_info.get('gender', '未知'),
                            "sPay": format_currency(record.get('Pay', 0)),
                            "dSumBalance": format_currency(record.get('Balance', 0)),
                            "sPayType": f"{record.get('PayTypeName', '未知')}：¥{record.get('Pay', 0)}",
                            "dtCreateDate": record.get('TransactionTime', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            "sProofName": "学员账户充值提现凭证",
                            "sBizType": "充值提现",
                            "sRegZoneName": "客服行政"
                        }
                    }
                    account_records.append(certificate_data)
                elif record.get('OrderTypeName') == '学员账户充值':
                    certificate_data = {
                        'biz_type': 6,  # 学员账户凭证
                        'biz_name': '学员账户充值凭证',
                        'data': {
                            "nSchoolId": 35,
                            "sSchoolName": "南昌学校",
                            "sTelePhone": "400-175-9898",
                            "sOperator": student_info.get('operator', 'system'),
                            "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Title": "充值凭证",
                            "PrintNumber": 1,
                            "YNVIEWPrint": 1,
                            "PrintDocument": "",
                            "sStudentCode": record['StudentCode'],
                            "sStudentName": student_info.get('student_name') or record.get('StudentName') or '未知姓名',
                            "sGender": student_info.get('gender', '未知'),
                            "sPay": format_currency(record.get('Pay', 0)),
                            "dSumBalance": format_currency(record.get('Balance', 0)),
                            "sPayType": f"{record.get('PayTypeName', '未知')}：¥{record.get('Pay', 0)}",
                            "dtCreateDate": record.get('TransactionTime', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                            "sProofName": "学员账户充值凭证",
                            "sBizType": "充值",
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


if __name__ == "__main__":
    # 运行测试
    test_currency_format()