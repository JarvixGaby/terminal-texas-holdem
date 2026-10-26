#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LRU 缓存实现
提供线程安全的 LRU (Least Recently Used) 缓存机制
"""

from collections import OrderedDict
from typing import Any, Optional
import threading


class LRUCache:
    """
    LRU (Least Recently Used) 缓存

    当缓存达到最大容量时，自动移除最久未使用的项
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化 LRU 缓存

        Args:
            max_size: 缓存最大容量
        """
        if max_size <= 0:
            raise ValueError("max_size 必须大于 0")

        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.Lock()  # 线程安全

        # 统计信息
        self.hits = 0
        self.misses = 0

    def get(self, key: Any) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在返回 None
        """
        with self.lock:
            if key in self.cache:
                # 移动到末尾（标记为最近使用）
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None

    def put(self, key: Any, value: Any) -> None:
        """
        存入缓存

        Args:
            key: 缓存键
            value: 缓存值
        """
        with self.lock:
            if key in self.cache:
                # 更新值并移动到末尾
                self.cache.move_to_end(key)
                self.cache[key] = value
            else:
                # 新增项
                self.cache[key] = value
                # 如果超过容量，移除最久未使用的项
                if len(self.cache) > self.max_size:
                    self.cache.popitem(last=False)

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def size(self) -> int:
        """返回当前缓存大小"""
        with self.lock:
            return len(self.cache)

    def get_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            包含命中率、缓存大小等信息的字典
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f'{hit_rate:.2f}%',
                'size': len(self.cache),
                'max_size': self.max_size,
                'utilization': f'{len(self.cache) / self.max_size * 100:.1f}%'
            }

    def __len__(self) -> int:
        """返回缓存大小"""
        return self.size()

    def __contains__(self, key: Any) -> bool:
        """检查键是否在缓存中"""
        with self.lock:
            return key in self.cache
