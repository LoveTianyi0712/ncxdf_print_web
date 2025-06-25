#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学员凭证搜索处理器

基于最新的凭证信息.py文件重新设计
功能：
- search_student(): 搜索学员所有类型的凭证记录
- search_order(): 根据订单号搜索报班凭证

使用示例：
    from utils.certificate_processors.search_student_certificate import search_student
    
    result = search_student(None, current_user, 'NC12345678')
"""

import json
import requests
from datetime import datetime

def format_currency(amount):
    """
    格式化金额显示
    
    参数:
        amount: 金额数值或字符串
    
    返回:
        格式化后的金额字符串，如 "¥1,234.56"
    """
    if amount is None or amount == '':
        return "¥0.00"
    
    # 如果已经是带货币符号的字符串，先清理
    if isinstance(amount, str):
        amount = amount.replace('¥', '').replace(',', '').strip()
        if amount == '':
            return "¥0.00"
    
    try:
        # 转换为浮点数，保留2位小数
        amount = float(amount)
        # 使用千分位分隔符格式化
        return f"¥{amount:,.2f}"
    except (ValueError, TypeError):
        return "¥0.00"


def generate_certificate_description(biz_type, data):
    """
    为不同类型的凭证生成缩略描述信息
    
    参数:
        biz_type: 业务类型 (1=报班, 3=退班, 4=高端, 5=高端报名, 6=充值提现)
        data: 凭证数据
    
    返回:
        描述字符串
    """
    if not data:
        return ""
    
    try:
        print(f"生成凭证描述 - 业务类型: {biz_type}, 数据键: {list(data.keys())[:10]}")  # 调试信息
        if biz_type == 1:  # 报班凭证
            # 提取班级信息和费用
            classes = []
            total_fee = 0
            
            if 'ClassAndCardArray' in data and data['ClassAndCardArray']:
                print(f"报班凭证 - 找到 {len(data['ClassAndCardArray'])} 个班级")  # 调试
                for class_info in data['ClassAndCardArray']:
                    print(f"报班凭证 - 班级数据: {class_info}")  # 调试
                    class_name = class_info.get('sClassName', '')
                    print(f"报班凭证 - 提取班级名称: '{class_name}'")  # 调试
                    if class_name:  # 简化条件，只要有班级名称就添加
                        classes.append(class_name)
                        print(f"报班凭证 - 添加班级: {class_name}")  # 调试
                    # 累计费用
                    fee = class_info.get('dShouldFee', 0) or class_info.get('dFee', 0)
                    if fee:
                        total_fee += float(fee)
                        print(f"报班凭证 - 添加费用: {fee}")  # 调试
            
            # 如果没有班级信息，尝试从其他字段获取
            if not classes:
                if data.get('sClassName'):
                    classes.append(data['sClassName'])
                elif data.get('className'):
                    classes.append(data['className'])
            
            # 如果没有费用信息，尝试从其他字段获取
            if total_fee == 0:
                if data.get('dFee'):
                    total_fee = float(data['dFee'])
                elif data.get('dShouldFee'):
                    total_fee = float(data['dShouldFee'])
            
            # 构建描述
            print(f"报班凭证 - 最终班级列表: {classes}")  # 调试
            print(f"报班凭证 - 最终班级列表长度: {len(classes)}")  # 调试
            print(f"报班凭证 - 总费用: {total_fee}")  # 调试
            
            if classes:
                joined_classes = ', '.join(classes[:2])
                print(f"报班凭证 - joined_classes结果: '{joined_classes}'")  # 调试
                class_text = f"班级：{joined_classes}"  # 最多显示2个班级
                if len(classes) > 2:
                    class_text += f"等{len(classes)}个班级"
            else:
                class_text = "班级：未知"
            
            print(f"报班凭证 - 生成的班级文本: '{class_text}'")  # 调试
            
            if total_fee > 0:
                result = f"{class_text}，费用：{format_currency(total_fee)}"
            else:
                result = class_text
                
            print(f"报班凭证 - 最终描述: '{result}'")  # 调试
            return result
                
        elif biz_type == 3:  # 退班凭证
            # 提取退班信息
            classes = []
            refund_fee = 0
            
            if 'ClassAndCardArray' in data and data['ClassAndCardArray']:
                print(f"退班凭证 - 找到 {len(data['ClassAndCardArray'])} 个班级")  # 调试
                for class_info in data['ClassAndCardArray']:
                    print(f"退班凭证 - 班级数据: {class_info}")  # 调试
                    class_name = class_info.get('sOldClassName', '')
                    print(f"退班凭证 - 提取班级名称: '{class_name}'")  # 调试
                    if class_name:  # 简化条件，只要有班级名称就添加
                        classes.append(class_name)
                        print(f"退班凭证 - 添加班级: {class_name}")  # 调试
                    # 累计退费
                    fee = class_info.get('dQuitFee', 0) or class_info.get('dShouldQuitFee', 0)
                    if fee:
                        refund_fee += abs(float(fee))  # 退费通常是负数，取绝对值
                        print(f"退班凭证 - 添加退费: {abs(float(fee))}")  # 调试
            
            if not classes and data.get('sClassName'):
                classes.append(data['sClassName'])
            
            # 如果没有退费信息，尝试从其他字段获取
            if refund_fee == 0:
                if data.get('dQuitFee'):
                    refund_fee = abs(float(data['dQuitFee']))
                elif data.get('dShouldQuitFee'):
                    refund_fee = abs(float(data['dShouldQuitFee']))
            
            # 构建描述
            print(f"退班凭证 - 最终班级列表: {classes}")  # 调试
            print(f"退班凭证 - 退费金额: {refund_fee}")  # 调试
            
            if classes:
                class_text = f"退班：{', '.join(classes[:2])}"
                if len(classes) > 2:
                    class_text += f"等{len(classes)}个班级"
            else:
                class_text = "退班"
            
            print(f"退班凭证 - 生成的班级文本: '{class_text}'")  # 调试
            
            if refund_fee > 0:
                result = f"{class_text}，退费：{format_currency(refund_fee)}"
            else:
                result = class_text
                
            print(f"退班凭证 - 最终描述: '{result}'")  # 调试
            return result
                
        elif biz_type == 4 or biz_type == 5:  # 高端报名凭证
            product_name = data.get('productName', '高端产品')
            lesson_num = data.get('lessonNum', 0)
            lesson_fee = data.get('lessonFee', 0)
            
            if lesson_num and lesson_fee:
                return f"产品：{product_name}，{lesson_num}课时，费用：{format_currency(lesson_fee)}"
            elif lesson_num:
                return f"产品：{product_name}，{lesson_num}课时"
            else:
                return f"产品：{product_name}"
                
        elif biz_type == 6:  # 充值提现凭证
            biz_type_name = data.get('sBizType', '操作')
            pay_amount = 0
            
            # 从支付信息中提取金额
            pay_type = data.get('sPayType', '')
            if '¥' in pay_type:
                import re
                amounts = re.findall(r'¥([\d,]+(?:\.\d+)?)', pay_type)
                if amounts:
                    pay_amount = float(amounts[0].replace(',', ''))
            
            if pay_amount > 0:
                return f"类型：{biz_type_name}，金额：{format_currency(pay_amount)}"
            else:
                return f"类型：{biz_type_name}"
        
        return ""
        
    except Exception as e:
        print(f"生成凭证描述失败: {str(e)}")
        return ""

# 默认headers配置
DEFAULT_HEADERS = {
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

# 默认Cookies配置（实际使用时应该从用户会话或数据库获取）
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


def getProofByBizType(cookies, biz_type, proof_print_code):
    """
    根据业务类型和凭证打印代码获取凭证信息
    
    参数:
        cookies: 认证cookies字典
        biz_type: 业务类型 (1=报班凭证, 3=退班凭证等)
        proof_print_code: 凭证打印代码(批次代码)
    
    返回:
        成功: 返回凭证信息字典
        失败: 抛出异常
    """
    print(f"getProofByBizType 开始获取凭证，业务类型: {biz_type}, 批次代码: {proof_print_code}")
    
    headers = DEFAULT_HEADERS
    
    json_data = {
        'BizType': biz_type,
        'ProofPrintCode': proof_print_code,
        'SchoolId': 35,
    }

    try:
        response = requests.post(
            'https://erp.xdf.cn/apinisbff/api/print/getProofByBizType',
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        
        if response.status_code != 200:
            raise Exception(f"API请求失败，状态码: {response.status_code}")
        
        response_data = response.json()
        json_string = response_data['Data']['JsonString']
        json1 = json.loads(json_string)
        return json1[0]
        
    except Exception as e:
        print(f"获取批次 {proof_print_code} 的凭证信息失败: {str(e)}")
        raise


def search_ORDER(cookies, order_code):
    """
    根据订单号获取报班凭证信息
    
    参数:
        cookies: 认证cookies字典
        order_code: 订单号
    
    返回:
        成功: 返回包含报班凭证信息的列表
        失败: 返回空列表
    """
    print(f"search_ORDER 开始查询订单号: {order_code}")
    
    headers = DEFAULT_HEADERS
    
    json_data = {
        'schoolId': 35,
        'pageIndex': 1,
        'pageSize': 10,
        'orderCode': order_code,
        'batchCode': None,
        'studentCode': None,
        'studentName': None,
        'classCode': None,
        'goodsCode': None,
        'operateTypeCode': None,
        'batchStatus': None,
        'operateName': None,
        'createdOperator': None,
        'channel': None,
        'systemSource': None,
        'payOpName': None,
        'operateDate': None,
        'payStatus': None,
    }

    try:
        response = requests.post(
            'https://erp.xdf.cn/nises/apinises/order/OrderQueryWithPrivilege',
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        
        if response.status_code != 200:
            return []
        
        result = []
        for p in response.json()['Data']['Data']:
            try:
                # 只处理报班凭证，过滤掉退班凭证
                if p.get('operateType') == '报班':
                    biz_type = 1  # 报班凭证
                    biz_name = '报班凭证'
                    tips = getProofByBizType(cookies, biz_type, p['batchCode'])
                    if tips:
                        result.append({
                            'biz_type': biz_type,
                            'biz_name': biz_name,
                            'data': tips,
                            'description': generate_certificate_description(biz_type, tips)
                        })
            except:
                continue
        return result
        
    except Exception as e:
        print(f"查询订单 {order_code} 失败: {str(e)}")
        return []


def search_HighORDER(cookies, order_code):
    """
    查询高端订单信息
    """
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://erp.xdf.cn/vipnis/out-order/list?schoolId=35&systemSource=bm3&appId=bm3t%3D1750734573946',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        'X-Requested-With': 'XMLHttpRequest',
        'schoolId': '35',
        'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        'searchCondition': order_code,
        'pageNo': '1',
        'pageSize': '10',
        'schoolId': '35',
        'listFlag': '2',
        't': '1750735627806',
    }
    
    try:
        response = requests.get(
            'https://erp.xdf.cn/biz-vipnis/api/v1/biz/order/getOrderList',
            params=params,
            cookies=cookies,
            headers=headers,
        )
        
        if response.status_code != 200:
            return None
            
        order_data = response.json()['data']['orderInfoList'][0]
        x = getProofByHighBizType(cookies, order_code)
        if x:
            x['totalAmount'] = order_data['totalAmount']
            x['realAmount'] = order_data['realAmount']
            x['recieveAmount'] = order_data['recieveAmount']
            x['discountAmount'] = order_data['discountAmount']
            
            # 返回标准格式
            return {
                'biz_type': 5,  # 高端报名凭证
                'biz_name': '高端报名凭证',
                'data': x,
                'description': generate_certificate_description(5, x)
            }
        return None
        
    except Exception as e:
        print(f"查询高端订单 {order_code} 失败: {str(e)}")
        return None


def getProofByHighBizType(cookies, order_code):
    """
    获取高端订单凭证信息
    """
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://erp.xdf.cn/vipnis/out-order/list?schoolId=35&systemSource=bm3&appId=bm3t%3D1750734573946',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        'X-Requested-With': 'XMLHttpRequest',
        'schoolId': '35',
        'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        'orderCode': order_code,
        'schoolId': '35',
        't': '1750732256246',
    }

    try:
        response = requests.get(
            'https://erp.xdf.cn/biz-vipnis/api/v1/biz/order/getOrderInfo',
            params=params,
            cookies=cookies,
            headers=headers,
        )
        
        if response.status_code != 200:
            return None
            
        data = response.json()['data']
        
        try:
            return {
                "contractNo": data['productInfoList'][0]['contractNo'],
                'payTime': data['payTime'],
                'phone': data['phone'],
                'productName': data['productInfoList'][0]['productName'],
                'buyLessonNum': data['productInfoList'][0]['buyLessonNum'],
                'giftLessonNum': data['productInfoList'][0]['giftLessonNum'],
                'lessonNum': data['productInfoList'][0]['lessonNum'],
                'gradeName': data['gradeName'],
                'lessonFee': data['productInfoList'][0]['lessonFee'],
                'studentCode': data['studentCode'],
                'studentName': data['studentName'],
                'orderCode': data['orderCode'],
                'payInfo': f'{data["payInfo"][0]["payType"]}:¥{data["payInfo"][0]["payAmount"]}'
            }
        except:
            return None
            
    except Exception as e:
        print(f"获取高端订单凭证信息失败: {str(e)}")
        return None


def search_student(cookies, current_user, student_code):
    """
    根据学员号搜索学员的所有凭证信息
    基于新的凭证信息.py文件逻辑重新实现
    
    参数:
        cookies: 认证cookies字典 
        current_user: 当前用户对象
        student_code: 学员号
    
    返回:
        成功: 返回包含所有凭证信息的列表
        失败: 返回0(学员不存在)或404(请求失败)
    """
    print(f"search_student 开始查询学员: {student_code}")
    
    # 如果没有提供cookies，使用默认cookies
    if not cookies:
        cookies = DEFAULT_COOKIES
    
    headers = DEFAULT_HEADERS
    
    # 1. 查询学员基本信息
    json_data = {
        'SchoolId': 35,
        'QueryValue': student_code,
        'PageIndex': 1,
        'PageSize': 10,
    }
    
    try:
        response = requests.post(
            'https://erp.xdf.cn/apinisbff/Student/QueryStudentWithBound',
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        
        print(f"QueryStudentWithBound API 响应状态码: {response.status_code}")
        if response.status_code == 200:
            response_json = response.json()
            print(f"API 响应消息: {response_json.get('Msg', 'No message')}")
            print(f"API 响应结构: {list(response_json.keys())}")
            if 'Data' in response_json:
                print(f"Data字段类型: {type(response_json['Data'])}")
                if response_json['Data']:
                    print(f"Data字段内容预览: {str(response_json['Data'])[:200]}...")
        elif response.status_code == 403:
            # 处理403错误，通常表示认证失败
            print(f"API 响应内容: {response.text}")
            try:
                response_json = response.json()
                if response_json.get('msg') == 'REDIRECT TO SSO' or 'redirect' in response_json:
                    print("检测到SSO重定向，cookies已过期")
                    print("解决方案：")
                    print("1. 重新登录ERP系统")
                    print("2. 获取最新的cookies")
                    print("3. 在系统中更新cookies配置")
                else:
                    print(f"403错误详情: {response_json}")
            except:
                print("403错误，无法解析响应内容")
            return 404
        else:
            print(f"API 响应内容: {response.text[:500]}...")
        
        if response.status_code != 200:
            return 404
            
        response_json = response.json()
        if response_json.get('Msg') == '没有找到学员！':
            return 0
        
        # 检查是否真的找到了学员数据
        if not response_json.get('Data') or not response_json['Data'].get('studentInfo') or not response_json['Data']['studentInfo'].get('Data'):
            print("API返回成功但没有找到学员数据")
            return 0
        
        student_list = response_json['Data']['studentInfo']['Data']
        if not student_list:
            print("学员数据列表为空")
            return 0
        
        print(f"找到 {len(student_list)} 个学员记录")
        # 使用第一个学员记录
        student_info = student_list[0]
        print(f"学员信息: {student_info.get('Name', '未知')} ({student_info.get('Code', '未知')})")
        
    except Exception as e:
        print(f"查询学员基本信息失败: {str(e)}")
        return 404
    
    # 2. 查询学员充值提现记录
    json_data1 = {
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
    
    try:
        response1 = requests.post(
            'https://erp.xdf.cn/nises/apinises/StuStoreAccount/QueryStoreOrderPage',
            cookies=cookies,
            headers=headers,
            json=json_data1,
        )
    except Exception as e:
        print(f"查询充值提现记录失败: {str(e)}")
        response1 = None
    
    # 3. 查询学员性别信息
    json_data = {
        'SchoolId': 35,
        'StudentCode': student_code,
        'EnType': True,
    }
    
    try:
        response = requests.post('https://erp.xdf.cn/apinisbff/Student/QueryBrief', 
                               cookies=cookies, headers=headers, json=json_data)
        query_brief = response.json()['Data']
        s_gender = query_brief['Gender']
        if s_gender == 1:
            s_gender = '男'
        elif s_gender == 2:
            s_gender = '女'
        elif s_gender == 3:
            s_gender = '未知'
        else:
            s_gender = '未知'
    except Exception as e:
        print(f"查询学员性别失败: {str(e)}")
        s_gender = '未知'
    
    # 4. 查询班级信息
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
    
    try:
        response = requests.post(
            'https://erp.xdf.cn/nises/apinises/roster/homePageRosterRecordQuerySign',
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        class_data = response.json()['Data']['Data'] if response.status_code == 200 else []
    except Exception as e:
        print(f"查询班级信息失败: {str(e)}")
        class_data = []
    
    # 5. 查询订单信息
    json_data2 = {
        'schoolId': 35,
        'pageIndex': 1,
        'pageSize': 40,
        'orderCode': None,
        'batchCode': None,
        'studentCode': student_code,
        'studentName': None,
        'classCode': None,
        'goodsCode': None,
        'operateTypeCode': None,
        'batchStatus': None,
        'operateName': None,
        'createdOperator': None,
        'channel': None,
        'systemSource': None,
        'payOpName': None,
        'operateDate': None,
        'payStatus': None,
    }
    
    try:
        response2 = requests.post(
            'https://erp.xdf.cn/nises/apinises/order/OrderQueryWithPrivilege',
            cookies=cookies,
            headers=headers,
            json=json_data2,
        )
        order_data = response2.json()['Data']['Data'] if response2.status_code == 200 else []
    except Exception as e:
        print(f"查询订单信息失败: {str(e)}")
        order_data = []
    
    # 6. 查询高端订单信息
    params = {
        'operateTypeCode': 'B',
        'searchCondition': student_code,
        'pageNo': '1',
        'pageSize': '40',
        'schoolId': '35',
        'listFlag': '2',
        't': '1750731323395',
    }

    try:
        response3 = requests.get(
            'https://erp.xdf.cn/biz-vipnis/api/v1/biz/order/getOrderList',
            params=params,
            cookies=cookies,
            headers=headers,
        )
        high_order_data = response3.json()['data']['orderInfoList'] if response3.status_code == 200 else []
    except Exception as e:
        print(f"查询高端订单信息失败: {str(e)}")
        high_order_data = []
    
    # 7. 组装数据
    data = []
    
    # 7.1 添加班级凭证
    for d in class_data:
        a = {
            'biz_type': 101,  # 班级凭证
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
                'nTryLesson': d['TryLesson'],
                # 时间信息
                'sRegisterTime': d['PrintTime'],
                'sPrintAddress': d['PrintAddress'],
                'sPrintTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                # 费用信息
                'dFee': d['Fee'],  # 商品标准金额
                'dVoucherFee': d['Voucher'],  # 商品优惠金额
                'dShouldFee': d['Fee'],  # 商品应收金额
                'dRealFee': d['UsedPay'],  # 商品实收金额
                # 操作信息
                'sOperator': current_user.username,
                # 图像数据（可选）
                'RWMImage': '',
            }
        }
        data.append(a)
    
    # 7.2 添加充值提现凭证
    if response1 and response1.status_code == 200:
        for B in response1.json()['Data']['Data']:
            if B['OrderTypeName'] == '学员账户充值提现':
                certificate_data = {
                    "nSchoolId": 35,
                    "sSchoolName": "南昌学校",
                    "sTelePhone": "400-175-9898",
                    "sOperator": current_user.name if current_user.name else current_user.username,
                    "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Title": "提现凭证",
                    "PrintNumber": 1,
                    "YNVIEWPrint": 1,
                    "PrintDocument": "",
                    "sStudentCode": B['StudentCode'],
                    "sStudentName": B['StudentName'],
                    "sGender": s_gender,
                    "dSumBalance": f"余额：¥{B['Balance']}",
                    "sOperationAmount": f"提现金额：¥{B['Pay']}",
                    "sPayType": f"{B['PayTypeName']}：{B['PayTypeName']}¥{B['Pay']}",
                    "dtCreateDate": B['TransactionTime'],
                    "sProofName": "学员账户充值提现凭证",
                    "sBizType": "提现",
                    "sRegZoneName": "客服行政"
                }
                c = {
                    'biz_type': 6,
                    'biz_name': '学员账户充值提现凭证',
                    'data': certificate_data,
                    'description': generate_certificate_description(6, certificate_data)
                }
                data.append(c)
            elif B['OrderTypeName'] == '学员账户充值':
                certificate_data = {
                    "nSchoolId": 35,
                    "sSchoolName": "南昌学校",
                    "sTelePhone": "400-175-9898",
                    "sOperator": current_user.name if current_user.name else current_user.username,
                    "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Title": "充值凭证",
                    "PrintNumber": 1,
                    "YNVIEWPrint": 1,
                    "PrintDocument": "",
                    "sStudentCode": B['StudentCode'],
                    "sStudentName": B['StudentName'],
                    "sGender": s_gender,
                    "dSumBalance": f"余额：¥{B['Balance']}",
                    "sOperationAmount": f"充值金额：¥{B['Pay']}",
                    "sPayType": f"{B['PayTypeName']}：{B['PayTypeName']}¥{B['Pay']}",
                    "dtCreateDate": B['TransactionTime'],
                    "sProofName": "学员账户充值凭证",
                    "sBizType": "充值",
                    "sRegZoneName": "客服行政"
                }
                c = {
                    'biz_type': 6,
                    'biz_name': '学员账户充值凭证',
                    'data': certificate_data,
                    'description': generate_certificate_description(6, certificate_data)
                }
                data.append(c)
    
    # 7.3 添加报班凭证（过滤掉退班数据）
    for C in order_data:
        # 只处理报班数据，退班数据不显示
        if C['batchStatusName'] == '交易成功' and C['operateType'] == '报班':
            try:
                F = getProofByBizType(cookies, 1, C['batchCode'])  # 1 = 报班凭证
                if F:
                    description = generate_certificate_description(1, F)
                    print(f"报班凭证添加到结果 - 批次: {C['batchCode']}, 描述: '{description}'")  # 调试
                    data.append({
                        'biz_type': 1,
                        'biz_name': '报班凭证',
                        'data': F,
                        'description': description
                    })
            except Exception as e:
                print(f"获取报班凭证失败: {str(e)}")
                continue
    
    # 7.4 添加高端订单凭证
    for D in high_order_data:
        try:
            x = getProofByHighBizType(cookies, D['orderCode'])
            if x:
                x['totalAmount'] = D['totalAmount']
                x['realAmount'] = D['realAmount']
                x['recieveAmount'] = D['recieveAmount']
                x['discountAmount'] = D['discountAmount']
                data.append({
                    'biz_type': 4,  # 假设高端订单凭证使用biz_type 4
                    'biz_name': '高端报名凭证',
                    'data': x,
                    'description': generate_certificate_description(4, x)
                })
        except Exception as e:
            print(f"获取高端订单凭证失败: {str(e)}")
            continue
    
    print(f"search_student 返回 {len(data)} 条凭证记录")
    
    # 返回标准格式，包含学员信息和凭证列表
    return {
        'student_name': student_info.get('Name', '未知'),
        'student_code': student_info.get('Code', student_code),
        'gender': s_gender,
        'operator': current_user.name if current_user and current_user.name else current_user.username if current_user else '系统',
        'reports': data
    }


def search_order(cookies, current_user, order_code):
    """
    根据订单号搜索凭证信息（统一返回格式）
    
    参数:
        cookies: 认证cookies字典
        current_user: 当前用户对象  
        order_code: 订单号
    
    返回:
        成功: 返回与search_student相同的格式
        失败: 返回0或404
    """
    print(f"search_order 开始查询订单号: {order_code}")
    
    # 如果没有提供cookies，使用默认cookies
    if not cookies:
        cookies = DEFAULT_COOKIES
    
    # 1. 尝试查询普通订单
    reports = search_ORDER(cookies, order_code)
    
    # 2. 如果普通订单没有结果，尝试查询高端订单
    if not reports:
        high_order = search_HighORDER(cookies, order_code)
        if high_order:
            reports = [high_order]
    
    if not reports:
        print("未找到订单凭证信息")
        return 0
    
    # 3. 尝试从凭证数据中提取学员信息
    student_name = '未知'
    student_code = '未知'
    
    # 从第一个凭证中提取学员信息
    if reports and reports[0].get('data'):
        first_report = reports[0]['data']
        
        # 尝试多种方式获取学员信息
        if 'Student' in first_report and first_report['Student']:
            student_info = first_report['Student']
            student_name = student_info.get('sStudentName', '未知')
            student_code = student_info.get('sStudentCode', '未知')
        else:
            student_name = first_report.get('sStudentName') or first_report.get('studentName') or '未知'
            student_code = first_report.get('sStudentCode') or first_report.get('studentCode') or '未知'
        
        print(f"订单查询 - 提取学员信息: 姓名={student_name}, 编码={student_code}")  # 调试
    
    # 4. 返回与search_student相同的格式
    result = {
        'student_name': student_name,
        'student_code': student_code,
        'gender': '未知',
        'operator': current_user.name if current_user and current_user.name else current_user.username if current_user else '系统',
        'reports': reports,
        'order_code': order_code  # 额外添加订单号字段
    }
    
    print(f"search_order 返回 {len(reports)} 条凭证记录")
    return result


def search_student_classes(cookies, current_user, student_code):
    """
    search_student函数的别名，用于向后兼容
    
    参数:
        cookies: 认证cookies字典
        current_user: 当前用户对象
        student_code: 学员号
    
    返回:
        与search_student相同的返回格式
    """
    return search_student(cookies, current_user, student_code)


# 测试函数保持不变
def test_currency_format():
    print("Testing currency format...")
    test_cases = [
        (1234.56, "¥1,234.56"),
        ("1234.56", "¥1,234.56"),
        ("¥1,234.56", "¥1,234.56"),
        (0, "¥0.00"),
        ("", "¥0.00"),
        (None, "¥0.00"),
        ("invalid", "¥0.00"),
    ]
    
    for amount, expected in test_cases:
        result = format_currency(amount)
        status = "✓" if result == expected else "✗"
        print(f"  {status} format_currency({amount!r}) = {result!r} (expected: {expected!r})")


def validate_cookies(cookies):
    """
    验证cookies是否有效
    
    参数:
        cookies: 认证cookies字典
    
    返回:
        True: cookies有效
        False: cookies无效
    """
    print("开始验证cookies有效性...")
    
    headers = DEFAULT_HEADERS
    json_data = {
        'SchoolId': 35,
        'QueryValue': 'TEST',  # 使用测试查询
        'PageIndex': 1,
        'PageSize': 1,
    }
    
    try:
        response = requests.post(
            'https://erp.xdf.cn/apinisbff/Student/QueryStudentWithBound',
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("Cookies验证成功 ✓")
            return True
        elif response.status_code == 403:
            try:
                response_json = response.json()
                if response_json.get('msg') == 'REDIRECT TO SSO':
                    print("Cookies已过期，需要重新登录 ✗")
                else:
                    print(f"Cookies验证失败: {response_json} ✗")
            except:
                print("Cookies验证失败：403错误 ✗")
            return False
        else:
            print(f"Cookies验证失败，状态码: {response.status_code} ✗")
            return False
            
    except Exception as e:
        print(f"Cookies验证异常: {e} ✗")
        return False


def get_cookies_help_text():
    """
    返回获取cookies的帮助文本
    """
    return """
=== 如何获取最新的Cookies ===

1. 清除浏览器缓存：
   - 按 Ctrl+Shift+Delete 清除缓存
   - 或使用无痕/隐私模式

2. 重新登录ERP系统：
   - 访问 https://erp.xdf.cn
   - 输入用户名和密码登录

3. 获取Cookies：
   - 按F12打开开发者工具
   - 切换到Network标签页
   - 在ERP中进行任意操作
   - 找到请求，查看Request Headers中的Cookie字段
   - 复制完整的Cookie字符串

4. 更新系统配置：
   - 在打印系统中访问"Cookies配置"页面
   - 添加新配置或更新现有配置
   - 粘贴新的cookies数据

注意：Cookies通常几小时后会过期，需要定期更新。
"""

if __name__ == "__main__":
    test_currency_format()