# -*- coding: utf-8 -*-
"""
凭证处理器包
每个凭证类型都有独立的处理器模块
"""

from .student_account_certificate import (
    StudentAccountCertificateProcessor,
    generate_student_account_certificate
)

__all__ = [
    'StudentAccountCertificateProcessor',
    'generate_student_account_certificate'
] 