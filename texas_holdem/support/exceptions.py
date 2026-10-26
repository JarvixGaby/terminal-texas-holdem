#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 自定义异常类
统一的异常处理和错误消息格式
"""


class PokerGameException(Exception):
    """扑克游戏基础异常类"""
    pass


class InvalidBetException(PokerGameException):
    """无效下注异常"""
    def __init__(self, player_name: str, amount: int, reason: str):
        self.player_name = player_name
        self.amount = amount
        self.reason = reason
        super().__init__(
            f"玩家 {player_name} 的下注无效 (金额: {amount}): {reason}"
        )


class InvalidCardException(PokerGameException):
    """无效卡牌异常"""
    def __init__(self, message: str):
        super().__init__(f"卡牌错误: {message}")


class GameStateException(PokerGameException):
    """游戏状态异常"""
    def __init__(self, message: str):
        super().__init__(f"游戏状态错误: {message}")


class AIDecisionException(PokerGameException):
    """AI 决策异常"""
    def __init__(self, ai_name: str, reason: str):
        self.ai_name = ai_name
        self.reason = reason
        super().__init__(
            f"AI {ai_name} 决策失败: {reason}"
        )


class InfiniteLoopException(PokerGameException):
    """无限循环异常"""
    def __init__(self, phase: str, iteration_count: int):
        self.phase = phase
        self.iteration_count = iteration_count
        super().__init__(
            f"检测到潜在无限循环 (阶段: {phase}, 迭代次数: {iteration_count})"
        )
