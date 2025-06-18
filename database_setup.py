#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
MySQL数据库的创建和初始化
"""

import os
import sys
import pymysql
from config import Config

def create_mysql_database():
    """创建MySQL数据库"""
    try:
        config = Config()
        
        # 连接MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=config.MYSQL_HOST,
            port=int(config.MYSQL_PORT),
            user=config.MYSQL_USERNAME,
            password=config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DATABASE}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ MySQL数据库 '{config.MYSQL_DATABASE}' 创建成功")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ MySQL数据库创建失败: {str(e)}")
        print("请检查MySQL服务是否启动，以及连接参数是否正确")
        return False

def init_database():
    """初始化数据库表和数据"""
    try:
        from app import app, db, create_admin_user
        
        with app.app_context():
            # 创建所有表
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 创建默认管理员账户
            create_admin_user()
            print("✅ 默认管理员账户创建成功")
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("南昌新东方凭证打印系统 - MySQL数据库初始化")
    print("=" * 50)
    
    config = Config()
    print(f"MySQL配置: {config.MYSQL_USERNAME}@{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DATABASE}")
    
    # 创建MySQL数据库
    if not create_mysql_database():
        print("数据库创建失败，退出")
        sys.exit(1)
    
    # 初始化数据库表和数据
    if init_database():
        print("\n🎉 数据库初始化完成！")
    else:
        print("\n❌ 数据库初始化失败！")
        sys.exit(1)

if __name__ == "__main__":
    main() 