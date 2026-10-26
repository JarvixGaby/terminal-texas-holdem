# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 历史牌局记录系统
实现牌局记录、存储和查询功能
"""

import json
import os
import tempfile
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from texas_holdem.engine.card import Card, Suit, Rank


@dataclass
class PlayerAction:
    """玩家动作记录"""
    player_name: str
    action: str  # fold, check, call, raise
    amount: int
    chips_before: int
    chips_after: int
    timestamp: float
    decision_evaluation: Optional[Dict[str, Any]] = None
    action_metadata: Optional[Dict[str, Any]] = None


@dataclass
class GamePhase:
    """游戏阶段记录"""
    phase: str  # preflop, flop, turn, river, showdown
    community_cards: List[str]  # 公共牌的字符串表示
    pot_size: int
    current_bet: int
    actions: List[PlayerAction]


@dataclass
class PlayerHand:
    """玩家手牌记录"""
    player_name: str
    hole_cards: List[str]  # 底牌的字符串表示
    final_chips: int
    is_winner: bool
    hand_rank: str  # 最终牌型
    winnings: int  # 赢得的筹码


@dataclass
class GameRecord:
    """完整的牌局记录"""
    game_id: str
    timestamp: float
    date_time: str
    players: List[str]  # 玩家名单
    small_blind: int
    big_blind: int
    dealer_position: int
    phases: List[GamePhase]
    final_hands: List[PlayerHand]
    total_pot: int
    winner_names: List[str]
    duration_seconds: float
    ai_styles: Optional[Dict[str, str]] = None  # AI玩家的实际分配风格
    outcome_metadata: Dict[str, Any] = field(default_factory=dict)


class GameHistoryManager:
    """历史牌局管理器"""
    
    def __init__(self, history_file: str = "game_history.json"):
        """
        初始化历史管理器
        
        Args:
            history_file: 历史记录文件路径
        """
        self.history_file = history_file
        self.current_game_record: Optional[GameRecord] = None
        self.game_start_time: Optional[float] = None
        
    def start_new_game_record(self, players: List[str], small_blind: int, 
                             big_blind: int, dealer_position: int) -> str:
        """
        开始新的牌局记录
        
        Args:
            players: 玩家名单
            small_blind: 小盲注
            big_blind: 大盲注
            dealer_position: 庄家位置
            
        Returns:
            str: 游戏ID
        """
        game_id = self._generate_game_id()
        timestamp = time.time()
        self.game_start_time = timestamp
        
        self.current_game_record = GameRecord(
            game_id=game_id,
            timestamp=timestamp,
            date_time=datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            players=players,
            small_blind=small_blind,
            big_blind=big_blind,
            dealer_position=dealer_position,
            phases=[],
            final_hands=[],
            total_pot=0,
            winner_names=[],
            duration_seconds=0.0,
            ai_styles={},  # 初始化AI风格字典
            outcome_metadata={},
        )
        
        return game_id
    
    def start_new_phase(self, phase: str, community_cards: List[Card], 
                       pot_size: int, current_bet: int):
        """开始新的游戏阶段"""
        if not self.current_game_record:
            return
        
        community_cards_str = [str(card) for card in community_cards]
        
        new_phase = GamePhase(
            phase=phase,
            community_cards=community_cards_str,
            pot_size=pot_size,
            current_bet=current_bet,
            actions=[]
        )
        
        self.current_game_record.phases.append(new_phase)
    
    def record_action(self, player_name: str, action: str, amount: int,
                     chips_before: int, chips_after: int,
                     decision_evaluation: Optional[Dict[str, Any]] = None,
                     action_metadata: Optional[Dict[str, Any]] = None):
        """记录玩家动作"""
        if not self.current_game_record or not self.current_game_record.phases:
            return
        
        player_action = PlayerAction(
            player_name=player_name,
            action=action,
            amount=amount,
            chips_before=chips_before,
            chips_after=chips_after,
            timestamp=time.time(),
            decision_evaluation=decision_evaluation,
            action_metadata=action_metadata,
        )
        
        # 添加到当前阶段
        current_phase = self.current_game_record.phases[-1]
        current_phase.actions.append(player_action)
    
    def record_ai_styles(self, ai_styles: Dict[str, str]):
        """记录AI玩家的实际分配风格"""
        if not self.current_game_record:
            return
        self.current_game_record.ai_styles = ai_styles
    
    def get_current_game_record(self) -> Optional[Dict]:
        """
        获取当前游戏记录（转换为字典格式，用于即时复盘）
        
        Returns:
            游戏记录字典，如果没有当前游戏则返回None
        """
        if not self.current_game_record:
            return None
        
        record = self.current_game_record
        
        return {
            'game_id': record.game_id,
            'timestamp': record.timestamp,
            'date_time': record.date_time,
            'players': record.players,
            'small_blind': record.small_blind,
            'big_blind': record.big_blind,
            'dealer_position': record.dealer_position,
            'phases': [
                {
                    'phase': phase.phase,
                    'community_cards': phase.community_cards,
                    'pot_size': phase.pot_size,
                    'current_bet': phase.current_bet,
                    'actions': [
                        {
                            'player_name': action.player_name,
                            'action': action.action,
                            'amount': action.amount,
                            'chips_before': action.chips_before,
                            'chips_after': action.chips_after,
                            'timestamp': action.timestamp,
                            'decision_evaluation': action.decision_evaluation,
                            'action_metadata': action.action_metadata,
                        }
                        for action in phase.actions
                    ]
                }
                for phase in record.phases
            ],
            'final_hands': record.final_hands,
            'total_pot': record.total_pot,
            'winner_names': record.winner_names,
            'ai_styles': record.ai_styles,
            'outcome_metadata': record.outcome_metadata
        }
    
    def finish_game(self, final_hands: List[Dict], total_pot: int, 
                   winner_names: List[str],
                   outcome_metadata: Optional[Dict[str, Any]] = None):
        """完成牌局记录"""
        if not self.current_game_record:
            return
        
        # 记录最终手牌信息
        for hand_info in final_hands:
            player_hand = PlayerHand(
                player_name=hand_info['player_name'],
                hole_cards=hand_info['hole_cards'],
                final_chips=hand_info['final_chips'],
                is_winner=hand_info['player_name'] in winner_names,
                hand_rank=hand_info.get('hand_rank', ''),
                winnings=hand_info.get('winnings', 0)
            )
            self.current_game_record.final_hands.append(player_hand)
        
        # 设置游戏结果
        self.current_game_record.total_pot = total_pot
        self.current_game_record.winner_names = winner_names
        self.current_game_record.outcome_metadata = dict(outcome_metadata or {})
        
        # 计算游戏时长
        if self.game_start_time:
            self.current_game_record.duration_seconds = time.time() - self.game_start_time
        
        # 保存到文件
        self._save_game_record()
        
        # 清空当前记录
        self.current_game_record = None
        self.game_start_time = None
    
    def get_player_history(self, player_name: str) -> Dict[str, Any]:
        """
        获取玩家历史战绩
        
        Args:
            player_name: 玩家名称
            
        Returns:
            Dict: 包含玩家统计信息的字典
        """
        games = self._load_all_games()
        
        total_games = 0
        wins = 0
        total_winnings = 0
        total_losses = 0
        
        game_details = []
        
        for game in games:
            # 检查玩家是否参与了这局游戏
            player_hand = None
            for hand in game.final_hands:
                if hand.player_name == player_name:
                    player_hand = hand
                    break
            
            if player_hand:
                total_games += 1
                if player_hand.is_winner:
                    wins += 1
                    total_winnings += player_hand.winnings
                else:
                    # 计算损失（初始筹码减去最终筹码，但需要从游戏记录中推算）
                    loss = max(0, player_hand.winnings)  # 如果winnings是负数，表示损失
                    total_losses += abs(loss)
                
                game_details.append({
                    'game_id': game.game_id,
                    'date_time': game.date_time,
                    'is_winner': player_hand.is_winner,
                    'winnings': player_hand.winnings,
                    'hand_rank': player_hand.hand_rank,
                    'total_pot': game.total_pot
                })
        
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        net_profit = total_winnings - total_losses
        
        return {
            'player_name': player_name,
            'total_games': total_games,
            'wins': wins,
            'losses': total_games - wins,
            'win_rate': round(win_rate, 2),
            'total_winnings': total_winnings,
            'total_losses': total_losses,
            'net_profit': net_profit,
            'recent_games': game_details[-10:]  # 最近10局
        }
    
    def get_game_by_id(self, game_id: str) -> Optional[GameRecord]:
        """根据游戏ID获取完整的游戏记录"""
        games = self._load_all_games()
        for game in games:
            if game.game_id == game_id:
                return game
        return None
    
    def list_recent_games(self, limit: int = 20) -> List[GameRecord]:
        """获取最近的游戏列表"""
        games = self._load_all_games()
        # 按时间戳排序，最新的在前
        games.sort(key=lambda x: x.timestamp, reverse=True)
        return games[:limit]
    
    def _generate_game_id(self) -> str:
        """生成唯一的游戏ID"""
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        return f"game_{timestamp}"
    
    def _save_game_record(self):
        """保存游戏记录到文件"""
        if not self.current_game_record:
            return
        
        # A damaged file must never be interpreted as an empty history.
        games = self._load_all_games()
        
        # 添加新记录
        games.append(self.current_game_record)
        
        # 保存到文件
        directory = os.path.dirname(os.path.abspath(self.history_file))
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=directory,
                prefix='.game_history_', suffix='.tmp', delete=False,
            ) as f:
                temp_path = f.name
                json.dump([asdict(game) for game in games], f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, self.history_file)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _load_all_games(self) -> List[GameRecord]:
        """从文件加载所有游戏记录"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                games_data = json.load(f)
                
            # 转换为GameRecord对象
            games = []
            for game_data in games_data:
                # 转换phases
                phases = []
                for phase_data in game_data.get('phases', []):
                    actions = []
                    for action_data in phase_data.get('actions', []):
                        action_data = dict(action_data)
                        action_data.setdefault('decision_evaluation', None)
                        action_data.setdefault('action_metadata', None)
                        actions.append(PlayerAction(**action_data))
                    phase = GamePhase(
                        phase=phase_data['phase'],
                        community_cards=phase_data['community_cards'],
                        pot_size=phase_data['pot_size'],
                        current_bet=phase_data['current_bet'],
                        actions=actions
                    )
                    phases.append(phase)
                
                # 转换final_hands
                final_hands = [PlayerHand(**hand_data) for hand_data in game_data.get('final_hands', [])]
                
                # 创建GameRecord
                game = GameRecord(
                    game_id=game_data['game_id'],
                    timestamp=game_data['timestamp'],
                    date_time=game_data['date_time'],
                    players=game_data['players'],
                    small_blind=game_data['small_blind'],
                    big_blind=game_data['big_blind'],
                    dealer_position=game_data['dealer_position'],
                    phases=phases,
                    final_hands=final_hands,
                    total_pot=game_data['total_pot'],
                    winner_names=game_data['winner_names'],
                    duration_seconds=game_data.get('duration_seconds', 0.0),
                    ai_styles=game_data.get('ai_styles', {}),
                    outcome_metadata=game_data.get('outcome_metadata', {})
                )
                games.append(game)
            
            return games
            
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise ValueError(f"无法读取历史牌局文件 {self.history_file}: {e}") from e
    
    @staticmethod
    def card_from_string(card_str: str) -> Card:
        """从字符串创建Card对象"""
        if len(card_str) < 2:
            raise ValueError(f"无效的卡片字符串: {card_str}")
        
        # 解析花色
        suit_char = card_str[-1]
        suit_map = {'♥': Suit.HEARTS, '♦': Suit.DIAMONDS, '♣': Suit.CLUBS, '♠': Suit.SPADES}
        if suit_char not in suit_map:
            raise ValueError(f"无效的花色: {suit_char}")
        suit = suit_map[suit_char]
        
        # 解析点数
        rank_str = card_str[:-1]
        rank_map = {
            '2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, '5': Rank.FIVE,
            '6': Rank.SIX, '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
            '10': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN, 'K': Rank.KING, 'A': Rank.ACE
        }
        if rank_str not in rank_map:
            raise ValueError(f"无效的点数: {rank_str}")
        rank = rank_map[rank_str]
        
        return Card(suit, rank)
