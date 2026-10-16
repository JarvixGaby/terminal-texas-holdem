#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能AI决策系统
实现差异化风格、手牌感知、位置策略、诈唬、学习等功能
"""

import random
import json
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from card import Card, Rank
from hand_evaluator import HandEvaluator
from player_styles import PlayerStyle


class AISkillLevel(Enum):
    """AI技能等级"""
    BEGINNER = "beginner"      # 新手：基础策略，容易读懂
    INTERMEDIATE = "intermediate"  # 中级：较好策略，适度混合
    ADVANCED = "advanced"      # 高级：复杂策略，难以预测
    EXPERT = "expert"          # 专家：接近最优策略，极难对付


@dataclass
class HandStrength:
    """手牌强度评估"""
    raw_strength: float     # 原始强度 (0-1)
    relative_strength: float  # 相对强度 (考虑公共牌)
    potential: float        # 改进潜力
    category: str          # 手牌类别


@dataclass
class OpponentModel:
    """对手模型"""
    vpip: float = 25.0          # 入局率
    pfr: float = 15.0           # 翻牌前加注率
    aggression: float = 1.5     # 侵略因子
    fold_to_cbet: float = 65.0  # 对持续下注的弃牌率
    three_bet: float = 5.0      # 3bet频率
    recent_actions: List[str] = None
    
    def __post_init__(self):
        if self.recent_actions is None:
            self.recent_actions = []


class SmartAIDecisionEngine:
    """智能AI决策引擎"""
    
    def __init__(self, player_name: str, skill_level: AISkillLevel = AISkillLevel.INTERMEDIATE):
        self.player_name = player_name
        self.skill_level = skill_level
        
        # 当前局的风格（每局随机分配）
        self.current_style: Optional[PlayerStyle] = None
        
        # 对手建模
        self.opponent_models: Dict[str, OpponentModel] = {}
        
        # 学习数据
        self.game_memory: List[Dict] = []
        
        # 位置映射
        self.position_names = {
            0: "UTG",      # Under the Gun
            1: "MP",       # Middle Position  
            2: "CO",       # Cut Off
            3: "BTN",      # Button
            4: "SB",       # Small Blind
            5: "BB"        # Big Blind
        }
        
    def assign_random_style(self):
        """为新局随机分配风格"""
        styles = list(PlayerStyle)
        
        # 确保权重数量与风格数量匹配
        num_styles = len(styles)
        
        # 根据技能等级调整风格分布 - 权重对应: NITT, ROCK, TAG, TIGHT_PASSIVE, LAG, LOOSE_PASSIVE, CALLING_STATION, MANIAC, FISH, SHARK, BALANCED
        if self.skill_level == AISkillLevel.BEGINNER:
            # 新手更倾向于简单风格，增加多样性
            weights = [8, 12, 12, 10, 8, 12, 8, 5, 10, 5, 10]
        elif self.skill_level == AISkillLevel.INTERMEDIATE:
            # 中级平衡分布，确保所有风格都有合理出现概率
            weights = [8, 10, 15, 8, 12, 10, 8, 8, 6, 8, 7]
        elif self.skill_level == AISkillLevel.ADVANCED:
            # 高级更多复杂风格，但保持多样性
            weights = [5, 8, 18, 5, 15, 8, 10, 10, 3, 12, 6]
        else:  # EXPERT
            # 专家主要使用高级风格，但仍有多样性
            weights = [3, 5, 20, 3, 18, 5, 8, 12, 2, 15, 9]
        
        # 确保权重数量正确
        if len(weights) != num_styles:
            # 如果不匹配，使用均匀分布
            weights = [1] * num_styles
            
        self.current_style = random.choices(styles, weights=weights, k=1)[0]
        # 风格只在复盘中显示，游戏进行时不显示
    
    def evaluate_hand_strength(self, hole_cards: List[Card], community_cards: List[Card] = None) -> HandStrength:
        """评估手牌强度"""
        if community_cards is None:
            community_cards = []
            
        # 翻牌前手牌强度表
        preflop_strength = self._get_preflop_strength(hole_cards)
        
        if not community_cards:
            return HandStrength(
                raw_strength=preflop_strength,
                relative_strength=preflop_strength,
                potential=self._calculate_potential(hole_cards),
                category=self._categorize_hand(hole_cards)
            )
        
        # 翻牌后评估
        all_cards = hole_cards + community_cards
        if len(all_cards) >= 5:
            try:
                hand_rank, _ = HandEvaluator.evaluate_hand(all_cards)
                relative_strength = self._convert_rank_to_strength(hand_rank)
            except:
                relative_strength = preflop_strength
        else:
            relative_strength = preflop_strength
            
        return HandStrength(
            raw_strength=preflop_strength,
            relative_strength=relative_strength,
            potential=self._calculate_draw_potential(hole_cards, community_cards),
            category=self._categorize_made_hand(all_cards) if len(all_cards) >= 5 else self._categorize_hand(hole_cards)
        )
    
    def _get_preflop_strength(self, hole_cards: List[Card]) -> float:
        """获取翻牌前手牌强度"""
        if len(hole_cards) != 2:
            return 0.0
            
        card1, card2 = hole_cards
        rank1, rank2 = card1.rank.numeric_value, card2.rank.numeric_value
        
        # 确保大牌在前
        high_rank = max(rank1, rank2)
        low_rank = min(rank1, rank2)
        
        # 是否同花
        suited = card1.suit == card2.suit
        
        # 强度评估表（简化版）
        if high_rank == 14 and low_rank == 14:  # AA
            return 0.95
        elif high_rank == 13 and low_rank == 13:  # KK
            return 0.90
        elif high_rank == 12 and low_rank == 12:  # QQ
            return 0.85
        elif high_rank == 14 and low_rank == 13:  # AK
            return 0.80 if suited else 0.75
        elif high_rank == 11 and low_rank == 11:  # JJ
            return 0.80
        elif high_rank == 14 and low_rank == 12:  # AQ
            return 0.75 if suited else 0.70
        elif high_rank == 10 and low_rank == 10:  # TT
            return 0.75
        elif high_rank == 14 and low_rank == 11:  # AJ
            return 0.70 if suited else 0.65
        elif high_rank == 13 and low_rank == 12:  # KQ
            return 0.70 if suited else 0.65
        elif high_rank == 9 and low_rank == 9:   # 99
            return 0.70
        elif high_rank == 14 and low_rank == 10:  # AT
            return 0.65 if suited else 0.55
        elif high_rank >= 8:  # 中等对子和高牌
            pair_bonus = 0.15 if high_rank == low_rank else 0.0  # 增加对子奖励
            suited_bonus = 0.08 if suited else 0.0  # 增加同花奖励
            connected_bonus = 0.05 if abs(high_rank - low_rank) <= 2 else 0.0  # 连牌奖励
            return min(0.75, (high_rank + low_rank) / 25 + pair_bonus + suited_bonus + connected_bonus)
        else:  # 弱牌
            suited_bonus = 0.08 if suited else 0.0  # 增加同花奖励
            connected_bonus = 0.06 if abs(high_rank - low_rank) <= 2 else 0.0  # 增加连牌奖励
            # 给弱牌更多机会，特别是同花连牌
            base_strength = (high_rank + low_rank) / 26  # 提高基础强度
            return max(0.15, base_strength + suited_bonus + connected_bonus)
    
    def _convert_rank_to_strength(self, hand_rank) -> float:
        """将牌型等级转换为强度值"""
        # 根据HandRank转换为0-1的强度值
        rank_strengths = {
            10: 1.0,    # 皇家同花顺
            9: 0.95,    # 同花顺
            8: 0.90,    # 四条
            7: 0.85,    # 葫芦
            6: 0.75,    # 同花
            5: 0.65,    # 顺子
            4: 0.55,    # 三条
            3: 0.45,    # 两对
            2: 0.35,    # 一对
            1: 0.25     # 高牌
        }
        return rank_strengths.get(hand_rank.rank_value, 0.25)
    
    def _calculate_potential(self, hole_cards: List[Card]) -> float:
        """计算手牌改进潜力"""
        if len(hole_cards) != 2:
            return 0.0
            
        card1, card2 = hole_cards
        
        # 同花潜力
        flush_potential = 0.3 if card1.suit == card2.suit else 0.0
        
        # 顺子潜力
        rank_diff = abs(card1.rank.numeric_value - card2.rank.numeric_value)
        straight_potential = max(0, (5 - rank_diff) / 10) if rank_diff <= 4 else 0.0
        
        # 对子潜力（未对子手牌）
        pair_potential = 0.2 if card1.rank != card2.rank else 0.0
        
        return min(1.0, flush_potential + straight_potential + pair_potential)
    
    def _calculate_draw_potential(self, hole_cards: List[Card], community_cards: List[Card]) -> float:
        """计算听牌潜力"""
        # 简化实现：检查同花听和顺子听
        all_cards = hole_cards + community_cards
        
        # 同花听检查
        suits = {}
        for card in all_cards:
            suits[card.suit] = suits.get(card.suit, 0) + 1
        
        flush_draw = any(count == 4 for count in suits.values())
        
        # 顺子听检查（简化）
        ranks = sorted([card.rank.numeric_value for card in all_cards])
        straight_draw = False
        for i in range(len(ranks) - 3):
            if ranks[i+3] - ranks[i] <= 4:
                straight_draw = True
                break
        
        potential = 0.0
        if flush_draw:
            potential += 0.4
        if straight_draw:
            potential += 0.3
            
        return min(1.0, potential)
    
    def _categorize_hand(self, hole_cards: List[Card]) -> str:
        """分类翻牌前手牌"""
        if len(hole_cards) != 2:
            return "unknown"
            
        card1, card2 = hole_cards
        rank1, rank2 = card1.rank.numeric_value, card2.rank.numeric_value
        
        if rank1 == rank2:
            if rank1 >= 10:
                return "premium_pair"
            elif rank1 >= 7:
                return "medium_pair"
            else:
                return "small_pair"
        
        high_rank = max(rank1, rank2)
        
        if high_rank == 14:  # A
            return "ace_high"
        elif high_rank >= 10:
            return "broadway"
        elif card1.suit == card2.suit:
            return "suited_connector" if abs(rank1 - rank2) <= 3 else "suited"
        else:
            return "offsuit"
    
    def _categorize_made_hand(self, all_cards: List[Card]) -> str:
        """分类已成型手牌"""
        try:
            hand_rank, _ = HandEvaluator.evaluate_hand(all_cards)
            return hand_rank.display.lower().replace(" ", "_")
        except:
            return "high_card"
    
    def calculate_position_factor(self, position: int, total_players: int) -> float:
        """计算位置因子（根据风格调整强度）"""
        # 将绝对位置转换为相对位置 (0=最早位置, 1=最晚位置)
        if total_players <= 2:
            return 0.0
        
        relative_position = position / (total_players - 1)
        
        # 基础位置调整
        if relative_position < 0.33:
            base_adjustment = -0.1    # 前位置劣势
        elif relative_position < 0.67:
            base_adjustment = 0.0     # 中位置中性
        else:
            base_adjustment = 0.1     # 后位置优势
        
        # 根据风格调整位置敏感度
        style_position_multiplier = {
            PlayerStyle.NITT: 0.2,             # 超紧对位置最不敏感
            PlayerStyle.ROCK: 0.5,             # 超紧手对位置不太敏感
            PlayerStyle.TAG: 1.2,              # 紧凶对位置很敏感
            PlayerStyle.TIGHT_PASSIVE: 0.3,    # 紧弱对位置不敏感
            PlayerStyle.LAG: 1.5,              # 松凶对位置最敏感
            PlayerStyle.LOOSE_PASSIVE: 0.4,    # 松弱对位置认识不足
            PlayerStyle.CALLING_STATION: 0.2,  # 跟注站对位置不敏感
            PlayerStyle.MANIAC: 1.0,           # 疯子中等位置敏感度
            PlayerStyle.FISH: 0.4,             # 鱼对位置认识不足
            PlayerStyle.SHARK: 1.3,            # 鲨鱼很懂位置
            PlayerStyle.BALANCED: 1.0          # 平衡标准敏感度
        }.get(self.current_style, 1.0)
        
        return base_adjustment * style_position_multiplier
    
    def update_opponent_model(self, opponent_name: str, action: str, amount: int = 0):
        """更新对手模型"""
        if opponent_name not in self.opponent_models:
            self.opponent_models[opponent_name] = OpponentModel()
        
        model = self.opponent_models[opponent_name]
        model.recent_actions.append(action)
        
        # 保持最近20个动作
        if len(model.recent_actions) > 20:
            model.recent_actions.pop(0)
        
        # 更新统计数据（简化实现）
        if action in ["call", "raise", "bet"]:
            # 更新VPIP（参与率）
            total_actions = len(model.recent_actions)
            participative_actions = sum(1 for a in model.recent_actions if a in ["call", "raise", "bet"])
            model.vpip = (participative_actions / total_actions) * 100 if total_actions > 0 else 25.0
            
        if action in ["raise", "bet"]:
            # 更新侵略性
            aggressive_actions = sum(1 for a in model.recent_actions if a in ["raise", "bet"])
            total_actions = len(model.recent_actions)
            model.aggression = aggressive_actions / max(1, total_actions - model.recent_actions.count("fold"))
    
    def should_bluff(self, hand_strength: HandStrength, pot_size: int, opponent_count: int) -> bool:
        """决定是否诈唬"""
        if self.current_style is None:
            return False
            
        # 基础诈唬频率（根据风格调整）
        base_bluff_freq = {
            PlayerStyle.NITT: 0.005,            # 超紧几乎不诈唬
            PlayerStyle.ROCK: 0.02,             # 超紧手很少诈唬
            PlayerStyle.TAG: 0.08,              # 紧凶适度诈唬
            PlayerStyle.TIGHT_PASSIVE: 0.01,    # 紧弱很少诈唬
            PlayerStyle.LAG: 0.15,              # 松凶经常诈唬
            PlayerStyle.LOOSE_PASSIVE: 0.03,    # 松弱偶尔诈唬
            PlayerStyle.CALLING_STATION: 0.01,  # 跟注站很少诈唬
            PlayerStyle.MANIAC: 0.25,           # 疯子频繁诈唬
            PlayerStyle.FISH: 0.05,             # 鱼不理性诈唬
            PlayerStyle.SHARK: 0.12,            # 鲨鱼精明诈唬
            PlayerStyle.BALANCED: 0.10          # 平衡适中诈唬
        }.get(self.current_style, 0.05)
        
        # 根据技能等级调整
        skill_multiplier = {
            AISkillLevel.BEGINNER: 0.3,
            AISkillLevel.INTERMEDIATE: 0.7,
            AISkillLevel.ADVANCED: 1.0,
            AISkillLevel.EXPERT: 1.2
        }.get(self.skill_level, 1.0)
        
        # 情况调整
        situation_multiplier = 1.0
        
        # 对手越少，诈唬越容易成功
        if opponent_count == 1:
            situation_multiplier *= 1.5
        elif opponent_count >= 3:
            situation_multiplier *= 0.6
            
        # 有听牌潜力时增加诈唬频率（半诈唬）
        if hand_strength.potential > 0.3:
            situation_multiplier *= 1.8
            
        final_bluff_freq = base_bluff_freq * skill_multiplier * situation_multiplier
        return random.random() < final_bluff_freq
    
    def make_decision(self, hole_cards: List[Card], community_cards: List[Card], 
                     current_bet: int, min_raise: int, pot_size: int, 
                     player_chips: int, position: int, total_players: int,
                     opponents_in_hand: List[str]) -> Tuple[str, int]:
        """智能决策主函数"""
        
        # 如果还没分配风格，先分配
        if self.current_style is None:
            self.assign_random_style()
        
        # 评估手牌强度
        hand_strength = self.evaluate_hand_strength(hole_cards, community_cards)
        
        # 计算位置因子
        position_factor = self.calculate_position_factor(position, total_players)
        
        # 基础决策强度（结合手牌强度和位置）
        base_strength = hand_strength.relative_strength + position_factor
        
        # 根据风格调整决策阈值
        style_adjustments = self._get_style_adjustments()
        
        # 计算最终决策强度
        decision_strength = base_strength * style_adjustments["aggression_multiplier"]
        
        # 添加技能等级的随机性
        skill_noise = self._get_skill_noise()
        decision_strength += skill_noise
        
        # 决策逻辑
        if current_bet > player_chips:
            return ("fold", 0)
        
        # 计算下注比例
        bet_ratio = current_bet / max(player_chips, 1)
        
        # 筹码保护（根据风格调整）
        if bet_ratio > style_adjustments["fold_threshold"]:
            if decision_strength < 0.7:  # 除非手牌很强
                return ("fold", 0)
        
        # 诈唬检查
        should_bluff = self.should_bluff(hand_strength, pot_size, len(opponents_in_hand))
        
        if current_bet == 0:
            # 无人下注
            if decision_strength > style_adjustments["bet_threshold"] or should_bluff:
                bet_size = self._calculate_bet_size(pot_size, decision_strength, should_bluff)
                bet_amount = min(bet_size, player_chips)
                return ("raise", bet_amount)
            else:
                return ("check", 0)
        else:
            # 有人下注 - current_bet是需要跟注的金额
            if decision_strength > style_adjustments["raise_threshold"] or should_bluff:
                # 加注 - 计算总的加注目标金额
                raise_size = self._calculate_raise_size(current_bet, pot_size, decision_strength, should_bluff)
                # 总的下注目标 = 需要跟注 + 额外加注
                total_raise_amount = current_bet + raise_size
                if total_raise_amount <= player_chips and total_raise_amount >= min_raise:
                    return ("raise", total_raise_amount)
                else:
                    # 如果不能加注，就跟注
                    return ("call", current_bet)
            elif decision_strength > style_adjustments["call_threshold"]:
                # 跟注 - 直接返回需要跟注的金额
                return ("call", current_bet)
            else:
                # 弃牌
                return ("fold", 0)
    
    def _get_style_adjustments(self) -> Dict[str, float]:
        """获取风格调整参数"""
        adjustments = {
            PlayerStyle.NITT: {
                "aggression_multiplier": 0.6,
                "fold_threshold": 0.15,  # 提高到15% (更现实)
                "bet_threshold": 0.65,   # 进一步降低门槛
                "raise_threshold": 0.7,  # 大幅降低加注门槛
                "call_threshold": 0.55   # 降低门槛
            },
            PlayerStyle.ROCK: {
                "aggression_multiplier": 0.8,
                "fold_threshold": 0.22,  # 提高到22%
                "bet_threshold": 0.6,    # 进一步降低门槛
                "raise_threshold": 0.65, # 大幅降低加注门槛
                "call_threshold": 0.45   # 降低门槛
            },
            PlayerStyle.TAG: {
                "aggression_multiplier": 1.1,
                "fold_threshold": 0.35,  # 提高到35%
                "bet_threshold": 0.45,   # 进一步降低门槛
                "raise_threshold": 0.5,  # 大幅降低加注门槛
                "call_threshold": 0.35   # 降低门槛
            },
            PlayerStyle.TIGHT_PASSIVE: {
                "aggression_multiplier": 0.7,
                "fold_threshold": 0.25,  # 提高到25%
                "bet_threshold": 0.6,    # 进一步降低门槛
                "raise_threshold": 0.7,  # 大幅降低加注门槛
                "call_threshold": 0.3    # 降低门槛
            },
            PlayerStyle.LAG: {
                "aggression_multiplier": 1.3,
                "fold_threshold": 0.45,  # 松凶玩家，入局率更高
                "bet_threshold": 0.3,    # 进一步降低门槛
                "raise_threshold": 0.35, # 大幅降低加注门槛
                "call_threshold": 0.25   # 降低门槛
            },
            PlayerStyle.LOOSE_PASSIVE: {
                "aggression_multiplier": 0.8,
                "fold_threshold": 0.5,   # 松被动，入局率最高
                "bet_threshold": 0.55,   # 进一步降低门槛
                "raise_threshold": 0.65, # 降低加注门槛
                "call_threshold": 0.15   # 保持较低，喜欢跟注
            },
            PlayerStyle.CALLING_STATION: {
                "aggression_multiplier": 0.6,
                "fold_threshold": 0.55,  # 跟注站，很少弃牌
                "bet_threshold": 0.6,    # 进一步降低门槛
                "raise_threshold": 0.7,  # 降低加注门槛
                "call_threshold": 0.1    # 非常低，几乎总是跟注
            },
            PlayerStyle.MANIAC: {
                "aggression_multiplier": 1.5,
                "fold_threshold": 0.6,   # 疯子玩家，几乎不弃牌
                "bet_threshold": 0.1,    # 极低门槛
                "raise_threshold": 0.15, # 极低加注门槛
                "call_threshold": 0.3    # 降低门槛
            },
            PlayerStyle.FISH: {
                "aggression_multiplier": 0.9,
                "fold_threshold": 0.4,   # 鱼玩家，经常入局
                "bet_threshold": 0.5,    # 进一步降低门槛
                "raise_threshold": 0.6,  # 降低加注门槛
                "call_threshold": 0.2    # 降低门槛
            },
            PlayerStyle.SHARK: {
                "aggression_multiplier": 1.2,
                "fold_threshold": 0.32,  # 鲨鱼玩家，平衡入局
                "bet_threshold": 0.4,    # 进一步降低门槛
                "raise_threshold": 0.45, # 降低加注门槛
                "call_threshold": 0.35   # 降低门槛
            },
            PlayerStyle.BALANCED: {
                "aggression_multiplier": 1.0,
                "fold_threshold": 0.3,   # 平衡玩家
                "bet_threshold": 0.45,   # 进一步降低门槛
                "raise_threshold": 0.5,  # 降低加注门槛
                "call_threshold": 0.3    # 降低门槛
            }
        }
        
        # 默认平衡风格
        default = {
            "aggression_multiplier": 1.0,
            "fold_threshold": 0.3,   # 更合理的默认值
            "bet_threshold": 0.45,   # 进一步降低门槛
            "raise_threshold": 0.5,  # 大幅降低加注门槛
            "call_threshold": 0.3    # 降低门槛
        }
        
        return adjustments.get(self.current_style, default)
    
    def _get_skill_noise(self) -> float:
        """获取技能等级对应的随机噪音"""
        noise_levels = {
            AISkillLevel.BEGINNER: 0.15,    # 大量随机性
            AISkillLevel.INTERMEDIATE: 0.10,  # 中等随机性
            AISkillLevel.ADVANCED: 0.05,    # 少量随机性
            AISkillLevel.EXPERT: 0.02       # 极少随机性
        }
        
        noise_range = noise_levels.get(self.skill_level, 0.10)
        return random.uniform(-noise_range, noise_range)
    
    def _calculate_bet_size(self, pot_size: int, strength: float, is_bluff: bool) -> int:
        """计算下注大小"""
        # 获取风格调整
        style_adjustments = self._get_style_adjustments()
        
        if is_bluff:
            # 诈唬下注，根据风格调整
            base_size = pot_size * random.uniform(0.3, 0.6)
            style_multiplier = style_adjustments.get("aggression_factor", 1.0)
            return max(int(base_size * style_multiplier), pot_size // 4)
        else:
            # 价值下注，根据手牌强度和风格
            if strength > 0.8:
                base_size = pot_size * random.uniform(0.6, 1.0)
            elif strength > 0.6:
                base_size = pot_size * random.uniform(0.4, 0.7)
            else:
                base_size = pot_size * random.uniform(0.2, 0.4)
            
            style_multiplier = style_adjustments.get("aggression_factor", 1.0)
            return max(int(base_size * style_multiplier), pot_size // 6)
    
    def _calculate_raise_size(self, current_bet: int, pot_size: int, strength: float, is_bluff: bool) -> int:
        """计算加注大小"""
        if is_bluff:
            # 诈唬加注
            return int(pot_size * random.uniform(0.4, 0.8))
        else:
            # 价值加注
            if strength > 0.85:
                return int(pot_size * random.uniform(0.8, 1.2))
            elif strength > 0.7:
                return int(pot_size * random.uniform(0.5, 0.9))
            else:
                return int(pot_size * random.uniform(0.3, 0.6))
    
    def get_current_style(self) -> Optional[PlayerStyle]:
        """获取当前分配的风格"""
        return self.current_style
    
    def reset_for_new_game(self):
        """新游戏重置"""
        self.current_style = None
        self.opponent_models.clear()
        self.game_memory.clear()


# 全局AI引擎管理器
class AIEngineManager:
    """AI引擎管理器"""
    
    def __init__(self):
        self.engines: Dict[str, SmartAIDecisionEngine] = {}
        self.current_skill_level = AISkillLevel.INTERMEDIATE
        
    def get_engine(self, player_name: str) -> SmartAIDecisionEngine:
        """获取或创建AI引擎"""
        if player_name not in self.engines:
            self.engines[player_name] = SmartAIDecisionEngine(player_name, self.current_skill_level)
        return self.engines[player_name]
    
    def set_skill_level(self, level: AISkillLevel):
        """设置全局技能等级"""
        self.current_skill_level = level
        # 更新现有引擎的技能等级
        for engine in self.engines.values():
            engine.skill_level = level
    
    def get_all_ai_styles(self) -> Dict[str, PlayerStyle]:
        """获取所有AI的当前风格"""
        styles = {}
        for player_name, engine in self.engines.items():
            style = engine.get_current_style()
            if style:
                styles[player_name] = style
        return styles
    
    def reset_for_new_game(self):
        """新游戏重置（保留技能等级）"""
        for engine in self.engines.values():
            engine.reset_for_new_game()


# 全局实例
ai_engine_manager = AIEngineManager()
