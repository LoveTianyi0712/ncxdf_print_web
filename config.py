#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 数据库配置 - 支持SQLite和MySQL
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite').lower()
    
    if DATABASE_TYPE == 'mysql':
        # MySQL配置
        MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
        MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
        MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'print_system')
        MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME', 'root')
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
        
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    else:
        # SQLite配置（默认）
        SQLALCHEMY_DATABASE_URI = 'sqlite:///print_system.db'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 