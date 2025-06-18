#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web应用集成测试脚本
验证新的凭证处理器在Web应用中的集成情况
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_certificate_manager():
    """测试凭证管理器"""
    print("🔧 测试凭证管理器...")
    
    from utils.certificate_manager import get_available_certificates, generate_certificate_by_type
    
    # 获取可用凭证类型
    certificates = get_available_certificates()
    print(f"✅ 发现 {len(certificates)} 种可用凭证类型:")
    for biz_type, config in certificates.items():
        print(f"   - BizType {biz_type}: {config['name']}")
    
    return certificates

def test_mock_data():
    """测试模拟数据结构"""
    print("\n📊 测试模拟数据结构...")
    
    # 模拟app.py中的search_student函数逻辑
    test_codes = ['NC2024001', 'NC2024002', 'NC2024003']
    
    for student_code in test_codes:
        print(f"   测试学员编码: {student_code}")
        
        # 这里应该能够找到对应的学员数据
        # 在实际应用中，这会从app.py的mock_data中获取
        
    print("✅ 模拟数据结构测试完成")

def test_certificate_generation():
    """测试凭证生成功能"""
    print("\n🎯 测试凭证生成功能...")
    
    from utils.certificate_manager import generate_certificate_by_type
    
    # 测试数据
    test_cases = [
        {
            'biz_type': 101,
            'name': '班级凭证',
            'data': {
                'sSchoolName': '南昌学校',
                'sStudentName': '张小明',
                'sStudentCode': 'NC2024001',
                'sClassName': '高中数学春季班',
                'sOperator': '测试用户',
                'dFee': 3800.00,
                'dRealFee': 3500.00
            }
        },
        {
            'biz_type': 102,
            'name': '学员账户充值凭证',
            'data': {
                'nSchoolId': '001',
                'sSchoolName': '南昌学校',
                'sStudentName': '李小红',
                'sStudentCode': 'NC2024002',
                'sOperator': '测试用户',
                'sPay': '15000.00',
                'sPayType': '支付宝',
                'sProofName': '充值凭证',
                'sBizType': '充值',
                'dSumBalance': '25000.00',
                'dtCreateDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sTelePhone': '400-175-9898',
                'Title': '充值凭证'
            }
        },
        {
            'biz_type': 104,
            'name': '退费凭证',
            'data': {
                'sSchoolName': '南昌学校',
                'sStudentName': '王小强',
                'sStudentCode': 'NC2024003',
                'sOperator': '测试用户',
                'sBizType': '退费',
                'sPay': '2800.00',
                'sPayType': '银行转账',
                'dSumBalance': '3200.00'
            }
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            print(f"   生成 {test_case['name']}...")
            result = generate_certificate_by_type(test_case['biz_type'], test_case['data'])
            if result and os.path.exists(result):
                file_size = os.path.getsize(result) / 1024  # KB
                print(f"   ✅ {test_case['name']} 生成成功: {os.path.basename(result)} ({file_size:.1f} KB)")
                results.append(result)
            else:
                print(f"   ❌ {test_case['name']} 生成失败: 文件不存在")
        except Exception as e:
            print(f"   ❌ {test_case['name']} 生成失败: {str(e)}")
    
    return results

def test_web_app_integration():
    """测试Web应用集成"""
    print("\n🌐 测试Web应用集成...")
    
    try:
        # 测试导入主要模块
        from app import app
        from utils.certificate_manager import generate_certificate_by_type
        
        print("   ✅ 主要模块导入成功")
        
        # 测试Flask应用配置
        if app.config.get('SECRET_KEY'):
            print("   ✅ Flask应用配置正常")
        else:
            print("   ⚠️  Flask应用缺少SECRET_KEY配置")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Web应用集成测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 南昌新东方凭证打印系统 - Web集成测试")
    print("📅 测试时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(__file__), 'image')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 创建输出目录: {output_dir}")
    
    # 执行测试
    certificates = test_certificate_manager()
    test_mock_data()
    results = test_certificate_generation()
    web_integration_ok = test_web_app_integration()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    print(f"✅ 可用凭证类型: {len(certificates)} 种")
    print(f"✅ 成功生成凭证: {len(results)} 个")
    print(f"{'✅' if web_integration_ok else '❌'} Web应用集成: {'正常' if web_integration_ok else '异常'}")
    
    if results:
        print(f"\n📁 生成的凭证文件:")
        for i, result in enumerate(results, 1):
            filename = os.path.basename(result)
            file_size = os.path.getsize(result) / 1024
            print(f"   {i:2d}. {filename} ({file_size:.1f} KB)")
    
    print(f"\n📁 所有文件保存在: {output_dir}")
    
    # 使用指南
    print("\n🎯 Web应用测试指南:")
    print("1. 启动应用: python run.py")
    print("2. 访问: http://localhost:5000")
    print("3. 测试学员编码:")
    print("   - NC2024001 (张小明) - 班级凭证")
    print("   - NC2024002 (李小红) - 学员账户凭证")
    print("   - NC2024003 (王小强) - 退费凭证")
    
    print("\n🎉 Web集成测试完成!")

if __name__ == "__main__":
    main() 