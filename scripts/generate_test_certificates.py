#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
凭证处理器测试数据生成脚本
为三个核心凭证处理器生成测试数据
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.certificate_processors.student_account_certificate import generate_student_account_certificate
from utils.certificate_processors.enrollment_certificate import generate_enrollment_certificate
from utils.certificate_processors.refund_fee_certificate import generate_refund_fee_certificate

def generate_student_account_test():
    """生成学员账户充值提现凭证测试数据"""
    print("=" * 60)
    print("🏦 生成学员账户充值提现凭证测试数据")
    print("=" * 60)
    
    # 充值凭证测试数据
    recharge_data = {
        'nSchoolId': '001',
        'sSchoolName': '南昌学校',
        'sOperator': '财务张老师',
        'sStudentCode': 'NC2024002',
        'sStudentName': '李小红',
        'sPay': '15000.00',
        'sPayType': '支付宝',
        'sProofName': '充值凭证',
        'sBizType': '充值',
        'dSumBalance': '25000.00',
        'dtCreateDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sTelePhone': '400-175-9898',
        'Title': '充值凭证'
    }
    
    # 提现凭证测试数据
    withdraw_data = {
        'nSchoolId': '001',
        'sSchoolName': '南昌学校',
        'sOperator': '财务王老师',
        'sStudentCode': 'NC2024002',
        'sStudentName': '李小红',
        'sPay': '8000.00',
        'sPayType': '银行转账',
        'sProofName': '提现凭证',
        'sBizType': '提现',
        'dSumBalance': '17000.00',
        'dtCreateDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sTelePhone': '400-175-9898',
        'Title': '提现凭证'
    }
    
    try:
        print("1️⃣  生成充值凭证...")
        result1 = generate_student_account_certificate(recharge_data)
        print(f"   ✅ 充值凭证生成成功: {os.path.basename(result1)}")
        
        print("2️⃣  生成提现凭证...")
        result2 = generate_student_account_certificate(withdraw_data)
        print(f"   ✅ 提现凭证生成成功: {os.path.basename(result2)}")
        
        return [result1, result2]
        
    except Exception as e:
        print(f"   ❌ 学员账户凭证生成失败: {e}")
        return []

def generate_enrollment_test():
    """生成班级凭证测试数据"""
    print("\n" + "=" * 60)
    print("🎓 生成班级凭证（报班凭证）测试数据")
    print("=" * 60)
    
    # 班级凭证测试数据
    enrollment_data = {
        # 基本信息
        'sSchoolName': '南昌学校',
        'sTelePhone': '400-175-9898',
        'sChannel': '直营',
        
        # 学员信息
        'sStudentName': '张小明',
        'sStudentCode': 'NC2024001',
        'sGender': '男',
        'sCardCode': 'CARD001234',
        
        # 班级信息
        'sClassName': '高中数学春季班',
        'sClassCode': 'MATH2024SP001',
        'sSeatNo': 'A015',
        'dtBeginDate': '2024-03-01',
        'dtEndDate': '2024-06-30',
        'nTryLesson': '2节',
        
        # 时间信息
        'sRegisterTime': '2024-02-15 10:30:00 报名成功，欢迎参加南昌学校高中数学春季班学习！',
        'sPrintAddress': '南昌市红谷滩新区学府大道1号南昌学校',
        'sPrintTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        
        # 费用信息
        'dFee': 3800.00,           # 商品标准金额
        'dVoucherFee': 300.00,     # 商品优惠金额
        'dShouldFee': 3800.00,     # 商品应收金额
        'dRealFee': 3500.00,       # 商品实收金额
        
        # 操作信息
        'sOperator': '招生李老师',
        
        # 图像数据（可选）
        'RWMImage': ''
    }
    
    try:
        print("1️⃣  生成班级凭证...")
        result = generate_enrollment_certificate(enrollment_data)
        print(f"   ✅ 班级凭证生成成功: {os.path.basename(result)}")
        
        return [result]
        
    except Exception as e:
        print(f"   ❌ 班级凭证生成失败: {e}")
        return []

def generate_refund_fee_test():
    """生成退费凭证测试数据"""
    print("\n" + "=" * 60)
    print("💰 生成退费凭证测试数据")
    print("=" * 60)
    
    # 退费凭证测试数据
    refund_data = {
        # 基本信息
        'sSchoolName': '南昌学校',
        'sTelePhone': '400-175-9898',
        'Title': '退费凭证',
        'sBizType': '退费',
        'sOperator': '财务刘老师',
        'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dtCreateDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        
        # 学员信息
        'sStudentName': '王小强',
        'sStudentCode': 'NC2024003',
        'sGender': '男',
        'sSeatNo': 'B012',
        'sRegZoneName': '南昌红谷滩校区',
        
        # 金额信息
        'sPay': '2800.00',              # 退费金额
        'sPayType': '银行转账',          # 退费方式
        'dSumBalance': '3200.00',       # 余额
    }
    
    try:
        print("1️⃣  生成退费凭证...")
        result = generate_refund_fee_certificate(refund_data)
        print(f"   ✅ 退费凭证生成成功: {os.path.basename(result)}")
        
        return [result]
        
    except Exception as e:
        print(f"   ❌ 退费凭证生成失败: {e}")
        return []

def main():
    """主函数"""
    print("🚀 南昌新东方凭证打印系统 - 测试数据生成器")
    print("📅 生成时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 创建输出目录: {output_dir}")
    
    all_results = []
    
    # 生成各类凭证测试数据
    all_results.extend(generate_student_account_test())
    all_results.extend(generate_enrollment_test())
    all_results.extend(generate_refund_fee_test())
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 生成结果总结")
    print("=" * 60)
    
    if all_results:
        print(f"✅ 成功生成 {len(all_results)} 个凭证文件:")
        for i, result in enumerate(all_results, 1):
            filename = os.path.basename(result)
            file_size = os.path.getsize(result) / 1024  # KB
            print(f"   {i:2d}. {filename} ({file_size:.1f} KB)")
        
        print(f"\n📁 所有文件保存在: {output_dir}")
        print("🎯 可以在Web应用中使用以下学员编码进行测试:")
        print("   - NC2024001 (张小明) - 班级凭证")
        print("   - NC2024002 (李小红) - 学员账户凭证")
        print("   - NC2024003 (王小强) - 退费凭证")
        
    else:
        print("❌ 没有成功生成任何凭证文件")
    
    print("\n🎉 测试数据生成完成!")

if __name__ == "__main__":
    main() 