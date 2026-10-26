#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 常量定义
集中管理所有游戏常量，避免魔法数字
"""

from texas_holdem.engine.game_rules import MAX_PLAYERS as TABLE_MAX_PLAYERS
from texas_holdem.engine.game_rules import MIN_PLAYERS as TABLE_MIN_PLAYERS

# ============================================================================
# 游戏基础常量
# ============================================================================

# 默认游戏设置
DEFAULT_SMALL_BLIND = 5
DEFAULT_BIG_BLIND = 10
DEFAULT_INITIAL_CHIPS = 1000
DEFAULT_AI_COUNT = 2

# 玩家数量限制
MIN_PLAYERS = TABLE_MIN_PLAYERS
MAX_PLAYERS = TABLE_MAX_PLAYERS
MIN_AI_PLAYERS = 1
MAX_AI_PLAYERS = 9

# 筹码限制
MIN_CHIPS = 100
MAX_CHIPS = 100000
MIN_BLIND = 1
MAX_BLIND = 1000

# ============================================================================
# 手牌强度等级
# ============================================================================

class HandRankValue:
    """手牌等级值"""
    ROYAL_FLUSH = 10      # 皇家同花顺
    STRAIGHT_FLUSH = 9    # 同花顺
    FOUR_OF_A_KIND = 8    # 四条
    FULL_HOUSE = 7        # 葫芦
    FLUSH = 6             # 同花
    STRAIGHT = 5          # 顺子
    THREE_OF_A_KIND = 4   # 三条
    TWO_PAIR = 3          # 两对
    ONE_PAIR = 2          # 一对
    HIGH_CARD = 1         # 高牌


# 手牌强度映射（用于AI决策）
HAND_STRENGTH_MAP = {
    HandRankValue.ROYAL_FLUSH: 1.00,
    HandRankValue.STRAIGHT_FLUSH: 0.98,
    HandRankValue.FOUR_OF_A_KIND: 0.95,
    HandRankValue.FULL_HOUSE: 0.88,
    HandRankValue.FLUSH: 0.78,
    HandRankValue.STRAIGHT: 0.70,
    HandRankValue.THREE_OF_A_KIND: 0.58,
    HandRankValue.TWO_PAIR: 0.45,
    HandRankValue.ONE_PAIR: 0.32,
    HandRankValue.HIGH_CARD: 0.20,
}

# ============================================================================
# AI决策阈值
# ============================================================================

class AIThresholds:
    """AI决策阈值"""
    
    # 翻牌前加注阈值
    PREFLOP_RAISE_STRONG = 0.75    # 强牌加注
    PREFLOP_RAISE_MEDIUM = 0.55    # 中等牌加注
    PREFLOP_CALL_MIN = 0.35        # 最低跟注强度
    
    # 翻牌后决策阈值
    POSTFLOP_VALUE_BET = 0.65      # 价值下注阈值
    POSTFLOP_BLUFF = 0.25          # 诈唬阈值
    POSTFLOP_FOLD = 0.20           # 弃牌阈值
    
    # 底池赔率相关
    POT_ODDS_MARGIN = 1.5          # 胜率需超过所需的倍数
    
    # 位置加成
    POSITION_BONUS_LATE = 0.10     # 后位加成
    POSITION_BONUS_MIDDLE = 0.05  # 中位加成
    
    # 诈唬频率
    BLUFF_FREQUENCY_BASE = 0.10   # 基础诈唬频率
    BLUFF_FREQUENCY_DRY = 0.15    # 干燥牌面诈唬频率
    BLUFF_FREQUENCY_WET = 0.05    # 湿润牌面诈唬频率


# ============================================================================
# 玩家风格参数
# ============================================================================

class PlayerStyleParams:
    """玩家风格参数"""
    
    # VPIP (入局率) 分类
    VPIP_TIGHT = 20       # 紧凑型
    VPIP_NORMAL = 30      # 正常型
    VPIP_LOOSE = 40       # 松散型
    
    # PFR (翻牌前加注率) 分类
    PFR_PASSIVE = 10      # 被动型
    PFR_NORMAL = 18       # 正常型
    PFR_AGGRESSIVE = 25   # 激进型
    
    # 攻击性系数分类
    AF_PASSIVE = 1.0      # 被动
    AF_NORMAL = 1.5       # 正常
    AF_AGGRESSIVE = 2.5   # 激进


# ============================================================================
# 胜率计算参数
# ============================================================================

class OddsCalculatorParams:
    """胜率计算参数"""
    
    # 蒙特卡洛模拟次数
    SIMULATIONS_FAST = 1000
    SIMULATIONS_NORMAL = 3000
    SIMULATIONS_ACCURATE = 8000
    SIMULATIONS_PRECISE = 15000
    
    # 缓存大小
    CACHE_SIZE_SMALL = 1000
    CACHE_SIZE_MEDIUM = 5000
    CACHE_SIZE_LARGE = 10000


# ============================================================================
# 显示相关常量
# ============================================================================

class DisplayConstants:
    """显示相关常量"""
    
    # 界面宽度
    UI_WIDTH = 60
    TABLE_WIDTH = 50
    
    # 进度条
    PROGRESS_BAR_WIDTH = 30
    
    # 图表
    CHART_WIDTH = 50
    CHART_HEIGHT = 12


# ============================================================================
# 游戏阶段名称
# ============================================================================

class GamePhase:
    """游戏阶段"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


