#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时间工具模块
提供北京时间相关的工具函数
"""

from datetime import datetime
import pytz

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

def get_beijing_time_str(format_str='%Y-%m-%d %H:%M:%S'):
    """获取格式化的北京时间字符串"""
    return get_beijing_time().strftime(format_str)

def get_beijing_timestamp():
    """获取北京时间的时间戳字符串（用于文件名）"""
    return get_beijing_time().strftime('%Y%m%d%H%M%S')

def get_beijing_datetime():
    """获取北京时间的datetime对象（用于数据库）"""
    return get_beijing_time().replace(tzinfo=None) 