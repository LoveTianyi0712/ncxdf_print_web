#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
南昌新东方凭证打印系统启动脚本
运行此脚本启动Web应用程序
"""

from app import app, db, create_admin_user

if __name__ == '__main__':
    # 创建数据库表和默认管理员账户
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    print("=" * 50)
    print("南昌新东方凭证打印系统")
    print("=" * 50)
    print("系统正在启动...")
    print("访问地址: http://localhost:5000")
    print("如需登录账号请联系管理员")
    print("=" * 50)
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000) 