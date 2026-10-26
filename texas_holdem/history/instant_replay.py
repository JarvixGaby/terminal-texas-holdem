#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 即时复盘系统
每局结束后自动分析：关键决策点、EV计算、改进建议
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from texas_holdem.engine.card import Card
from texas_holdem.engine.hand_evaluator import HandEvaluator


class DecisionQuality(Enum):
    """决策质量评级"""
    EXCELLENT = ("优秀", "🌟", 3)
    GOOD = ("良好", "✅", 2)
    ACCEPTABLE = ("可接受", "⚠️", 1)
    QUESTIONABLE = ("存疑", "❓", 0)
    MISTAKE = ("失误", "❌", -1)
    BLUNDER = ("严重失误", "💀", -2)


@dataclass
class DecisionPoint:
    """决策点记录"""
    phase: str                    # 游戏阶段
    player_name: str              # 玩家名
    action: str                   # 实际动作
    amount: int                   # 金额
    pot_size: int                 # 彩池大小
    bet_to_call: int              # 需要跟注金额
    hand_strength: float          # 当时手牌强度
    equity: float                 # 当时胜率
    ev_estimate: float            # 期望值估算
    quality: DecisionQuality      # 决策质量
    suggestion: str               # 建议
    reasoning: str                # 理由


@dataclass
class HandAnalysis:
    """手牌分析结果"""
    game_id: str
    player_name: str
    hole_cards: List[str]
    community_cards: List[str]
    final_result: str             # 最终结果 (win/lose/fold)
    winnings: int                 # 盈亏
    
    decision_points: List[DecisionPoint] = field(default_factory=list)
    overall_score: int = 0        # 总体评分 (0-100)
    key_mistakes: List[str] = field(default_factory=list)
    key_successes: List[str] = field(default_factory=list)
    improvement_tips: List[str] = field(default_factory=list)


