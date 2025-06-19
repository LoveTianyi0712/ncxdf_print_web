#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
班级凭证搜索模块

该模块提供搜索学生班级信息的功能，并返回格式化的班级凭证数据。

主要功能：
- search_student(): 根据学生编号搜索班级信息
- search_student_classes(): search_student的别名函数

使用示例：
    from utils.certificate_processors.search_class_certificate import search_student
    
    # 使用默认配置搜索
    result = search_student(None, current_user, 'NC12345678')
    
    # 使用自定义cookies搜索
    my_cookies = {'key': 'value'}
    result = search_student(my_cookies, current_user, 'NC12345678')

返回值：
- 成功: 返回包含班级凭证数据的列表
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


def search_student(cookies, current_user, student_code):
    """
    搜索学生班级信息
    
    参数:
        cookies: 认证cookies字典，如果为None或空，将使用DEFAULT_COOKIES
        current_user: 当前用户对象，用于记录操作者信息
        student_code: 学生编号字符串
    
    返回:
        成功: 返回班级凭证数据列表，每个元素包含biz_type、biz_name和data字段
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
            return 404
            
        if response.json()['Msg'] == '没有找到学员！':
            return 0
        
        # 第二步：获取学生详细信息
        json_data = {
            'SchoolId': 35,
            'StudentCode': student_code,  # 修复：使用实际的student_code参数
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
            return 404
            
        query_brief = response.json()['Data']
        s_gender = query_brief['Gender']
        if s_gender == 1:
            s_gender = '男'
        elif s_gender == 2:
            s_gender = '女'
        elif s_gender == 3:
            s_gender = '未知'

        # 第三步：查询学生的班级信息
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
        
        if response.status_code != 200:
            return 404
        
        # 构造班级凭证数据
        data = []
        for d in response.json()['Data']['Data']:
            certificate_data = {
                'biz_type': 5,  # 班级凭证（使用老系统的编码）
                'biz_name': '班级凭证',
                'data': {
                    # 基本信息
                    'sSchoolName': '南昌学校',
                    'sTelePhone': '400-175-9898',
                    'sChannel': '直营',
                    # 学员信息
                    'sStudentName': d['StudentName'],
                    'sStudentCode': d['StudentCode'],
                    'sGender': s_gender,
                    'sCardCode': d['CardCode'],
                    # 班级信息
                    'sClassName': d['ClassName'],
                    'sClassCode': d['ClassCode'],
                    'sSeatNo': d['CardCode'][-1] if d['CardCode'][-2] == '0' else d['CardCode'][-2:],
                    'dtBeginDate': d['BeginDate'],
                    'dtEndDate': d['EndDate'],
                    'nTryLesson': '是' if d['TryLesson'] else '否',
                    # 时间信息
                    'sRegisterTime': d['PrintTime'],
                    'sPrintAddress': d['PrintAddress'],
                    'sPrintTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    # 费用信息（格式化为带人民币符号的字符串）
                    'dFee': format_currency(d['Fee']),  # 商品标准金额
                    'dVoucherFee': format_currency(d['Voucher']),  # 商品优惠金额
                    'dShouldFee': format_currency(d['Fee']),  # 商品应收金额
                    'dRealFee': format_currency(d['UsedPay']),  # 商品实收金额
                    # 操作信息
                    'sOperator': current_user.username,
                    # 图像数据（可选）
                    'RWMImage': ''
                }
            }
            data.append(certificate_data)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {str(e)}")
        return 404
    except Exception as e:
        print(f"搜索学生班级信息时发生错误: {str(e)}")
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