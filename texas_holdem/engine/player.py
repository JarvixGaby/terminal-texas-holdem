# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 玩家类
实现玩家的基本功能和动作
"""

from typing import List, Optional
from texas_holdem.engine.card import Card


class Player:
    """玩家类"""
    
    def __init__(self, name: str, chips: int = 1000):
        """
        初始化玩家
        
        Args:
            name: 玩家姓名
            chips: 初始筹码数量
        """
        self.name = name
        self.chips = chips
        self.hand: List[Card] = []  # 手牌（2张）
        self.current_bet = 0  # 当前回合下注金额
        self.total_bet = 0    # 总下注金额
        self.is_folded = False  # 是否弃牌
        self.is_all_in = False  # 是否全押

    def reset_for_new_hand(self):
        """为新的一手牌重置玩家状态"""
        self.hand = []
        self.current_bet = 0
        self.total_bet = 0
        self.is_folded = False
        self.is_all_in = False

    def deal_cards(self, cards: List[Card]):
        """发牌给玩家"""
        self.hand = cards

    def add_card(self, card: Card):
        """添加一张牌到手牌"""
        if len(self.hand) < 2:
            self.hand.append(card)

    def bet(self, amount: int) -> int:
        """
        下注

        Args:
            amount: 下注金额

        Returns:
            int: 实际下注金额
        """
        # 输入验证：下注金额不能为负数
        if amount < 0:
            raise ValueError(f"下注金额不能为负数: {amount}")

        # 如果下注金额为0，直接返回
        if amount == 0:
            return 0

        if amount >= self.chips:
            # 全押
            actual_bet = self.chips
            self.chips = 0
            self.is_all_in = True
        else:
            actual_bet = amount
            self.chips -= amount

        self.current_bet += actual_bet
        self.total_bet += actual_bet
        return actual_bet

    def call(self, amount_to_call: int) -> int:
        """
        跟注
        
        Args:
            amount_to_call: 需要跟注的金额
            
        Returns:
            int: 实际跟注金额
        """
        return self.bet(amount_to_call)

    def raise_bet(self, raise_amount: int) -> int:
        """
        加注
        
        Args:
            raise_amount: 加注金额
            
        Returns:
            int: 实际加注金额
        """
        return self.bet(raise_amount)

    def fold(self):
        """弃牌"""
        self.is_folded = True

    def check(self):
        """过牌（不下注）"""
        pass

    def can_bet(self, amount: int) -> bool:
        """检查是否可以下注指定金额"""
        return not self.is_folded and self.chips >= amount

    def can_call(self, amount_to_call: int) -> bool:
        """检查是否可以跟注"""
        return not self.is_folded and (self.chips >= amount_to_call or self.chips > 0)

    def can_raise(self, min_raise: int) -> bool:
        """检查是否可以加注"""
        return not self.is_folded and self.chips >= min_raise

    def can_check(self, current_bet_to_match: int) -> bool:
        """检查是否可以过牌"""
        return not self.is_folded and self.current_bet >= current_bet_to_match

    def get_hand_string(self) -> str:
        """获取手牌的字符串表示"""
        if len(self.hand) == 2:
            return f"{self.hand[0]} {self.hand[1]}"
        return "无手牌"

    def __str__(self):
        return f"{self.name} (筹码: {self.chips})"

    def __repr__(self):
        return self.__str__()


class HumanPlayer(Player):
    """人类玩家类"""
    
    def __init__(self, name: str, chips: int = 1000):
        super().__init__(name, chips)
        self.player_type = "human"


class AIPlayer(Player):
    """AI玩家类（支持标准AI和高级AI）"""
    
    # 类变量：控制是否使用高级AI
    USE_ADVANCED_AI = True  # 设为True启用高级AI
    
    def __init__(self, name: str, chips: int = 1000, archetype_name: str | None = None):
        super().__init__(name, chips)
        self.player_type = "ai"
        self.ai_mode = "advanced" if AIPlayer.USE_ADVANCED_AI else "standard"
        if archetype_name is not None:
            from texas_holdem.ai.ai_profiles import get_archetype_profile
            get_archetype_profile(archetype_name)
        self.archetype_name = archetype_name
        self.last_decision_metadata = None
        # AI引擎将在首次使用时创建
        
    def make_decision(self, current_bet: int, min_raise: int, pot_size: int, 
                     community_cards: list = None, position: int = 0, 
                     total_players: int = 6, opponents_in_hand: list = None,
                     table_current_bet: int = None,
                     player_current_bet: int = 0,
                     action_history: list = None) -> tuple:
        """
        AI决策逻辑
        
        支持两种模式：
        - standard: 原有的智能AI系统（基于风格）
        - advanced: 高级AI系统（范围思维、GTO策略）
        
        Args:
            current_bet: 当前需要跟注的金额
            min_raise: 最小加注金额
            pot_size: 当前彩池大小
            community_cards: 公共牌列表
            position: 玩家位置
            total_players: 总玩家数
            opponents_in_hand: 仍在牌局中的对手名单
            
        Returns:
            tuple: (动作, 金额) - 动作可以是 'fold', 'check', 'call', 'raise'
        """
        # 根据模式选择AI引擎
        self.last_decision_metadata = None
        if self.ai_mode == "advanced":
            return self._advanced_decision(
                current_bet, min_raise, pot_size, 
                community_cards, position, total_players, opponents_in_hand,
                table_current_bet, player_current_bet, action_history
            )
        else:
            return self._standard_decision(
                current_bet, min_raise, pot_size,
                community_cards, position, total_players, opponents_in_hand
            )
    
    def _advanced_decision(self, current_bet: int, min_raise: int, pot_size: int,
                          community_cards: list, position: int, total_players: int,
                          opponents_in_hand: list, table_current_bet: int = None,
                          player_current_bet: int = 0,
                          action_history: list = None) -> tuple:
        """
        高级AI决策
        使用范围思维、GTO策略、剥削调整等高级技术
        """
        try:
            from texas_holdem.ai.advanced_ai_engine import advanced_ai_manager
            
            # 获取高级AI引擎
            engine = advanced_ai_manager.get_engine(self.name, archetype_name=self.archetype_name)
            
            # 确定游戏阶段
            if not community_cards:
                phase = "preflop"
            elif len(community_cards) == 3:
                phase = "flop"
            elif len(community_cards) == 4:
                phase = "turn"
            else:
                phase = "river"
            
            # 使用高级决策
            action, amount = engine.make_decision(
                hole_cards=self.hand,
                community_cards=community_cards or [],
                current_bet=current_bet,
                min_raise=min_raise,
                pot_size=pot_size,
                player_chips=self.chips,
                position=position,
                total_players=total_players,
                opponents_in_hand=opponents_in_hand or [],
                phase=phase,
                table_current_bet=table_current_bet,
                player_current_bet=player_current_bet,
                action_history=action_history or [],
            )
            self.last_decision_metadata = getattr(engine, "last_decision_explanation", None)
            return (action, amount)
            
        except ImportError as e:
            # 高级AI模块不可用，回退到标准AI
            import traceback
            print(f"⚠️ 高级AI模块不可用，使用标准AI")
            print(f"   原因: {e}")
            return self._standard_decision(
                current_bet, min_raise, pot_size,
                community_cards, position, total_players, opponents_in_hand
            )
        except Exception as e:
            import traceback
            print(f"⚠️ 高级AI决策异常 ({self.name}): {e}")
            print(f"   堆栈信息:")
            traceback.print_exc()
            print(f"   使用回退策略")
            return self._fallback_decision(current_bet, min_raise)
    
    def _standard_decision(self, current_bet: int, min_raise: int, pot_size: int,
                          community_cards: list, position: int, total_players: int,
                          opponents_in_hand: list) -> tuple:
        """
        标准AI决策（原有的智能AI系统）
        基于玩家风格和简单的手牌强度评估
        """
        try:
            from texas_holdem.ai.smart_ai_system import ai_engine_manager
            
            # 获取AI引擎
            engine = ai_engine_manager.get_engine(self.name)
            
            # 使用智能决策
            action, amount = engine.make_decision(
                hole_cards=self.hand,
                community_cards=community_cards or [],
                current_bet=current_bet,
                min_raise=min_raise,
                pot_size=pot_size,
                player_chips=self.chips,
                position=position,
                total_players=total_players,
                opponents_in_hand=opponents_in_hand or []
            )
            return (action, amount)
            
        except Exception as e:
            import traceback
            print(f"⚠️ 标准AI决策异常 ({self.name}): {e}")
            print(f"   堆栈信息:")
            traceback.print_exc()
            print(f"   使用回退策略")
            return self._fallback_decision(current_bet, min_raise)
    
    def _fallback_decision(self, current_bet: int, min_raise: int) -> tuple:
        """回退策略（简单决策）"""
        import random
        
        if current_bet > self.chips:
            return ('fold', 0)
        
        bet_ratio = current_bet / max(self.chips, 1)
        rand = random.random()
        
        if current_bet == 0:
            if rand < 0.7:
                return ('check', 0)
            else:
                bet_amount = min(min_raise, self.chips // 4)
                return ('raise', bet_amount)
        else:
            if bet_ratio > 0.3 or rand < 0.3:
                return ('fold', 0)
            elif rand < 0.8:
                return ('call', current_bet)
            else:
                raise_amount = min(min_raise, self.chips // 3)
                if raise_amount > 0:
                    return ('raise', current_bet + raise_amount)
                else:
                    return ('call', current_bet)
    
    @classmethod
    def set_ai_mode(cls, use_advanced: bool):
        """设置AI模式（类方法）"""
        cls.USE_ADVANCED_AI = use_advanced
        print(f"🤖 AI模式已设置为: {'高级' if use_advanced else '标准'}")
