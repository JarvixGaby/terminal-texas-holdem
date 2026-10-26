#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级AI决策引擎
实现接近真实玩家的德州扑克策略：
- 范围思维（Range-based thinking）
- GTO基础策略（Game Theory Optimal）
- 剥削策略（Exploitative play）
- 高级诈唬系统（Balanced bluffing）
- 下注尺度优化（Bet sizing）
- 板面纹理分析（Board texture analysis）
- 蒙特卡洛胜率计算（Monte Carlo equity）
- 位置分层手牌范围（Position-based ranges）
- 混合策略随机化（Mixed strategy randomization）
"""

import random
import math
from itertools import combinations
from typing import Any, Dict, List, Tuple, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.engine.hand_evaluator import HandEvaluator
from texas_holdem.ai.constants import (
    Position, HAND_TIERS, POSITION_OPEN_RANGES, POSITION_3BET_RANGES,
    POSITION_COLD_CALL_RANGES, BB_DEFENSE_RANGES,
    MixedStrategyFreqs, PotOddsParams
)
from texas_holdem.ai.ai_profiles import AIArchetypeProfile, get_archetype_profile


class BoardTexture(Enum):
    """公共牌面纹理类型"""
    DRY = "干燥"           # 如 K-7-2 rainbow，听牌少
    WET = "湿润"           # 如 J-T-9 两同花，听牌多
    COORDINATED = "协调"   # 连牌多，顺子可能性高
    PAIRED = "配对"        # 公共牌有对子
    MONOTONE = "单色"      # 三张同花色
    RAINBOW = "彩虹"       # 三张不同花色


class ActionLine(Enum):
    """行动线路类型"""
    VALUE_BET = "value"        # 价值下注
    BLUFF = "bluff"            # 纯诈唬
    SEMI_BLUFF = "semi_bluff"  # 半诈唬（有听牌）
    THIN_VALUE = "thin_value"  # 薄价值
    CHECK_CALL = "check_call"  # 过牌跟注（抓诈唬）
    CHECK_FOLD = "check_fold"  # 过牌弃牌
    CHECK_RAISE = "check_raise" # 过牌加注（陷阱）


@dataclass
class HandRange:
    """
    手牌范围表示
    用于范围思维 - 考虑对手可能持有的所有手牌组合
    """
    # 使用简化的范围表示：按强度分组
    premium: Set[str] = field(default_factory=lambda: {"AA", "KK", "QQ", "AKs", "AKo"})
    strong: Set[str] = field(default_factory=lambda: {"JJ", "TT", "AQs", "AQo", "AJs", "KQs"})
    medium: Set[str] = field(default_factory=lambda: {"99", "88", "77", "ATs", "KJs", "QJs", "JTs"})
    speculative: Set[str] = field(default_factory=lambda: {"66", "55", "44", "33", "22", "suited_connectors"})
    weak: Set[str] = field(default_factory=lambda: {"random_hands"})
    
    def get_range_for_action(self, action: str, position: str) -> Set[str]:
        """根据动作和位置获取可能的手牌范围"""
        if action == "raise" and position in ["UTG", "MP"]:
            return self.premium | self.strong
        elif action == "raise" and position in ["CO", "BTN"]:
            return self.premium | self.strong | self.medium
        elif action == "call":
            return self.medium | self.speculative
        else:
            return self.weak


@dataclass
class OpponentProfile:
    """
    对手档案 - 详细的对手建模
    """
    name: str
    # 基础统计
    vpip: float = 25.0              # 入局率
    pfr: float = 18.0               # 翻牌前加注率
    three_bet: float = 6.0          # 3bet频率
    fold_to_three_bet: float = 60.0 # 对3bet的弃牌率
    
    # 翻牌后统计
    cbet_flop: float = 65.0         # 翻牌持续下注率
    cbet_turn: float = 50.0         # 转牌持续下注率
    fold_to_cbet: float = 45.0      # 对持续下注弃牌率
    
    # 侵略性指标
    aggression_factor: float = 2.0   # 侵略因子 (bet+raise)/call
    wtsd: float = 28.0              # 摊牌率 (Went to Showdown)
    won_at_sd: float = 52.0         # 摊牌胜率
    
    # 漏洞标记
    folds_too_much: bool = False     # 弃牌过多
    calls_too_much: bool = False     # 跟注过多
    bluffs_too_much: bool = False    # 诈唬过多
    bet_sizing_tells: bool = False   # 下注尺度有破绽
    
    # 历史动作
    recent_actions: List[Tuple[str, int]] = field(default_factory=list)
    
    # 增强的统计追踪
    hands_played: int = 0                # 总手数
    hands_vpip: int = 0                  # 入局手数
    hands_pfr: int = 0                   # 翻牌前加注手数
    hands_3bet: int = 0                  # 3bet手数
    hands_fold_to_3bet: int = 0          # 面对3bet弃牌次数
    hands_faced_3bet: int = 0            # 面对3bet次数
    
    # 位置统计
    position_stats: Dict[str, Dict] = field(default_factory=lambda: {
        "UTG": {"hands": 0, "vpip": 0, "pfr": 0},
        "MP": {"hands": 0, "vpip": 0, "pfr": 0},
        "CO": {"hands": 0, "vpip": 0, "pfr": 0},
        "BTN": {"hands": 0, "vpip": 0, "pfr": 0},
        "SB": {"hands": 0, "vpip": 0, "pfr": 0},
        "BB": {"hands": 0, "vpip": 0, "pfr": 0},
    })
    
    # 翻牌后统计
    cbet_opportunities: int = 0          # 持续下注机会
    cbet_made: int = 0                   # 实际持续下注次数
    faced_cbet: int = 0                  # 面对持续下注次数
    folded_to_cbet: int = 0              # 面对持续下注弃牌次数
    
    def update_from_action(self, action: str, amount: int, phase: str, 
                          position: str = None, is_new_hand: bool = False):
        """
        根据观察到的动作更新档案
        增强版：追踪更详细的统计数据
        """
        self.recent_actions.append((action, amount))
        if len(self.recent_actions) > 100:  # 增加历史记录
            self.recent_actions.pop(0)
        
        # 新手牌开始
        if is_new_hand:
            self.hands_played += 1
            if position and position in self.position_stats:
                self.position_stats[position]["hands"] += 1
        
        # 翻牌前统计
        if phase == "preflop":
            if action in ["raise", "call"]:
                self.hands_vpip += 1
                if position and position in self.position_stats:
                    self.position_stats[position]["vpip"] += 1
            
            if action == "raise":
                self.hands_pfr += 1
                if position and position in self.position_stats:
                    self.position_stats[position]["pfr"] += 1
        
        # 更新统计
        if self.hands_played > 0:
            self.vpip = (self.hands_vpip / self.hands_played) * 100
            self.pfr = (self.hands_pfr / self.hands_played) * 100
        
        if self.hands_faced_3bet > 0:
            self.fold_to_three_bet = (self.hands_fold_to_3bet / self.hands_faced_3bet) * 100
        
        if self.cbet_opportunities > 0:
            self.cbet_flop = (self.cbet_made / self.cbet_opportunities) * 100
        
        if self.faced_cbet > 0:
            self.fold_to_cbet = (self.folded_to_cbet / self.faced_cbet) * 100
        
        # 计算侵略因子
        total = len(self.recent_actions)
        raises = sum(1 for a, _ in self.recent_actions if a == "raise")
        calls = sum(1 for a, _ in self.recent_actions if a == "call")
        folds = sum(1 for a, _ in self.recent_actions if a == "fold")
        
        if calls > 0:
            self.aggression_factor = raises / calls
        
        # 检测漏洞
        if self.hands_played >= 20:  # 需要足够样本
            self.folds_too_much = self.fold_to_cbet > 55 or (folds / max(1, total) > 0.45)
            self.calls_too_much = calls / max(1, total) > 0.45 and raises / max(1, total) < 0.15
            self.bluffs_too_much = self.aggression_factor > 3.0 and self.wtsd < 25
    
    def record_3bet_faced(self, folded: bool):
        """记录面对3bet的情况"""
        self.hands_faced_3bet += 1
        if folded:
            self.hands_fold_to_3bet += 1
    
    def record_cbet_opportunity(self, made_cbet: bool):
        """记录持续下注机会"""
        self.cbet_opportunities += 1
        if made_cbet:
            self.cbet_made += 1
    
    def record_faced_cbet(self, folded: bool):
        """记录面对持续下注"""
        self.faced_cbet += 1
        if folded:
            self.folded_to_cbet += 1
    
    def get_position_vpip(self, position: str) -> float:
        """获取特定位置的VPIP"""
        stats = self.position_stats.get(position, {})
        hands = stats.get("hands", 0)
        vpip = stats.get("vpip", 0)
        return (vpip / hands * 100) if hands > 0 else self.vpip
    
    def get_leak_summary(self) -> List[str]:
        """获取漏洞摘要"""
        leaks = []
        if self.folds_too_much:
            leaks.append("弃牌过多 - 可以多诈唬")
        if self.calls_too_much:
            leaks.append("跟注站 - 减少诈唬，多价值下注")
        if self.bluffs_too_much:
            leaks.append("诈唬过多 - 多跟注抓诈唬")
        if self.vpip > 35:
            leaks.append("入局太松 - 可以加宽价值范围")
        if self.vpip < 18:
            leaks.append("入局太紧 - 可以多偷盲")
        return leaks
    
    def get_estimated_range(self, action: str, phase: str, position: str) -> str:
        """估计对手的手牌范围"""
        if phase == "preflop":
            if action == "raise":
                if position in ["UTG", "MP"]:
                    return "tight"  # 10-15%的手牌
                else:
                    return "medium"  # 20-30%的手牌
            elif action == "3bet":
                return "very_tight"  # 5-8%的手牌
        else:
            if action == "raise":
                return "strong_or_bluff"
            elif action == "call":
                return "medium_or_draw"
        return "wide"


class BoardAnalyzer:
    """
    公共牌分析器
    分析牌面纹理、听牌可能性、范围互动
    """
    
    @staticmethod
    def analyze_texture(community_cards: List[Card]) -> Dict:
        """分析公共牌纹理"""
        if not community_cards:
            return {"texture": BoardTexture.DRY, "danger_level": 0}
        
        ranks = [c.rank.numeric_value for c in community_cards]
        suits = [c.suit for c in community_cards]
        
        result = {
            "texture": BoardTexture.DRY,
            "danger_level": 0,  # 0-10, 10最危险
            "flush_possible": False,
            "flush_draw_possible": False,
            "straight_possible": False,
            "straight_draw_possible": False,
            "paired": False,
            "high_cards": sum(1 for r in ranks if r >= 11),
            "connectedness": 0,
        }
        
        # 检查同花/同花听牌
        suit_counts = defaultdict(int)
        for suit in suits:
            suit_counts[suit] += 1
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        
        if max_suit_count >= 3:
            result["flush_possible"] = True
            result["danger_level"] += 4
            result["texture"] = BoardTexture.MONOTONE
        elif max_suit_count == 2 and len(community_cards) >= 3:
            result["flush_draw_possible"] = True
            result["danger_level"] += 2
        
        # 检查顺子/顺子听牌
        unique_ranks = sorted(set(ranks))
        if len(unique_ranks) >= 3:
            # 检查连续性
            gaps = [unique_ranks[i+1] - unique_ranks[i] for i in range(len(unique_ranks)-1)]
            if all(g <= 2 for g in gaps) and max(unique_ranks) - min(unique_ranks) <= 4:
                result["straight_possible"] = True
                result["danger_level"] += 3
                result["texture"] = BoardTexture.COORDINATED
            elif any(g <= 2 for g in gaps):
                result["straight_draw_possible"] = True
                result["danger_level"] += 1
        
        # 检查配对
        if len(ranks) != len(set(ranks)):
            result["paired"] = True
            result["danger_level"] += 2
            result["texture"] = BoardTexture.PAIRED
        
        # 计算协调性
        result["connectedness"] = BoardAnalyzer._calculate_connectedness(ranks)
        
        # 综合判断纹理
        if result["danger_level"] <= 2:
            result["texture"] = BoardTexture.DRY
        elif result["danger_level"] <= 5:
            result["texture"] = BoardTexture.WET
        
        if len(set(suits)) == len(suits) and len(suits) >= 3:
            if result["texture"] == BoardTexture.DRY:
                result["texture"] = BoardTexture.RAINBOW
        
        return result
    
    @staticmethod
    def _calculate_connectedness(ranks: List[int]) -> float:
        """计算牌面连接度 (0-1)"""
        if len(ranks) < 2:
            return 0.0
        
        sorted_ranks = sorted(set(ranks))
        total_gaps = sum(sorted_ranks[i+1] - sorted_ranks[i] - 1 
                        for i in range(len(sorted_ranks)-1))
        max_gaps = len(sorted_ranks) * 4  # 最大间隔
        
        return 1.0 - (total_gaps / max_gaps) if max_gaps > 0 else 0.0
    
    @staticmethod
    def get_equity_vs_range(hole_cards: List[Card], community_cards: List[Card], 
                           opponent_range: str) -> float:
        """
        计算对抗特定范围的胜率
        简化版本：基于范围类型估算
        """
        if not hole_cards or len(hole_cards) != 2:
            return 0.5
        
        # 评估自己的手牌强度
        card1, card2 = hole_cards
        rank1, rank2 = card1.rank.numeric_value, card2.rank.numeric_value
        high_rank = max(rank1, rank2)
        low_rank = min(rank1, rank2)
        suited = card1.suit == card2.suit
        paired = rank1 == rank2
        
        # 基础胜率
        base_equity = 0.5
        
        # 根据手牌调整
        if paired:
            if high_rank >= 11:  # JJ+
                base_equity = 0.75
            elif high_rank >= 8:  # 88-TT
                base_equity = 0.60
            else:
                base_equity = 0.50
        elif high_rank == 14:  # Ax
            if low_rank >= 11:  # AJ+
                base_equity = 0.65
            else:
                base_equity = 0.55
        elif suited and abs(rank1 - rank2) <= 2:  # 同花连牌
            base_equity = 0.45
        else:
            base_equity = 0.40
        
        # 根据对手范围调整
        range_adjustments = {
            "very_tight": -0.15,  # 对手范围很紧，我们胜率降低
            "tight": -0.10,
            "medium": 0.0,
            "wide": 0.10,         # 对手范围宽，我们胜率提高
            "strong_or_bluff": -0.05,
            "medium_or_draw": 0.05,
        }
        
        adjustment = range_adjustments.get(opponent_range, 0.0)
        
        # 如果有公共牌，进一步调整
        if community_cards:
            all_cards = hole_cards + community_cards
            if len(all_cards) >= 5:
                try:
                    hand_rank, _ = HandEvaluator.evaluate_hand(all_cards)
                    # 根据成牌强度调整
                    if hand_rank.rank_value >= 7:  # 葫芦以上
                        base_equity = 0.90
                    elif hand_rank.rank_value >= 5:  # 顺子/同花
                        base_equity = 0.75
                    elif hand_rank.rank_value >= 3:  # 两对以上
                        base_equity = 0.60
                except:
                    pass
        
        return min(0.95, max(0.05, base_equity + adjustment))


class BetSizingEngine:
    """
    下注尺度引擎
    根据目的和情况选择最优下注尺度
    """

    SIZING_BUCKETS = {
        "small": 1 / 3,
        "half-pot": 0.50,
        "two-thirds-pot": 2 / 3,
        "pot-ish": 0.90,
        "all-in": 1.00,
    }

    ACTION_LINE_BUCKETS = {
        ActionLine.VALUE_BET: ("two-thirds-pot", "pot-ish"),
        ActionLine.THIN_VALUE: ("small", "half-pot"),
        ActionLine.BLUFF: ("small", "half-pot"),
        ActionLine.SEMI_BLUFF: ("half-pot", "two-thirds-pot"),
        ActionLine.CHECK_RAISE: ("pot-ish", "all-in"),
    }
    
    @staticmethod
    def calculate_bet_size(pot_size: int, player_chips: int, 
                          action_line: ActionLine, 
                          board_texture: Dict,
                          opponent_profile: Optional[OpponentProfile] = None) -> int:
        """
        计算最优下注尺度
        
        Args:
            pot_size: 当前彩池
            player_chips: 玩家剩余筹码
            action_line: 下注目的/行动线路
            board_texture: 牌面纹理分析
            opponent_profile: 对手档案
        
        Returns:
            下注金额
        """
        bucket_name = BetSizingEngine.select_bucket(action_line, board_texture, opponent_profile)
        if bucket_name == "all-in":
            return max(0, player_chips)

        ratio = BetSizingEngine.SIZING_BUCKETS[bucket_name]
        bet_amount = int(max(pot_size, 0) * ratio)
        min_bet = min(player_chips, max(10, max(pot_size, 0) // 4))
        return min(max(bet_amount, min_bet), max(0, player_chips))

    @staticmethod
    def select_bucket(
        action_line: ActionLine,
        board_texture: Dict,
        opponent_profile: Optional[OpponentProfile] = None,
    ) -> str:
        """Select a simple named bucket for the action purpose."""
        buckets = list(BetSizingEngine.ACTION_LINE_BUCKETS.get(action_line, ("half-pot",)))
        danger_level = board_texture.get("danger_level", 5)

        if action_line == ActionLine.VALUE_BET:
            if opponent_profile and opponent_profile.calls_too_much:
                return "pot-ish"
            if danger_level >= 6:
                return "pot-ish"
            if danger_level <= 2:
                return "two-thirds-pot"
        elif action_line == ActionLine.THIN_VALUE:
            if opponent_profile and opponent_profile.calls_too_much:
                return "half-pot"
            if danger_level <= 2:
                return "small"
        elif action_line == ActionLine.SEMI_BLUFF:
            if danger_level >= 6:
                return "two-thirds-pot"
        elif action_line == ActionLine.BLUFF:
            if opponent_profile and opponent_profile.folds_too_much:
                return "small"
            if danger_level >= 6:
                return "half-pot"

        return random.choice(buckets)
    
    @staticmethod
    def _round_bet(amount: int) -> int:
        """将下注金额圆整到合理的数字"""
        if amount < 50:
            return (amount // 5) * 5 or 5
        elif amount < 200:
            return (amount // 10) * 10
        elif amount < 500:
            return (amount // 25) * 25
        else:
            return (amount // 50) * 50


class PositionRangeManager:
    """
    位置范围管理器
    根据位置和游戏情况确定是否应该玩某手牌
    """
    
    @staticmethod
    def get_position_name(position: int, total_players: int) -> str:
        """
        将数字位置转换为位置名称
        position: 0 为小盲注位，随后按座位顺序递增；两人桌 0 同时是按钮位
        """
        if total_players == 2:
            # In heads-up play the button also posts the small blind.
            return Position.BTN if position == 0 else Position.BB
        if total_players == 3:
            # 短桌简化处理
            if position == total_players - 1:
                return Position.BTN
            elif position == 0:
                return Position.SB
            else:
                return Position.BB
        
        # 标准6-9人桌
        positions_from_button = total_players - position - 1
        
        if positions_from_button == 0:
            return Position.BTN
        elif positions_from_button == 1:
            return Position.CO
        elif positions_from_button == total_players - 1:
            return Position.SB
        elif positions_from_button == total_players - 2:
            return Position.BB
        elif positions_from_button >= total_players - 4:
            return Position.MP
        else:
            return Position.UTG
    
    @staticmethod
    def hand_to_notation(hole_cards: List[Card]) -> str:
        """将手牌转换为标准记号 (如 AA, AKs, AKo)"""
        if len(hole_cards) != 2:
            return ""
        
        c1, c2 = hole_cards
        r1, r2 = c1.rank.numeric_value, c2.rank.numeric_value
        s1, s2 = c1.suit, c2.suit
        
        # 确保高牌在前
        if r1 < r2:
            r1, r2 = r2, r1
            s1, s2 = s2, s1
        
        rank_symbols = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T',
                       9: '9', 8: '8', 7: '7', 6: '6', 5: '5', 4: '4', 3: '3', 2: '2'}
        
        high_symbol = rank_symbols.get(r1, str(r1))
        low_symbol = rank_symbols.get(r2, str(r2))
        
        if r1 == r2:
            return f"{high_symbol}{high_symbol}"
        elif s1 == s2:
            return f"{high_symbol}{low_symbol}s"
        else:
            return f"{high_symbol}{low_symbol}o"
    
    @staticmethod
    def is_hand_in_range(hand_notation: str, tier_names: Set[str]) -> bool:
        """检查手牌是否在指定的范围内"""
        for tier_name in tier_names:
            tier = HAND_TIERS.get(tier_name, set())
            if hand_notation in tier:
                return True
            # 检查通用类型匹配
            if "suited_connectors" in tier and hand_notation.endswith("s"):
                # 检查是否是同花连牌
                if len(hand_notation) == 3:
                    h, l = hand_notation[0], hand_notation[1]
                    ranks = "AKQJT98765432"
                    if h in ranks and l in ranks:
                        h_idx, l_idx = ranks.index(h), ranks.index(l)
                        if abs(h_idx - l_idx) <= 2:
                            return True
        return False
    
    @staticmethod
    def should_open_raise(hole_cards: List[Card], position: str) -> Tuple[bool, float]:
        """
        判断是否应该开池加注
        Returns: (是否应该开池, 建议频率)
        """
        notation = PositionRangeManager.hand_to_notation(hole_cards)
        if not notation:
            return False, 0.0
        
        range_config = POSITION_OPEN_RANGES.get(position, POSITION_OPEN_RANGES[Position.MP])
        tier_names = range_config["range"]
        
        if PositionRangeManager.is_hand_in_range(notation, tier_names):
            return True, 1.0
        
        # 边缘手牌：混合策略
        # 检查是否在下一个tier（可以有一定概率开池）
        all_tiers = ["tier1", "tier2", "tier3", "tier4", "tier5", "tier6"]
        max_tier_in_range = max((all_tiers.index(t) for t in tier_names if t in all_tiers), default=-1)
        
        if max_tier_in_range < 5:  # 还有更宽的范围
            next_tier = all_tiers[max_tier_in_range + 1]
            if PositionRangeManager.is_hand_in_range(notation, {next_tier}):
                # 边缘手牌有25%的概率开池
                return True, 0.25
        
        return False, 0.0
    
    @staticmethod
    def should_3bet(hole_cards: List[Card], position: str) -> Tuple[bool, float]:
        """判断是否应该3bet"""
        notation = PositionRangeManager.hand_to_notation(hole_cards)
        if not notation:
            return False, 0.0
        
        tier_names = POSITION_3BET_RANGES.get(position, POSITION_3BET_RANGES[Position.MP])
        
        if PositionRangeManager.is_hand_in_range(notation, tier_names):
            return True, 1.0
        
        return False, 0.0
    
    @staticmethod
    def should_cold_call(hole_cards: List[Card], position: str) -> Tuple[bool, float]:
        """判断是否应该冷跟"""
        notation = PositionRangeManager.hand_to_notation(hole_cards)
        if not notation:
            return False, 0.0
        
        tier_names = POSITION_COLD_CALL_RANGES.get(position, set())
        
        if PositionRangeManager.is_hand_in_range(notation, tier_names):
            return True, 1.0
        
        return False, 0.0


class MixedStrategyDecider:
    """
    混合策略决策器
    实现真人般的随机性决策
    """
    
    @staticmethod
    def should_slow_play(hand_strength: float) -> bool:
        """判断是否应该慢打"""
        if hand_strength >= 0.90:  # 超强牌
            return random.random() < MixedStrategyFreqs.SLOW_PLAY_MONSTER
        elif hand_strength >= 0.75:  # 强牌
            return random.random() < MixedStrategyFreqs.SLOW_PLAY_STRONG
        return False
    
    @staticmethod
    def get_bluff_probability(has_position: bool, has_draw: bool) -> float:
        """获取诈唬概率"""
        base_prob = MixedStrategyFreqs.BLUFF_FREQ_IP if has_position else MixedStrategyFreqs.BLUFF_FREQ_OOP
        
        if has_draw:
            # 有听牌时更倾向于半诈唬
            return MixedStrategyFreqs.SEMI_BLUFF_FREQ
        
        return base_prob
    
    @staticmethod
    def should_bluff(has_position: bool, has_draw: bool) -> bool:
        """判断是否应该诈唬"""
        prob = MixedStrategyDecider.get_bluff_probability(has_position, has_draw)
        return random.random() < prob
    
    @staticmethod
    def get_marginal_action() -> str:
        """获取边缘牌的混合动作"""
        roll = random.random()
        if roll < MixedStrategyFreqs.MARGINAL_CHECK_CALL:
            return "check_call"
        elif roll < MixedStrategyFreqs.MARGINAL_CHECK_CALL + MixedStrategyFreqs.MARGINAL_CHECK_FOLD:
            return "check_fold"
        else:
            return "thin_value"
    
    @staticmethod
    def should_reraise_strong(hand_strength: float) -> bool:
        """强牌面对加注时是否应该再加注（vs平跟）"""
        if hand_strength >= 0.85:
            # 超强牌更多再加注
            return random.random() < 0.60
        return random.random() < MixedStrategyFreqs.STRONG_VS_RAISE_RERAISE
    
    @staticmethod
    def add_noise(probability: float) -> float:
        """给概率添加随机噪音，模拟真人的不一致性"""
        noise = random.gauss(0, MixedStrategyFreqs.DECISION_NOISE)
        return max(0.0, min(1.0, probability + noise))


class AdvancedAIEngine:
    """
    高级AI决策引擎
    
    实现策略：
    1. 范围思维 - 考虑自己和对手的手牌范围
    2. GTO基础 - 混合策略，平衡价值和诈唬
    3. 剥削调整 - 针对对手漏洞调整策略
    4. 位置意识 - 充分利用位置优势
    5. 多街规划 - 考虑后续街道的行动
    6. 蒙特卡洛胜率 - 使用真实模拟计算胜率
    7. 位置范围系统 - 按位置使用不同的手牌范围
    8. 混合策略 - 随机化决策避免可预测
    """
    
    def __init__(
        self,
        player_name: str,
        skill_level: str = "advanced",
        archetype_name: Optional[str] = None,
        archetype_profile: Optional[AIArchetypeProfile] = None,
    ):
        self.player_name = player_name
        self.skill_level = skill_level
        if archetype_profile is not None and archetype_name is not None:
            raise ValueError("select either archetype_name or archetype_profile, not both")
        self.archetype_profile = archetype_profile
        if archetype_name is not None:
            self.archetype_profile = get_archetype_profile(archetype_name)
        
        # 对手档案
        self.opponent_profiles: Dict[str, OpponentProfile] = {}
        
        # 当前局状态
        self.current_hand_history: List[Dict] = []
        self.preflop_aggressor: Optional[str] = None
        self.last_aggressor: Optional[str] = None
        self.last_decision_explanation: Optional[Dict[str, Any]] = None
        
        # 蒙特卡洛胜率计算器 (延迟加载避免循环导入)
        self._equity_calculator = None
        
        # 位置范围管理器
        self.position_manager = PositionRangeManager()
        
        # 混合策略决策器
        self.mixed_strategy = MixedStrategyDecider()
        
        # 策略参数（可调节）- 已优化使行为更接近真实玩家
        self.aggression_factor = 0.8   # 侵略性系数 (降低，避免过度激进)
        self.bluff_frequency = 0.08    # 基础诈唬频率 (从0.15降至0.08，更保守)
        self.value_bet_threshold = 0.60  # 价值下注阈值 (提高，需要更强牌才下注)
        
        # 翻牌前参数 - 控制入局频率 (真实玩家约15-25% VPIP)
        self.preflop_params = {
            "open_raise_threshold": 0.50,   # 开池加注最低手牌强度 (约前20%的牌)
            "call_threshold": 0.40,         # 跟注最低手牌强度 (约前30%的牌)
            "three_bet_threshold": 0.75,    # 3bet最低手牌强度 (约前8%的牌)
            "cold_call_threshold": 0.55,    # 冷跟最低手牌强度 (约前15%的牌)
        }
        
        # GTO混合策略参数 - 降低激进频率
        self.gto_params = {
            "check_raise_freq": 0.05,  # 过牌加注频率 (从0.08降至0.05)
            "donk_bet_freq": 0.03,     # 反主动下注频率 (从0.05降至0.03)
            "slow_play_freq": 0.12,    # 慢打频率 (从0.10升至0.12，更多慢打)
            "overbet_freq": 0.02,      # 超池下注频率 (从0.03降至0.02)
        }
    
    def _get_equity_calculator(self):
        """延迟加载胜率计算器"""
        if self._equity_calculator is None:
            try:
                from texas_holdem.ai.optimized_odds_calculator import get_ai_equity_calculator
                self._equity_calculator = get_ai_equity_calculator()
            except ImportError:
                self._equity_calculator = None
        return self._equity_calculator
    
    def _get_monte_carlo_equity(self, hole_cards: List[Card], community_cards: List[Card],
                                num_opponents: int) -> float:
        """使用蒙特卡洛模拟获取真实胜率"""
        calculator = self._get_equity_calculator()
        if calculator:
            try:
                return calculator.get_equity(hole_cards, community_cards, num_opponents)
            except Exception:
                pass
        # 回退到静态估算
        return self._estimate_static_equity(hole_cards, community_cards)
    
    def _estimate_static_equity(self, hole_cards: List[Card], community_cards: List[Card]) -> float:
        """静态胜率估算 (当蒙特卡洛不可用时)"""
        if not hole_cards:
            return 0.5
        
        hand_strength = self._evaluate_hand_strength(
            hole_cards, community_cards, 
            BoardAnalyzer.analyze_texture(community_cards)
        )
        return hand_strength.get("raw_strength", 0.5)
    
    def _should_call_by_pot_odds(self, pot_size: int, bet_to_call: int, 
                                  equity: float, has_draw: bool = False) -> bool:
        """基于底池赔率决定是否跟注"""
        if bet_to_call <= 0:
            return True
        
        # 计算底池赔率 (需要的胜率)
        pot_odds = bet_to_call / (pot_size + bet_to_call)
        
        # 如果有听牌，考虑隐含赔率
        if has_draw:
            implied_multiplier = PotOddsParams.IMPLIED_ODDS_FLUSH_DRAW
            required_equity = pot_odds / implied_multiplier
        else:
            required_equity = pot_odds
        
        # 胜率必须超过所需胜率才跟注
        return equity >= max(required_equity, PotOddsParams.MIN_EQUITY_TO_CALL)
    
    def make_decision(self, hole_cards: List[Card], community_cards: List[Card],
                     current_bet: int, min_raise: int, pot_size: int,
                     player_chips: int, position: int, total_players: int,
                     opponents_in_hand: List[str], phase: str = None,
                     table_current_bet: int = None,
                     player_current_bet: int = 0,
                     action_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, int]:
        """
        高级AI决策主函数
        
        决策流程：
        1. 确定位置和游戏阶段
        2. 使用蒙特卡洛计算真实胜率
        3. 翻牌前使用位置范围系统
        4. 翻牌后使用底池赔率+胜率决策
        5. 应用混合策略增加随机性
        6. 剥削调整
        """
        
        # 确定游戏阶段
        if phase is None:
            if not community_cards:
                phase = "preflop"
            elif len(community_cards) == 3:
                phase = "flop"
            elif len(community_cards) == 4:
                phase = "turn"
            else:
                phase = "river"
        
        # 获取位置名称
        position_name = PositionRangeManager.get_position_name(position, total_players)
        
        # 1. 分析牌面纹理
        board_texture = BoardAnalyzer.analyze_texture(community_cards)
        
        # 2. 使用蒙特卡洛计算真实胜率
        num_opponents = len(opponents_in_hand) if opponents_in_hand else 1
        monte_carlo_equity = self._get_monte_carlo_equity(hole_cards, community_cards, num_opponents)
        
        # 3. 评估手牌强度 (用于分类和范围分析)
        hand_strength = self._evaluate_hand_strength(hole_cards, community_cards, board_texture)
        
        # 4. 评估位置优势
        position_advantage = self._evaluate_position(position, total_players)
        has_position = position_advantage > 0.5
        
        # 5. 检查是否有听牌
        has_draw = hand_strength.get("draw_strength", 0) > 0.2
        
        # 6. 翻牌前特殊处理 - 使用位置范围系统
        if phase == "preflop":
            action, amount = self._preflop_decision_v2(
                hole_cards, position_name, monte_carlo_equity,
                current_bet, min_raise, pot_size, player_chips, opponents_in_hand
            )
            if action:
                self.last_decision_explanation = self._build_decision_explanation(
                    action=action,
                    amount=amount,
                    phase=phase,
                    current_bet=current_bet,
                    pot_size=pot_size,
                    equity=monte_carlo_equity,
                    hand_strength=hand_strength,
                    has_draw=has_draw,
                    board_texture=board_texture,
                    action_history=action_history or [],
                )
                return action, amount
        
        if table_current_bet is None:
            table_current_bet = current_bet

        # 7. 翻牌后决策 - 使用底池赔率和胜率
        action, amount = self._postflop_decision_v2(
            hole_cards, community_cards, monte_carlo_equity, hand_strength,
            current_bet, min_raise, pot_size, player_chips,
            has_position, has_draw, board_texture, opponents_in_hand, phase,
            table_current_bet, player_current_bet, action_history or []
        )
        self.last_decision_explanation = self._build_decision_explanation(
            action=action,
            amount=amount,
            phase=phase,
            current_bet=current_bet,
            pot_size=pot_size,
            equity=monte_carlo_equity,
            hand_strength=hand_strength,
            has_draw=has_draw,
            board_texture=board_texture,
            action_history=action_history or [],
        )
        
        return action, amount

    def _build_decision_explanation(
        self,
        action: str,
        amount: int,
        phase: str,
        current_bet: int,
        pot_size: int,
        equity: float,
        hand_strength: Dict[str, Any],
        has_draw: bool,
        board_texture: Dict[str, Any],
        action_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        tags: List[str] = []
        facing_bet = current_bet > 0
        is_cbet_opportunity = self._is_flop_cbet_opportunity(phase, action_history)
        is_facing_cbet = self._is_facing_flop_cbet(phase, action_history)

        if is_cbet_opportunity and action == "raise":
            tags.append("c-bet")
        if is_facing_cbet:
            tags.append("fold-to-cbet" if action == "fold" else "continue-vs-cbet")
        if facing_bet and action == "call":
            tags.append("pot-odds")
        if action == "raise":
            if equity >= 0.60 or hand_strength.get("showdown_value") is True:
                tags.append("value")
            elif has_draw:
                tags.append("semi-bluff")
            elif "c-bet" not in tags:
                tags.append("pressure")
        elif action == "check":
            tags.append("pot-control")
        elif action == "fold" and "fold-to-cbet" not in tags:
            tags.append("fold")

        if not tags:
            tags.append(action)

        return {
            "schema_version": 1,
            "source": "AdvancedAIEngine",
            "summary": self._summarize_decision(action, tags),
            "tags": tags,
            "factors": {
                "phase": phase,
                "action": action,
                "amount": int(amount or 0),
                "facing_bet": facing_bet,
                "pot_odds": round(current_bet / (pot_size + current_bet), 3)
                if facing_bet and pot_size + current_bet > 0
                else None,
                "board_texture": self._public_texture_name(board_texture),
                "profile": self.archetype_profile.name if self.archetype_profile else "default",
            },
        }

    def _summarize_decision(self, action: str, tags: List[str]) -> str:
        if "c-bet" in tags:
            return "Continuation bet with a plausible initiative advantage."
        if "fold-to-cbet" in tags:
            return "Folding weak continuation against flop pressure."
        if "pot-odds" in tags:
            return "Continuing because the call price looks plausible."
        if "value" in tags:
            return "Applying pressure with a value-leaning hand."
        if "semi-bluff" in tags:
            return "Applying pressure with draw equity."
        if action == "check":
            return "Keeping the pot controlled when checking is available."
        if action == "fold":
            return "Declining a costly continue with limited incentive."
        return "Taking a simple pressure line."

    def _public_texture_name(self, board_texture: Dict[str, Any]) -> str:
        texture = board_texture.get("texture")
        if hasattr(texture, "name"):
            return str(texture.name).lower()
        if hasattr(texture, "value"):
            return str(texture.value)
        return str(texture or "unknown")
    
    def _preflop_decision_v2(self, hole_cards: List[Card], position_name: str,
                            equity: float, current_bet: int, min_raise: int,
                            pot_size: int, player_chips: int,
                            opponents_in_hand: List[str]) -> Tuple[Optional[str], int]:
        """
        新版翻牌前决策 - 使用位置范围系统
        
        关键原则:
        1. 只有在范围内的牌才能开池/3bet
        2. 面对加注时，弱牌应该弃牌而不是跟注
        3. 底池赔率只用于边缘决策，不能让弱牌入局
        """
        # 获取手牌记号
        hand_notation = PositionRangeManager.hand_to_notation(hole_cards)

        if self.archetype_profile is not None:
            return self._profiled_preflop_decision(
                hole_cards=hole_cards,
                position_name=position_name,
                equity=equity,
                current_bet=current_bet,
                min_raise=min_raise,
                pot_size=pot_size,
                player_chips=player_chips,
            )
        
        # 没有加注时 (只有盲注)
        if current_bet <= 10:
            if current_bet <= 0:
                should_open, open_freq = PositionRangeManager.should_open_raise(hole_cards, position_name)
                if should_open and random.random() < open_freq:
                    raise_size = max(min_raise, 20)
                    return "raise", min(raise_size, player_chips)
                return "check", 0

            should_open, open_freq = PositionRangeManager.should_open_raise(hole_cards, position_name)
            
            if should_open:
                # 应用混合策略频率
                if random.random() < open_freq:
                    # 开池加注: 2.5-3倍大盲
                    raise_size = int(current_bet * random.uniform(2.5, 3.0))
                    return "raise", min(raise_size, player_chips)
                else:
                    # 边缘手牌有时limp而不是加注 (不推荐但真人会这样)
                    if current_bet <= player_chips and random.random() < 0.3:
                        return "call", current_bet
                    return "fold", 0
            
            # 不在开池范围内的牌 - 直接弃牌
            # 真人玩家不会用垃圾牌入局
            return "fold", 0

        # 面对加注 (current_bet > 10)
        else:
            should_3bet, three_bet_freq = PositionRangeManager.should_3bet(hole_cards, position_name)
            should_cold_call, cold_call_freq = PositionRangeManager.should_cold_call(hole_cards, position_name)
            
            # 计算加注的相对大小
            raise_size_bb = current_bet / 10  # 假设大盲是10
            is_large_raise = raise_size_bb >= 4  # 4倍大盲以上算大加注
            
            # === 3bet决策 ===
            if should_3bet:
                # 只有部分时候3bet (混合策略)
                if random.random() < three_bet_freq:
                    # 3bet尺度: 3-3.5倍
                    raise_size = int(current_bet * random.uniform(3.0, 3.5))
                    if raise_size <= player_chips:
                        return "raise", raise_size
                    # 筹码不够3bet就跟注
                    if player_chips > 0:
                        return "call", min(current_bet, player_chips)
                    return "fold", 0
                else:
                    # 3bet范围内的牌不3bet时，可以平跟
                    if player_chips > 0:
                        return "call", min(current_bet, player_chips)
            
            # === 冷跟决策 ===
            if should_cold_call:
                # 冷跟范围内的牌
                if random.random() < cold_call_freq:
                    if current_bet <= player_chips:
                        return "call", current_bet
                # 冷跟范围内但没跟注，弃牌
                return "fold", 0
            
            # === 不在任何范围内 - 弃牌 ===
            # 这是关键：不在范围内的牌不应该入局
            # 即使底池赔率好，弱牌也不应该跟注
            return "fold", 0

    def _profiled_preflop_decision(self, hole_cards: List[Card], position_name: str,
                                   equity: float, current_bet: int, min_raise: int,
                                   pot_size: int,
                                   player_chips: int) -> Tuple[Optional[str], int]:
        """Apply explicit archetype tendencies to preflop entry/raise choices only."""
        profile = self.archetype_profile
        if profile is None or len(hole_cards) != 2:
            return None, 0

        card1, card2 = hole_cards
        high_rank = max(card1.rank.numeric_value, card2.rank.numeric_value)
        low_rank = min(card1.rank.numeric_value, card2.rank.numeric_value)
        suited = card1.suit == card2.suit
        paired = card1.rank.numeric_value == card2.rank.numeric_value
        raw_strength = self._get_preflop_strength(high_rank, low_rank, suited, paired)
        category = self._categorize_preflop_hand(high_rank, low_rank, suited, paired)
        position_bonus = self._profile_position_bonus(position_name)

        vpip_threshold = max(
            0.18,
            min(0.88, 0.78 - profile.vpip_target * 0.95 - position_bonus),
        )
        profile_is_calling_station = profile.name == "calling_station"
        if profile_is_calling_station:
            # The generic threshold selects roughly a quarter of dealt hands
            # before price checks and the call roll, far below this profile's
            # intended entry rate. Widen only its passive entry range.
            vpip_threshold = max(0.18, vpip_threshold - 0.14)
        pfr_threshold = max(
            0.28,
            min(0.92, 0.90 - profile.pfr_target * 0.75 - profile.aggression_bias * 0.15 - position_bonus),
        )
        call_probability = max(profile.call_bias, profile.vpip_target)
        if profile_is_calling_station:
            call_probability = max(call_probability, 0.92)
        raise_probability = min(
            0.95,
            max(
                0.04,
                (profile.pfr_target / max(profile.vpip_target, 0.01))
                * (0.50 + profile.aggression_bias),
            ),
        )

        is_premium = category in {"premium_pair", "premium_broadways"} or raw_strength >= 0.82
        wants_to_enter = raw_strength >= vpip_threshold or is_premium
        wants_to_raise = raw_strength >= pfr_threshold or is_premium
        pot_odds = current_bet / (pot_size + current_bet) if current_bet > 0 and pot_size + current_bet > 0 else 0.0
        equity_far_below_price = (
            current_bet > 0
            and equity < pot_odds - 0.15
            and not is_premium
        )
        clearly_negative_raise_price = (
            profile_is_calling_station
            and current_bet > 10
            and equity < pot_odds - 0.12
            and not is_premium
        )
        clearly_negative_blind_price = (
            profile_is_calling_station
            and 0 < current_bet <= 10
            and equity < pot_odds - 0.12
            and not is_premium
        )
        strong_price_call = (
            current_bet > 0
            and current_bet <= player_chips
            and (category != "marginal" or raw_strength >= 0.30)
            and equity >= pot_odds + 0.20
            and not equity_far_below_price
        )

        if current_bet <= 0:
            if wants_to_raise and random.random() < max(raise_probability, 0.55 if is_premium else 0.0):
                return "raise", self._legal_preflop_raise_amount(max(min_raise, 20), player_chips)
            return "check", 0

        if current_bet <= 10:
            if equity_far_below_price or clearly_negative_blind_price:
                return "fold", 0
            if not wants_to_enter:
                # Completing the small blind costs less than a full cold call.
                # This passive profile can continue outside its normal range
                # when the public price is covered by its estimated equity.
                if (
                    profile_is_calling_station
                    and position_name == Position.SB
                    and current_bet <= player_chips
                    and equity >= pot_odds
                ):
                    return "call", current_bet
                return "fold", 0
            if wants_to_raise and random.random() < max(raise_probability, 0.55 if is_premium else 0.0):
                raise_size = int(current_bet * self._profile_open_raise_multiplier(profile))
                return "raise", self._legal_preflop_raise_amount(max(min_raise, raise_size), player_chips)
            if is_premium and player_chips > 0:
                return "call", min(current_bet, player_chips)
            if current_bet <= player_chips and random.random() < call_probability:
                return "call", current_bet
            if strong_price_call:
                return "call", current_bet
            return "fold", 0

        three_bet_threshold = max(0.50, pfr_threshold + 0.10 - profile.three_bet_frequency)
        if raw_strength >= three_bet_threshold or is_premium:
            three_bet_probability = min(0.95, max(profile.three_bet_frequency, profile.aggression_bias * 0.45))
            if random.random() < three_bet_probability:
                raise_size = int(current_bet * (2.4 + profile.sizing_bias))
                if raise_size <= player_chips:
                    return "raise", self._legal_preflop_raise_amount(max(min_raise, raise_size), player_chips)
            if is_premium and player_chips > 0:
                return "call", min(current_bet, player_chips)

        call_threshold = max(0.18, vpip_threshold - profile.call_bias * 0.18)
        if clearly_negative_raise_price:
            return "fold", 0
        if strong_price_call:
            return "call", current_bet
        if raw_strength >= call_threshold and current_bet <= player_chips and not equity_far_below_price:
            if random.random() < call_probability:
                return "call", current_bet
        return "fold", 0

    def _profile_position_bonus(self, position_name: str) -> float:
        if position_name == Position.BTN:
            return 0.08
        if position_name == Position.CO:
            return 0.05
        if position_name == Position.SB:
            return -0.03
        if position_name == Position.BB:
            return 0.02
        if position_name == Position.UTG:
            return -0.05
        return 0.0

    def _profile_open_raise_multiplier(self, profile: AIArchetypeProfile) -> float:
        return 2.2 + profile.sizing_bias * 0.8

    def _legal_preflop_raise_amount(self, amount: int, player_chips: int) -> int:
        return min(max(int(amount), 0), player_chips)
    
    def _postflop_decision_v2(self, hole_cards: List[Card], community_cards: List[Card],
                             equity: float, hand_strength: Dict,
                             current_bet: int, min_raise: int, pot_size: int,
                             player_chips: int, has_position: bool, has_draw: bool,
                             board_texture: Dict, opponents_in_hand: List[str],
                             phase: str, table_current_bet: int = None,
                             player_current_bet: int = 0,
                             action_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, int]:
        """
        新版翻牌后决策 - 使用底池赔率和混合策略
        """
        raw_strength = hand_strength.get("raw_strength", 0.5)
        category = hand_strength.get("category", "")
        
        # 无需跟注 (check/bet场景)
        if current_bet == 0:
            return self._handle_no_bet_scenario(
                equity, raw_strength, has_position, has_draw, 
                pot_size, player_chips, min_raise, board_texture, opponents_in_hand,
                phase, action_history or []
            )
        
        # 需要跟注 (call/raise/fold场景)
        if table_current_bet is None:
            table_current_bet = current_bet
        return self._handle_facing_bet_scenario(
            equity, raw_strength, has_position, has_draw,
            current_bet, pot_size, player_chips, min_raise, 
            board_texture, opponents_in_hand, phase, table_current_bet, player_current_bet,
            action_history or []
        )
    
    def _handle_no_bet_scenario(self, equity: float, raw_strength: float,
                                has_position: bool, has_draw: bool,
                                pot_size: int, player_chips: int, min_raise: int,
                                board_texture: Dict, opponents_in_hand: List[str],
                                phase: str = "",
                                action_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, int]:
        """
        处理无需跟注的场景 (check/bet)
        使用Monte Carlo胜率(equity)作为主要决策依据
        """
        
        if self._is_flop_cbet_opportunity(phase, action_history or []):
            profile = self.archetype_profile or get_archetype_profile()
            cbet_probability = self._cbet_probability(profile, board_texture, has_position, has_draw)
            if random.random() < cbet_probability:
                action_line = ActionLine.SEMI_BLUFF if has_draw else ActionLine.BLUFF
                bet_size = BetSizingEngine.calculate_bet_size(
                    pot_size, player_chips, action_line, board_texture
                )
                return "raise", self._legal_no_bet_raise_amount(bet_size, min_raise, player_chips)

        # 使用equity作为主要决策依据 (Monte Carlo胜率更准确)
        # 超强牌: 胜率>75%
        if equity >= 0.75:
            # Value bet strong made hands. Earlier random slow-play checks created
            # repeated missed-value grades in the benchmark gate because checking
            # with very high equity leaves too much EV unrealized.
            bet_size = BetSizingEngine.calculate_bet_size(
                pot_size, player_chips, ActionLine.VALUE_BET, board_texture
            )
            return "raise", self._legal_no_bet_raise_amount(bet_size, min_raise, player_chips)
        
        # Prefer a cheap showdown with medium equity for the passive station.
        # Strong (75%+) value bets and its explicit flop c-bets remain above.
        if (
            equity >= 0.45
            and self.archetype_profile is not None
            and self.archetype_profile.name == "calling_station"
        ):
            return "check", 0

        # 强牌: 胜率60-75%
        if equity >= 0.60:
            bet_size = BetSizingEngine.calculate_bet_size(
                pot_size, player_chips, ActionLine.VALUE_BET, board_texture
            )
            return "raise", self._legal_no_bet_raise_amount(bet_size, min_raise, player_chips)
        
        # 中等牌: 胜率45-60%
        if equity >= 0.45:
            # 混合策略
            marginal_action = MixedStrategyDecider.get_marginal_action()
            if marginal_action == "thin_value":
                bet_size = BetSizingEngine.calculate_bet_size(
                    pot_size, player_chips, ActionLine.THIN_VALUE, board_texture
                )
                return "raise", self._legal_no_bet_raise_amount(bet_size, min_raise, player_chips)
            return "check", 0
        
        # 有听牌: 半诈唬
        if has_draw:
            if random.random() < MixedStrategyFreqs.SEMI_BLUFF_FREQ:
                bet_size = BetSizingEngine.calculate_bet_size(
                    pot_size, player_chips, ActionLine.SEMI_BLUFF, board_texture
                )
                return "raise", self._legal_no_bet_raise_amount(bet_size, min_raise, player_chips)
            return "check", 0
        
        # 弱牌: 考虑诈唬 (有位置时)
        if has_position and MixedStrategyDecider.should_bluff(has_position, has_draw):
            bet_size = BetSizingEngine.calculate_bet_size(
                pot_size, player_chips, ActionLine.BLUFF, board_texture
            )
            return "raise", self._legal_no_bet_raise_amount(bet_size, min_raise, player_chips)
        
        return "check", 0

    def _legal_no_bet_raise_amount(self, bet_size: int, min_raise: int, player_chips: int) -> int:
        return min(max(bet_size, min_raise), player_chips)

    def _legal_facing_bet_raise_amount(
        self,
        bet_size: int,
        table_current_bet: int,
        min_raise: int,
        player_chips: int,
        player_current_bet: int = 0,
    ) -> Optional[int]:
        max_total_bet = player_chips + max(player_current_bet, 0)
        total_raise = table_current_bet + bet_size
        total_raise = min(max(total_raise, min_raise), max_total_bet)
        if total_raise >= min_raise or total_raise == max_total_bet:
            return total_raise
        return None

    def _last_preflop_aggressor(self, action_history: List[Dict[str, Any]]) -> Optional[str]:
        aggressor = None
        for action in action_history:
            if action.get("phase") == "preflop" and action.get("action") in {"raise", "bet"}:
                aggressor = action.get("player_name")
        return aggressor

    def _is_flop_cbet_opportunity(self, phase: str, action_history: List[Dict[str, Any]]) -> bool:
        if phase != "flop":
            return False
        if any(action.get("phase") == "flop" for action in action_history):
            return False
        return self._last_preflop_aggressor(action_history) == self.player_name

    def _is_facing_flop_cbet(self, phase: str, action_history: List[Dict[str, Any]]) -> bool:
        if phase != "flop":
            return False
        preflop_aggressor = self._last_preflop_aggressor(action_history)
        if not preflop_aggressor or preflop_aggressor == self.player_name:
            return False
        flop_aggressors = [
            action.get("player_name")
            for action in action_history
            if action.get("phase") == "flop" and action.get("action") in {"raise", "bet"}
        ]
        return bool(flop_aggressors) and flop_aggressors[0] == preflop_aggressor

    def _cbet_probability(
        self,
        profile: AIArchetypeProfile,
        board_texture: Dict,
        has_position: bool,
        has_draw: bool,
    ) -> float:
        probability = profile.cbet_frequency
        danger_level = board_texture.get("danger_level", 0)
        if danger_level <= 2:
            probability += 0.10
        elif danger_level >= 6:
            probability -= 0.12
        if has_position:
            probability += 0.04
        if has_draw:
            probability += profile.bluff_frequency * 0.5
        return max(0.05, min(0.88, probability))

    def _fold_to_cbet_probability(self, profile: AIArchetypeProfile, board_texture: Dict) -> float:
        probability = profile.fold_to_cbet_bias
        if board_texture.get("danger_level", 0) <= 2:
            probability += 0.08
        elif board_texture.get("danger_level", 0) >= 6:
            probability -= 0.08
        probability -= profile.showdown_stickiness * 0.12
        return max(0.05, min(0.85, probability))
    
    def _handle_facing_bet_scenario(self, equity: float, raw_strength: float,
                                    has_position: bool, has_draw: bool,
                                    current_bet: int, pot_size: int, player_chips: int,
                                    min_raise: int, board_texture: Dict,
                                    opponents_in_hand: List[str], phase: str,
                                    table_current_bet: int = None,
                                    player_current_bet: int = 0,
                                    action_history: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, int]:
        """
        处理面对下注的场景 (call/raise/fold)
        使用Monte Carlo胜率和底池赔率做决策
        """
        
        # 计算底池赔率
        pot_odds = current_bet / (pot_size + current_bet) if (pot_size + current_bet) > 0 else 0.5
        
        # 计算是否值得跟注 (胜率需要超过底池赔率)
        implied_multiplier = 1.3 if has_draw else 1.0  # 听牌有隐含赔率
        required_equity = pot_odds / implied_multiplier
        should_call = equity >= max(required_equity, 0.25)  # 最低25%胜率
        equity_far_below_price = equity <= pot_odds - 0.25
        if table_current_bet is None:
            table_current_bet = current_bet
        is_facing_cbet = self._is_facing_flop_cbet(phase, action_history or [])
        profile_is_calling_station = (
            self.archetype_profile is not None
            and self.archetype_profile.name == "calling_station"
        )
        
        # === 超强牌 (胜率>75%): 考虑加注 ===
        if equity >= 0.75:
            if not profile_is_calling_station and MixedStrategyDecider.should_reraise_strong(equity):
                bet_size = BetSizingEngine.calculate_bet_size(
                    pot_size, player_chips, ActionLine.VALUE_BET, board_texture
                )
                raise_size = self._legal_facing_bet_raise_amount(
                    bet_size, table_current_bet, min_raise, player_chips, player_current_bet
                )
                if raise_size is not None:
                    return "raise", raise_size
            # 平跟 (陷阱)
            if current_bet <= player_chips:
                return "call", current_bet
            return "fold", 0
        
        # === 强牌 (胜率60-75%): 混合加注/跟注 ===
        if equity >= 0.60:
            if not profile_is_calling_station and random.random() < 0.30:  # 30%时候加注
                bet_size = BetSizingEngine.calculate_bet_size(
                    pot_size, player_chips, ActionLine.THIN_VALUE, board_texture
                )
                raise_size = self._legal_facing_bet_raise_amount(
                    bet_size, table_current_bet, min_raise, player_chips, player_current_bet
                )
                if raise_size is not None:
                    return "raise", raise_size
            if current_bet <= player_chips:
                return "call", current_bet
            return "fold", 0
        
        # === 中等牌 (胜率45-60%): 基于底池赔率 ===
        if equity >= 0.45:
            if should_call and current_bet <= player_chips:
                return "call", current_bet
            return "fold", 0

        # === 听牌 (胜率<45%但有draw): 基于隐含赔率 ===
        if has_draw:
            # 计算需要的隐含赔率
            if should_call and current_bet <= player_chips:
                return "call", current_bet
            # 有时候转诈唬加注 (半诈唬)
            if has_position and random.random() < 0.15:
                bet_size = BetSizingEngine.calculate_bet_size(
                    pot_size, player_chips, ActionLine.SEMI_BLUFF, board_texture
                )
                raise_size = self._legal_facing_bet_raise_amount(
                    bet_size, table_current_bet, min_raise, player_chips, player_current_bet
                )
                if raise_size is not None:
                    return "raise", raise_size
            return "fold", 0
        
        # === 弱牌 (胜率<45%无draw): 考虑诈唬或弃牌 ===
        if is_facing_cbet and self.archetype_profile is not None:
            fold_probability = self._fold_to_cbet_probability(self.archetype_profile, board_texture)
            if not equity_far_below_price and random.random() >= fold_probability and current_bet <= player_chips:
                return "call", current_bet

        # 偶尔诈唬加注 (有位置时)
        if has_position and equity < 0.25 and random.random() < 0.08:
            bet_size = BetSizingEngine.calculate_bet_size(
                pot_size, player_chips, ActionLine.BLUFF, board_texture
            )
            raise_size = self._legal_facing_bet_raise_amount(
                bet_size, table_current_bet, min_raise, player_chips, player_current_bet
            )
            if raise_size is not None:
                return "raise", raise_size
        
        # 默认弃牌
        return "fold", 0
    
    def _preflop_decision(self, hand_strength: Dict, position_advantage: float,
                         current_bet: int, min_raise: int, pot_size: int,
                         player_chips: int) -> Tuple[Optional[str], int]:
        """
        翻牌前专用决策逻辑
        返回 (action, amount) 或 (None, 0) 表示使用通用逻辑
        """
        raw_strength = hand_strength.get("raw_strength", 0.0)
        category = hand_strength.get("category", "marginal")
        
        # === 无人加注时 (只有盲注) ===
        if current_bet <= 10:  # 只有盲注级别的下注
            # 根据手牌强度和位置决定是否开池
            open_threshold = self.preflop_params["open_raise_threshold"]
            
            # 位置调整：后位可以开更宽的范围
            adjusted_threshold = open_threshold - position_advantage * 0.15
            
            if raw_strength >= adjusted_threshold:
                # 开池加注 2.5-3倍大盲
                raise_amount = min_raise + int(pot_size * random.uniform(0.5, 1.0))
                return "raise", min(raise_amount, player_chips)
            elif raw_strength >= self.preflop_params["call_threshold"]:
                # 跟注
                if current_bet <= player_chips:
                    return "call", current_bet
            else:
                # 弱牌弃牌
                return "fold", 0
        
        # === 面对加注 ===
        else:
            # 判断是否是3bet场景 (已有人加注)
            if current_bet > 20:  # 超过2倍大盲，可能是加注
                # 3bet门槛更高
                three_bet_threshold = self.preflop_params["three_bet_threshold"]
                
                # 只有premium牌才3bet
                if raw_strength >= three_bet_threshold or category == "premium_pair":
                    raise_amount = current_bet * 3
                    if raise_amount <= player_chips:
                        return "raise", raise_amount
                    return "call", current_bet  # 筹码不够就跟注
                
                # 冷跟门槛
                cold_call_threshold = self.preflop_params["cold_call_threshold"]
                if raw_strength >= cold_call_threshold:
                    if current_bet <= player_chips:
                        return "call", current_bet
                
                # 其他情况弃牌
                return "fold", 0
            else:
                # 普通跟注
                if raw_strength >= self.preflop_params["call_threshold"]:
                    return "call", current_bet
                return "fold", 0
        
        # 返回None表示使用通用决策逻辑
        return None, 0
    
    def _evaluate_hand_strength(self, hole_cards: List[Card], 
                               community_cards: List[Card],
                               board_texture: Dict) -> Dict:
        """
        评估手牌强度
        返回详细的手牌分析
        """
        result = {
            "raw_strength": 0.0,      # 绝对强度
            "relative_strength": 0.0,  # 相对强度（考虑范围）
            "nut_potential": 0.0,      # 坚果潜力
            "showdown_value": False,   # 是否有摊牌价值
            "draw_strength": 0.0,      # 听牌强度
            "blocker_value": 0.0,      # 阻挡牌价值
            "category": "unknown"
        }
        
        if not hole_cards or len(hole_cards) != 2:
            return result
        
        card1, card2 = hole_cards
        rank1, rank2 = card1.rank.numeric_value, card2.rank.numeric_value
        high_rank = max(rank1, rank2)
        low_rank = min(rank1, rank2)
        suited = card1.suit == card2.suit
        paired = rank1 == rank2
        
        # 翻牌前强度
        if not community_cards:
            result["raw_strength"] = self._get_preflop_strength(high_rank, low_rank, suited, paired)
            result["relative_strength"] = result["raw_strength"]
            result["category"] = self._categorize_preflop_hand(high_rank, low_rank, suited, paired)
            return result
        
        # 翻牌后评估
        all_cards = hole_cards + community_cards
        
        # 评估成牌强度
        if len(all_cards) >= 5:
            try:
                hand_rank, kickers = self._evaluate_best_available_hand(all_cards)
                result["raw_strength"] = self._convert_hand_rank(hand_rank)
                result["category"] = hand_rank.display
                
                # 判断是否有摊牌价值
                result["showdown_value"] = result["raw_strength"] >= 0.35
                
                # 评估相对强度（考虑牌面）
                result["relative_strength"] = self._adjust_for_board(
                    result["raw_strength"], board_texture, hand_rank
                )
                
            except:
                result["raw_strength"] = 0.3
                result["relative_strength"] = 0.3
        
        # 评估听牌强度
        result["draw_strength"] = self._evaluate_draws(hole_cards, community_cards)
        
        # 评估阻挡牌价值
        result["blocker_value"] = self._evaluate_blockers(hole_cards, community_cards, board_texture)
        
        # 坚果潜力
        result["nut_potential"] = self._evaluate_nut_potential(hole_cards, community_cards)
        
        return result

    def _evaluate_best_available_hand(self, cards: List[Card]):
        """Evaluate the current best made hand for flop, turn, or river cards."""
        if len(cards) == 7:
            return HandEvaluator.evaluate_hand(cards)
        if len(cards) == 5:
            return HandEvaluator._evaluate_five_cards(cards)
        if len(cards) == 6:
            best_rank = None
            best_kickers = None
            for combo in combinations(cards, 5):
                hand_rank, kickers = HandEvaluator._evaluate_five_cards(list(combo))
                if best_rank is None or HandEvaluator._is_better_hand(
                    hand_rank,
                    kickers,
                    best_rank,
                    best_kickers,
                ):
                    best_rank = hand_rank
                    best_kickers = kickers
            return best_rank, best_kickers
        raise ValueError("at least five cards are required")
    
    def _get_preflop_strength(self, high: int, low: int, suited: bool, paired: bool) -> float:
        """翻牌前手牌强度"""
        if paired:
            # 对子
            pair_strength = {
                14: 0.95, 13: 0.90, 12: 0.85, 11: 0.80, 10: 0.75,
                9: 0.70, 8: 0.65, 7: 0.60, 6: 0.55, 5: 0.52,
                4: 0.50, 3: 0.48, 2: 0.46
            }
            return pair_strength.get(high, 0.50)
        
        # 非对子
        suited_bonus = 0.04 if suited else 0
        
        # AK
        if high == 14 and low == 13:
            return 0.82 + suited_bonus
        # AQ
        elif high == 14 and low == 12:
            return 0.75 + suited_bonus
        # AJ, KQ
        elif (high == 14 and low == 11) or (high == 13 and low == 12):
            return 0.70 + suited_bonus
        # AT, KJ, QJ
        elif high >= 12 and low >= 10:
            return 0.60 + suited_bonus
        # 同花A
        elif high == 14 and suited:
            return 0.55 + (low - 2) * 0.01
        # 同花连牌 (有价值)
        elif suited and abs(high - low) == 1 and low >= 5:
            return 0.45 + (low - 5) * 0.02  # 同花连牌 0.45-0.53
        # 非同花连牌 (价值较低)
        elif abs(high - low) == 1 and low >= 5:
            return 0.30 + (low - 5) * 0.02  # 非同花连牌只有 0.30-0.38，不值得主动开池
        # 其他同花牌
        elif suited and abs(high - low) <= 2:
            return 0.35 + (low - 2) * 0.01
        else:
            # 其他随机牌 - 给低值
            return max(0.15, (high + low) / 28 * 0.3 + suited_bonus)
    
    def _categorize_preflop_hand(self, high: int, low: int, suited: bool, paired: bool) -> str:
        """分类翻牌前手牌"""
        if paired:
            if high >= 11:
                return "premium_pair"
            elif high >= 7:
                return "medium_pair"
            else:
                return "small_pair"
        
        if high == 14:
            if low >= 11:
                return "premium_broadways"
            else:
                return "Ax"
        
        if high >= 10 and low >= 10:
            return "broadways"
        
        if suited and abs(high - low) <= 2:
            return "suited_connectors"
        
        return "marginal"
    
    def _convert_hand_rank(self, hand_rank) -> float:
        """将牌型等级转换为强度值"""
        rank_map = {
            10: 1.00,  # 皇家同花顺
            9: 0.98,   # 同花顺
            8: 0.95,   # 四条
            7: 0.88,   # 葫芦
            6: 0.78,   # 同花
            5: 0.70,   # 顺子
            4: 0.58,   # 三条
            3: 0.45,   # 两对
            2: 0.32,   # 一对
            1: 0.20,   # 高牌
        }
        return rank_map.get(hand_rank.rank_value, 0.20)
    
    def _adjust_for_board(self, raw_strength: float, board_texture: Dict, hand_rank) -> float:
        """根据牌面调整强度"""
        adjusted = raw_strength
        
        # 湿润牌面降低非坚果牌的强度
        if board_texture.get("danger_level", 0) >= 6:
            if raw_strength < 0.75:
                adjusted *= 0.85
        
        # 配对牌面上的普通对子价值降低
        if board_texture.get("paired", False):
            if hand_rank.rank_value == 2:  # 一对
                adjusted *= 0.80
        
        return adjusted
    
    def _evaluate_draws(self, hole_cards: List[Card], community_cards: List[Card]) -> float:
        """评估听牌强度"""
        if len(community_cards) >= 5:  # 河牌没有听牌
            return 0.0
        
        all_cards = hole_cards + community_cards
        draw_strength = 0.0
        
        # 检查同花听牌
        suits = [c.suit for c in all_cards]
        suit_counts = defaultdict(int)
        for s in suits:
            suit_counts[s] += 1
        
        # 检查哪张花色有4张
        for suit, count in suit_counts.items():
            if count == 4:
                # 检查是否用到了手牌
                hole_suits = [c.suit for c in hole_cards]
                if suit in hole_suits:
                    draw_strength += 0.35  # 同花听牌 (9 outs)
                    # 如果是高牌同花听牌
                    hole_ranks = [c.rank.numeric_value for c in hole_cards if c.suit == suit]
                    if any(r >= 11 for r in hole_ranks):
                        draw_strength += 0.10  # 额外价值
        
        # 检查顺子听牌 (简化)
        ranks = sorted([c.rank.numeric_value for c in all_cards])
        unique_ranks = list(set(ranks))
        
        # 检查两头顺子听牌 (8 outs)
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] == 3:
                draw_strength += 0.30
                break
        
        # 检查卡顺听牌 (4 outs)
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] == 4:
                gaps = [unique_ranks[j+1] - unique_ranks[j] for j in range(i, i+3)]
                if gaps.count(2) == 1 and gaps.count(1) == 2:
                    draw_strength += 0.15
                    break
        
        return min(0.60, draw_strength)  # 上限60%
    
    def _evaluate_blockers(self, hole_cards: List[Card], community_cards: List[Card],
                          board_texture: Dict) -> float:
        """评估阻挡牌价值"""
        blocker_value = 0.0
        
        if not community_cards:
            return 0.0
        
        hole_ranks = [c.rank.numeric_value for c in hole_cards]
        hole_suits = [c.suit for c in hole_cards]
        board_ranks = [c.rank.numeric_value for c in community_cards]
        
        # 阻挡坚果同花
        if board_texture.get("flush_draw_possible") or board_texture.get("flush_possible"):
            # 检查我们是否持有该花色的A
            for i, card in enumerate(hole_cards):
                if card.rank.numeric_value == 14:  # A
                    board_suit_cards = [c for c in community_cards if c.suit == card.suit]
                    if len(board_suit_cards) >= 2:
                        blocker_value += 0.15  # 阻挡坚果同花
        
        # 阻挡顺子
        if board_texture.get("straight_possible"):
            # 持有关键牌阻挡顺子
            key_cards = set()
            sorted_board = sorted(board_ranks)
            if len(sorted_board) >= 3:
                for r in range(sorted_board[0] - 2, sorted_board[-1] + 3):
                    if 2 <= r <= 14:
                        key_cards.add(r)
            
            for rank in hole_ranks:
                if rank in key_cards:
                    blocker_value += 0.05
        
        return min(0.25, blocker_value)
    
    def _evaluate_nut_potential(self, hole_cards: List[Card], community_cards: List[Card]) -> float:
        """评估成为坚果牌的潜力"""
        if len(community_cards) >= 5:
            return 0.0
        
        potential = 0.0
        
        # 持有大对子
        if hole_cards[0].rank == hole_cards[1].rank:
            rank = hole_cards[0].rank.numeric_value
            if rank >= 10:
                potential += 0.20  # 可能中set成坚果
        
        # 持有同花大牌
        if hole_cards[0].suit == hole_cards[1].suit:
            high_rank = max(c.rank.numeric_value for c in hole_cards)
            if high_rank >= 12:
                potential += 0.15  # 可能成坚果同花
        
        # 持有AK这样的顶对潜力
        ranks = [c.rank.numeric_value for c in hole_cards]
        if 14 in ranks or 13 in ranks:
            potential += 0.10
        
        return min(0.40, potential)
    
    def _evaluate_position(self, position: int, total_players: int) -> float:
        """
        评估位置优势
        返回 -1 到 1 的值，正值表示有位置优势
        """
        if total_players <= 2:
            return 0.0 if position == 0 else 0.3
        
        # 相对位置 (0 = 最早, 1 = 最晚)
        relative_pos = position / (total_players - 1)
        
        if relative_pos >= 0.8:  # BTN 或接近
            return 0.5
        elif relative_pos >= 0.6:  # CO
            return 0.3
        elif relative_pos >= 0.4:  # MP
            return 0.0
        else:  # 早位
            return -0.3
    
    def _analyze_opponent_ranges(self, opponents: List[str], phase: str) -> Dict[str, str]:
        """分析对手的手牌范围"""
        ranges = {}
        
        for opponent in opponents:
            profile = self.opponent_profiles.get(opponent)
            if profile:
                # 根据对手历史行为估计范围
                if profile.recent_actions:
                    last_action, _ = profile.recent_actions[-1]
                    ranges[opponent] = profile.get_estimated_range(
                        last_action, phase, "unknown"
                    )
                else:
                    ranges[opponent] = "medium"
            else:
                # 没有历史数据，假设中等范围
                ranges[opponent] = "medium"
        
        return ranges
    
    def _calculate_equity_vs_ranges(self, hole_cards: List[Card], 
                                   community_cards: List[Card],
                                   opponent_ranges: Dict[str, str]) -> float:
        """计算对抗所有对手范围的综合胜率"""
        if not opponent_ranges:
            return 0.5
        
        total_equity = 0.0
        for opponent, range_type in opponent_ranges.items():
            equity = BoardAnalyzer.get_equity_vs_range(
                hole_cards, community_cards, range_type
            )
            total_equity += equity
        
        # 多个对手时胜率降低
        num_opponents = len(opponent_ranges)
        avg_equity = total_equity / num_opponents
        
        # 对手数量惩罚
        multiplier = 1.0 - (num_opponents - 1) * 0.15
        multiplier = max(0.5, multiplier)
        
        return avg_equity * multiplier
    
    def _select_action_line(self, hand_strength: Dict, equity: float,
                           position_advantage: float, current_bet: int,
                           pot_size: int, player_chips: int, 
                           phase: str, board_texture: Dict) -> ActionLine:
        """
        选择行动线路
        这是决策的核心 - 决定我们要走哪条路线
        """
        relative_strength = hand_strength.get("relative_strength", 0.5)
        draw_strength = hand_strength.get("draw_strength", 0.0)
        blocker_value = hand_strength.get("blocker_value", 0.0)
        showdown_value = hand_strength.get("showdown_value", False)
        
        # 组合强度 = 成牌强度 + 听牌强度
        combined_strength = relative_strength + draw_strength * 0.5
        
        # SPR (Stack to Pot Ratio) 筹码彩池比
        spr = player_chips / max(pot_size, 1)
        
        # === 强牌策略 ===
        if combined_strength >= 0.75:
            # 坚果级别手牌
            if random.random() < self.gto_params["slow_play_freq"] and current_bet == 0:
                return ActionLine.CHECK_CALL  # 偶尔慢打
            return ActionLine.VALUE_BET
        
        # === 中强牌策略 ===
        elif combined_strength >= 0.50:
            if current_bet == 0:
                # 无人下注时
                if position_advantage > 0:
                    return ActionLine.VALUE_BET  # 有位置打价值
                else:
                    # 无位置时混合策略
                    if random.random() < 0.6:
                        return ActionLine.THIN_VALUE
                    return ActionLine.CHECK_CALL
            else:
                # 面对下注
                if equity >= 0.45:
                    return ActionLine.CHECK_CALL  # 跟注
                else:
                    return ActionLine.CHECK_FOLD
        
        # === 听牌策略 ===
        elif draw_strength >= 0.25:
            if current_bet == 0:
                # 半诈唬下注
                return ActionLine.SEMI_BLUFF
            else:
                # 计算底池赔率
                odds_needed = current_bet / (pot_size + current_bet)
                if draw_strength >= odds_needed:
                    return ActionLine.CHECK_CALL  # 赔率足够跟注
                elif draw_strength + blocker_value >= odds_needed * 0.8:
                    # 考虑阻挡牌价值，可能半诈唬加注
                    if random.random() < 0.3:
                        return ActionLine.SEMI_BLUFF
                    return ActionLine.CHECK_CALL
                return ActionLine.CHECK_FOLD
        
        # === 弱牌策略 ===
        else:
            if current_bet == 0:
                # 考虑诈唬 - 限制最大诈唬频率
                bluff_frequency = self.bluff_frequency * (1 + position_advantage * 0.5)  # 减少位置加成
                bluff_frequency *= (1 + blocker_value * 0.5)  # 减少阻挡牌加成
                bluff_frequency = min(0.15, bluff_frequency)  # 限制最大诈唬率15%
                
                if random.random() < bluff_frequency:
                    return ActionLine.BLUFF
                return ActionLine.CHECK_FOLD
            else:
                # 面对下注的弱牌 - 大多数情况应该弃牌
                # 只有在极好的位置和很小的下注时才考虑浮动
                pot_odds = current_bet / (pot_size + current_bet + 0.01)
                if position_advantage > 0.4 and pot_odds < 0.25 and random.random() < 0.05:
                    return ActionLine.CHECK_CALL  # 浮动跟注 (降低频率从10%到5%)
                return ActionLine.CHECK_FOLD
    
    def _execute_action_line(self, action_line: ActionLine, current_bet: int,
                            min_raise: int, pot_size: int, player_chips: int,
                            board_texture: Dict, 
                            opponents: List[str]) -> Tuple[str, int]:
        """执行选定的行动线路"""
        
        # 获取对手档案
        opponent_profile = None
        if opponents:
            opponent_profile = self.opponent_profiles.get(opponents[0])
        
        if action_line == ActionLine.CHECK_FOLD:
            if current_bet == 0:
                return "check", 0
            return "fold", 0
        
        elif action_line == ActionLine.CHECK_CALL:
            if current_bet == 0:
                return "check", 0
            if current_bet <= player_chips:
                return "call", current_bet
            return "fold", 0
        
        elif action_line in [ActionLine.VALUE_BET, ActionLine.THIN_VALUE, 
                            ActionLine.BLUFF, ActionLine.SEMI_BLUFF]:
            # 计算下注尺度
            bet_size = BetSizingEngine.calculate_bet_size(
                pot_size, player_chips, action_line, board_texture, opponent_profile
            )
            
            if current_bet == 0:
                # 开池下注
                return "raise", bet_size
            else:
                # 加注
                total_raise = current_bet + bet_size
                if total_raise >= min_raise and total_raise <= player_chips:
                    return "raise", total_raise
                elif current_bet <= player_chips:
                    return "call", current_bet
                return "fold", 0
        
        elif action_line == ActionLine.CHECK_RAISE:
            # 过牌加注（需要特殊处理）
            if current_bet == 0:
                return "check", 0
            else:
                # 对方下注后我们加注
                raise_size = BetSizingEngine.calculate_bet_size(
                    pot_size + current_bet, player_chips, action_line, 
                    board_texture, opponent_profile
                )
                total_raise = current_bet + raise_size
                if total_raise <= player_chips:
                    return "raise", total_raise
                return "call", current_bet
        
        return "check", 0
    
    def _apply_exploitative_adjustments(self, action: str, amount: int,
                                       opponents: List[str], hand_strength: Dict,
                                       current_bet: int) -> Tuple[str, int]:
        """
        应用剥削性调整
        针对对手的漏洞调整策略
        """
        if not opponents:
            return action, amount
        
        # 获取第一个对手的档案
        profile = self.opponent_profiles.get(opponents[0])
        if not profile:
            return action, amount
        
        # === 对手弃牌过多 ===
        if profile.folds_too_much:
            # 适度增加诈唬频率 (但不要太激进)
            if action == "check" and hand_strength.get("relative_strength", 0) < 0.3:
                if random.random() < 0.12:  # 从30%降到12%
                    return "raise", max(amount, current_bet + 50)
        
        # === 对手跟注过多 ===
        if profile.calls_too_much:
            # 减少诈唬，增加薄价值下注
            if action == "raise" and hand_strength.get("relative_strength", 0) < 0.3:
                # 有阻挡牌价值才诈唬
                if hand_strength.get("blocker_value", 0) < 0.1:
                    return "check", 0
            # 薄价值下注更大
            elif action == "raise" and hand_strength.get("showdown_value", False):
                amount = int(amount * 1.2)
        
        # === 对手诈唬过多 ===
        if profile.bluffs_too_much:
            # 更多跟注抓诈唬
            if action == "fold" and hand_strength.get("showdown_value", False):
                if random.random() < 0.4:  # 40%概率改为跟注
                    return "call", current_bet
        
        return action, amount
    
    def update_opponent(self, opponent_name: str, action: str, amount: int, phase: str,
                       position: str = None, is_new_hand: bool = False):
        """
        更新对手档案
        增强版：支持位置统计和新手牌标记
        """
        if opponent_name not in self.opponent_profiles:
            self.opponent_profiles[opponent_name] = OpponentProfile(name=opponent_name)
        
        self.opponent_profiles[opponent_name].update_from_action(
            action, amount, phase, position, is_new_hand
        )
        
        # 记录进攻者
        if action == "raise":
            self.last_aggressor = opponent_name
            if phase == "preflop":
                self.preflop_aggressor = opponent_name
    
    def get_opponent_leaks(self, opponent_name: str) -> List[str]:
        """获取对手的漏洞列表"""
        profile = self.opponent_profiles.get(opponent_name)
        if profile:
            return profile.get_leak_summary()
        return []
    
    def get_opponent_stats(self, opponent_name: str) -> Dict:
        """获取对手的统计数据"""
        profile = self.opponent_profiles.get(opponent_name)
        if profile:
            return {
                "vpip": round(profile.vpip, 1),
                "pfr": round(profile.pfr, 1),
                "3bet": round(profile.three_bet, 1),
                "fold_to_3bet": round(profile.fold_to_three_bet, 1),
                "cbet": round(profile.cbet_flop, 1),
                "fold_to_cbet": round(profile.fold_to_cbet, 1),
                "af": round(profile.aggression_factor, 2),
                "hands": profile.hands_played,
                "leaks": profile.get_leak_summary()
            }
        return {}
    
    def reset_for_new_hand(self):
        """新手牌重置"""
        self.current_hand_history.clear()
        self.preflop_aggressor = None
        self.last_aggressor = None


class AdvancedAIEngineManager:
    """高级AI引擎管理器"""
    
    def __init__(self):
        self.engines: Dict[str, AdvancedAIEngine] = {}
        self.default_skill = "advanced"
    
    def get_engine(self, player_name: str, archetype_name: Optional[str] = None) -> AdvancedAIEngine:
        """获取或创建AI引擎"""
        if player_name not in self.engines:
            self.engines[player_name] = AdvancedAIEngine(
                player_name, self.default_skill, archetype_name=archetype_name,
            )
        elif archetype_name is not None and (
            self.engines[player_name].archetype_profile is None
            or self.engines[player_name].archetype_profile.name != archetype_name
        ):
            # A new local session can reuse a display name with a different persona.
            self.engines[player_name] = AdvancedAIEngine(
                player_name, self.default_skill, archetype_name=archetype_name,
            )
        return self.engines[player_name]
    
    def reset_for_new_game(self):
        """新游戏重置"""
        for engine in self.engines.values():
            engine.reset_for_new_hand()
    
    def update_all_opponents(self, player_name: str, action: str, amount: int, phase: str):
        """通知所有AI更新对手模型"""
        for engine_name, engine in self.engines.items():
            if engine_name != player_name:
                engine.update_opponent(player_name, action, amount, phase)


# 全局实例
advanced_ai_manager = AdvancedAIEngineManager()


# === 测试代码 ===
if __name__ == "__main__":
    from texas_holdem.engine.card import Card, Suit, Rank
    
    # 创建测试引擎
    engine = AdvancedAIEngine("TestAI", "advanced")
    
    # 测试场景1: 翻牌前 AA
    hole_cards = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)]
    action, amount = engine.make_decision(
        hole_cards=hole_cards,
        community_cards=[],
        current_bet=10,
        min_raise=20,
        pot_size=15,
        player_chips=1000,
        position=3,
        total_players=6,
        opponents_in_hand=["Player2", "Player3"]
    )
    print(f"场景1 - AA 翻牌前: {action} {amount}")
    
    # 测试场景2: 翻牌后有同花听牌
    hole_cards = [Card(Suit.HEARTS, Rank.KING), Card(Suit.HEARTS, Rank.QUEEN)]
    community_cards = [
        Card(Suit.HEARTS, Rank.TEN),
        Card(Suit.HEARTS, Rank.FIVE),
        Card(Suit.SPADES, Rank.TWO)
    ]
    action, amount = engine.make_decision(
        hole_cards=hole_cards,
        community_cards=community_cards,
        current_bet=50,
        min_raise=100,
        pot_size=150,
        player_chips=900,
        position=4,
        total_players=6,
        opponents_in_hand=["Player2"]
    )
    print(f"场景2 - KQs 同花听牌: {action} {amount}")
    
    # 测试场景3: 干燥牌面的空气牌
    hole_cards = [Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.DIAMONDS, Rank.SIX)]
    community_cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.CLUBS, Rank.TWO)
    ]
    action, amount = engine.make_decision(
        hole_cards=hole_cards,
        community_cards=community_cards,
        current_bet=0,
        min_raise=20,
        pot_size=100,
        player_chips=800,
        position=5,  # BTN位置
        total_players=6,
        opponents_in_hand=["Player2"]
    )
    print(f"场景3 - 76o 干燥AK2 (BTN): {action} {amount}")
    
    print("\n高级AI引擎测试完成!")
