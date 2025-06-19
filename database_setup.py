#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
MySQL数据库的创建和初始化
"""

import os
import sys
import pymysql
from config import Config, config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from app import app, db, User

# 安装PyMySQL作为MySQLdb的替代
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# 从环境变量获取配置模式，默认为development
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

db = SQLAlchemy(app)

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
            
            # 创建默认的Cookies配置（如果不存在）
            create_default_cookies_config()
            print("✅ 默认Cookies配置创建成功")
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        return False

def create_default_cookies_config():
    """创建默认的Cookies配置"""
    try:
        from app import CookiesConfig, User
        
        # 检查是否已存在活跃配置
        existing_config = CookiesConfig.query.filter_by(is_active=True).first()
        if existing_config:
            print("已存在活跃的Cookies配置，跳过创建默认配置")
            return
        
        # 获取管理员用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("未找到管理员用户，跳过创建默认Cookies配置")
            return
        
        # 创建默认配置（使用原来的DEFAULT_COOKIES）
        default_cookies = {
            'FE_USER_CODE': 'NC24048S6UzC',
            'FE_USER_NAME': '%E5%BC%A0%E8%B0%A6235',
            'rem': 'on',
            'XDFUUID': 'ce6a5a3d-9251-5279-d83a-8f1fc6dcd799',
            'erpSchoolId': '35',
            'gr_user_id': '581a8283-1851-4e73-a092-9075db03f151',
            'a28834c02dcdb241_gr_last_sent_cs1': 'zhangqian235@xdf.cn',
            '964de61476ecd75d_gr_last_sent_cs1': '01027b0e73ba43728dc1e96228e6d606',
            'a28834c02dcdb241_gr_cs1': 'zhangqian235@xdf.cn',
            '964de61476ecd75d_gr_cs1': '01027b0e73ba43728dc1e96228e6d606',
            'jiaowuSchoolId': '35',
            'OA_USER_KEY': 'YjQ2NTBkM2NjNzA0MTUwZTNlMGNmNjQwMDczMGVkNzE7emhhbmdxaWFuMjM1OzE3NDk3ODAwMDM%3D',
            'e2e': 'A2722AEC8CB1725A84385253E3D81D09',
            'casgwusercred': 'NGjz2HfXFFWhcL8Ih_gnED4-mc30XuIwvU7M7bF6wQBciD11s9Pj4GZNsoLFfBhezRZ3fF3uBWh0jJ_MIi9xp56CT6r6-E51i9CfYubbVa-jPmWHuQVTOnsZG0r2miw-F5Z6lkbev2yXITkrUajCbakhU0xK-ZWvarh6jPTzn7U',
            'crosgwusercred': '4qLA-_bkyBtbQspD5OITWCxRI1aviyzNjG-Q-VBq4Gma1hjjUgP2g2yGPmbIjfpQSiiHv2zNTZmJUXEnjbzDUg546d24fe41ac0ff94a449d5f52e6aeba',
            'e2mf': '4c558bdd0e2f4b8893daf159e6a3d4f7',
            'erpUserId': 'zhangqian235',
        }
        
        import json
        from app import db
        
        default_config = CookiesConfig(
            name='默认ERP Cookies配置',
            cookies_data=json.dumps(default_cookies, ensure_ascii=False),
            is_active=True,
            created_by=admin_user.id,
            test_status='未测试'
        )
        
        db.session.add(default_config)
        db.session.commit()
        
        print("✅ 已创建默认Cookies配置")
        
    except Exception as e:
        print(f"⚠️ 创建默认Cookies配置失败: {str(e)}")
        # 不抛出异常，因为这不是必需的

def migrate_database():
    """执行数据库迁移"""
    with app.app_context():
        try:
            from sqlalchemy import text
            # 检查is_deleted字段是否已存在
            result = db.session.execute(text("SHOW COLUMNS FROM print_log LIKE 'is_deleted'"))
            if result.fetchone() is None:
                # 字段不存在，添加字段
                print("正在为PrintLog表添加is_deleted字段...")
                db.session.execute(text("ALTER TABLE print_log ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL"))
                db.session.commit()
                print("is_deleted字段添加成功！")
            else:
                print("is_deleted字段已存在，跳过迁移。")
        except Exception as e:
            print(f"数据库迁移失败: {str(e)}")
            db.session.rollback()

def setup_database():
    """初始化数据库"""
    with app.app_context():
        print("正在创建数据库表...")
        db.create_all()
        print("数据库表创建完成！")

def create_admin_user():
    """创建管理员用户"""
    with app.app_context():
        # 检查是否已存在管理员
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("管理员用户已存在")
            return
        
        # 创建管理员用户
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_first_login=False,  # 管理员默认已激活
            is_deleted=False  # 确保管理员不被删除
        )
        db.session.add(admin)
        db.session.commit()
        print("管理员用户创建成功: admin / admin123")

def migrate_user_table():
    """为User表添加is_deleted字段的迁移"""
    with app.app_context():
        try:
            # 检查is_deleted字段是否已存在
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('user')]
            
            if 'is_deleted' not in columns:
                print("正在为User表添加is_deleted字段...")
                # 使用新的语法执行SQL
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE user ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL'))
                    connection.commit()
                print("is_deleted字段添加成功！")
            else:
                print("is_deleted字段已存在，跳过迁移")
                
        except Exception as e:
            print(f"迁移过程中出现错误: {str(e)}")
            print("这可能是因为表结构已经是最新的")

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
    migrate_database()
    migrate_user_table()
    create_admin_user()
    main() 