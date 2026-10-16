#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
玩家风格分析系统
分析玩家的游戏风格，包括紧凶、松凶、跟注站等
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
import os


class PlayerStyle(Enum):
    """玩家风格类型"""
    
    # 紧手风格
    NITT = ("nitt", "超紧手", "🪨", "只玩最强的牌，极少下注和加注")
    ROCK = ("rock", "石头玩家", "🗿", "非常保守，只玩强牌，很少诈唬")
    
    # 紧凶风格  
    TAG = ("tag", "紧凶", "🎯", "选择性强，但一旦参与就积极下注")
    TIGHT_PASSIVE = ("tight_passive", "紧弱", "🐌", "谨慎选牌，但缺乏攻击性")
    
    # 松手风格
    LAG = ("lag", "松凶", "🔥", "参与很多手牌，极具攻击性")
    LOOSE_PASSIVE = ("loose_passive", "松弱", "🐟", "参与很多手牌，但很少主动下注")
    CALLING_STATION = ("calling_station", "跟注站", "📞", "很少弃牌，总是跟注到底")
    
    # 特殊风格
    MANIAC = ("maniac", "疯子", "🤪", "极度疯狂，频繁下注加注，难以预测")
    FISH = ("fish", "鱼", "🐠", "新手玩家，决策不合理，容易被利用")
    SHARK = ("shark", "鲨鱼", "🦈", "高手玩家，能够适应不同情况")
    BALANCED = ("balanced", "平衡", "⚖️", "各方面都比较均衡的玩家")
    
    def __init__(self, code, display_name, emoji, description):
        self.code = code
        self.display_name = display_name
        self.emoji = emoji
        self.description = description


@dataclass
class PlayerStats:
    """玩家统计数据"""
    hands_played: int = 0           # 参与的手牌数
    vpip: float = 0.0              # 自愿投入彩池率 (Voluntary Put In Pot)
    pfr: float = 0.0               # 翻牌前加注率 (Pre-Flop Raise)
    aggression_factor: float = 0.0  # 攻击性系数 (bet+raise)/(call)
    fold_to_bet: float = 0.0       # 面对下注时的弃牌率
    cbet: float = 0.0              # 持续下注率 (Continuation Bet)
    
    # 位置统计
    early_position_vpip: float = 0.0
    late_position_vpip: float = 0.0
    
    # 下注模式
    total_bets: int = 0
    total_raises: int = 0
    total_calls: int = 0
    total_folds: int = 0
    total_checks: int = 0
    
    # 摊牌表现
    showdowns_won: int = 0
    showdowns_total: int = 0
    
    def calculate_derived_stats(self):
        """计算衍生统计数据"""
        if self.hands_played > 0:
            self.vpip = (self.total_calls + self.total_bets + self.total_raises) / self.hands_played * 100
            self.pfr = self.total_raises / self.hands_played * 100
            
        if self.total_calls > 0:
            self.aggression_factor = (self.total_bets + self.total_raises) / self.total_calls
        
        total_actions = self.total_bets + self.total_raises + self.total_calls + self.total_folds + self.total_checks
        if total_actions > 0:
            self.fold_to_bet = self.total_folds / total_actions * 100


