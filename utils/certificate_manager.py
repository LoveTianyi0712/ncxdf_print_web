#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
凭证管理器 - 统一调用各个独立凭证处理器的入口
"""

import os
from datetime import datetime

# 凭证类型映射表
CERTIFICATE_MAPPING = {
    1: {
        'name': '报班凭证',
        'template': '报班凭证.mrt',
        'processor': 'enrollment_certificate'
    },
    3: {
        'name': '退班凭证', 
        'template': '退班凭证.mrt',
        'processor': 'withdrawal_certificate'
    },
    6: {
        'name': '学员账户充值提现凭证',
        'template': '学员账户充值提现凭证.mrt',
        'processor': 'student_account_certificate'
    },
    8: {
        'name': '退费凭证',
        'template': '退费凭证.mrt', 
        'processor': 'refund_certificate'
    }
}

class CertificateManager:
    """凭证管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.template_dir = os.path.join(self.base_dir, "properties")
        self.output_dir = os.path.join(self.base_dir, "image")
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def get_available_certificates(self):
        """获取可用的凭证类型"""
        available = {}
        for biz_type, config in CERTIFICATE_MAPPING.items():
            template_path = os.path.join(self.template_dir, config['template'])
            if os.path.exists(template_path):
                available[biz_type] = config
        return available
    
    def generate_certificate(self, biz_type, data, currency_symbol="¥"):
        """生成指定类型的凭证"""
        if biz_type not in CERTIFICATE_MAPPING:
            raise ValueError(f"不支持的凭证类型: {biz_type}")
        
        config = CERTIFICATE_MAPPING[biz_type]
        processor_name = config['processor']
        
        print(f"使用处理器: {processor_name}")
        print(f"处理凭证: {config['name']}")
        
        # 根据处理器类型调用相应的处理函数
        if processor_name == 'student_account_certificate':
            return self._generate_student_account_certificate(data, currency_symbol)
        elif processor_name == 'enrollment_certificate':
            return self._generate_enrollment_certificate(data, currency_symbol)
        elif processor_name == 'withdrawal_certificate':
            return self._generate_withdrawal_certificate(data, currency_symbol)
        elif processor_name == 'refund_certificate':
            return self._generate_refund_certificate(data, currency_symbol)
        else:
            raise ValueError(f"未实现的处理器: {processor_name}")
    
    def _generate_student_account_certificate(self, data, currency_symbol):
        """生成学员账户充值提现凭证"""
        try:
            from utils.certificate_processors.student_account_certificate import generate_student_account_certificate
            return generate_student_account_certificate(data, currency_symbol)
        except ImportError as e:
            print(f"导入学员账户凭证处理器失败: {str(e)}")
            # 回退到旧的方法
            return self._fallback_generate(6, data, currency_symbol)
    
    def _generate_enrollment_certificate(self, data, currency_symbol):
        """生成报班凭证"""
        # TODO: 实现报班凭证处理器
        print("报班凭证处理器尚未实现，使用回退方法")
        return self._fallback_generate(1, data, currency_symbol)
    
    def _generate_withdrawal_certificate(self, data, currency_symbol):
        """生成退班凭证"""
        # TODO: 实现退班凭证处理器
        print("退班凭证处理器尚未实现，使用回退方法")
        return self._fallback_generate(3, data, currency_symbol)
    
    def _generate_refund_certificate(self, data, currency_symbol):
        """生成退费凭证"""
        # TODO: 实现退费凭证处理器
        print("退费凭证处理器尚未实现，使用回退方法")
        return self._fallback_generate(8, data, currency_symbol)
    
    def _fallback_generate(self, biz_type, data, currency_symbol):
        """回退到原始的print_simulator方法"""
        try:
            from utils.print_simulator import print_certificate_by_biz_type
            return print_certificate_by_biz_type(biz_type, data, currency_symbol)
        except Exception as e:
            print(f"回退方法也失败了: {str(e)}")
            raise
    
    def generate_certificate_by_template(self, template_name, data, currency_symbol="¥"):
        """根据模板名称生成凭证"""
        # 查找对应的biz_type
        biz_type = None
        for bt, config in CERTIFICATE_MAPPING.items():
            if config['template'] == template_name:
                biz_type = bt
                break
        
        if biz_type is None:
            raise ValueError(f"未找到模板对应的处理器: {template_name}")
        
        return self.generate_certificate(biz_type, data, currency_symbol)


# 便捷函数
def generate_certificate_by_type(biz_type, data, currency_symbol="¥"):
    """生成指定类型凭证的便捷函数"""
    manager = CertificateManager()
    return manager.generate_certificate(biz_type, data, currency_symbol)

def generate_certificate_by_template(template_name, data, currency_symbol="¥"):
    """根据模板名称生成凭证的便捷函数"""
    manager = CertificateManager()
    return manager.generate_certificate_by_template(template_name, data, currency_symbol)

def get_available_certificates():
    """获取可用凭证类型的便捷函数"""
    manager = CertificateManager()
    return manager.get_available_certificates()

def print_certificate_info():
    """打印凭证信息"""
    manager = CertificateManager()
    certificates = manager.get_available_certificates()
    
    print("=== 可用的凭证类型 ===")
    for biz_type, config in certificates.items():
        print(f"BizType {biz_type}: {config['name']}")
        print(f"  - 模板文件: {config['template']}")
        print(f"  - 处理器: {config['processor']}")
        print()


if __name__ == "__main__":
    # 显示可用凭证信息
    print_certificate_info()
    
    # 测试学员账户充值提现凭证
    print("="*50)
    print("测试学员账户充值提现凭证")
    print("="*50)
    
    test_data = {
        "nSchoolId": 35,
        "sSchoolName": "南昌学校",
        "sTelePhone": "400-175-9898",
        "sOperator": "张会计",
        "dtCreate": "2024-12-23 17:30:00",
        "Title": "提现凭证",
        "sStudentCode": "NC6080119764",
        "sStudentName": "测试学员",
        "sGender": "男",
        "sPay": "提现金额：¥1500.00",
        "dSumBalance": "余额：¥500.00",
        "sPayType": "提现方式：银行卡",
        "dtCreateDate": "2024-12-23 17:30:00",
        "sProofName": "提现凭证",
        "sBizType": "提现",
        "nBizId": 126560058,
        "sRegZoneName": "财务处"
    }
    
    try:
        result = generate_certificate_by_type(6, test_data)
        print(f"✅ 测试成功，生成文件: {result}")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}") 