class InstantReplayAnalyzer:
    """即时复盘分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 预设的手牌强度参考
        self.preflop_strength = self._build_preflop_strength()
    
    def _build_preflop_strength(self) -> Dict[str, float]:
        """构建翻牌前手牌强度表"""
        return {
            'AA': 0.95, 'KK': 0.90, 'QQ': 0.85, 'JJ': 0.80, 'TT': 0.75,
            'AKs': 0.82, 'AKo': 0.78, 'AQs': 0.76, 'AQo': 0.72,
            '99': 0.70, '88': 0.65, 'AJs': 0.72, 'KQs': 0.72,
            '77': 0.60, '66': 0.55, 'ATs': 0.68,
        }
    
    def analyze_hand(self, game_record: Dict, player_name: str) -> HandAnalysis:
        """
        分析一局游戏
        
        Args:
            game_record: 游戏记录字典
            player_name: 要分析的玩家名
            
        Returns:
            手牌分析结果
        """
        # 初始化分析结果
        analysis = HandAnalysis(
            game_id=game_record.get('game_id', 'unknown'),
            player_name=player_name,
            hole_cards=[],
            community_cards=[],
            final_result="unknown",
            winnings=0
        )
        
        # 获取玩家信息
        final_hands = game_record.get('final_hands', [])
        player_data = None
        for hand in final_hands:
            if hand.get('player_name') == player_name:
                player_data = hand
                break
        
        if player_data:
            analysis.hole_cards = player_data.get('hole_cards', [])
            analysis.winnings = player_data.get('winnings', 0)
            
            if player_data.get('hand_rank') == '已弃牌':
                analysis.final_result = "fold"
            elif player_name in game_record.get('winner_names', []):
                analysis.final_result = "win"
            else:
                analysis.final_result = "lose"
        
        # 分析每个阶段的决策
        phases = game_record.get('phases', [])
        for phase_data in phases:
            phase_name = phase_data.get('phase', '')
            community_cards = phase_data.get('community_cards', [])
            pot_size = phase_data.get('pot_size', 0)
            
            # 更新公共牌
            if community_cards:
                analysis.community_cards = community_cards
            
            # 分析该阶段的每个动作
            for action_data in phase_data.get('actions', []):
                if action_data.get('player_name') == player_name:
                    decision = self._analyze_decision(
                        phase=phase_name,
                        action_data=action_data,
                        hole_cards=analysis.hole_cards,
                        community_cards=community_cards,
                        pot_size=pot_size
                    )
                    if decision:
                        analysis.decision_points.append(decision)
        
        # 计算总体评分和生成建议
        self._calculate_overall_score(analysis)
        self._generate_improvement_tips(analysis)
        
        return analysis
    
    def _analyze_decision(self, phase: str, action_data: Dict, 
                         hole_cards: List[str], community_cards: List[str],
                         pot_size: int) -> Optional[DecisionPoint]:
        """分析单个决策点"""
        action = action_data.get('action', '')
        amount = action_data.get('amount', 0)
        chips_before = action_data.get('chips_before', 1000)
        chips_after = action_data.get('chips_after', 1000)
        
        # 计算需要跟注的金额
        bet_to_call = chips_before - chips_after if action == 'call' else 0
        if action == 'raise':
            bet_to_call = amount
        
        # 估算手牌强度
        hand_strength = self._estimate_hand_strength(hole_cards, community_cards, phase)
        
        # 估算胜率
        equity = self._estimate_equity(hand_strength, phase)
        
        # 计算EV
        ev_estimate = self._calculate_ev(action, amount, pot_size, equity, bet_to_call)
        
        # 评估决策质量
        quality, suggestion, reasoning = self._evaluate_decision_quality(
            action, amount, pot_size, bet_to_call, hand_strength, equity, phase
        )
        
        return DecisionPoint(
            phase=phase,
            player_name=action_data.get('player_name', ''),
            action=action,
            amount=amount,
            pot_size=pot_size,
            bet_to_call=bet_to_call,
            hand_strength=hand_strength,
            equity=equity,
            ev_estimate=ev_estimate,
            quality=quality,
            suggestion=suggestion,
            reasoning=reasoning
        )
    
    def _estimate_hand_strength(self, hole_cards: List[str], 
                               community_cards: List[str], phase: str) -> float:
        """估算手牌强度"""
        if not hole_cards:
            return 0.3
        
        # 翻牌前
        if phase == "preflop" or not community_cards:
            hand_key = self._get_hand_key(hole_cards)
            return self.preflop_strength.get(hand_key, 0.35)
        
        # 翻牌后 - 尝试评估
        try:
            cards = []
            for card_str in hole_cards + community_cards:
                cards.append(self._parse_card(card_str))
            
            if len(cards) >= 5:
                from itertools import combinations
                best_rank = None
                
                for combo in combinations(cards, 5):
                    rank, _ = HandEvaluator._evaluate_five_cards(list(combo))
                    if best_rank is None or rank.rank_value > best_rank.rank_value:
                        best_rank = rank
                
                if best_rank:
                    return self._rank_to_strength(best_rank.rank_value)
        except Exception:
            pass
        
        return 0.35
    
    def _get_hand_key(self, hole_cards: List[str]) -> str:
        """获取手牌键值"""
        if len(hole_cards) != 2:
            return "unknown"
        
        card1, card2 = hole_cards
        # 解析牌面
        rank1 = card1[:-1] if len(card1) > 1 else card1[0]
        rank2 = card2[:-1] if len(card2) > 1 else card2[0]
        suit1 = card1[-1]
        suit2 = card2[-1]
        
        # 标准化牌面表示
        rank_order = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '10': 10,
                     '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        
        r1 = rank_order.get(rank1, 0)
        r2 = rank_order.get(rank2, 0)
        
        if r1 < r2:
            r1, r2 = r2, r1
            rank1, rank2 = rank2, rank1
            suit1, suit2 = suit2, suit1
        
        # 转换显示
        display = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T'}
        d1 = display.get(r1, rank1)
        d2 = display.get(r2, rank2)
        
        if r1 == r2:
            return f"{d1}{d2}"
        elif suit1 == suit2:
            return f"{d1}{d2}s"
        else:
            return f"{d1}{d2}o"
    
    def _parse_card(self, card_str: str):
        """解析卡牌字符串为Card对象"""
        from texas_holdem.engine.card import Card, Suit, Rank
        
        suit_map = {'♥': Suit.HEARTS, '♦': Suit.DIAMONDS, 
                   '♣': Suit.CLUBS, '♠': Suit.SPADES}
        rank_map = {'2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, 
                   '5': Rank.FIVE, '6': Rank.SIX, '7': Rank.SEVEN,
                   '8': Rank.EIGHT, '9': Rank.NINE, '10': Rank.TEN,
                   'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN,
                   'K': Rank.KING, 'A': Rank.ACE}
        
        suit_char = card_str[-1]
        rank_str = card_str[:-1]
        
        suit = suit_map.get(suit_char)
        rank = rank_map.get(rank_str)
        
        if suit and rank:
            return Card(suit, rank)
        raise ValueError(f"无法解析卡牌: {card_str}")
    
    def _rank_to_strength(self, rank_value: int) -> float:
        """牌型等级转强度"""
        strength_map = {
            10: 1.00, 9: 0.98, 8: 0.95, 7: 0.88,
            6: 0.78, 5: 0.70, 4: 0.58, 3: 0.45,
            2: 0.32, 1: 0.20
        }
        return strength_map.get(rank_value, 0.25)
    
    def _estimate_equity(self, hand_strength: float, phase: str) -> float:
        """估算胜率"""
        # 简化的胜率估算
        base_equity = hand_strength
        
        # 翻牌前略微降低
        if phase == "preflop":
            base_equity *= 0.9
        
        return min(0.95, max(0.05, base_equity))
    
    def _calculate_ev(self, action: str, amount: int, pot_size: int,
                     equity: float, bet_to_call: int) -> float:
        """计算期望值"""
        if action == "fold":
            return 0  # 弃牌EV为0
        
        if action == "check":
            return pot_size * equity  # 过牌保留胜率
        
        if action == "call":
            # EV = (赢的概率 * 赢的金额) - (输的概率 * 输的金额)
            win_amount = pot_size + bet_to_call
            ev = equity * win_amount - (1 - equity) * bet_to_call
            return ev
        
        if action == "raise":
            # 加注EV更复杂，简化处理
            win_amount = pot_size + amount
            ev = equity * win_amount - (1 - equity) * amount
            return ev
        
        return 0
    
    def _evaluate_decision_quality(self, action: str, amount: int, pot_size: int,
                                  bet_to_call: int, hand_strength: float,
                                  equity: float, phase: str
                                  ) -> Tuple[DecisionQuality, str, str]:
        """评估决策质量"""
        
        # 计算底池赔率
        required_equity = 0.0
        if bet_to_call > 0:
            required_equity = bet_to_call / (pot_size + bet_to_call)
        
        # 评估逻辑
        if action == "fold":
            if equity >= 0.5:
                return (DecisionQuality.MISTAKE, 
                       "不应弃牌",
                       f"胜率{equity*100:.0f}%足够高，不应弃牌")
            elif equity >= required_equity and bet_to_call > 0:
                return (DecisionQuality.QUESTIONABLE,
                       "考虑跟注",
                       f"底池赔率足够(需{required_equity*100:.0f}%，有{equity*100:.0f}%)")
            else:
                return (DecisionQuality.GOOD,
                       "正确弃牌",
                       "胜率不足，弃牌正确")
        
        elif action == "call":
            if equity >= required_equity * 1.5:
                return (DecisionQuality.ACCEPTABLE,
                       "考虑加注",
                       f"胜率很高({equity*100:.0f}%)，可以加注获取更多价值")
            elif equity >= required_equity:
                return (DecisionQuality.GOOD,
                       "合理跟注",
                       f"底池赔率合适")
            else:
                return (DecisionQuality.MISTAKE,
                       "不应跟注",
                       f"胜率({equity*100:.0f}%)低于所需({required_equity*100:.0f}%)")
        
        elif action == "raise":
            if hand_strength >= 0.6:
                return (DecisionQuality.EXCELLENT,
                       "优秀价值加注",
                       "强牌加注获取价值")
            elif hand_strength >= 0.4:
                return (DecisionQuality.GOOD,
                       "合理加注",
                       "中等牌力，加注合理")
            elif hand_strength >= 0.25:
                return (DecisionQuality.ACCEPTABLE,
                       "激进打法",
                       "半诈唬或位置加注")
            else:
                return (DecisionQuality.QUESTIONABLE,
                       "风险较高",
                       "牌力较弱，诈唬风险大")
        
        elif action == "check":
            if hand_strength >= 0.7:
                return (DecisionQuality.QUESTIONABLE,
                       "考虑下注",
                       "强牌应该下注获取价值")
            else:
                return (DecisionQuality.GOOD,
                       "合理过牌",
                       "控制底池或设置陷阱")
        
        return (DecisionQuality.ACCEPTABLE, "一般", "标准打法")
    
    def _calculate_overall_score(self, analysis: HandAnalysis):
        """计算总体评分"""
        if not analysis.decision_points:
            analysis.overall_score = 50
            return
        
        total_score = 0
        for dp in analysis.decision_points:
            # 根据决策质量加分
            quality_scores = {
                DecisionQuality.EXCELLENT: 100,
                DecisionQuality.GOOD: 80,
                DecisionQuality.ACCEPTABLE: 60,
                DecisionQuality.QUESTIONABLE: 40,
                DecisionQuality.MISTAKE: 20,
                DecisionQuality.BLUNDER: 0
            }
            total_score += quality_scores.get(dp.quality, 50)
            
            # 记录关键失误和成功
            if dp.quality in [DecisionQuality.MISTAKE, DecisionQuality.BLUNDER]:
                analysis.key_mistakes.append(f"{dp.phase}: {dp.reasoning}")
            elif dp.quality == DecisionQuality.EXCELLENT:
                analysis.key_successes.append(f"{dp.phase}: {dp.reasoning}")
        
        analysis.overall_score = int(total_score / len(analysis.decision_points))
    
    def _generate_improvement_tips(self, analysis: HandAnalysis):
        """生成改进建议"""
        tips = []
        
        # 基于决策点生成建议
        fold_with_equity = False
        call_without_odds = False
        missed_value = False
        
        for dp in analysis.decision_points:
            if dp.action == "fold" and dp.equity >= 0.4:
                fold_with_equity = True
            if dp.action == "call" and dp.equity < dp.bet_to_call / (dp.pot_size + dp.bet_to_call + 0.01):
                call_without_odds = True
            if dp.action == "check" and dp.hand_strength >= 0.7:
                missed_value = True
        
        if fold_with_equity:
            tips.append("注意不要在胜率足够时弃牌，学会计算底池赔率")
        
        if call_without_odds:
            tips.append("避免在底池赔率不足时跟注，这是长期亏损的来源")
        
        if missed_value:
            tips.append("强牌要敢于下注，错过价值是常见的漏洞")
        
        # 基于结果添加建议
        if analysis.final_result == "fold" and analysis.winnings == 0:
            tips.append("弃牌不一定是错误，但要确保是基于正确的理由")
        
        if not tips:
            if analysis.overall_score >= 80:
                tips.append("表现优秀！继续保持这种决策水平")
            else:
                tips.append("整体表现尚可，继续积累经验")
        
        analysis.improvement_tips = tips
    
    def format_summary(self, analysis: HandAnalysis) -> str:
        """格式化显示分析摘要"""
        lines = []
        
        # 标题
        lines.append("")
        lines.append("┌" + "─" * 56 + "┐")
        lines.append("│" + " 📋 本局回顾 ".center(54) + "│")
        lines.append("├" + "─" * 56 + "┤")
        
        # 基本信息
        result_emoji = {"win": "🏆", "lose": "😢", "fold": "🏳️"}.get(analysis.final_result, "❓")
        result_text = {"win": "获胜", "lose": "失败", "fold": "弃牌"}.get(analysis.final_result, "未知")
        
        lines.append(f"│ {result_emoji} 结果: {result_text:<20} 盈亏: {analysis.winnings:>+6} 筹码 │")
        lines.append(f"│ 🃏 手牌: {' '.join(analysis.hole_cards):<44} │")
        
        # 评分
        score = analysis.overall_score
        if score >= 80:
            score_emoji = "🌟"
            score_desc = "优秀"
        elif score >= 60:
            score_emoji = "✅"
            score_desc = "良好"
        elif score >= 40:
            score_emoji = "⚠️"
            score_desc = "一般"
        else:
            score_emoji = "❌"
            score_desc = "需改进"
        
        score_bar = "█" * (score // 10) + "░" * (10 - score // 10)
        lines.append(f"│ {score_emoji} 评分: [{score_bar}] {score}/100 ({score_desc}){' '*5}│")
        
        # 关键失误
        if analysis.key_mistakes:
            lines.append("├" + "─" * 56 + "┤")
            lines.append("│ ❌ 关键失误:" + " " * 43 + "│")
            for mistake in analysis.key_mistakes[:2]:  # 最多显示2个
                mistake_short = mistake[:48] + "..." if len(mistake) > 48 else mistake
                lines.append(f"│    • {mistake_short:<50} │")
        
        # 关键成功
        if analysis.key_successes:
            lines.append("├" + "─" * 56 + "┤")
            lines.append("│ ✅ 正确决策:" + " " * 43 + "│")
            for success in analysis.key_successes[:2]:
                success_short = success[:48] + "..." if len(success) > 48 else success
                lines.append(f"│    • {success_short:<50} │")
        
        # 改进建议
        lines.append("├" + "─" * 56 + "┤")
        lines.append("│ 💡 改进建议:" + " " * 43 + "│")
        for tip in analysis.improvement_tips[:2]:
            tip_short = tip[:48] + "..." if len(tip) > 48 else tip
            lines.append(f"│    • {tip_short:<50} │")
        
        # 底部
        lines.append("└" + "─" * 56 + "┘")
        lines.append("")
        
        return "\n".join(lines)
    
    def format_detailed(self, analysis: HandAnalysis) -> str:
        """格式化显示详细分析"""
        lines = []
        
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"详细复盘 - 游戏ID: {analysis.game_id}")
        lines.append("=" * 60)
        
        lines.append(f"\n手牌: {' '.join(analysis.hole_cards)}")
        lines.append(f"公共牌: {' '.join(analysis.community_cards)}")
        lines.append(f"结果: {analysis.final_result} | 盈亏: {analysis.winnings:+}")
        
        lines.append("\n决策点分析:")
        lines.append("-" * 60)
        
        for i, dp in enumerate(analysis.decision_points, 1):
            emoji = dp.quality.value[1]
            lines.append(f"\n{i}. {dp.phase.upper()} - {dp.action} {dp.amount}")
            lines.append(f"   {emoji} {dp.quality.value[0]}: {dp.reasoning}")
            lines.append(f"   手牌强度: {dp.hand_strength*100:.0f}% | 胜率: {dp.equity*100:.0f}%")
            lines.append(f"   建议: {dp.suggestion}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)


# ============================================================================
# 全局实例
# ============================================================================

_replay_analyzer: Optional[InstantReplayAnalyzer] = None


def get_replay_analyzer() -> InstantReplayAnalyzer:
    """获取复盘分析器单例"""
    global _replay_analyzer
    if _replay_analyzer is None:
        _replay_analyzer = InstantReplayAnalyzer()
    return _replay_analyzer


# ============================================================================
# 便捷函数
# ============================================================================

def analyze_and_display(game_record: Dict, player_name: str, detailed: bool = False) -> str:
    """分析并显示结果"""
    analyzer = get_replay_analyzer()
    analysis = analyzer.analyze_hand(game_record, player_name)
    
    if detailed:
        return analyzer.format_detailed(analysis)
    else:
        return analyzer.format_summary(analysis)


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    # 创建测试数据
    test_game_record = {
        "game_id": "test_123",
        "winner_names": ["玩家1"],
        "final_hands": [
            {
                "player_name": "玩家1",
                "hole_cards": ["A♠", "K♥"],
                "final_chips": 1150,
                "hand_rank": "高牌 (A 高)",
                "winnings": 150
            },
            {
                "player_name": "AI_Alice",
                "hole_cards": ["Q♠", "J♥"],
                "final_chips": 850,
                "hand_rank": "已弃牌",
                "winnings": 0
            }
        ],
        "phases": [
            {
                "phase": "preflop",
                "community_cards": [],
                "pot_size": 15,
                "actions": [
                    {"player_name": "玩家1", "action": "raise", "amount": 30, 
                     "chips_before": 1000, "chips_after": 970},
                    {"player_name": "AI_Alice", "action": "call", "amount": 30,
                     "chips_before": 1000, "chips_after": 970}
                ]
            },
            {
                "phase": "flop",
                "community_cards": ["T♠", "7♥", "2♣"],
                "pot_size": 75,
                "actions": [
                    {"player_name": "玩家1", "action": "bet", "amount": 50,
                     "chips_before": 970, "chips_after": 920},
                    {"player_name": "AI_Alice", "action": "fold", "amount": 0,
                     "chips_before": 970, "chips_after": 970}
                ]
            }
        ]
    }
    
    print("测试即时复盘系统")
    print("=" * 60)
    
    analyzer = get_replay_analyzer()
    analysis = analyzer.analyze_hand(test_game_record, "玩家1")
    
    print(analyzer.format_summary(analysis))
    print("\n" + "=" * 60)
    print("详细分析:")
    print(analyzer.format_detailed(analysis))


