# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 优化版胜率计算器
实现缓存机制、多级精度和性能优化的蒙特卡洛模拟
"""

import random
import hashlib
import time
from typing import List, Dict, Tuple, Optional
from itertools import combinations
from functools import lru_cache
from card import Card, Deck, Suit, Rank
from hand_evaluator import HandEvaluator


class PerformanceLevel:
    """性能等级配置"""
    FAST = {"simulation_count": 1000, "name": "快速"}
    NORMAL = {"simulation_count": 3000, "name": "标准"}
    ACCURATE = {"simulation_count": 8000, "name": "精确"}
    PRECISE = {"simulation_count": 15000, "name": "极精确"}


class OptimizedOddsCalculator:
    """优化版德州扑克胜率计算器"""
    
    def __init__(self, performance_level: Dict = PerformanceLevel.NORMAL):
        """
        初始化优化版胜率计算器
        
        Args:
            performance_level: 性能等级配置
        """
        self.simulation_count = performance_level["simulation_count"]
        self.performance_name = performance_level["name"]
        
        # 缓存配置
        self.cache_enabled = True
        self.cache_max_size = 1000
        self._preflop_cache = {}
        self._postflop_cache = {}
        
        # 性能统计
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_calculations = 0
        
    def set_performance_level(self, level: Dict):
        """动态调整性能等级"""
        self.simulation_count = level["simulation_count"]
        self.performance_name = level["name"]
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_calculations": self.total_calculations,
            "cache_size": len(self._preflop_cache) + len(self._postflop_cache)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._preflop_cache.clear()
        self._postflop_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _generate_cache_key(self, player_hands: List[List[Card]], 
                          community_cards: List[Card] = None, 
                          num_opponents: int = 0) -> str:
        """生成缓存键"""
        # 将手牌和公共牌转换为排序后的字符串
        hands_str = []
        for hand in player_hands:
            hand_str = sorted([str(card) for card in hand])
            hands_str.append("-".join(hand_str))
        
        key_parts = ["|".join(hands_str)]
        
        if community_cards:
            community_str = sorted([str(card) for card in community_cards])
            key_parts.append("-".join(community_str))
        
        if num_opponents > 0:
            key_parts.append(f"opp_{num_opponents}")
        
        key_parts.append(f"sim_{self.simulation_count}")
        
        # 使用MD5生成短key
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def calculate_preflop_odds(self, player_hands: List[List[Card]], 
                              num_opponents: int) -> Dict[str, float]:
        """
        计算翻牌前胜率（带缓存）
        
        Args:
            player_hands: 每个玩家的手牌列表
            num_opponents: 对手数量
            
        Returns:
            Dict: 每个玩家的胜率
        """
        if not player_hands:
            return {}
        
        # 检查缓存
        cache_key = self._generate_cache_key(player_hands, num_opponents=num_opponents)
        if self.cache_enabled and cache_key in self._preflop_cache:
            self.cache_hits += 1
            return self._preflop_cache[cache_key].copy()
        
        self.cache_misses += 1
        self.total_calculations += 1
        
        # 执行计算
        start_time = time.time()
        result = self._calculate_preflop_odds_core(player_hands, num_opponents)
        calculation_time = time.time() - start_time
        
        # 存储到缓存
        if self.cache_enabled:
            if len(self._preflop_cache) >= self.cache_max_size:
                # 简单的LRU：删除一半旧条目
                keys_to_remove = list(self._preflop_cache.keys())[:self.cache_max_size // 2]
                for key in keys_to_remove:
                    del self._preflop_cache[key]
            
            self._preflop_cache[cache_key] = result.copy()
        
        # 添加计算时间信息
        result['_meta'] = {
            'calculation_time': f"{calculation_time:.3f}s",
            'simulation_count': self.simulation_count,
            'performance_level': self.performance_name,
            'from_cache': False
        }
        
        return result
    
    def calculate_postflop_odds(self, player_hands: List[List[Card]], 
                               community_cards: List[Card]) -> Dict[str, float]:
        """
        计算翻牌后胜率（带缓存）
        
        Args:
            player_hands: 每个玩家的手牌列表
            community_cards: 已发出的公共牌
            
        Returns:
            Dict: 每个玩家的胜率
        """
        if not player_hands or not community_cards:
            return {}
        
        # 检查缓存
        cache_key = self._generate_cache_key(player_hands, community_cards)
        if self.cache_enabled and cache_key in self._postflop_cache:
            self.cache_hits += 1
            cached_result = self._postflop_cache[cache_key].copy()
            cached_result['_meta']['from_cache'] = True
            return cached_result
        
        self.cache_misses += 1
        self.total_calculations += 1
        
        # 执行计算
        start_time = time.time()
        result = self._calculate_postflop_odds_core(player_hands, community_cards)
        calculation_time = time.time() - start_time
        
        # 存储到缓存
        if self.cache_enabled:
            if len(self._postflop_cache) >= self.cache_max_size:
                # 简单的LRU：删除一半旧条目
                keys_to_remove = list(self._postflop_cache.keys())[:self.cache_max_size // 2]
                for key in keys_to_remove:
                    del self._postflop_cache[key]
            
            self._postflop_cache[cache_key] = result.copy()
        
        # 添加计算时间信息
        result['_meta'] = {
            'calculation_time': f"{calculation_time:.3f}s",
            'simulation_count': self.simulation_count,
            'performance_level': self.performance_name,
            'from_cache': False
        }
        
        return result
    
    def _calculate_preflop_odds_core(self, player_hands: List[List[Card]], 
                                   num_opponents: int) -> Dict[str, float]:
        """翻牌前胜率计算核心逻辑"""
        # 创建已知牌列表
        known_cards = []
        for hand in player_hands:
            known_cards.extend(hand)
        
        wins = [0] * len(player_hands)
        ties = [0] * len(player_hands)
        
        # 优化：预先创建牌堆模板
        base_deck = Deck()
        for card in known_cards:
            if card in base_deck.cards:
                base_deck.cards.remove(card)
        
        for _ in range(self.simulation_count):
            # 复制牌堆而不是重新创建
            deck = Deck()
            deck.cards = base_deck.cards.copy()
            deck.shuffle()
            
            # 发5张公共牌
            community_cards = []
            for _ in range(5):
                if deck.cards:
                    community_cards.append(deck.deal_card())
            
            # 如果有额外对手，为他们发牌
            opponent_hands = []
            for _ in range(num_opponents):
                if len(deck.cards) >= 2:
                    opponent_hand = [deck.deal_card(), deck.deal_card()]
                    opponent_hands.append(opponent_hand)
            
            # 计算所有玩家的最佳手牌
            all_hands = player_hands + opponent_hands
            results = []
            
            for hand in all_hands:
                if len(hand) >= 2 and len(community_cards) == 5:
                    all_seven = hand + community_cards
                    hand_rank, kickers = HandEvaluator.evaluate_hand(all_seven)
                    results.append((hand_rank, kickers))
                else:
                    results.append(None)
            
            # 找出胜者
            if all(result is not None for result in results):
                winner_indices = self._find_winners(results)
                
                # 记录结果
                for i in range(len(player_hands)):
                    if i in winner_indices:
                        if len(winner_indices) == 1:
                            wins[i] += 1
                        else:
                            ties[i] += 1
        
        # 计算胜率
        odds = {}
        for i, hand in enumerate(player_hands):
            total_points = wins[i] + ties[i] * 0.5
            win_rate = (total_points / self.simulation_count) * 100
            player_name = f"玩家{i+1}"
            odds[player_name] = round(win_rate, 2)
        
        return odds
    
    def _calculate_postflop_odds_core(self, player_hands: List[List[Card]], 
                                    community_cards: List[Card]) -> Dict[str, float]:
        """翻牌后胜率计算核心逻辑"""
        # 创建已知牌列表
        known_cards = []
        for hand in player_hands:
            known_cards.extend(hand)
        known_cards.extend(community_cards)
        
        wins = [0] * len(player_hands)
        ties = [0] * len(player_hands)
        
        # 计算需要发的公共牌数量
        cards_needed = 5 - len(community_cards)
        
        # 优化：预先创建牌堆模板
        base_deck = Deck()
        for card in known_cards:
            if card in base_deck.cards:
                base_deck.cards.remove(card)
        
        for _ in range(self.simulation_count):
            # 复制牌堆而不是重新创建
            deck = Deck()
            deck.cards = base_deck.cards.copy()
            deck.shuffle()
            
            # 发剩余的公共牌
            final_community = community_cards.copy()
            for _ in range(cards_needed):
                if deck.cards:
                    final_community.append(deck.deal_card())
            
            # 计算所有玩家的最佳手牌
            results = []
            for hand in player_hands:
                if len(hand) >= 2 and len(final_community) == 5:
                    all_seven = hand + final_community
                    hand_rank, kickers = HandEvaluator.evaluate_hand(all_seven)
                    results.append((hand_rank, kickers))
                else:
                    results.append(None)
            
            # 找出胜者
            if all(result is not None for result in results):
                winner_indices = self._find_winners(results)
                
                # 记录结果
                for i in range(len(player_hands)):
                    if i in winner_indices:
                        if len(winner_indices) == 1:
                            wins[i] += 1
                        else:
                            ties[i] += 1
        
        # 计算胜率
        odds = {}
        for i, hand in enumerate(player_hands):
            total_points = wins[i] + ties[i] * 0.5
            win_rate = (total_points / self.simulation_count) * 100
            player_name = f"玩家{i+1}"
            odds[player_name] = round(win_rate, 2)
        
        return odds
    
    def calculate_hand_strength(self, hole_cards: List[Card], 
                               community_cards: List[Card]) -> Dict[str, any]:
        """
        计算当前手牌强度（优化版）
        
        Args:
            hole_cards: 玩家手牌
            community_cards: 公共牌
            
        Returns:
            Dict: 包含手牌强度信息的字典
        """
        if len(hole_cards) != 2:
            return {}
        
        result = {
            'current_hand': None,
            'current_rank': None,
            'outs': [],
            'draw_odds': {}
        }
        
        # 如果有公共牌，计算当前最佳手牌
        if community_cards:
            all_cards = hole_cards + community_cards
            if len(all_cards) >= 5:
                # 优化：只计算一次而不是填充到7张
                current_rank, kickers = HandEvaluator.evaluate_hand(all_cards)
                result['current_hand'] = HandEvaluator.get_hand_description(all_cards)
                result['current_rank'] = current_rank.display
        
        # 计算听牌机会（如果公共牌少于5张）
        if len(community_cards) < 5:
            result['outs'] = self._calculate_outs(hole_cards, community_cards)
            result['draw_odds'] = self._calculate_draw_odds(result['outs'], 5 - len(community_cards))
        
        return result
    
    def _find_winners(self, hand_results: List[Tuple]) -> List[int]:
        """找出获胜的玩家索引（优化版）"""
        if not hand_results:
            return []
        
        best_rank = None
        best_kickers = None
        winners = []
        
        for i, (rank, kickers) in enumerate(hand_results):
            if best_rank is None:
                best_rank = rank
                best_kickers = kickers
                winners = [i]
            else:
                comparison = HandEvaluator._is_better_hand(rank, kickers, best_rank, best_kickers)
                if comparison:
                    # 新的更好的手牌
                    best_rank = rank
                    best_kickers = kickers
                    winners = [i]
                elif not HandEvaluator._is_better_hand(best_rank, best_kickers, rank, kickers):
                    # 平局
                    winners.append(i)
        
        return winners
    
    def _calculate_outs(self, hole_cards: List[Card], 
                       community_cards: List[Card]) -> List[str]:
        """计算听牌张数（优化版）"""
        outs = []
        
        # 创建已知牌集合（使用set提高查找效率）
        known_cards = set()
        for card in hole_cards + community_cards:
            known_cards.add((card.rank.numeric_value, card.suit))
        
        # 检查同花听牌
        suit_counts = {}
        for card in hole_cards + community_cards:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        
        for suit, count in suit_counts.items():
            if count == 4:
                # 同花听牌，需要1张同花色的牌
                flush_outs = 0
                for rank in Rank:
                    if (rank.numeric_value, suit) not in known_cards:
                        flush_outs += 1
                outs.append(f"同花听牌: {flush_outs}张")
                break
        
        # 检查顺子听牌（优化版）
        ranks = sorted([card.rank.numeric_value for card in hole_cards + community_cards])
        unique_ranks = list(set(ranks))
        
        if len(unique_ranks) >= 4:
            # 检查连续性
            for i in range(len(unique_ranks) - 3):
                consecutive = 0
                for j in range(i, len(unique_ranks)):
                    if j == i or unique_ranks[j] == unique_ranks[j-1] + 1:
                        consecutive += 1
                    else:
                        break
                
                if consecutive >= 4:
                    outs.append("可能的顺子听牌")
                    break
        
        return outs
    
    def _calculate_draw_odds(self, outs: List[str], cards_to_come: int) -> Dict[str, float]:
        """计算听牌成功概率（优化版）"""
        draw_odds = {}
        
        if not outs:
            return draw_odds
        
        # 简化计算：假设有9张outs（同花听牌）
        estimated_outs = 9
        unknown_cards = 47  # 52 - 2(hole) - 3(flop)，根据实际情况调整
        
        if cards_to_come == 1:
            # 只剩一张牌
            odds = (estimated_outs / unknown_cards) * 100
            draw_odds['下一张牌'] = round(odds, 2)
        elif cards_to_come == 2:
            # 还有两张牌
            # 使用更精确的公式
            turn_miss = (unknown_cards - estimated_outs) / unknown_cards
            river_hit = estimated_outs / (unknown_cards - 1)
            turn_hit = estimated_outs / unknown_cards
            
            total_odds = (turn_hit + turn_miss * river_hit) * 100
            draw_odds['转牌+河牌'] = round(total_odds, 2)
        
        return draw_odds


# ============================================================================
# AI决策专用方法
# ============================================================================

class AIEquityCalculator:
    """
    AI决策专用的快速胜率计算器
    使用较少的模拟次数以换取更快的响应速度
    """
    
    def __init__(self, simulation_count: int = 500):
        # 使用更少的模拟次数以加快AI决策；基准测试可降低次数以缩短整轮门禁运行时间
        self._calculator = OptimizedOddsCalculator(PerformanceLevel.FAST)
        self._equity_cache = {}
        self._cache_max_size = 500
        self.simulation_count = max(1, int(simulation_count))
    
    def get_equity(self, hole_cards: List[Card], community_cards: List[Card],
                  num_opponents: int = 1) -> float:
        """
        快速计算手牌对抗多个随机对手的胜率
        
        Args:
            hole_cards: 玩家手牌 (2张)
            community_cards: 公共牌 (0-5张)
            num_opponents: 对手数量
            
        Returns:
            float: 胜率 (0.0 - 1.0)
        """
        if not hole_cards or len(hole_cards) != 2:
            return 0.5
        
        # 生成缓存键
        cache_key = self._make_cache_key(hole_cards, community_cards, num_opponents)
        
        if cache_key in self._equity_cache:
            return self._equity_cache[cache_key]
        
        # 计算胜率
        equity = self._calculate_equity(hole_cards, community_cards, num_opponents)
        
        # 缓存结果
        if len(self._equity_cache) >= self._cache_max_size:
            # 清除一半缓存
            keys_to_remove = list(self._equity_cache.keys())[:self._cache_max_size // 2]
            for key in keys_to_remove:
                del self._equity_cache[key]
        
        self._equity_cache[cache_key] = equity
        return equity
    
    def _make_cache_key(self, hole_cards: List[Card], community_cards: List[Card],
                       num_opponents: int) -> str:
        """生成缓存键"""
        hole_str = "-".join(sorted(str(c) for c in hole_cards))
        comm_str = "-".join(sorted(str(c) for c in community_cards)) if community_cards else "none"
        return f"{hole_str}|{comm_str}|{num_opponents}"
    
    def _calculate_equity(self, hole_cards: List[Card], community_cards: List[Card],
                         num_opponents: int) -> float:
        """执行蒙特卡洛模拟计算胜率"""
        if not community_cards:
            # 翻牌前: 简化计算
            return self._preflop_equity(hole_cards, num_opponents)
        
        # 翻牌后: 使用蒙特卡洛模拟
        return self._postflop_equity(hole_cards, community_cards, num_opponents)
    
    def _preflop_equity(self, hole_cards: List[Card], num_opponents: int) -> float:
        """翻牌前胜率估算"""
        wins = 0
        ties = 0
        simulations = self.simulation_count
        
        # 创建基础牌堆
        base_deck = Deck()
        for card in hole_cards:
            if card in base_deck.cards:
                base_deck.cards.remove(card)
        
        for _ in range(simulations):
            deck = Deck()
            deck.cards = base_deck.cards.copy()
            deck.shuffle()
            
            # 生成对手手牌
            opponent_hands = []
            for _ in range(num_opponents):
                opp_hand = [deck.cards.pop(), deck.cards.pop()]
                opponent_hands.append(opp_hand)
            
            # 生成公共牌
            community = [deck.cards.pop() for _ in range(5)]
            
            # 评估所有手牌
            my_cards = hole_cards + community
            my_rank, my_kickers = HandEvaluator.evaluate_hand(my_cards)
            
            i_win = True
            is_tie = False
            
            for opp_hand in opponent_hands:
                opp_cards = opp_hand + community
                opp_rank, opp_kickers = HandEvaluator.evaluate_hand(opp_cards)
                
                if HandEvaluator._is_better_hand(opp_rank, opp_kickers, my_rank, my_kickers):
                    i_win = False
                    break
                elif not HandEvaluator._is_better_hand(my_rank, my_kickers, opp_rank, opp_kickers):
                    is_tie = True
            
            if i_win:
                if is_tie:
                    ties += 1
                else:
                    wins += 1
        
        return (wins + ties * 0.5) / simulations
    
    def _postflop_equity(self, hole_cards: List[Card], community_cards: List[Card],
                        num_opponents: int) -> float:
        """翻牌后胜率计算"""
        wins = 0
        ties = 0
        simulations = self.simulation_count
        cards_to_come = 5 - len(community_cards)
        
        # 创建基础牌堆
        base_deck = Deck()
        for card in hole_cards + community_cards:
            if card in base_deck.cards:
                base_deck.cards.remove(card)
        
        for _ in range(simulations):
            deck = Deck()
            deck.cards = base_deck.cards.copy()
            deck.shuffle()
            
            # 生成对手手牌
            opponent_hands = []
            for _ in range(num_opponents):
                opp_hand = [deck.cards.pop(), deck.cards.pop()]
                opponent_hands.append(opp_hand)
            
            # 完成公共牌
            full_community = list(community_cards)
            for _ in range(cards_to_come):
                full_community.append(deck.cards.pop())
            
            # 评估所有手牌
            my_cards = hole_cards + full_community
            my_rank, my_kickers = HandEvaluator.evaluate_hand(my_cards)
            
            i_win = True
            is_tie = False
            
            for opp_hand in opponent_hands:
                opp_cards = opp_hand + full_community
                opp_rank, opp_kickers = HandEvaluator.evaluate_hand(opp_cards)
                
                if HandEvaluator._is_better_hand(opp_rank, opp_kickers, my_rank, my_kickers):
                    i_win = False
                    break
                elif not HandEvaluator._is_better_hand(my_rank, my_kickers, opp_rank, opp_kickers):
                    is_tie = True
            
            if i_win:
                if is_tie:
                    ties += 1
                else:
                    wins += 1
        
        return (wins + ties * 0.5) / simulations


# 全局单例
_ai_equity_calculator: Optional[AIEquityCalculator] = None
_odds_calculator: Optional[OptimizedOddsCalculator] = None


def get_ai_equity_calculator(simulation_count: int | None = None) -> AIEquityCalculator:
    """获取AI专用胜率计算器单例"""
    global _ai_equity_calculator
    requested_simulation_count = 500 if simulation_count is None else simulation_count
    if _ai_equity_calculator is None:
        _ai_equity_calculator = AIEquityCalculator(simulation_count=requested_simulation_count)
    elif simulation_count is not None and getattr(_ai_equity_calculator, "simulation_count", 500) != requested_simulation_count:
        _ai_equity_calculator = AIEquityCalculator(simulation_count=requested_simulation_count)
    return _ai_equity_calculator


def get_odds_calculator() -> OptimizedOddsCalculator:
    """获取通用胜率计算器单例"""
    global _odds_calculator
    if _odds_calculator is None:
        _odds_calculator = OptimizedOddsCalculator(PerformanceLevel.NORMAL)
    return _odds_calculator


# 向后兼容的工厂函数
def create_odds_calculator(fast_mode: bool = False) -> OptimizedOddsCalculator:
    """
    创建胜率计算器的工厂函数
    
    Args:
        fast_mode: 是否使用快速模式
        
    Returns:
        OptimizedOddsCalculator: 优化版胜率计算器实例
    """
    if fast_mode:
        return OptimizedOddsCalculator(PerformanceLevel.FAST)
    else:
        return OptimizedOddsCalculator(PerformanceLevel.NORMAL)


# 兼容性别名
OddsCalculator = OptimizedOddsCalculator
