#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 实时辅助系统
在玩家回合时提供：胜率显示、底池赔率计算、建议动作、听牌分析
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from card import Card, Suit, Rank
from hand_evaluator import HandEvaluator


class SuggestedAction(Enum):
    """建议动作类型"""
    STRONG_RAISE = ("强烈加注", "🔥")
    RAISE = ("加注", "📈")
    CALL = ("跟注", "✅")
    CHECK = ("过牌", "⏸️")
    FOLD = ("弃牌", "❌")
    BORDERLINE_CALL = ("边缘跟注", "⚠️")


@dataclass
class OutsInfo:
    """听牌信息"""
    outs_count: int           # outs数量
    description: str          # 描述
    probability_turn: float   # 转牌中牌概率
    probability_river: float  # 河牌中牌概率
    probability_both: float   # 转牌+河牌中牌概率


@dataclass
class AnalysisResult:
    """分析结果"""
    # 手牌强度
    current_hand: str           # 当前成牌
    hand_strength: float        # 手牌强度 (0-1)
    
    # 胜率估算
    equity: float               # 估算胜率
    equity_description: str     # 胜率描述
    
    # 底池赔率
    pot_odds: float             # 底池赔率
    pot_odds_description: str   # 赔率描述
    required_equity: float      # 需要的胜率
    
    # 听牌分析
    outs: List[OutsInfo]        # 听牌信息列表
    total_outs: int             # 总outs数
    
    # 建议
    suggested_action: SuggestedAction
    reasoning: str              # 推理说明
    
    # 额外信息
    spr: float                  # 筹码彩池比
    position_advantage: bool    # 是否有位置优势


