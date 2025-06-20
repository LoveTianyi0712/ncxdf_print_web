#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from datetime import timedelta

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MySQL数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'print_system')
    MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    
    # 数据库连接池配置 - 优化并发性能
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,        # 连接池大小
        'pool_timeout': 30,     # 连接超时时间
        'pool_recycle': 3600,   # 连接回收时间(1小时)
        'max_overflow': 30,     # 最大溢出连接数
        'pool_pre_ping': True,  # 连接前预检查
        # 设置事务隔离级别为READ COMMITTED，提高并发性能
        'isolation_level': 'READ_COMMITTED'
    }
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = True
    # 生产环境使用更大的连接池
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 50,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'max_overflow': 100,
        'pool_pre_ping': True,
        'isolation_level': 'READ_COMMITTED'
    }

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 