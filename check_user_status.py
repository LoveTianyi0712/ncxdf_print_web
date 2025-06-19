#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查用户激活状态脚本
显示所有用户的首次登录状态
"""

from app import app, db, User

def check_user_status():
    """检查所有用户的激活状态"""
    with app.app_context():
        users = User.query.all()
        
        print("=" * 60)
        print("用户激活状态列表")
        print("=" * 60)
        print(f"{'ID':<5} {'用户名':<15} {'角色':<10} {'启用状态':<10} {'激活状态':<10}")
        print("-" * 60)
        
        for user in users:
            enabled_status = "启用" if user.is_enabled else "禁用"
            activation_status = "已激活" if not user.is_first_login else "待激活"
            
            print(f"{user.id:<5} {user.username:<15} {user.role:<10} {enabled_status:<10} {activation_status:<10}")
        
        print("-" * 60)
        
        # 统计信息
        total_users = len(users)
        enabled_users = len([u for u in users if u.is_enabled])
        activated_users = len([u for u in users if not u.is_first_login])
        pending_users = len([u for u in users if u.is_first_login])
        admin_users = len([u for u in users if u.role == 'admin'])
        regular_users = len([u for u in users if u.role == 'user'])
        
        print(f"\n统计信息：")
        print(f"总用户数: {total_users}")
        print(f"启用用户: {enabled_users}")
        print(f"已激活用户: {activated_users}")
        print(f"待激活用户: {pending_users}")
        print(f"管理员: {admin_users}")
        print(f"普通用户: {regular_users}")

if __name__ == "__main__":
    check_user_status() 