class RealtimeAssistant:
    """实时辅助分析器"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化实时辅助器
        
        Args:
            enabled: 是否启用辅助
        """
        self.enabled = enabled
        
        # 翻牌前手牌强度表 (简化版)
        self.preflop_rankings = self._build_preflop_rankings()
    
    def _build_preflop_rankings(self) -> Dict[str, float]:
        """构建翻牌前手牌强度排名"""
        rankings = {}
        
        # 对子
        pairs = {
            'AA': 0.95, 'KK': 0.90, 'QQ': 0.85, 'JJ': 0.80, 'TT': 0.75,
            '99': 0.70, '88': 0.65, '77': 0.60, '66': 0.55, '55': 0.52,
            '44': 0.50, '33': 0.48, '22': 0.46
        }
        rankings.update(pairs)
        
        # 大牌组合 (同花/非同花)
        broadways = {
            'AKs': 0.82, 'AKo': 0.78, 'AQs': 0.76, 'AQo': 0.72,
            'AJs': 0.72, 'AJo': 0.68, 'ATs': 0.68, 'ATo': 0.64,
            'KQs': 0.72, 'KQo': 0.68, 'KJs': 0.68, 'KJo': 0.64,
            'KTs': 0.64, 'KTo': 0.60, 'QJs': 0.66, 'QJo': 0.62,
            'QTs': 0.62, 'QTo': 0.58, 'JTs': 0.62, 'JTo': 0.58
        }
        rankings.update(broadways)
        
        # 同花连牌
        suited_connectors = {
            'T9s': 0.55, '98s': 0.52, '87s': 0.50, '76s': 0.48,
            '65s': 0.46, '54s': 0.44
        }
        rankings.update(suited_connectors)
        
        # 同花A
        suited_aces = {
            'A9s': 0.58, 'A8s': 0.56, 'A7s': 0.54, 'A6s': 0.52,
            'A5s': 0.54, 'A4s': 0.52, 'A3s': 0.50, 'A2s': 0.48
        }
        rankings.update(suited_aces)
        
        return rankings
    
    def analyze(self, hole_cards: List[Card], community_cards: List[Card],
                pot_size: int, bet_to_call: int, player_chips: int,
                position: int = 0, total_players: int = 6,
                num_opponents: int = 1) -> AnalysisResult:
        """
        分析当前局面
        
        Args:
            hole_cards: 手牌
            community_cards: 公共牌
            pot_size: 当前彩池
            bet_to_call: 需要跟注的金额
            player_chips: 玩家剩余筹码
            position: 玩家位置
            total_players: 总玩家数
            num_opponents: 剩余对手数
            
        Returns:
            分析结果
        """
        # 1. 评估当前手牌
        current_hand, hand_strength = self._evaluate_hand(hole_cards, community_cards)
        preflop_hand_key = self._get_preflop_hand_key(hole_cards) if not community_cards and len(hole_cards) == 2 else ""
        
        # 2. 估算胜率
        equity = self._estimate_equity(hole_cards, community_cards, num_opponents)
        equity_desc = self._get_equity_description(equity)
        
        # 3. 计算底池赔率
        pot_odds, required_equity = self._calculate_pot_odds(pot_size, bet_to_call)
        pot_odds_desc = self._get_pot_odds_description(pot_odds, required_equity)
        
        # 4. 分析听牌
        outs = self._analyze_outs(hole_cards, community_cards)
        total_outs = sum(o.outs_count for o in outs)
        
        # 5. 计算SPR
        spr = player_chips / max(pot_size, 1)
        
        # 6. 判断位置优势
        position_advantage = position >= (total_players * 0.6)
        
        # 7. 生成建议
        suggested_action, reasoning = self._generate_suggestion(
            hand_strength, equity, pot_odds, required_equity,
            total_outs, spr, position_advantage, bet_to_call, player_chips,
            len(community_cards), preflop_hand_key
        )
        
        return AnalysisResult(
            current_hand=current_hand,
            hand_strength=hand_strength,
            equity=equity,
            equity_description=equity_desc,
            pot_odds=pot_odds,
            pot_odds_description=pot_odds_desc,
            required_equity=required_equity,
            outs=outs,
            total_outs=total_outs,
            suggested_action=suggested_action,
            reasoning=reasoning,
            spr=spr,
            position_advantage=position_advantage
        )
    
    def _evaluate_hand(self, hole_cards: List[Card], 
                      community_cards: List[Card]) -> Tuple[str, float]:
        """评估当前手牌"""
        if not hole_cards or len(hole_cards) != 2:
            return "未知", 0.0
        
        # 翻牌前
        if not community_cards:
            hand_key = self._get_preflop_hand_key(hole_cards)
            strength = self.preflop_rankings.get(hand_key, 0.35)
            return f"翻牌前: {hand_key}", strength
        
        # 翻牌后
        all_cards = hole_cards + community_cards
        if len(all_cards) >= 5:
            try:
                # HandEvaluator.evaluate_hand 需要7张牌，补齐占位牌
                if len(all_cards) < 7:
                    # 使用最佳5张牌组合评估
                    from itertools import combinations
                    best_rank = None
                    best_desc = "高牌"
                    
                    for combo in combinations(all_cards, 5):
                        combo_list = list(combo)
                        rank, kickers = HandEvaluator._evaluate_five_cards(combo_list)
                        if best_rank is None or rank.rank_value > best_rank.rank_value:
                            best_rank = rank
                            best_desc = rank.display
                    
                    if best_rank:
                        strength = self._hand_rank_to_strength(best_rank)
                        return best_desc, strength
                else:
                    hand_rank, kickers = HandEvaluator.evaluate_hand(all_cards)
                    hand_desc = HandEvaluator.get_hand_description(all_cards)
                    strength = self._hand_rank_to_strength(hand_rank)
                    return hand_desc, strength
            except Exception as e:
                # 如果评估失败，返回基础估算
                return "手牌评估中", 0.35
        
        return "等待更多公共牌", 0.3
    
    def _get_preflop_hand_key(self, hole_cards: List[Card]) -> str:
        """获取翻牌前手牌的键值"""
        card1, card2 = hole_cards
        rank1, rank2 = card1.rank.numeric_value, card2.rank.numeric_value
        
        # 确保大牌在前
        if rank1 < rank2:
            rank1, rank2 = rank2, rank1
            card1, card2 = card2, card1
        
        # 转换为显示字符
        rank_chars = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T'}
        r1 = rank_chars.get(rank1, str(rank1))
        r2 = rank_chars.get(rank2, str(rank2))
        
        if rank1 == rank2:
            return f"{r1}{r2}"
        elif card1.suit == card2.suit:
            return f"{r1}{r2}s"
        else:
            return f"{r1}{r2}o"
    
    def _hand_rank_to_strength(self, hand_rank) -> float:
        """将牌型等级转换为强度值"""
        strength_map = {
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
        return strength_map.get(hand_rank.rank_value, 0.20)
    
    def _estimate_equity(self, hole_cards: List[Card], 
                        community_cards: List[Card],
                        num_opponents: int) -> float:
        """
        估算胜率（简化版本，不做蒙特卡洛模拟）
        使用规则启发式估算
        """
        if not hole_cards or len(hole_cards) != 2:
            return 0.5
        
        # 获取手牌强度
        _, hand_strength = self._evaluate_hand(hole_cards, community_cards)
        
        # 基础胜率 = 手牌强度
        base_equity = hand_strength
        
        # 根据对手数量调整
        # 更多对手 = 更低胜率
        opponent_factor = 1.0 - (num_opponents - 1) * 0.12
        opponent_factor = max(0.5, opponent_factor)
        
        # 翻牌后听牌加成
        if community_cards and len(community_cards) >= 3:
            draw_bonus = self._calculate_draw_equity(hole_cards, community_cards)
            base_equity += draw_bonus * 0.3  # 听牌贡献30%
        
        equity = base_equity * opponent_factor
        return min(0.95, max(0.05, equity))
    
    def _calculate_draw_equity(self, hole_cards: List[Card], 
                               community_cards: List[Card]) -> float:
        """计算听牌带来的额外胜率"""
        draw_equity = 0.0
        all_cards = hole_cards + community_cards
        
        # 检查同花听牌
        suits = [c.suit for c in all_cards]
        suit_counts = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1
        
        if max(suit_counts.values()) == 4:
            draw_equity += 0.35  # 同花听牌约35%
        
        # 检查顺子听牌 (简化)
        ranks = sorted([c.rank.numeric_value for c in all_cards])
        unique_ranks = list(set(ranks))
        
        # 检查是否有4张连续的牌
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] <= 4:
                draw_equity += 0.25  # 顺子听牌约25%
                break
        
        return min(0.5, draw_equity)

    def _has_poor_preflop_playability(self, hand_key: str) -> bool:
        """Return True for offsuit, disconnected trash hands that realize equity poorly."""
        if not hand_key or len(hand_key) < 2:
            return False
        if hand_key.endswith("s") or len(hand_key) == 2:
            return False

        ranks = hand_key[:-1]
        if len(ranks) != 2:
            return False

        rank_values = {
            "A": 14,
            "K": 13,
            "Q": 12,
            "J": 11,
            "T": 10,
            "9": 9,
            "8": 8,
            "7": 7,
            "6": 6,
            "5": 5,
            "4": 4,
            "3": 3,
            "2": 2,
        }
        high = rank_values.get(ranks[0], 0)
        low = rank_values.get(ranks[1], 0)
        if high == 0 or low == 0:
            return False

        is_broadwayish = high >= 12 and low >= 10
        is_ace_with_playable_kicker = high == 14 and low >= 10
        is_connected = high - low <= 2
        return not (is_broadwayish or is_ace_with_playable_kicker or is_connected)
    
    def _calculate_pot_odds(self, pot_size: int, bet_to_call: int) -> Tuple[float, float]:
        """
        计算底池赔率
        
        Returns:
            (底池赔率比例, 需要的胜率)
        """
        if bet_to_call <= 0:
            return 0.0, 0.0
        
        # 底池赔率 = 跟注后的彩池 : 跟注金额
        total_pot = pot_size + bet_to_call
        pot_odds = total_pot / bet_to_call
        
        # 需要的胜率 = 跟注金额 / (当前彩池 + 跟注金额)
        required_equity = bet_to_call / total_pot
        
        return pot_odds, required_equity
    
    def _get_equity_description(self, equity: float) -> str:
        """获取胜率描述"""
        if equity >= 0.80:
            return "极强 (80%+)"
        elif equity >= 0.65:
            return "强牌 (65-80%)"
        elif equity >= 0.50:
            return "中等偏强 (50-65%)"
        elif equity >= 0.35:
            return "中等 (35-50%)"
        elif equity >= 0.20:
            return "偏弱 (20-35%)"
        else:
            return "弱牌 (<20%)"
    
    def _get_pot_odds_description(self, pot_odds: float, required_equity: float) -> str:
        """获取底池赔率描述"""
        if pot_odds <= 0:
            return "无需跟注"
        
        return f"{pot_odds:.1f}:1 (需{required_equity*100:.1f}%胜率)"
    
    def _analyze_outs(self, hole_cards: List[Card], 
                     community_cards: List[Card]) -> List[OutsInfo]:
        """分析听牌outs"""
        outs_list = []
        
        if not community_cards or len(community_cards) < 3:
            return outs_list
        
        all_cards = hole_cards + community_cards
        cards_remaining = 52 - len(all_cards)
        cards_to_come = 5 - len(community_cards)
        
        # 检查同花听牌
        suits = [c.suit for c in all_cards]
        suit_counts = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1
        
        for suit, count in suit_counts.items():
            if count == 4:
                # 检查是否用到了手牌
                hole_suit_count = sum(1 for c in hole_cards if c.suit == suit)
                if hole_suit_count >= 1:
                    outs = 13 - count  # 同花色剩余牌数
                    turn_prob = outs / cards_remaining * 100
                    river_prob = outs / (cards_remaining - 1) * 100 if cards_to_come == 2 else 0
                    both_prob = self._calculate_combined_probability(outs, cards_remaining)
                    
                    outs_list.append(OutsInfo(
                        outs_count=outs,
                        description="同花听牌",
                        probability_turn=turn_prob,
                        probability_river=river_prob,
                        probability_both=both_prob if cards_to_come == 2 else turn_prob
                    ))
        
        # 检查顺子听牌
        ranks = sorted(set([c.rank.numeric_value for c in all_cards]))
        
        # 两头顺子听牌检查
        for i in range(len(ranks) - 3):
            if ranks[i+3] - ranks[i] == 3:
                # 可能是两头顺
                needed_low = ranks[i] - 1
                needed_high = ranks[i+3] + 1
                outs = 0
                
                if 2 <= needed_low <= 14:
                    outs += 4
                if 2 <= needed_high <= 14:
                    outs += 4
                
                if outs > 0:
                    turn_prob = outs / cards_remaining * 100
                    both_prob = self._calculate_combined_probability(outs, cards_remaining)
                    
                    outs_list.append(OutsInfo(
                        outs_count=outs,
                        description="两头顺子听牌" if outs == 8 else "卡顺听牌",
                        probability_turn=turn_prob,
                        probability_river=0,
                        probability_both=both_prob if cards_to_come == 2 else turn_prob
                    ))
                    break
        
        return outs_list
    
    def _calculate_combined_probability(self, outs: int, cards_remaining: int) -> float:
        """计算转牌+河牌的综合概率"""
        # P(中牌) = 1 - P(转牌不中) * P(河牌不中)
        miss_turn = (cards_remaining - outs) / cards_remaining
        miss_river = (cards_remaining - 1 - outs) / (cards_remaining - 1)
        hit_probability = 1 - (miss_turn * miss_river)
        return hit_probability * 100
    
    def _generate_suggestion(self, hand_strength: float, equity: float,
                            pot_odds: float, required_equity: float,
                            total_outs: int, spr: float,
                            position_advantage: bool, bet_to_call: int,
                            player_chips: int, num_community_cards: int,
                            preflop_hand_key: str = ""
                            ) -> Tuple[SuggestedAction, str]:
        """生成建议动作和推理"""
        reasons = []
        
        # 无需跟注的情况
        if bet_to_call == 0:
            if hand_strength >= 0.70:
                reasons.append(f"强牌(强度{hand_strength:.0%})，应该下注获取价值")
                return SuggestedAction.RAISE, "; ".join(reasons)
            elif hand_strength >= 0.45 or total_outs >= 8:
                reasons.append("中等牌力或有听牌，可以下注半诈唬")
                return SuggestedAction.RAISE, "; ".join(reasons)
            elif position_advantage and hand_strength >= 0.25:
                reasons.append("有位置优势，可以尝试偷池")
                return SuggestedAction.RAISE, "; ".join(reasons)
            else:
                reasons.append("牌力较弱，过牌等待机会")
                return SuggestedAction.CHECK, "; ".join(reasons)
        
        # 需要跟注的情况
        # 翻牌前不要只按裸胜率/底池赔率推荐垃圾牌跟注：弱可玩性牌实际胜率实现率很差。
        if num_community_cards == 0 and self._has_poor_preflop_playability(preflop_hand_key):
            reasons.append(
                f"{preflop_hand_key}翻牌前可玩性/实现率较差，裸胜率不应直接等同于可跟注价值"
            )
            return SuggestedAction.FOLD, "; ".join(reasons)

        # 计算有效胜率（包含听牌）
        effective_equity = equity
        if total_outs >= 8 and num_community_cards < 5:
            # 有强听牌，增加有效胜率
            effective_equity = min(0.90, equity + total_outs * 0.02)
            reasons.append(f"有{total_outs}张outs，提升有效胜率")
        
        # 比较胜率和所需胜率
        if effective_equity >= required_equity * 1.5:
            # 胜率远高于所需
            if hand_strength >= 0.65:
                reasons.append(f"胜率({effective_equity:.0%})远超所需({required_equity:.0%})，强牌应加注")
                return SuggestedAction.STRONG_RAISE, "; ".join(reasons)
            else:
                reasons.append(f"胜率足够，但牌力一般，跟注为宜")
                return SuggestedAction.CALL, "; ".join(reasons)
        
        elif effective_equity >= required_equity:
            # 胜率略高于所需
            reasons.append(f"胜率({effective_equity:.0%})达到所需({required_equity:.0%})")
            
            if hand_strength >= 0.50:
                reasons.append("牌力中等偏强，跟注合理")
                return SuggestedAction.CALL, "; ".join(reasons)
            else:
                reasons.append("边缘情况，需谨慎考虑")
                return SuggestedAction.BORDERLINE_CALL, "; ".join(reasons)
        
        else:
            # 胜率不足
            equity_gap = required_equity - effective_equity
            
            if equity_gap <= 0.10 and (position_advantage or total_outs >= 6):
                reasons.append(f"胜率({effective_equity:.0%})略低于所需({required_equity:.0%})，但有位置/听牌")
                return SuggestedAction.BORDERLINE_CALL, "; ".join(reasons)
            else:
                reasons.append(f"胜率({effective_equity:.0%})不足所需({required_equity:.0%})，建议弃牌")
                return SuggestedAction.FOLD, "; ".join(reasons)
    
    def format_display(self, analysis: AnalysisResult, show_full: bool = True) -> str:
        """
        格式化显示分析结果
        
        Args:
            analysis: 分析结果
            show_full: 是否显示完整信息
            
        Returns:
            格式化后的字符串
        """
        lines = []
        
        # 标题
        lines.append("")
        lines.append("┌" + "─" * 56 + "┐")
        lines.append("│" + " 📊 实时辅助分析 ".center(54) + "│")
        lines.append("├" + "─" * 56 + "┤")
        
        # 当前手牌
        lines.append(f"│ 🃏 当前成牌: {analysis.current_hand:<40} │")
        
        # 胜率信息
        equity_bar = self._create_progress_bar(analysis.equity, 20)
        lines.append(f"│ 📈 估算胜率: {equity_bar} {analysis.equity*100:>5.1f}%{' '*8}│")
        lines.append(f"│    {analysis.equity_description:<52} │")
        
        if show_full:
            # 底池赔率
            if analysis.pot_odds > 0:
                lines.append("├" + "─" * 56 + "┤")
                lines.append(f"│ 💰 底池赔率: {analysis.pot_odds_description:<40} │")
                
                # 比较胜率和所需胜率
                if analysis.equity >= analysis.required_equity:
                    comparison = "✅ 胜率足够"
                else:
                    comparison = "❌ 胜率不足"
                lines.append(f"│    {comparison:<52} │")
            
            # 听牌信息
            if analysis.outs:
                lines.append("├" + "─" * 56 + "┤")
                lines.append(f"│ 🎯 听牌分析 (共 {analysis.total_outs} 张outs):{' '*28}│")
                
                for out in analysis.outs:
                    lines.append(f"│    • {out.description}: {out.outs_count}张 "
                               f"({out.probability_both:.1f}%){' '*20}│")
        
        # 建议
        lines.append("├" + "─" * 56 + "┤")
        action = analysis.suggested_action
        lines.append(f"│ {action.value[1]} 建议动作: {action.value[0]:<42} │")
        
        # 推理（可能需要换行）
        reasoning = analysis.reasoning
        if len(reasoning) > 50:
            # 分行显示
            words = reasoning.split("; ")
            current_line = "│    "
            for word in words:
                if len(current_line) + len(word) + 2 > 56:
                    lines.append(current_line.ljust(57) + "│")
                    current_line = "│    " + word
                else:
                    if current_line == "│    ":
                        current_line += word
                    else:
                        current_line += "; " + word
            if current_line != "│    ":
                lines.append(current_line.ljust(57) + "│")
        else:
            lines.append(f"│    {reasoning:<52} │")
        
        # 底部
        lines.append("└" + "─" * 56 + "┘")
        lines.append("")
        
        return "\n".join(lines)
    
    def format_compact(self, analysis: AnalysisResult) -> str:
        """紧凑格式显示"""
        action = analysis.suggested_action
        
        # 单行紧凑格式
        equity_str = f"{analysis.equity*100:.0f}%"
        outs_str = f"{analysis.total_outs}outs" if analysis.total_outs > 0 else ""
        
        parts = [
            f"胜率:{equity_str}",
            f"建议:{action.value[1]}{action.value[0]}"
        ]
        
        if outs_str:
            parts.insert(1, outs_str)
        
        if analysis.pot_odds > 0:
            odds_ok = "✅" if analysis.equity >= analysis.required_equity else "❌"
            parts.insert(1, f"赔率{odds_ok}")
        
        return " | ".join(parts)
    
    def _create_progress_bar(self, value: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int(value * width)
        empty = width - filled
        
        # 根据值选择颜色指示
        if value >= 0.65:
            indicator = "🟢"
        elif value >= 0.45:
            indicator = "🟡"
        else:
            indicator = "🔴"
        
        bar = "█" * filled + "░" * empty
        return f"{indicator}[{bar}]"


# ============================================================================
# 全局实例
# ============================================================================

_assistant_instance: Optional[RealtimeAssistant] = None


def get_assistant(enabled: bool = True) -> RealtimeAssistant:
    """获取辅助器单例实例"""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = RealtimeAssistant(enabled)
    return _assistant_instance


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    from card import Card, Suit, Rank
    
    assistant = RealtimeAssistant()
    
    print("=" * 60)
    print("测试场景1: 翻牌前 AA")
    print("=" * 60)
    
    hole_cards = [Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE)]
    result = assistant.analyze(
        hole_cards=hole_cards,
        community_cards=[],
        pot_size=15,
        bet_to_call=10,
        player_chips=990,
        position=3,
        total_players=6,
        num_opponents=2
    )
    print(assistant.format_display(result))
    
    print("=" * 60)
    print("测试场景2: 翻牌后同花听牌")
    print("=" * 60)
    
    hole_cards = [Card(Suit.HEARTS, Rank.KING), Card(Suit.HEARTS, Rank.QUEEN)]
    community_cards = [
        Card(Suit.HEARTS, Rank.TEN),
        Card(Suit.HEARTS, Rank.FIVE),
        Card(Suit.SPADES, Rank.TWO)
    ]
    result = assistant.analyze(
        hole_cards=hole_cards,
        community_cards=community_cards,
        pot_size=150,
        bet_to_call=50,
        player_chips=900,
        position=4,
        total_players=6,
        num_opponents=1
    )
    print(assistant.format_display(result))
    
    print("=" * 60)
    print("测试场景3: 弱牌面对大注")
    print("=" * 60)
    
    hole_cards = [Card(Suit.CLUBS, Rank.SEVEN), Card(Suit.DIAMONDS, Rank.SIX)]
    community_cards = [
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.CLUBS, Rank.TWO)
    ]
    result = assistant.analyze(
        hole_cards=hole_cards,
        community_cards=community_cards,
        pot_size=100,
        bet_to_call=80,
        player_chips=800,
        position=2,
        total_players=6,
        num_opponents=2
    )
    print(assistant.format_display(result))
    
    print("\n紧凑格式示例:")
    print(assistant.format_compact(result))

