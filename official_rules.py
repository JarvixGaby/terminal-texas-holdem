#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克正式比赛规则系统
Official Texas Hold'em Tournament Rules Implementation
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum
import time


class GameVariant(Enum):
    """游戏变种"""
    NO_LIMIT = "no_limit"          # 无限注
    POT_LIMIT = "pot_limit"        # 底池限注
    FIXED_LIMIT = "fixed_limit"    # 限注


class ActionType(Enum):
    """动作类型"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass
class SidePot:
    """边池"""
    amount: int
    eligible_players: List[str]  # 有资格赢得此边池的玩家
    all_in_player: str  # 触发此边池的全押玩家


@dataclass
class BettingAction:
    """下注动作记录"""
    player_name: str
    action: ActionType
    amount: int
    total_investment: int  # 该玩家在当前手牌中的总投入
    timestamp: float


class OfficialRulesEngine:
    """正式规则引擎"""
    
    def __init__(self, variant: GameVariant = GameVariant.NO_LIMIT):
        self.variant = variant
        self.side_pots: List[SidePot] = []
        self.main_pot = 0
        self.action_history: List[BettingAction] = []
        self.action_timeout = 30.0  # 行动时间限制（秒）
        
    def validate_action(self, player_name: str, action: ActionType, amount: int, 
                       player_chips: int, current_bet: int, pot_size: int,
                       min_raise: int) -> Tuple[bool, str, int]:
        """
        验证玩家动作的合法性
        
        Returns:
            (is_valid, error_message, corrected_amount)
        """
        
        if action == ActionType.FOLD:
            return True, "", 0
            
        elif action == ActionType.CHECK:
            if current_bet > 0:
                return False, "有下注时不能过牌，请选择跟注、加注或弃牌", 0
            return True, "", 0
            
        elif action == ActionType.CALL:
            if current_bet == 0:
                return False, "没有下注时不能跟注，请选择过牌或下注", 0
            
            call_amount = min(current_bet, player_chips)
            return True, "", call_amount
            
        elif action == ActionType.BET:
            if current_bet > 0:
                return False, "已有下注时不能下注，请选择跟注、加注或弃牌", 0
            
            if self.variant == GameVariant.NO_LIMIT:
                if amount < min_raise or amount > player_chips:
                    return False, f"下注金额必须在 {min_raise}-{player_chips} 之间", 0
                    
            elif self.variant == GameVariant.POT_LIMIT:
                max_bet = pot_size
                if amount < min_raise or amount > min(max_bet, player_chips):
                    return False, f"下注金额必须在 {min_raise}-{min(max_bet, player_chips)} 之间", 0
                    
            elif self.variant == GameVariant.FIXED_LIMIT:
                if amount != min_raise:
                    return True, "", min_raise  # 自动修正为固定金额
                    
            return True, "", amount
            
        elif action == ActionType.RAISE:
            if current_bet == 0:
                return False, "没有下注时不能加注，请选择过牌或下注", 0
            
            total_amount = amount  # amount是总的下注额
            
            if self.variant == GameVariant.NO_LIMIT:
                min_total = current_bet + min_raise
                if total_amount < min_total or total_amount > player_chips:
                    return False, f"加注总额必须在 {min_total}-{player_chips} 之间", 0
                    
            elif self.variant == GameVariant.POT_LIMIT:
                max_raise = current_bet + pot_size + current_bet  # 可以加注到底池+跟注的金额
                min_total = current_bet + min_raise
                max_total = min(max_raise, player_chips)
                if total_amount < min_total or total_amount > max_total:
                    return False, f"加注总额必须在 {min_total}-{max_total} 之间", 0
                    
            elif self.variant == GameVariant.FIXED_LIMIT:
                correct_amount = current_bet + min_raise
                if total_amount != correct_amount:
                    return True, "", correct_amount  # 自动修正
                    
            return True, "", total_amount
            
        return False, "无效的动作类型", 0
    
    def calculate_side_pots(self, players_investments: Dict[str, int], 
                           folded_players: List[str]) -> Tuple[int, List[SidePot]]:
        """
        计算边池分配
        
        Args:
            players_investments: {player_name: total_investment}
            folded_players: 已弃牌的玩家列表
            
        Returns:
            (main_pot_amount, side_pots_list)
        """
        
        # 获取所有参与的玩家和投资额
        active_investments = {name: amount for name, amount in players_investments.items() 
                            if name not in folded_players and amount > 0}
        
        if len(active_investments) <= 1:
            total_pot = sum(players_investments.values())
            return total_pot, []
        
        # 按投资额排序
        sorted_investments = sorted(active_investments.items(), key=lambda x: x[1])
        
        side_pots = []
        remaining_players = list(active_investments.keys())
        
        for i, (player, investment) in enumerate(sorted_investments[:-1]):
            current_level = investment
            next_level = sorted_investments[i + 1][1]
            
            if current_level < next_level:
                # 创建边池
                pot_per_player = current_level
                side_pot_amount = pot_per_player * len(remaining_players)
                
                side_pot = SidePot(
                    amount=side_pot_amount,
                    eligible_players=remaining_players.copy(),
                    all_in_player=player
                )
                side_pots.append(side_pot)
                
                # 减少剩余投资并移除全押玩家
                remaining_players.remove(player)
                for j in range(i + 1, len(sorted_investments)):
                    sorted_investments[j] = (
                        sorted_investments[j][0],
                        sorted_investments[j][1] - current_level
                    )
        
        # 主池（最后剩余的金额）
        if remaining_players:
            final_investment = sorted_investments[-1][1]
            main_pot_amount = final_investment * len(remaining_players)
        else:
            main_pot_amount = 0
            
        return main_pot_amount, side_pots
    
    def get_pot_odds(self, call_amount: int, pot_size: int) -> Tuple[float, str]:
        """
        计算底池赔率
        
        Returns:
            (odds_ratio, odds_description)
        """
        if call_amount <= 0:
            return 0.0, "无需跟注"
            
        total_pot_after_call = pot_size + call_amount
        odds_ratio = call_amount / total_pot_after_call
        
        # 转换为常见的赔率表示
        if odds_ratio <= 0.1:
            odds_desc = "优秀赔率 (>9:1)"
        elif odds_ratio <= 0.2:
            odds_desc = "良好赔率 (4:1-9:1)"
        elif odds_ratio <= 0.33:
            odds_desc = "一般赔率 (2:1-4:1)"
        elif odds_ratio <= 0.5:
            odds_desc = "较差赔率 (1:1-2:1)"
        else:
            odds_desc = "不利赔率 (<1:1)"
            
        return odds_ratio, odds_desc
    
    def validate_string_betting(self, action_string: str) -> Tuple[bool, str]:
        """
        检查字符串下注规则
        在真实比赛中，玩家不能说"我跟注你的100，然后再加注到200"
        必须一次性声明完整动作
        """
        
        # 检查是否包含多个动作词
        action_words = ['跟注', '加注', '下注', 'call', 'raise', 'bet']
        found_actions = [word for word in action_words if word in action_string.lower()]
        
        if len(found_actions) > 1:
            return False, "字符串下注违规：不能在同一动作中声明多个下注行为"
        
        return True, ""
    
    def check_action_timeout(self, action_start_time: float) -> bool:
        """检查动作是否超时"""
        elapsed = time.time() - action_start_time
        return elapsed > self.action_timeout
    
    def get_betting_limits(self, variant: GameVariant, pot_size: int, 
                          current_bet: int, big_blind: int) -> Dict[str, int]:
        """
        获取不同变种的下注限制
        """
        
        if variant == GameVariant.NO_LIMIT:
            return {
                "min_bet": big_blind,
                "min_raise": big_blind,
                "max_bet": float('inf'),
                "max_raise": float('inf')
            }
            
        elif variant == GameVariant.POT_LIMIT:
            max_bet = pot_size
            max_raise = pot_size + current_bet + current_bet  # 底池 + 跟注 + 跟注
            return {
                "min_bet": big_blind,
                "min_raise": big_blind,
                "max_bet": max_bet,
                "max_raise": max_raise
            }
            
        elif variant == GameVariant.FIXED_LIMIT:
            return {
                "min_bet": big_blind,
                "min_raise": big_blind,
                "max_bet": big_blind,
                "max_raise": big_blind
            }
            
        return {}


class TournamentRules:
    """锦标赛规则"""
    
    def __init__(self):
        self.blind_levels = []
        self.current_level = 0
        self.level_duration = 15 * 60  # 15分钟
        self.ante_levels = {}  # {level: ante_amount}
        
    def setup_standard_structure(self):
        """设置标准锦标赛盲注结构"""
        self.blind_levels = [
            (10, 20),      # Level 1
            (15, 30),      # Level 2
            (25, 50),      # Level 3
            (50, 100),     # Level 4
            (75, 150),     # Level 5
            (100, 200),    # Level 6
            (150, 300),    # Level 7
            (200, 400),    # Level 8
            (300, 600),    # Level 9
            (400, 800),    # Level 10
            (500, 1000),   # Level 11
            (750, 1500),   # Level 12
            (1000, 2000),  # Level 13
            (1500, 3000),  # Level 14
            (2000, 4000),  # Level 15
        ]
        
        # 从Level 4开始有前注
        self.ante_levels = {
            4: 25, 5: 25, 6: 25, 7: 50, 8: 50, 9: 75, 10: 100,
            11: 100, 12: 150, 13: 200, 14: 300, 15: 400
        }
    
    def get_current_blinds(self) -> Tuple[int, int, int]:
        """
        获取当前盲注
        
        Returns:
            (small_blind, big_blind, ante)
        """
        if self.current_level < len(self.blind_levels):
            sb, bb = self.blind_levels[self.current_level]
            ante = self.ante_levels.get(self.current_level + 1, 0)
            return sb, bb, ante
        else:
            # 最高级别
            sb, bb = self.blind_levels[-1]
            ante = self.ante_levels.get(len(self.blind_levels), 0)
            return sb, bb, ante
    
    def advance_blinds(self):
        """推进到下一盲注级别"""
        if self.current_level < len(self.blind_levels) - 1:
            self.current_level += 1
            return True
        return False
    
    def calculate_payout_structure(self, buy_in: int, num_players: int) -> Dict[int, int]:
        """
        计算奖励结构
        
        Args:
            buy_in: 买入费用
            num_players: 参赛人数
            
        Returns:
            {position: payout_amount}
        """
        total_prize_pool = buy_in * num_players
        
        if num_players <= 10:
            # 小型锦标赛 - 前3名有奖励
            return {
                1: int(total_prize_pool * 0.50),  # 冠军50%
                2: int(total_prize_pool * 0.30),  # 亚军30%
                3: int(total_prize_pool * 0.20),  # 季军20%
            }
        elif num_players <= 50:
            # 中型锦标赛 - 前6名有奖励
            return {
                1: int(total_prize_pool * 0.40),  # 40%
                2: int(total_prize_pool * 0.25),  # 25%
                3: int(total_prize_pool * 0.15),  # 15%
                4: int(total_prize_pool * 0.10),  # 10%
                5: int(total_prize_pool * 0.06),  # 6%
                6: int(total_prize_pool * 0.04),  # 4%
            }
        else:
            # 大型锦标赛 - 前10名有奖励
            return {
                1: int(total_prize_pool * 0.35),  # 35%
                2: int(total_prize_pool * 0.20),  # 20%
                3: int(total_prize_pool * 0.13),  # 13%
                4: int(total_prize_pool * 0.10),  # 10%
                5: int(total_prize_pool * 0.08),  # 8%
                6: int(total_prize_pool * 0.06),  # 6%
                7: int(total_prize_pool * 0.04),  # 4%
                8: int(total_prize_pool * 0.02),  # 2%
                9: int(total_prize_pool * 0.01),  # 1%
                10: int(total_prize_pool * 0.01), # 1%
            }


# 全局规则引擎实例
official_rules_engine = OfficialRulesEngine()
tournament_rules = TournamentRules()
