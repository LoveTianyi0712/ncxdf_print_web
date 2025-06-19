#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建测试用户脚本
用于测试首次登录强制修改密码功能
"""

from app import app, db, User
from werkzeug.security import generate_password_hash

def create_test_user():
    """创建测试用户"""
    with app.app_context():
        # 检查是否已存在测试用户
        existing_user = User.query.filter_by(username='testuser').first()
        if existing_user:
            print("测试用户已存在，删除原有用户...")
            db.session.delete(existing_user)
            db.session.commit()
        
        # 创建新的测试用户
        test_user = User(
            username='testuser',
            password_hash=generate_password_hash('123456'),
            role='user',
            is_first_login=True  # 设为首次登录
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print("✅ 测试用户创建成功！")
        print("用户名: testuser")
        print("密码: 123456")
        print("首次登录: 是")
        print("\n测试步骤：")
        print("1. 使用上述账号登录系统")
        print("2. 系统应该自动跳转到首次登录修改密码页面")
        print("3. 修改密码后应该可以正常使用系统")

if __name__ == "__main__":
    create_test_user() 