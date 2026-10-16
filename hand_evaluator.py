# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 牌型评估器
实现牌型判断和比较功能（带 LRU 缓存优化）
"""

from typing import List, Tuple, Dict
from collections import Counter
from functools import lru_cache
from card import Card, Rank, Suit
from enum import Enum
from lru_cache import LRUCache


# ============================================================================
# 缓存配置
# ============================================================================

# 5张牌评估缓存大小
FIVE_CARD_CACHE_SIZE = 10000

# 7张牌最佳组合缓存大小
SEVEN_CARD_CACHE_SIZE = 5000


class HandRank(Enum):
    """牌型等级枚举（从小到大）"""
    HIGH_CARD = (1, "高牌")
    PAIR = (2, "一对")
    TWO_PAIR = (3, "两对")
    THREE_OF_A_KIND = (4, "三条")
    STRAIGHT = (5, "顺子")
    FLUSH = (6, "同花")
    FULL_HOUSE = (7, "葫芦")
    FOUR_OF_A_KIND = (8, "四条")
    STRAIGHT_FLUSH = (9, "同花顺")
    ROYAL_FLUSH = (10, "皇家同花顺")

    def __init__(self, rank_value, display):
        self.rank_value = rank_value
        self.display = display

    def __lt__(self, other):
        return self.rank_value < other.rank_value

    def __str__(self):
        return self.display


class HandEvaluator:
    """牌型评估器（带 LRU 缓存优化）"""

    # 类级别 LRU 缓存
    _five_card_cache = LRUCache(max_size=FIVE_CARD_CACHE_SIZE)
    _seven_card_cache = LRUCache(max_size=SEVEN_CARD_CACHE_SIZE)
    
    @staticmethod
    def _cards_to_tuple(cards: List[Card]) -> tuple:
        """将卡牌列表转换为可哈希的元组（用于缓存键）"""
        return tuple(sorted((c.suit.value, c.rank.numeric_value) for c in cards))
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """
        评估牌型（带缓存）
        
        Args:
            cards: 7张牌（2张手牌 + 5张公共牌）
            
        Returns:
            Tuple[HandRank, List[int]]: (牌型, 关键牌点数列表)
        """
        if len(cards) != 7:
            raise ValueError("必须提供7张牌进行评估")
        
        # 尝试从缓存获取
        cache_key = HandEvaluator._cards_to_tuple(cards)
        cached_result = HandEvaluator._seven_card_cache.get(cache_key)
        if cached_result is not None:
            rank, kickers = cached_result
            return rank, list(kickers)

        # 从7张牌中找出最好的5张牌组合
        best_hand = HandEvaluator._find_best_five_card_hand(cards)
        result = HandEvaluator._evaluate_five_cards(best_hand)

        # 存入 LRU 缓存（自动管理容量）
        HandEvaluator._seven_card_cache.put(cache_key, (result[0], tuple(result[1])))

        return result

    @staticmethod
    def _find_best_five_card_hand(cards: List[Card]) -> List[Card]:
        """从7张牌中找出最好的5张牌组合"""
        from itertools import combinations
        
        best_hand = None
        best_rank = None
        best_kickers = None
        
        # 枚举所有可能的5张牌组合
        for combo in combinations(cards, 5):
            hand_rank, kickers = HandEvaluator._evaluate_five_cards(list(combo))
            
            if best_hand is None or HandEvaluator._is_better_hand(
                hand_rank, kickers, best_rank, best_kickers
            ):
                best_hand = list(combo)
                best_rank = hand_rank
                best_kickers = kickers
        
        return best_hand

    @staticmethod
    def _evaluate_five_cards(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """评估5张牌的牌型（带缓存）"""
        if len(cards) != 5:
            raise ValueError("必须提供5张牌进行评估")
        
        # 尝试从缓存获取
        cache_key = HandEvaluator._cards_to_tuple(cards)
        cached_result = HandEvaluator._five_card_cache.get(cache_key)
        if cached_result is not None:
            rank, kickers = cached_result
            return rank, list(kickers)
        
        # 按点数排序
        cards_by_rank = sorted(cards, key=lambda c: c.rank.numeric_value, reverse=True)
        ranks = [card.rank.numeric_value for card in cards_by_rank]
        suits = [card.suit for card in cards_by_rank]
        
        # 统计每个点数出现的次数
        rank_counts = Counter(ranks)
        count_values = sorted(rank_counts.values(), reverse=True)
        
        # 检查是否是同花
        is_flush = len(set(suits)) == 1
        
        # 检查是否是顺子
        is_straight, straight_high = HandEvaluator._check_straight(ranks)
        
        # 判断牌型并获取结果
        result = None
        
        if is_straight and is_flush:
            if ranks == [14, 13, 12, 11, 10]:  # A, K, Q, J, 10
                result = (HandRank.ROYAL_FLUSH, [14])
            else:
                result = (HandRank.STRAIGHT_FLUSH, [straight_high])
        
        elif count_values == [4, 1]:
            # 四条
            four_kind = [rank for rank, count in rank_counts.items() if count == 4][0]
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            result = (HandRank.FOUR_OF_A_KIND, [four_kind, kicker])
        
        elif count_values == [3, 2]:
            # 葫芦
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            result = (HandRank.FULL_HOUSE, [three_kind, pair])
        
        elif is_flush:
            result = (HandRank.FLUSH, ranks)
        
        elif is_straight:
            result = (HandRank.STRAIGHT, [straight_high])
        
        elif count_values == [3, 1, 1]:
            # 三条
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            result = (HandRank.THREE_OF_A_KIND, [three_kind] + kickers)
        
        elif count_values == [2, 2, 1]:
            # 两对
            pairs = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            result = (HandRank.TWO_PAIR, pairs + [kicker])
        
        elif count_values == [2, 1, 1, 1]:
            # 一对
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            result = (HandRank.PAIR, [pair] + kickers)
        
        else:
            # 高牌
            result = (HandRank.HIGH_CARD, ranks)
        
        # 存入 LRU 缓存（自动管理容量）
        HandEvaluator._five_card_cache.put(cache_key, (result[0], tuple(result[1])))

        return result[0], result[1]

    @staticmethod
    def _check_straight(ranks: List[int]) -> Tuple[bool, int]:
        """
        检查是否是顺子

        顺子定义：5张连续的牌
        特殊情况：A-2-3-4-5（A 作为 1 使用）

        Args:
            ranks: 牌的点数列表

        Returns:
            (是否是顺子, 顺子的最高牌点数)
        """
        # 去重并从大到小排序
        unique_ranks = sorted(set(ranks), reverse=True)

        # 至少需要5张不同点数的牌才可能组成顺子
        if len(unique_ranks) < 5:
            return False, 0

        # 检查普通顺子（例如：10-9-8-7-6）
        # 遍历所有可能的5张连续牌
        for i in range(len(unique_ranks) - 4):
            # 检查是否连续：最高牌 - 最低牌 = 4
            if unique_ranks[i] - unique_ranks[i + 4] == 4:
                # 返回顺子的最高牌
                return True, unique_ranks[i]

        # 检查特殊顺子：A-2-3-4-5（轮子/Wheel）
        # 在这种情况下，A（14）作为 1 使用
        wheel_straight = {14, 5, 4, 3, 2}  # A, 5, 4, 3, 2
        if wheel_straight.issubset(set(unique_ranks)):
            # A-2-3-4-5 的顺子，5 是最高牌（A 作为 1）
            return True, 5

        # 没有找到顺子
        return False, 0

    @staticmethod
    def _is_better_hand(rank1: HandRank, kickers1: List[int], 
                       rank2: HandRank, kickers2: List[int]) -> bool:
        """比较两手牌的大小"""
        if rank1.rank_value != rank2.rank_value:
            return rank1.rank_value > rank2.rank_value
        
        # 牌型相同，比较关键牌
        for k1, k2 in zip(kickers1, kickers2):
            if k1 != k2:
                return k1 > k2
        
        return False

    @staticmethod
    def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
        """
        比较两手牌的大小
        
        Args:
            hand1: 第一手牌（7张）
            hand2: 第二手牌（7张）
            
        Returns:
            int: 1 表示hand1获胜，-1 表示hand2获胜，0 表示平局
        """
        rank1, kickers1 = HandEvaluator.evaluate_hand(hand1)
        rank2, kickers2 = HandEvaluator.evaluate_hand(hand2)
        
        if HandEvaluator._is_better_hand(rank1, kickers1, rank2, kickers2):
            return 1
        elif HandEvaluator._is_better_hand(rank2, kickers2, rank1, kickers1):
            return -1
        else:
            return 0

    @staticmethod
    def get_hand_description(cards: List[Card]) -> str:
        """获取牌型的描述"""
        hand_rank, kickers = HandEvaluator.evaluate_hand(cards)
        
        # 构建描述字符串
        desc = hand_rank.display
        
        if hand_rank == HandRank.PAIR:
            desc += f" ({HandEvaluator._get_rank_display(kickers[0])})"
        elif hand_rank == HandRank.TWO_PAIR:
            desc += f" ({HandEvaluator._get_rank_display(kickers[0])} 和 {HandEvaluator._get_rank_display(kickers[1])})"
        elif hand_rank == HandRank.THREE_OF_A_KIND:
            desc += f" ({HandEvaluator._get_rank_display(kickers[0])})"
        elif hand_rank == HandRank.STRAIGHT:
            desc += f" (到 {HandEvaluator._get_rank_display(kickers[0])})"
        elif hand_rank == HandRank.FLUSH:
            desc += f" ({HandEvaluator._get_rank_display(kickers[0])} 高)"
        elif hand_rank == HandRank.FULL_HOUSE:
            desc += f" ({HandEvaluator._get_rank_display(kickers[0])} 满 {HandEvaluator._get_rank_display(kickers[1])})"
        elif hand_rank == HandRank.FOUR_OF_A_KIND:
            desc += f" ({HandEvaluator._get_rank_display(kickers[0])})"
        elif hand_rank == HandRank.STRAIGHT_FLUSH:
            desc += f" (到 {HandEvaluator._get_rank_display(kickers[0])})"
        elif hand_rank == HandRank.HIGH_CARD:
            desc += f" ({HandEvaluator._get_rank_display(kickers[0])} 高)"
        
        return desc

    @staticmethod
    def _get_rank_display(rank_value: int) -> str:
        """根据点数值获取显示字符串"""
        rank_map = {
            2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
            11: "J", 12: "Q", 13: "K", 14: "A"
        }
        return rank_map.get(rank_value, str(rank_value))
    
    @classmethod
    def clear_cache(cls):
        """清除评估缓存"""
        cls._five_card_cache.clear()
        cls._seven_card_cache.clear()
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, any]:
        """获取缓存统计信息"""
        five_stats = cls._five_card_cache.get_stats()
        seven_stats = cls._seven_card_cache.get_stats()

        return {
            'five_card_cache': five_stats,
            'seven_card_cache': seven_stats,
            'total_hits': five_stats['hits'] + seven_stats['hits'],
            'total_misses': five_stats['misses'] + seven_stats['misses']
        }