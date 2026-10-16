#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级分析系统
专业级德州扑克数据分析和性能评估
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class SessionStats:
    """单次游戏会话统计"""
    session_id: str
    start_time: str
    end_time: str
    hands_played: int
    profit_loss: int
    vpip: float
    pfr: float
    aggression_factor: float
    showdown_winrate: float
    bb_per_100_hands: float


@dataclass
class PositionalStats:
    """位置统计"""
    position: str
    hands_played: int
    vpip: float
    pfr: float
    winrate: float
    profit_loss: int


@dataclass
class HandStrengthAnalysis:
    """手牌强度分析"""
    hand_type: str
    times_played: int
    times_won: int
    average_profit: float
    best_profit: int
    worst_loss: int


class AdvancedAnalytics:
    """高级分析引擎"""
    
    def __init__(self, data_file: str = "advanced_stats.json"):
        self.data_file = data_file
        self.stats_data = self.load_stats()
    
    def load_stats(self) -> Dict[str, Any]:
        """加载统计数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "sessions": [],
                "hand_history": [],
                "performance_metrics": {}
            }
    
    def save_stats(self):
        """保存统计数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"统计数据保存失败: {e}")
    
    def record_hand_result(self, player_name: str, hand_data: Dict[str, Any]):
        """记录单手牌结果"""
        hand_record = {
            "timestamp": datetime.now().isoformat(),
            "player_name": player_name,
            "position": hand_data.get("position", "unknown"),
            "hole_cards": hand_data.get("hole_cards", []),
            "actions": hand_data.get("actions", []),
            "final_pot": hand_data.get("final_pot", 0),
            "profit_loss": hand_data.get("profit_loss", 0),
            "showdown": hand_data.get("went_to_showdown", False),
            "won": hand_data.get("won", False)
        }
        
        if "hand_history" not in self.stats_data:
            self.stats_data["hand_history"] = []
        
        self.stats_data["hand_history"].append(hand_record)
        self.save_stats()
    
    def calculate_bb_per_100(self, profit_loss: int, hands_played: int, big_blind: int) -> float:
        """计算每100手大盲注盈利"""
        if hands_played == 0:
            return 0.0
        return (profit_loss / big_blind) * (100 / hands_played)
    
    def calculate_aggression_factor(self, aggressive_actions: int, passive_actions: int) -> float:
        """计算侵略因子"""
        if passive_actions == 0:
            return float('inf') if aggressive_actions > 0 else 0.0
        return aggressive_actions / passive_actions
    
    def get_recent_performance(self, player_name: str, days: int = 7) -> Dict[str, Any]:
        """获取最近表现"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_hands = []
        
        for hand in self.stats_data.get("hand_history", []):
            if hand.get("player_name") == player_name:
                hand_time = datetime.fromisoformat(hand["timestamp"])
                if hand_time >= cutoff_date:
                    recent_hands.append(hand)
        
        if not recent_hands:
            return {"error": "没有足够的数据"}
        
        # 计算各项指标
        total_hands = len(recent_hands)
        total_profit = sum(hand["profit_loss"] for hand in recent_hands)
        showdown_hands = [h for h in recent_hands if h["showdown"]]
        won_hands = [h for h in recent_hands if h["won"]]
        
        return {
            "period": f"最近{days}天",
            "hands_played": total_hands,
            "total_profit": total_profit,
            "winrate": len(won_hands) / total_hands * 100 if total_hands > 0 else 0,
            "showdown_winrate": len([h for h in showdown_hands if h["won"]]) / len(showdown_hands) * 100 if showdown_hands else 0,
            "profit_per_hand": total_profit / total_hands if total_hands > 0 else 0
        }
    
    def analyze_positional_play(self, player_name: str) -> List[PositionalStats]:
        """分析位置打法"""
        position_data = defaultdict(lambda: {
            "hands": 0, "vpip_hands": 0, "pfr_hands": 0, 
            "won": 0, "profit": 0
        })
        
        for hand in self.stats_data.get("hand_history", []):
            if hand.get("player_name") != player_name:
                continue
                
            pos = hand.get("position", "unknown")
            position_data[pos]["hands"] += 1
            position_data[pos]["profit"] += hand["profit_loss"]
            
            if hand["won"]:
                position_data[pos]["won"] += 1
            
            # 分析动作判断VPIP和PFR (简化版)
            actions = hand.get("actions", [])
            if any(action in ["call", "raise", "bet"] for action in actions):
                position_data[pos]["vpip_hands"] += 1
            if any(action in ["raise", "bet"] for action in actions):
                position_data[pos]["pfr_hands"] += 1
        
        results = []
        for pos, data in position_data.items():
            if data["hands"] > 0:
                results.append(PositionalStats(
                    position=pos,
                    hands_played=data["hands"],
                    vpip=data["vpip_hands"] / data["hands"] * 100,
                    pfr=data["pfr_hands"] / data["hands"] * 100,
                    winrate=data["won"] / data["hands"] * 100,
                    profit_loss=data["profit"]
                ))
        
        return sorted(results, key=lambda x: x.hands_played, reverse=True)
    
    def analyze_hand_selection(self, player_name: str) -> List[HandStrengthAnalysis]:
        """分析手牌选择"""
        hand_data = defaultdict(lambda: {
            "played": 0, "won": 0, "profits": []
        })
        
        for hand in self.stats_data.get("hand_history", []):
            if hand.get("player_name") != player_name:
                continue
            
            hole_cards = hand.get("hole_cards", [])
            if len(hole_cards) == 2:
                # 简化手牌分类
                hand_type = self._classify_starting_hand(hole_cards)
                hand_data[hand_type]["played"] += 1
                hand_data[hand_type]["profits"].append(hand["profit_loss"])
                
                if hand["won"]:
                    hand_data[hand_type]["won"] += 1
        
        results = []
        for hand_type, data in hand_data.items():
            if data["played"] > 0:
                profits = data["profits"]
                results.append(HandStrengthAnalysis(
                    hand_type=hand_type,
                    times_played=data["played"],
                    times_won=data["won"],
                    average_profit=sum(profits) / len(profits),
                    best_profit=max(profits),
                    worst_loss=min(profits)
                ))
        
        return sorted(results, key=lambda x: x.times_played, reverse=True)
    
    def _classify_starting_hand(self, hole_cards: List[str]) -> str:
        """分类起手牌"""
        if len(hole_cards) != 2:
            return "unknown"
        
        # 简化的手牌分类
        try:
            card1, card2 = hole_cards
            rank1 = card1[0]
            rank2 = card2[0]
            suit1 = card1[1]
            suit2 = card2[1]
            
            # 将牌面值转换为数字便于比较
            rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                          '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
            
            val1 = rank_values.get(rank1, 0)
            val2 = rank_values.get(rank2, 0)
            
            # 确保大牌在前
            if val1 < val2:
                val1, val2 = val2, val1
                rank1, rank2 = rank2, rank1
            
            suited = suit1 == suit2
            
            # 对子
            if val1 == val2:
                if val1 >= 10:
                    return "高对 (TT+)"
                elif val1 >= 7:
                    return "中对 (77-99)"
                else:
                    return "小对 (22-66)"
            
            # 高牌组合
            if val1 == 14:  # A
                if val2 >= 10:
                    return f"A高强牌 (A{rank2}{'s' if suited else 'o'})"
                else:
                    return f"A高弱牌 (A{rank2}{'s' if suited else 'o'})"
            elif val1 >= 10:
                return f"Broadway (K{rank2}+)"
            else:
                return "弱牌组合"
                
        except:
            return "unknown"
    
    def generate_leak_analysis(self, player_name: str) -> Dict[str, Any]:
        """生成漏洞分析"""
        recent_hands = []
        for hand in self.stats_data.get("hand_history", []):
            if hand.get("player_name") == player_name:
                recent_hands.append(hand)
        
        if len(recent_hands) < 20:
            return {"error": "需要至少20手牌数据进行分析"}
        
        # 分析各种潜在漏洞
        total_hands = len(recent_hands)
        total_profit = sum(h["profit_loss"] for h in recent_hands)
        
        leaks = []
        
        # 位置漏洞分析
        position_stats = self.analyze_positional_play(player_name)
        early_pos_loss = sum(p.profit_loss for p in position_stats if 'early' in p.position.lower())
        if early_pos_loss < -100:
            leaks.append({
                "type": "位置漏洞",
                "description": "前位置亏损严重，建议收紧手牌选择",
                "severity": "高",
                "suggestion": "在前位置只玩最强的20%手牌"
            })
        
        # VPIP过高/过低
        avg_vpip = sum(p.vpip for p in position_stats) / len(position_stats) if position_stats else 0
        if avg_vpip > 35:
            leaks.append({
                "type": "入局率过高",
                "description": f"VPIP {avg_vpip:.1f}% 过高，容易陷入困难境地",
                "severity": "中",
                "suggestion": "收紧手牌选择，目标VPIP 20-25%"
            })
        elif avg_vpip < 15:
            leaks.append({
                "type": "过于紧手",
                "description": f"VPIP {avg_vpip:.1f}% 过低，错失盈利机会",
                "severity": "中",
                "suggestion": "适当放宽手牌标准，特别是后位置"
            })
        
        # 盈利能力分析
        bb_per_100 = self.calculate_bb_per_100(total_profit, total_hands, 10)  # 假设10大盲
        if bb_per_100 < -5:
            leaks.append({
                "type": "整体亏损",
                "description": f"每100手亏损 {abs(bb_per_100):.1f} 大盲注",
                "severity": "高",
                "suggestion": "需要全面检视策略，考虑降低难度"
            })
        
        return {
            "total_hands_analyzed": total_hands,
            "overall_profit": total_profit,
            "bb_per_100_hands": bb_per_100,
            "leaks_found": len(leaks),
            "leak_details": leaks,
            "overall_rating": self._calculate_skill_rating(bb_per_100, avg_vpip)
        }
    
    def _calculate_skill_rating(self, bb_per_100: float, vpip: float) -> str:
        """计算技能评级"""
        if bb_per_100 > 5:
            return "🚀 专家级 (Excellent)"
        elif bb_per_100 > 2:
            return "🏆 高级 (Advanced)"
        elif bb_per_100 > -2:
            return "🎯 中级 (Intermediate)"
        elif bb_per_100 > -5:
            return "🎓 初级 (Beginner)"
        else:
            return "📚 新手 (Novice)"
    
    def export_detailed_report(self, player_name: str, filename: str) -> bool:
        """导出详细分析报告"""
        try:
            report = {
                "player_name": player_name,
                "report_date": datetime.now().isoformat(),
                "recent_performance": self.get_recent_performance(player_name, 30),
                "positional_analysis": [asdict(p) for p in self.analyze_positional_play(player_name)],
                "hand_selection": [asdict(h) for h in self.analyze_hand_selection(player_name)],
                "leak_analysis": self.generate_leak_analysis(player_name)
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False


# 全局分析器实例
advanced_analytics = AdvancedAnalytics()


def asdict(obj):
    """简单的dataclass转字典函数"""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return obj
