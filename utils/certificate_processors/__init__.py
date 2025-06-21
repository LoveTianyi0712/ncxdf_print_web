# -*- coding: utf-8 -*-
"""
凭证处理器包
每个凭证类型都有独立的处理器模块
"""

from .student_account_certificate import (
    StudentAccountCertificateProcessor,
    generate_student_account_certificate
)

from .enrollment_certificate import (
    EnrollmentCertificateProcessor,
    generate_enrollment_certificate
)

from .refund_fee_certificate import (
    RefundFeeCertificateProcessor,
    generate_refund_fee_certificate
)

from .search_student_certificate import (
    search_student,
    search_student_classes
)

from .enrollment_registration_certificate import (
    EnrollmentRegistrationCertificateProcessor,
    generate_enrollment_registration_certificate,
    create_mock_data,
    test_enrollment_registration_certificate
)

__all__ = [
    'StudentAccountCertificateProcessor',
    'generate_student_account_certificate',
    'EnrollmentCertificateProcessor',
    'generate_enrollment_certificate',
    'RefundFeeCertificateProcessor',
    'generate_refund_fee_certificate',
    'search_student',
    'search_student_classes',
    'EnrollmentRegistrationCertificateProcessor',
    'generate_enrollment_registration_certificate',
    'create_mock_data',
    'test_enrollment_registration_certificate'
] 