import requests
from datetime import datetime
cookies = {
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
def  getProofByBizType(cookies,BizType,ProofPrintCode):
    json_data = {
        'BizType': BizType,
        'ProofPrintCode': ProofPrintCode,
        'SchoolId': 35,
    }

    response = requests.post(
        'https://erp.xdf.cn/apinisbff/api/print/getProofByBizType',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )
    json1 = json.loads(response.json()['Data']['JsonString'])
    return json1[0]
def  search_ORDER(cookies,orderCode):
    json_data = {
        'schoolId': 35,
        'pageIndex': 1,
        'pageSize': 10,
        'orderCode': orderCode,
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

    response = requests.post(
        'https://erp.xdf.cn/nises/apinises/order/OrderQueryWithPrivilege',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )
    RESULT=[]
    for p in response.json()['Data']['Data']:
        try:
            tips=getProofByBizType(cookies,p['batchCode'])
            RESULT.append(tips)
        except:
            continue
    return RESULT
def  search_HighORDER(cookies,orderCode):
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
        # 'Cookie': 'XDFUUID=eba414a3-3d55-2c52-02df-15e47928df05; gr_user_id=508c0b87-509e-4054-be65-123bb26726e1; x-e-dr=4c0f1940-5a62-4de3-987a-fcffb8314cd7; 863788c8cb539c69_gr_last_sent_cs1=gongjiajun@xdf.cn; 863788c8cb539c69_gr_cs1=gongjiajun@xdf.cn; e2e=ED200D127224ED3B00CE57AFCFE3C3CD; e2mf=cde5e1cdb33049588f0192b28ad2bb69; casgwusercred=W1bsAsnLkPk56SnJo8JnNM3ns67vUmsp0BjEBra2-R-_9k79NTAwhOxGj7-0s0GVn0KQl1L2FHSx6IXiN_07ikGrq5KzA-dne3R-gI0LbTXZTf44wyFvLFC0MT6x6Vf2MopnmeRfF_NnoOnlYqr0ZY4HhKpIbeyxwAc0zjPLzJA; crosgwusercred=ybvwXmec6AR0jUMNKBBPEihvTihHFtO1gFGpDkn_w2IllXb-FqbOrSqqregaraUBZrOD_I3pP7xP6qKTSGuS6ge24f46dc02e800d767a8b591dc2b7932; erpUserId=xujia57; FE_USER_CODE=NC2411l2kOrc; FE_USER_NAME=%E5%BE%90%E4%BD%B357; erpSchoolId=35',
    }

    params = {
        'searchCondition': orderCode,
        'pageNo': '1',
        'pageSize': '10',
        'schoolId': '35',
        'listFlag': '2',
        't': '1750735627806',
    }
    response = requests.get(
        'https://erp.xdf.cn/biz-vipnis/api/v1/biz/order/getOrderList',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    D=response.json()['data']['orderInfoList'][0]
    x=getProofByHighBizType(cookies,orderCode)
    x['totalAmount'] = D['totalAmount']
    x['realAmount'] = D['realAmount']
    x['recieveAmount'] = D['recieveAmount']
    x['discountAmount'] = D['discountAmount']
    return RESULT


def  getProofByHighBizType(cookies,orderCode):
    params = {
        'orderCode': orderCode,
        'schoolId': '35',
        't': '1750732256246',
    }

    response = requests.get(
        'https://erp.xdf.cn/biz-vipnis/api/v1/biz/order/getOrderInfo',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    DATA=response.json()['data']
    try:
        a={
            "contractNo":DATA['productInfoList'][0]['contractNo'],
            'payTime':DATA['payTime'],
            'phone':DATA['phone'],
            'productName': DATA['productInfoList'][0]['productName'],
            'buyLessonNum': DATA['productInfoList'][0]['buyLessonNum'],
            'giftLessonNum':DATA['productInfoList'][0]['giftLessonNum'],
            'lessonNum':DATA['productInfoList'][0]['lessonNum'],
            'gradeName': DATA['gradeName'],
            'lessonFee':DATA['productInfoList'][0]['lessonFee'],
            'studentCode': DATA['studentCode'],
            'studentName': DATA['studentName'],
            'orderCode': DATA['orderCode'],
            'payInfo':F'{DATA["payInfo"][0]["payType"]}:¥{DATA["payInfo"][0]["payAmount"]}'
        }
    except:
        a= None
    return a

def search_student(cookies,current_user,StudentCode):
    cookies=1
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
        # 'Cookie': 'FE_USER_CODE=NC24048S6UzC; FE_USER_NAME=%E5%BC%A0%E8%B0%A6235; rem=on; XDFUUID=ce6a5a3d-9251-5279-d83a-8f1fc6dcd799; erpSchoolId=35; gr_user_id=581a8283-1851-4e73-a092-9075db03f151; a28834c02dcdb241_gr_last_sent_cs1=zhangqian235@xdf.cn; 964de61476ecd75d_gr_last_sent_cs1=01027b0e73ba43728dc1e96228e6d606; a28834c02dcdb241_gr_cs1=zhangqian235@xdf.cn; 964de61476ecd75d_gr_cs1=01027b0e73ba43728dc1e96228e6d606; jiaowuSchoolId=35; OA_USER_KEY=YjQ2NTBkM2NjNzA0MTUwZTNlMGNmNjQwMDczMGVkNzE7emhhbmdxaWFuMjM1OzE3NDk3ODAwMDM%3D; e2e=A2722AEC8CB1725A84385253E3D81D09; casgwusercred=NGjz2HfXFFWhcL8Ih_gnED4-mc30XuIwvU7M7bF6wQBciD11s9Pj4GZNsoLFfBhezRZ3fF3uBWh0jJ_MIi9xp56CT6r6-E51i9CfYubbVa-jPmWHuQVTOnsZG0r2miw-F5Z6lkbev2yXITkrUajCbakhU0xK-ZWvarh6jPTzn7U; crosgwusercred=4qLA-_bkyBtbQspD5OITWCxRI1aviyzNjG-Q-VBq4Gma1hjjUgP2g2yGPmbIjfpQSiiHv2zNTZmJUXEnjbzDUg546d24fe41ac0ff94a449d5f52e6aeba; e2mf=4c558bdd0e2f4b8893daf159e6a3d4f7; erpUserId=zhangqian235',
    }
    json_data = {
        'SchoolId': 35,
        'QueryValue': StudentCode,
        'PageIndex': 1,
        'PageSize': 10,
    }
    response = requests.post(
        'https://erp.xdf.cn/apinisbff/Student/QueryStudentWithBound',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )
    data = []
    json_data1  = {
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
            'Value': StudentCode,
        },
    ],
    'Sort': [
        {
            'Field': 'CompleteDate',
            'Dir': 1,
        },
    ],
    }
    response1 = requests.post(
        'https://erp.xdf.cn/nises/apinises/StuStoreAccount/QueryStoreOrderPage',
        cookies=cookies,
        headers=headers,
        json=json_data1,
    )
    if response.status_code == 200 :
        if response.json()['Msg'] == '没有找到学员！':
            return 0
        else:
            json_data = {
                'SchoolId': 35,
                'StudentCode': 'StudentCode',
                'EnType': True,
            }

            response = requests.post('https://erp.xdf.cn/apinisbff/Student/QueryBrief', cookies=cookies,
                                     headers=headers, json=json_data)
            QueryBrief=response.json()['Data']
            sGender=QueryBrief['Gender']
            if sGender==1:
                sGender = '男'
            elif sGender==2:
                sGender = '女'
            elif sGender==3:
                sGender = '未知'

            json_data = {
                'SchoolId': 35,
                'PageIndex': 1,
                'PageSize': 40,
                'Filters': [
                    {
                        'Field': 'StudentCode',
                        'Operation': 0,
                        'Value': StudentCode,
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
            )

            json_data2 = {
                'schoolId': 35,
                'pageIndex': 1,
                'pageSize': 40,
                'orderCode': None,
                'batchCode': None,
                'studentCode': StudentCode,
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
            response2 = requests.post(
                'https://erp.xdf.cn/nises/apinises/order/OrderQueryWithPrivilege',
                cookies=cookies,
                headers=headers,
                json=json_data2,
            )
            params = {
                'operateTypeCode': 'B',
                'searchCondition': StudentCode,
                'pageNo': '1',
                'pageSize': '40',
                'schoolId': '35',
                'listFlag': '2',
                't': '1750731323395',
            }

            response3 = requests.get(
                'https://erp.xdf.cn/biz-vipnis/api/v1/biz/order/getOrderList',
                params=params,
                cookies=cookies,
                headers=headers,
            )
            for d in response.json()['Data']['Data']:
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
                        'sGender': sGender,
                        'sCardCode':d['CardCode'],
                        # 班级信息
                        'sClassName': d['ClassName'],
                        'sClassCode': d['ClassCode'],
                        'sSeatNo': d['CardCode'][-1] if d['CardCode'][-2] == '0' else d['CardCode'][-2:],
                        'dtBeginDate': d['BeginDate'],
                        'dtEndDate':  d['EndDate'],
                        'nTryLesson': d['TryLesson'],
                        # 时间信息
                        'sRegisterTime':  d['PrintTime'],
                        'sPrintAddress': d['PrintAddress'],
                        'sPrintTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        # 费用信息
                        'dFee':d['Fee'],  # 商品标准金额
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
            for B in response1.json()['Data']['Data']:
                if B['OrderTypeName']=='学员账户充值提现':
                    c = {
                        'biz_type': 6,
                        'biz_name': '学员账户充值提现凭证',
                        'data': {
                            "nSchoolId": 35,
                            "sSchoolName": "南昌学校",
                            "sTelePhone": "400-175-9898",
                            "sOperator": current_user.username,
                            "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Title": "提现凭证",
                            "PrintNumber": 1,
                            "YNVIEWPrint": 1,
                            "PrintDocument": "",
                            "sStudentCode": B['StudentCode'],
                            "sStudentName": B['StudentName'],
                            "sGender": sGender,
                            "dSumBalance": f"余额：¥{B['Balance']}",
                            "sPayType": f"{B['PayTypeName']}：{B['PayTypeName']}¥{B['Pay']}",
                            "dtCreateDate": B['TransactionTime'],
                            "sProofName": "学员账户充值提现凭证",
                            "sBizType": "提现",
                            "sRegZoneName": "客服行政"
                        }
                    }
                    data.append(c)
                elif B['OrderTypeName']=='学员账户充值':
                    c = {
                        'biz_type': 6,
                        'biz_name': '学员账户充值凭证',
                        'data': {
                            "nSchoolId": 35,
                            "sSchoolName": "南昌学校",
                            "sTelePhone": "400-175-9898",
                            "sOperator": current_user.username,
                            "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Title": "充值凭证",
                            "PrintNumber": 1,
                            "YNVIEWPrint": 1,
                            "PrintDocument": "",
                            "sStudentCode": B['StudentCode'],
                            "sStudentName": B['StudentName'],
                            "sGender": sGender,
                            "dSumBalance": f"余额：¥{B['Balance']}",
                            "sPayType": f"{B['PayTypeName']}：{B['PayTypeName']}¥{B['Pay']}",
                            "dtCreateDate": B['TransactionTime'],
                            "sProofName": "学员账户充值凭证",
                            "sBizType": "充值",
                            "sRegZoneName": "客服行政"
                        }
                    }
                    data.append(c)
                else:
                    continue
            for C in response2.json()['Data']['Data']:

                if C['batchStatusName']=='交易成功' and C['operateType'] =='退班':
                    F=getProofByBizType(cookies,3,C['batchCode'])
                    data.append(F)
                elif C['batchStatusName'] == '交易成功' and C['operateType'] == '报班':
                    F = getProofByBizType(cookies, 1, C['batchCode'])
                    data.append(F)
            for D in response3.json()['data']['orderInfoList']:
                x=getProofByHighBizType(cookies, D['orderCode'])
                x['totalAmount']=D['totalAmount']
                x['realAmount']=D['realAmount']
                x['recieveAmount']=D['recieveAmount']
                x['discountAmount']=D['discountAmount']
                data.append(x)
            return data
    else:
        return 404