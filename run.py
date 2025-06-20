#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
南昌新东方凭证打印系统启动脚本
运行此脚本启动Web应用程序
"""

import os
from app import app, db, create_admin_user, init_cookies_auto_check

if __name__ == '__main__':
    # 创建数据库表和默认管理员账户
    with app.app_context():
        db.create_all()
        create_admin_user()
        # 初始化cookies自动检测
        init_cookies_auto_check()
    
    # 从环境变量获取端口，默认5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    print("=" * 50)
    print("南昌新东方凭证打印系统")
    print("=" * 50)
    print("系统正在启动...")
    print(f"监听地址: 0.0.0.0:{port}")
    print("如需登录账号请联系管理员")
    print("默认管理员: admin / admin123")
    print("=" * 50)
    
    # 启动Flask应用
    app.run(debug=debug, host='0.0.0.0', port=port) 