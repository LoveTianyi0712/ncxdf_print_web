# -*- coding: utf-8 -*-
"""
Utils package for 南昌新东方凭证打印系统
支持多种凭证类型的通用打印系统
"""

from utils.certificate_processors.print_simulator import (
    ProofPrintSimulator, 
    TEMPLATE_MAPPING,
    CERTIFICATE_TYPES,
    TEMPLATE_NAME_TO_BIZTYPE,
    create_certificate_printer,
    print_certificate_by_type,
    print_certificate_by_biz_type,
    get_available_certificates,
    print_certificate_info,
    simulate_print_request
)

__all__ = [
    'ProofPrintSimulator', 
    'TEMPLATE_MAPPING',
    'CERTIFICATE_TYPES',
    'TEMPLATE_NAME_TO_BIZTYPE',
    'create_certificate_printer',
    'print_certificate_by_type',
    'print_certificate_by_biz_type',
    'get_available_certificates',
    'print_certificate_info',
    'simulate_print_request'
] 