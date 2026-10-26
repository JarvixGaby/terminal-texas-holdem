# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 卡片类
实现基本的卡片和牌堆功能
"""

import random
from enum import Enum
from typing import List, Optional


class Suit(Enum):
    """花色枚举"""
    HEARTS = "♥"    # 红桃
    DIAMONDS = "♦"  # 方块
    CLUBS = "♣"     # 梅花
    SPADES = "♠"    # 黑桃

    def __str__(self):
        return self.value


class Rank(Enum):
    """牌面大小枚举"""
    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "10")
    JACK = (11, "J")
    QUEEN = (12, "Q")
    KING = (13, "K")
    ACE = (14, "A")

    def __init__(self, numeric_value, display):
        self.numeric_value = numeric_value
        self.display = display

    def __str__(self):
        return self.display

    def __lt__(self, other):
        return self.numeric_value < other.numeric_value

    def __eq__(self, other):
        return self.numeric_value == other.numeric_value


class Card:
    """扑克牌类"""
    
    def __init__(self, suit: Suit, rank: Rank):
        """
        初始化卡片
        
        Args:
            suit: 花色
            rank: 牌面大小
        """
        self.suit = suit
        self.rank = rank

    def __str__(self):
        """返回卡片的字符串表示"""
        return f"{self.rank}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """判断两张牌是否相等"""
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __lt__(self, other):
        """比较牌的大小（只比较点数）"""
        return self.rank.numeric_value < other.rank.numeric_value


class Deck:
    """牌堆类"""

    def __init__(self):
        """初始化一副完整的牌"""
        self.cards: List[Card] = []
        self.dealt_cards: List[Card] = []  # 追踪已发出的牌
        self.reset()

    def reset(self):
        """重置牌堆，创建一副完整的52张牌"""
        self.cards = []
        self.dealt_cards = []
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        """洗牌"""
        random.shuffle(self.cards)

    def deal_card(self) -> Optional[Card]:
        """
        发一张牌

        Returns:
            Card: 发出的牌，如果牌堆为空则返回None
        """
        if self.cards:
            card = self.cards.pop()
            self.dealt_cards.append(card)
            return card
        return None

    def is_card_dealt(self, card: Card) -> bool:
        """检查某张牌是否已经被发出"""
        return card in self.dealt_cards

    def cards_remaining(self) -> int:
        """返回牌堆中剩余的牌数"""
        return len(self.cards)

    def __len__(self):
        return len(self.cards)