class PlayerStyleAnalyzer:
    """玩家风格分析器"""
    
    def __init__(self):
        self.player_stats: Dict[str, PlayerStats] = {}
        self.style_cache: Dict[str, PlayerStyle] = {}
        self.stats_file = "player_stats.json"
        self.load_stats()
    
    def load_stats(self):
        """加载玩家统计数据"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for player_name, stats_dict in data.items():
                        stats = PlayerStats()
                        for key, value in stats_dict.items():
                            if hasattr(stats, key):
                                setattr(stats, key, value)
                        stats.calculate_derived_stats()
                        self.player_stats[player_name] = stats
            except Exception as e:
                print(f"加载玩家统计数据失败: {e}")
    
    def save_stats(self):
        """保存玩家统计数据"""
        try:
            data = {}
            for player_name, stats in self.player_stats.items():
                data[player_name] = {
                    'hands_played': stats.hands_played,
                    'total_bets': stats.total_bets,
                    'total_raises': stats.total_raises,
                    'total_calls': stats.total_calls,
                    'total_folds': stats.total_folds,
                    'total_checks': stats.total_checks,
                    'showdowns_won': stats.showdowns_won,
                    'showdowns_total': stats.showdowns_total,
                }
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存玩家统计数据失败: {e}")
    
    def update_player_action(self, player_name: str, action: str, amount: int = 0):
        """更新玩家动作统计"""
        if player_name not in self.player_stats:
            self.player_stats[player_name] = PlayerStats()
        
        stats = self.player_stats[player_name]
        
        if action == "fold":
            stats.total_folds += 1
        elif action == "check":
            stats.total_checks += 1
        elif action == "call":
            stats.total_calls += 1
        elif action == "bet":
            stats.total_bets += 1
        elif action == "raise":
            stats.total_raises += 1
        
        # 清除风格缓存，需要重新计算
        if player_name in self.style_cache:
            del self.style_cache[player_name]
    
    def update_hand_participation(self, player_name: str, participated: bool):
        """更新手牌参与统计"""
        if player_name not in self.player_stats:
            self.player_stats[player_name] = PlayerStats()
        
        stats = self.player_stats[player_name]
        stats.hands_played += 1
        stats.calculate_derived_stats()
    
    def update_showdown(self, player_name: str, won: bool):
        """更新摊牌统计"""
        if player_name not in self.player_stats:
            self.player_stats[player_name] = PlayerStats()
        
        stats = self.player_stats[player_name]
        stats.showdowns_total += 1
        if won:
            stats.showdowns_won += 1
    
    def analyze_player_style(self, player_name: str) -> PlayerStyle:
        """分析玩家风格"""
        if player_name in self.style_cache:
            return self.style_cache[player_name]
        
        if player_name not in self.player_stats:
            return PlayerStyle.BALANCED  # 默认风格
        
        stats = self.player_stats[player_name]
        
        # 如果数据不足，返回默认风格
        if stats.hands_played < 10:
            return PlayerStyle.BALANCED
        
        stats.calculate_derived_stats()
        
        # 根据VPIP和PFR分析风格
        vpip = stats.vpip
        pfr = stats.pfr
        aggression = stats.aggression_factor
        
        style = self._classify_style(vpip, pfr, aggression, stats)
        self.style_cache[player_name] = style
        return style
    
    def _classify_style(self, vpip: float, pfr: float, aggression: float, stats: PlayerStats) -> PlayerStyle:
        """根据统计数据分类玩家风格"""
        
        # 疯子: 极高的VPIP和攻击性
        if vpip > 70 and aggression > 4:
            return PlayerStyle.MANIAC
        
        # 超紧手: 极低的VPIP
        if vpip < 10:
            return PlayerStyle.NITT
        
        # 石头玩家: 很低的VPIP，但有一定攻击性
        if vpip < 15 and pfr < 8 and aggression < 1.5:
            return PlayerStyle.ROCK
        
        # 跟注站: 高VPIP，低攻击性，低弃牌率
        if vpip > 40 and aggression < 1.0 and stats.fold_to_bet < 30:
            return PlayerStyle.CALLING_STATION
        
        # 鱼: 高VPIP，混乱的PFR，低攻击性
        if vpip > 50 and abs(vpip - pfr) > 30 and aggression < 1.5:
            return PlayerStyle.FISH
        
        # 松凶 (LAG): 高VPIP，高PFR，高攻击性
        if vpip > 30 and pfr > 20 and aggression > 2.5:
            return PlayerStyle.LAG
        
        # 紧凶 (TAG): 适中VPIP，适中PFR，高攻击性
        if 15 <= vpip <= 30 and 10 <= pfr <= 25 and aggression > 2.0:
            return PlayerStyle.TAG
        
        # 松弱: 高VPIP，低攻击性
        if vpip > 35 and aggression < 1.5:
            return PlayerStyle.LOOSE_PASSIVE
        
        # 紧弱: 低VPIP，低攻击性
        if vpip < 20 and aggression < 1.5:
            return PlayerStyle.TIGHT_PASSIVE
        
        # 鲨鱼: 均衡的数据，高胜率
        if stats.showdowns_total > 5:
            win_rate = stats.showdowns_won / stats.showdowns_total
            if win_rate > 0.6 and 20 <= vpip <= 35 and 1.5 <= aggression <= 3.0:
                return PlayerStyle.SHARK
        
        # 默认为平衡风格
        return PlayerStyle.BALANCED
    
    def get_player_stats_summary(self, player_name: str) -> str:
        """获取玩家统计摘要"""
        if player_name not in self.player_stats:
            return "暂无数据"
        
        stats = self.player_stats[player_name]
        style = self.analyze_player_style(player_name)
        
        summary = f"{style.emoji} {style.display_name}\n"
        summary += f"参与手牌: {stats.hands_played}\n"
        if stats.hands_played > 0:
            summary += f"VPIP: {stats.vpip:.1f}%\n"
            summary += f"PFR: {stats.pfr:.1f}%\n"
            summary += f"攻击性: {stats.aggression_factor:.1f}\n"
            
            if stats.showdowns_total > 0:
                win_rate = stats.showdowns_won / stats.showdowns_total * 100
                summary += f"摊牌胜率: {win_rate:.1f}%"
        
        return summary
    
    def get_style_description(self, player_name: str) -> str:
        """获取风格描述"""
        style = self.analyze_player_style(player_name)
        return f"{style.emoji} {style.display_name}: {style.description}"


# 全局实例
player_style_analyzer = PlayerStyleAnalyzer()
