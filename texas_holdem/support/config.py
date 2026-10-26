#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 配置管理
集中管理所有常量和配置参数
"""

from dataclasses import dataclass
from typing import Dict

from texas_holdem.engine.game_rules import (
    MAX_PLAYERS as TABLE_MAX_PLAYERS,
    MIN_PLAYERS as TABLE_MIN_PLAYERS,
)


# ============================================================================
# 游戏配置
# ============================================================================

@dataclass
class GameConfig:
    """游戏基础配置"""
    # 玩家数量限制
    MIN_PLAYERS: int = TABLE_MIN_PLAYERS
    MAX_PLAYERS: int = TABLE_MAX_PLAYERS

    # 默认盲注
    DEFAULT_SMALL_BLIND: int = 5
    DEFAULT_BIG_BLIND: int = 10

    # 默认筹码
    DEFAULT_CHIPS: int = 1000

    # 下注轮次保护
    MAX_BETTING_ITERATIONS: int = 100

    # AI 延迟（秒）
    AI_ACTION_DELAY: float = 1.0


# ============================================================================
# 缓存配置
# ============================================================================

@dataclass
class CacheConfig:
    """缓存配置"""
    # 手牌评估缓存大小
    FIVE_CARD_CACHE_SIZE: int = 10000
    SEVEN_CARD_CACHE_SIZE: int = 5000

    # 胜率计算缓存大小
    ODDS_CACHE_SIZE: int = 1000

    # 缓存启用开关
    CACHE_ENABLED: bool = True


# ============================================================================
# 性能配置
# ============================================================================

@dataclass
class PerformanceConfig:
    """性能配置"""
    # 蒙特卡洛模拟次数
    SIMULATION_FAST: int = 1000
    SIMULATION_NORMAL: int = 3000
    SIMULATION_ACCURATE: int = 8000
    SIMULATION_PRECISE: int = 15000

    # 默认性能等级
    DEFAULT_PERFORMANCE_LEVEL: str = "NORMAL"


# ============================================================================
# AI 配置
# ============================================================================

@dataclass
class AIConfig:
    """AI 配置"""
    # AI 模式
    USE_ADVANCED_AI: bool = True

    # AI 技能等级权重
    BEGINNER_WEIGHTS: list = None
    INTERMEDIATE_WEIGHTS: list = None
    ADVANCED_WEIGHTS: list = None
    EXPERT_WEIGHTS: list = None

    def __post_init__(self):
        if self.BEGINNER_WEIGHTS is None:
            self.BEGINNER_WEIGHTS = [8, 12, 12, 10, 8, 12, 8, 5, 10, 5, 10]
        if self.INTERMEDIATE_WEIGHTS is None:
            self.INTERMEDIATE_WEIGHTS = [8, 10, 15, 8, 12, 10, 8, 8, 6, 8, 7]
        if self.ADVANCED_WEIGHTS is None:
            self.ADVANCED_WEIGHTS = [5, 8, 18, 5, 15, 8, 10, 10, 3, 12, 6]
        if self.EXPERT_WEIGHTS is None:
            self.EXPERT_WEIGHTS = [3, 5, 20, 3, 18, 5, 8, 12, 2, 15, 9]


# ============================================================================
# 全局配置实例
# ============================================================================

game_config = GameConfig()
cache_config = CacheConfig()
performance_config = PerformanceConfig()
ai_config = AIConfig()


# ============================================================================
# 配置管理器
# ============================================================================

class ConfigManager:
    """配置管理器 - 提供运行时配置调整"""

    @staticmethod
    def get_game_config() -> GameConfig:
        """获取游戏配置"""
        return game_config

    @staticmethod
    def get_cache_config() -> CacheConfig:
        """获取缓存配置"""
        return cache_config

    @staticmethod
    def get_performance_config() -> PerformanceConfig:
        """获取性能配置"""
        return performance_config

    @staticmethod
    def get_ai_config() -> AIConfig:
        """获取 AI 配置"""
        return ai_config

    @staticmethod
    def set_performance_level(level: str) -> None:
        """
        设置性能等级

        Args:
            level: FAST, NORMAL, ACCURATE, PRECISE
        """
        performance_config.DEFAULT_PERFORMANCE_LEVEL = level.upper()
        print(f"✅ 性能等级已设置为: {level.upper()}")

    @staticmethod
    def enable_cache(enabled: bool = True) -> None:
        """启用/禁用缓存"""
        cache_config.CACHE_ENABLED = enabled
        status = "启用" if enabled else "禁用"
        print(f"✅ 缓存已{status}")

    @staticmethod
    def set_ai_mode(use_advanced: bool = True) -> None:
        """设置 AI 模式"""
        ai_config.USE_ADVANCED_AI = use_advanced
        mode = "高级" if use_advanced else "标准"
        print(f"✅ AI 模式已设置为: {mode}")

    @staticmethod
    def print_config() -> None:
        """打印当前配置"""
        print("\n" + "="*60)
        print("当前配置")
        print("="*60)

        print("\n🎮 游戏配置:")
        print(f"  玩家数量: {game_config.MIN_PLAYERS}-{game_config.MAX_PLAYERS}")
        print(f"  默认盲注: {game_config.DEFAULT_SMALL_BLIND}/{game_config.DEFAULT_BIG_BLIND}")
        print(f"  默认筹码: {game_config.DEFAULT_CHIPS}")

        print("\n💾 缓存配置:")
        print(f"  缓存启用: {'是' if cache_config.CACHE_ENABLED else '否'}")
        print(f"  5张牌缓存: {cache_config.FIVE_CARD_CACHE_SIZE}")
        print(f"  7张牌缓存: {cache_config.SEVEN_CARD_CACHE_SIZE}")

        print("\n⚡ 性能配置:")
        print(f"  当前等级: {performance_config.DEFAULT_PERFORMANCE_LEVEL}")
        print(f"  快速模拟: {performance_config.SIMULATION_FAST} 次")
        print(f"  标准模拟: {performance_config.SIMULATION_NORMAL} 次")
        print(f"  精确模拟: {performance_config.SIMULATION_ACCURATE} 次")

        print("\n🤖 AI 配置:")
        print(f"  AI 模式: {'高级' if ai_config.USE_ADVANCED_AI else '标准'}")

        print("="*60 + "\n")


# ============================================================================
# 便捷访问函数
# ============================================================================

def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return ConfigManager


if __name__ == "__main__":
    # 测试配置管理器
    ConfigManager.print_config()
