#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移脚本
添加首次登录字段
"""

import sys
import os
import pymysql
from config import Config

def migrate_database():
    """迁移数据库，添加is_first_login字段"""
    try:
        config = Config()
        
        # 连接MySQL数据库
        connection = pymysql.connect(
            host=config.MYSQL_HOST,
            port=int(config.MYSQL_PORT),
            user=config.MYSQL_USERNAME,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 检查字段是否已存在
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'user' 
                AND COLUMN_NAME = 'is_first_login'
            """, (config.MYSQL_DATABASE,))
            
            result = cursor.fetchone()
            if result[0] > 0:
                print("✅ is_first_login 字段已存在，跳过迁移")
                return True
            
            # 添加is_first_login字段
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN is_first_login TINYINT(1) NOT NULL DEFAULT 1 
                AFTER is_enabled
            """)
            
            # 将现有的管理员用户设置为非首次登录
            cursor.execute("""
                UPDATE user 
                SET is_first_login = 0 
                WHERE role = 'admin'
            """)
            
            connection.commit()
            print("✅ 成功添加 is_first_login 字段")
            print("✅ 已将管理员用户设置为非首次登录")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("南昌新东方凭证打印系统 - 数据库迁移")
    print("添加首次登录字段")
    print("=" * 50)
    
    if migrate_database():
        print("\n🎉 数据库迁移完成！")
        print("现在可以使用首次登录强制修改密码功能了。")
    else:
        print("\n❌ 数据库迁移失败！")
        sys.exit(1)

if __name__ == "__main__":
    main() 