# ============================================================================
# 动作类型
# ============================================================================

class ActionType:
    """动作类型"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


# ============================================================================
# 花色和牌面符号
# ============================================================================

SUIT_SYMBOLS = {
    'hearts': '♥',
    'diamonds': '♦',
    'clubs': '♣',
    'spades': '♠'
}

RANK_SYMBOLS = {
    2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
    10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
}

RANK_NAMES = {
    2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six',
    7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
    11: 'Jack', 12: 'Queen', 13: 'King', 14: 'Ace'
}


# ============================================================================
# 翻牌前手牌强度表
# ============================================================================

PREFLOP_HAND_RANKINGS = {
    # 对子
    'AA': 0.95, 'KK': 0.90, 'QQ': 0.85, 'JJ': 0.80, 'TT': 0.75,
    '99': 0.70, '88': 0.65, '77': 0.60, '66': 0.55, '55': 0.52,
    '44': 0.50, '33': 0.48, '22': 0.46,
    
    # 同花大牌
    'AKs': 0.82, 'AQs': 0.76, 'AJs': 0.72, 'ATs': 0.68,
    'KQs': 0.72, 'KJs': 0.68, 'KTs': 0.64,
    'QJs': 0.66, 'QTs': 0.62,
    'JTs': 0.62,
    
    # 非同花大牌
    'AKo': 0.78, 'AQo': 0.72, 'AJo': 0.68, 'ATo': 0.64,
    'KQo': 0.68, 'KJo': 0.64, 'KTo': 0.60,
    'QJo': 0.62, 'QTo': 0.58,
    'JTo': 0.58,
    
    # 同花连牌
    'T9s': 0.55, '98s': 0.52, '87s': 0.50, '76s': 0.48,
    '65s': 0.46, '54s': 0.44,
    
    # 同花A
    'A9s': 0.58, 'A8s': 0.56, 'A7s': 0.54, 'A6s': 0.52,
    'A5s': 0.54, 'A4s': 0.52, 'A3s': 0.50, 'A2s': 0.48,
}

# 默认手牌强度（未在表中的手牌）
DEFAULT_HAND_STRENGTH = 0.35


# ============================================================================
# 位置定义
# ============================================================================

class Position:
    """位置类型"""
    UTG = "UTG"      # Under The Gun (最早位置)
    UTG1 = "UTG+1"   # UTG+1
    MP = "MP"        # Middle Position (中间位置)
    MP1 = "MP+1"     # MP+1
    CO = "CO"        # Cut Off (按钮位前一位)
    BTN = "BTN"      # Button (按钮位/庄家位)
    SB = "SB"        # Small Blind (小盲)
    BB = "BB"        # Big Blind (大盲)


# ============================================================================
# 详细位置翻牌前范围 (基于真实玩家统计)
# 每个位置的开池范围、3bet范围、冷跟范围
# ============================================================================

# 手牌分组 - 按强度排序的前N%手牌
HAND_TIERS = {
    # Tier 1: 前5%的牌 (Premium)
    "tier1": {"AA", "KK", "QQ", "AKs", "AKo"},
    
    # Tier 2: 前10%的牌 (Strong)
    "tier2": {"JJ", "TT", "AQs", "AQo", "AJs", "KQs"},
    
    # Tier 3: 前15%的牌 (Good)
    "tier3": {"99", "88", "ATs", "AJo", "KJs", "KQo", "QJs"},
    
    # Tier 4: 前22%的牌 (Playable)
    "tier4": {"77", "66", "A9s", "A8s", "ATo", "KTs", "KJo", "QTs", "QJo", "JTs"},
    
    # Tier 5: 前30%的牌 (Speculative)
    "tier5": {"55", "44", "33", "22", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
              "K9s", "Q9s", "J9s", "T9s", "98s", "87s", "76s", "65s", "54s"},
    
    # Tier 6: 前40%的牌 (Marginal)
    "tier6": {"A9o", "K9o", "Q9o", "J9o", "T9o", "97s", "86s", "75s", "64s", "53s"},
}

# 位置特定的开池范围 (Open Raise Range)
POSITION_OPEN_RANGES = {
    Position.UTG: {
        "range": {"tier1", "tier2"},  # 约10%的牌
        "vpip_target": 12,
    },
    Position.UTG1: {
        "range": {"tier1", "tier2"},  # 约10%
        "vpip_target": 12,
    },
    Position.MP: {
        "range": {"tier1", "tier2", "tier3"},  # 约15%
        "vpip_target": 15,
    },
    Position.MP1: {
        "range": {"tier1", "tier2", "tier3"},  # 约15%
        "vpip_target": 16,
    },
    Position.CO: {
        "range": {"tier1", "tier2", "tier3", "tier4"},  # 约22%
        "vpip_target": 22,
    },
    Position.BTN: {
        "range": {"tier1", "tier2", "tier3", "tier4", "tier5"},  # 约30%
        "vpip_target": 28,
    },
    Position.SB: {
        "range": {"tier1", "tier2", "tier3", "tier4"},  # 约22%
        "vpip_target": 25,
    },
    Position.BB: {
        "range": {"tier1", "tier2", "tier3", "tier4", "tier5", "tier6"},  # 防守范围更宽
        "vpip_target": 40,  # BB主要是防守
    },
}

# 3-Bet范围 (对已有加注的再加注)
POSITION_3BET_RANGES = {
    Position.UTG: {"tier1"},  # 只用最强的牌3bet
    Position.UTG1: {"tier1"},
    Position.MP: {"tier1", "tier2"},
    Position.MP1: {"tier1", "tier2"},
    Position.CO: {"tier1", "tier2"},
    Position.BTN: {"tier1", "tier2", "tier3"},  # Button可以更宽
    Position.SB: {"tier1", "tier2"},
    Position.BB: {"tier1", "tier2", "tier3"},  # BB防守3bet可以宽一点
}

# 冷跟范围 (面对加注时跟注)
POSITION_COLD_CALL_RANGES = {
    Position.UTG: set(),  # UTG不应该冷跟
    Position.UTG1: set(),
    Position.MP: {"tier3"},  # 只跟一些中等强度的牌
    Position.MP1: {"tier3", "tier4"},
    Position.CO: {"tier3", "tier4"},
    Position.BTN: {"tier3", "tier4", "tier5"},  # Button有位置优势
    Position.SB: {"tier3"},  # SB位置不好，范围窄
    Position.BB: {"tier3", "tier4", "tier5"},  # BB有很好的底池赔率
}

# BB面对开池加注的防守范围
BB_DEFENSE_RANGES = {
    "vs_utg": {"tier1", "tier2", "tier3"},  # 对UTG开池紧一点
    "vs_mp": {"tier1", "tier2", "tier3", "tier4"},
    "vs_co": {"tier1", "tier2", "tier3", "tier4", "tier5"},
    "vs_btn": {"tier1", "tier2", "tier3", "tier4", "tier5", "tier6"},  # 对Button宽防守
    "vs_sb": {"tier1", "tier2", "tier3", "tier4", "tier5", "tier6"},  # 对SB也宽防守
}


# ============================================================================
# 混合策略频率 (用于模拟真人的随机性)
# ============================================================================

class MixedStrategyFreqs:
    """混合策略频率参数"""
    
    # 价值手牌的慢打频率
    SLOW_PLAY_MONSTER = 0.15    # 超强牌慢打15%
    SLOW_PLAY_STRONG = 0.10     # 强牌慢打10%
    
    # 诈唬频率 (基于位置)
    BLUFF_FREQ_IP = 0.12        # 有位置时诈唬12%
    BLUFF_FREQ_OOP = 0.06       # 无位置时诈唬6%
    
    # 半诈唬频率 (有听牌时)
    SEMI_BLUFF_FREQ = 0.35      # 有听牌时半诈唬35%
    
    # 边缘牌混合策略
    MARGINAL_CHECK_CALL = 0.50  # 边缘牌50%过牌跟注
    MARGINAL_CHECK_FOLD = 0.30  # 边缘牌30%过牌弃牌
    MARGINAL_BET = 0.20         # 边缘牌20%薄价值下注
    
    # 强牌面对加注的混合
    STRONG_VS_RAISE_CALL = 0.60   # 60%平跟
    STRONG_VS_RAISE_RERAISE = 0.40  # 40%再加注
    
    # 随机化决策的噪音
    DECISION_NOISE = 0.05       # 5%的随机偏差


# ============================================================================
# 底池赔率相关参数
# ============================================================================

class PotOddsParams:
    """底池赔率参数"""
    
    # 隐含赔率乘数 (根据听牌强度调整)
    IMPLIED_ODDS_FLUSH_DRAW = 1.3    # 同花听牌
    IMPLIED_ODDS_STRAIGHT_DRAW = 1.2  # 顺子听牌
    IMPLIED_ODDS_COMBO_DRAW = 1.5     # 组合听牌
    IMPLIED_ODDS_DEFAULT = 1.0        # 无听牌
    
    # 最小胜率要求调整
    MIN_EQUITY_TO_CALL = 0.25   # 至少25%胜率才考虑跟注
    MIN_EQUITY_TO_RAISE = 0.40  # 至少40%胜率才考虑加注

