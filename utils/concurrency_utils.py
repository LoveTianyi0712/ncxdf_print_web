#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
并发处理工具模块
提供数据库操作的并发安全机制
"""

import threading
import time
import uuid
from contextlib import contextmanager
from functools import wraps

# 全局锁管理器
class LockManager:
    """线程锁管理器"""
    
    def __init__(self):
        self._locks = {}
        self._lock_counter = threading.Lock()
    
    def get_lock(self, key):
        """获取指定键的锁"""
        with self._lock_counter:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]
    
    def remove_lock(self, key):
        """移除指定键的锁"""
        with self._lock_counter:
            if key in self._locks:
                del self._locks[key]

# 全局锁管理器实例
lock_manager = LockManager()

def with_lock(lock_key):
    """装饰器：为函数添加线程锁保护"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock = lock_manager.get_lock(lock_key)
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def generate_transaction_id():
    """生成唯一的事务ID"""
    timestamp = str(int(time.time() * 1000))
    unique_id = str(uuid.uuid4())[:8]
    return f"tx_{timestamp}_{unique_id}"

@contextmanager
def database_lock(lock_name, timeout=30):
    """数据库级别的命名锁"""
    from app import db
    
    lock_acquired = False
    try:
        # 尝试获取MySQL命名锁
        result = db.session.execute(
            f"SELECT GET_LOCK('{lock_name}', {timeout})"
        ).scalar()
        
        if result == 1:
            lock_acquired = True
            yield
        else:
            raise Exception(f"无法获取数据库锁: {lock_name}")
    finally:
        if lock_acquired:
            # 释放锁
            db.session.execute(f"SELECT RELEASE_LOCK('{lock_name}')")

def safe_batch_operation(items, batch_size=100, operation_func=None):
    """安全的批量操作"""
    if not items or not operation_func:
        return []
    
    results = []
    errors = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        try:
            batch_results = operation_func(batch)
            results.extend(batch_results)
        except Exception as e:
            errors.append(f"批次 {i//batch_size + 1} 处理失败: {str(e)}")
    
    return results, errors

class ConcurrentCounter:
    """线程安全的计数器"""
    
    def __init__(self, initial_value=0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, amount=1):
        """递增计数器"""
        with self._lock:
            self._value += amount
            return self._value
    
    def decrement(self, amount=1):
        """递减计数器"""
        with self._lock:
            self._value -= amount
            return self._value
    
    def get_value(self):
        """获取当前值"""
        with self._lock:
            return self._value
    
    def reset(self, new_value=0):
        """重置计数器"""
        with self._lock:
            old_value = self._value
            self._value = new_value
            return old_value

class ResourcePool:
    """线程安全的资源池"""
    
    def __init__(self, max_size=10):
        self.max_size = max_size
        self._pool = []
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
    
    def acquire(self, timeout=None):
        """获取资源"""
        with self._condition:
            while len(self._pool) == 0:
                if not self._condition.wait(timeout):
                    raise Exception("获取资源超时")
            return self._pool.pop()
    
    def release(self, resource):
        """释放资源"""
        with self._condition:
            if len(self._pool) < self.max_size:
                self._pool.append(resource)
                self._condition.notify()
    
    def size(self):
        """获取池大小"""
        with self._lock:
            return len(self._pool)

def retry_on_deadlock(max_retries=3, delay=0.1):
    """装饰器：在数据库死锁时重试"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # 检查是否是死锁或锁等待超时
                    if any(keyword in error_msg for keyword in ['deadlock', 'lock wait timeout', '1213', '1205']):
                        if attempt < max_retries - 1:
                            time.sleep(delay * (2 ** attempt))  # 指数退避
                            continue
                    
                    # 不是死锁或已达到最大重试次数
                    raise
            
            raise last_exception
        return wrapper
    return decorator 