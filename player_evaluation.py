#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
玩家风格评测系统
基于最近50局游戏数据分析玩家风格分布
"""

import json
from dataclasses import asdict
from typing import Dict, List, Tuple
from collections import defaultdict
from player_styles import PlayerStyle, player_style_analyzer
from game_history import GameHistoryManager


class PlayerEvaluationSystem:
    """玩家评测系统"""
    
    def __init__(self):
        self.evaluation_file = "player_evaluation.json"
        self.min_games_for_evaluation = 10  # 最少需要10局才能评测
        self._last_analyzed_count = 0
        
    def analyze_player_style_distribution(self, player_name: str, recent_games: int = 50) -> Dict[str, float]:
        """
        分析玩家在最近N局中的风格分布
        
        Args:
            player_name: 玩家名称
            recent_games: 分析最近多少局游戏
            
        Returns:
            Dict[str, float]: 风格名称 -> 百分比
        """
        self._last_analyzed_count = 0
        records = GameHistoryManager().list_recent_games(limit=100000)
        player_games = [asdict(record) for record in records
                        if player_name in record.players][:recent_games]
        
        if len(player_games) < self.min_games_for_evaluation:
            return {}
        self._last_analyzed_count = len(player_games)
        
        # 分析每局游戏中的玩家风格
        style_counts = defaultdict(int)
        total_games = len(player_games)
        
        for game_data in player_games:
            # 基于每局的统计数据判断风格
            style = self._analyze_game_style(player_name, game_data)
            if style:
                style_counts[style.display_name] += 1
        
        # 计算百分比
        style_distribution = {}
        for style_name, count in style_counts.items():
            percentage = (count / total_games) * 100
            style_distribution[style_name] = round(percentage, 1)
        
        return style_distribution
    
    def _analyze_game_style(self, player_name: str, game_data: Dict) -> PlayerStyle:
        """
        分析单局游戏中玩家的风格
        
        Args:
            player_name: 玩家名称
            game_data: 游戏数据
            
        Returns:
            PlayerStyle: 该局游戏体现的风格
        """
        # 统计该局游戏中玩家的行为
        total_actions = 0
        aggressive_actions = 0  # raise, bet
        passive_actions = 0     # call, check
        fold_actions = 0
        participated_phases = 0
        
        for phase in game_data.get("phases", []):
            player_acted_in_phase = False
            for action in phase.get("actions", []):
                if action.get("player_name") == player_name:
                    total_actions += 1
                    player_acted_in_phase = True
                    
                    action_type = action.get("action")
                    if action_type in ["raise", "bet"]:
                        aggressive_actions += 1
                    elif action_type in ["call", "check"]:
                        passive_actions += 1
                    elif action_type == "fold":
                        fold_actions += 1
                        break  # 弃牌后不再统计该阶段
            
            if player_acted_in_phase:
                participated_phases += 1
        
        if total_actions == 0:
            return None
        
        # 计算指标
        vpip = participated_phases / len(game_data.get("phases", [1])) * 100
        aggression_rate = aggressive_actions / max(total_actions, 1) * 100
        fold_rate = fold_actions / max(total_actions, 1) * 100
        
        # 根据行为模式判断风格
        if fold_rate > 70:
            return PlayerStyle.ROCK
        elif vpip < 20 and aggression_rate > 60:
            return PlayerStyle.TAG
        elif vpip > 60 and aggression_rate > 60:
            return PlayerStyle.LAG
        elif vpip > 60 and aggression_rate < 30:
            return PlayerStyle.CALLING_STATION
        elif aggression_rate > 80:
            return PlayerStyle.MANIAC
        elif vpip < 30 and aggression_rate < 30:
            return PlayerStyle.NIT
        elif 40 <= aggression_rate <= 60:
            return PlayerStyle.BALANCED
        else:
            return PlayerStyle.FISH
    
    def evaluate_player_style(self, player_name: str) -> Dict:
        """兼容主菜单调用的玩家风格评测入口。"""
        return self.get_comprehensive_evaluation(player_name)

    def get_comprehensive_evaluation(self, player_name: str) -> Dict:
        """
        获取玩家的综合评测报告
        
        Args:
            player_name: 玩家名称
            
        Returns:
            Dict: 包含风格分布、统计数据、建议等的综合报告
        """
        # 获取风格分布
        style_distribution = self.analyze_player_style_distribution(player_name)
        
        if not style_distribution:
            return {
                "error": "数据不足",
                "message": f"需要至少{self.min_games_for_evaluation}局游戏数据才能进行评测"
            }
        
        # 获取当前统计数据
        stored_stats = player_style_analyzer.player_stats.get(player_name)
        current_stats = asdict(stored_stats) if stored_stats else {}
        current_style = player_style_analyzer.analyze_player_style(player_name)
        
        # 找出主要风格（占比最高的）
        primary_style = max(style_distribution.items(), key=lambda x: x[1])
        secondary_styles = sorted(style_distribution.items(), key=lambda x: x[1], reverse=True)[1:3]
        
        # 生成建议
        suggestions = self._generate_suggestions(style_distribution, current_stats)
        
        return {
            "player_name": player_name,
            "games_analyzed": self._last_analyzed_count,
            "primary_style": {
                "name": primary_style[0],
                "percentage": primary_style[1]
            },
            "style_distribution": style_distribution,
            "secondary_styles": [{"name": name, "percentage": pct} for name, pct in secondary_styles if pct > 5],
            "current_stats": current_stats,
            "current_style": {
                "name": current_style.display_name,
                "description": current_style.description
            },
            "suggestions": suggestions
        }
    
    def _generate_suggestions(self, style_distribution: Dict[str, float], current_stats: Dict) -> List[str]:
        """
        根据风格分布生成改进建议
        
        Args:
            style_distribution: 风格分布
            current_stats: 当前统计数据
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        # 分析主要问题
        total_games = sum(style_distribution.values()) / 100  # 估算总局数
        
        if style_distribution.get("超紧手", 0) > 40:
            suggestions.append("🎯 你过于保守，可以尝试参与更多牌局，特别是位置好的时候")
        
        if style_distribution.get("跟注站", 0) > 30:
            suggestions.append("💪 建议增加主动性，多使用加注而不是被动跟注")
        
        if style_distribution.get("疯子", 0) > 20:
            suggestions.append("🛑 控制冲动，减少无意义的激进行为，提高下注的选择性")
        
        if style_distribution.get("鱼", 0) > 30:
            suggestions.append("📚 建议学习基础策略，提高手牌选择和位置意识")
        
        # 基于统计数据的建议
        vpip = current_stats.get("vpip", 0)
        if vpip < 15:
            suggestions.append("🔄 VPIP过低，可以适当放宽入局标准")
        elif vpip > 40:
            suggestions.append("🎯 VPIP过高，建议收紧手牌选择")
        
        pfr = current_stats.get("pfr", 0)
        if pfr < vpip * 0.5:
            suggestions.append("⚡ 提高翻牌前主动性，增加加注频率")
        
        # 正面鼓励
        if style_distribution.get("紧凶", 0) > 30:
            suggestions.append("✅ 紧凶风格很好，继续保持选择性和侵略性的平衡")
        
        if style_distribution.get("平衡", 0) > 25:
            suggestions.append("✅ 风格平衡，这是高手的标志，继续保持")
        
        return suggestions
    
    def save_evaluation(self, player_name: str, evaluation: Dict):
        """保存评测结果"""
        try:
            # 加载现有数据
            try:
                with open(self.evaluation_file, "r", encoding="utf-8") as f:
                    evaluations = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                evaluations = {}
            
            # 添加时间戳
            from datetime import datetime
            evaluation["timestamp"] = datetime.now().isoformat()
            
            # 保存评测结果
            evaluations[player_name] = evaluation
            
            with open(self.evaluation_file, "w", encoding="utf-8") as f:
                json.dump(evaluations, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存评测结果失败: {e}")
    
    def format_evaluation_report(self, evaluation: Dict) -> str:
        """格式化评测报告为可读文本"""
        if "error" in evaluation:
            return f"❌ {evaluation['error']}: {evaluation['message']}"
        
        player_name = evaluation["player_name"]
        primary_style = evaluation["primary_style"]
        style_dist = evaluation["style_distribution"]
        suggestions = evaluation["suggestions"]
        
        report = []
        report.append(f"🎮 {player_name} 的德州扑克风格评测报告")
        report.append("=" * 60)
        
        report.append(f"\n📊 主要风格: {primary_style['name']} ({primary_style['percentage']}%)")
        
        report.append(f"\n📈 风格分布（基于最近游戏）:")
        for style_name, percentage in sorted(style_dist.items(), key=lambda x: x[1], reverse=True):
            if percentage > 0:
                bar_length = int(percentage / 5)  # 每5%一个字符
                bar = "█" * bar_length + "░" * (20 - bar_length)
                report.append(f"  {style_name:12} │{bar}│ {percentage:5.1f}%")
        
        if evaluation.get("secondary_styles"):
            report.append(f"\n🔄 次要风格:")
            for style in evaluation["secondary_styles"]:
                report.append(f"  • {style['name']}: {style['percentage']}%")
        
        report.append(f"\n💡 改进建议:")
        for i, suggestion in enumerate(suggestions, 1):
            report.append(f"  {i}. {suggestion}")
        
        current_style = evaluation["current_style"]
        report.append(f"\n🎯 当前主要风格: {current_style['name']}")
        report.append(f"   📝 {current_style['description']}")
        
        return "\n".join(report)


# 全局实例
player_evaluation_system = PlayerEvaluationSystem()
