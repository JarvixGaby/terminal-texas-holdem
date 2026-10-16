#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏 - SQLite数据库层
提供统一的数据存储和查询接口，替代JSON文件存储
"""

import sqlite3
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class GameRecord:
    """游戏记录"""
    id: str
    timestamp: float
    date_time: str
    small_blind: int
    big_blind: int
    dealer_position: int
    total_pot: int
    duration_seconds: float
    ai_styles: Optional[Dict[str, str]] = None
    players: Optional[List[str]] = None
    winner_names: Optional[List[str]] = None


@dataclass
class PlayerInGame:
    """玩家在单局游戏中的记录"""
    game_id: str
    player_name: str
    hole_cards: List[str]
    final_chips: int
    is_winner: bool
    hand_rank: str
    winnings: int


@dataclass
class ActionRecord:
    """玩家动作记录"""
    id: Optional[int]
    game_id: str
    phase: str
    player_name: str
    action: str
    amount: int
    timestamp: float
    chips_before: int = 0
    chips_after: int = 0


@dataclass
class PlayerStats:
    """玩家统计数据"""
    player_name: str
    total_hands: int = 0
    total_bets: int = 0
    total_raises: int = 0
    total_calls: int = 0
    total_folds: int = 0
    total_checks: int = 0
    showdowns_won: int = 0
    showdowns_total: int = 0
    total_winnings: int = 0
    total_losses: int = 0
    updated_at: float = 0.0


# ============================================================================
# 数据库管理器
# ============================================================================

class DatabaseManager:
    """SQLite数据库管理器"""
    
    # 数据库版本，用于未来的迁移
    DB_VERSION = 1
    
    def __init__(self, db_path: str = "poker_game.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        try:
            yield self._connection
        except Exception as e:
            self._connection.rollback()
            raise e
    
    def _initialize_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建游戏表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    date_time TEXT NOT NULL,
                    small_blind INTEGER NOT NULL,
                    big_blind INTEGER NOT NULL,
                    dealer_position INTEGER NOT NULL,
                    total_pot INTEGER DEFAULT 0,
                    duration_seconds REAL DEFAULT 0,
                    ai_styles TEXT,
                    players TEXT,
                    winner_names TEXT
                )
            ''')
            
            # 创建玩家单局记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players_in_game (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    hole_cards TEXT,
                    final_chips INTEGER DEFAULT 0,
                    is_winner BOOLEAN DEFAULT 0,
                    hand_rank TEXT,
                    winnings INTEGER DEFAULT 0,
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            ''')
            
            # 创建动作记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount INTEGER DEFAULT 0,
                    timestamp REAL NOT NULL,
                    chips_before INTEGER DEFAULT 0,
                    chips_after INTEGER DEFAULT 0,
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            ''')
            
            # 创建玩家统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_stats (
                    player_name TEXT PRIMARY KEY,
                    total_hands INTEGER DEFAULT 0,
                    total_bets INTEGER DEFAULT 0,
                    total_raises INTEGER DEFAULT 0,
                    total_calls INTEGER DEFAULT 0,
                    total_folds INTEGER DEFAULT 0,
                    total_checks INTEGER DEFAULT 0,
                    showdowns_won INTEGER DEFAULT 0,
                    showdowns_total INTEGER DEFAULT 0,
                    total_winnings INTEGER DEFAULT 0,
                    total_losses INTEGER DEFAULT 0,
                    updated_at REAL DEFAULT 0
                )
            ''')
            
            # 创建数据库版本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # 设置数据库版本
            cursor.execute('''
                INSERT OR REPLACE INTO db_meta (key, value) VALUES ('version', ?)
            ''', (str(self.DB_VERSION),))
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_timestamp ON games(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_game_id ON actions(game_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_players_in_game_game_id ON players_in_game(game_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_players_in_game_player ON players_in_game(player_name)')
            
            conn.commit()
    
    # ========================================================================
    # 游戏记录操作
    # ========================================================================
    
    def save_game(self, game: GameRecord) -> bool:
        """
        保存游戏记录
        
        Args:
            game: 游戏记录对象
            
        Returns:
            是否保存成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO games 
                    (id, timestamp, date_time, small_blind, big_blind, dealer_position,
                     total_pot, duration_seconds, ai_styles, players, winner_names)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    game.id,
                    game.timestamp,
                    game.date_time,
                    game.small_blind,
                    game.big_blind,
                    game.dealer_position,
                    game.total_pot,
                    game.duration_seconds,
                    json.dumps(game.ai_styles) if game.ai_styles else None,
                    json.dumps(game.players) if game.players else None,
                    json.dumps(game.winner_names) if game.winner_names else None
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"保存游戏记录失败: {e}")
            return False
    
    def get_game(self, game_id: str) -> Optional[GameRecord]:
        """
        获取单个游戏记录
        
        Args:
            game_id: 游戏ID
            
        Returns:
            游戏记录或None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM games WHERE id = ?', (game_id,))
                row = cursor.fetchone()
                
                if row:
                    return GameRecord(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        date_time=row['date_time'],
                        small_blind=row['small_blind'],
                        big_blind=row['big_blind'],
                        dealer_position=row['dealer_position'],
                        total_pot=row['total_pot'],
                        duration_seconds=row['duration_seconds'],
                        ai_styles=json.loads(row['ai_styles']) if row['ai_styles'] else None,
                        players=json.loads(row['players']) if row['players'] else None,
                        winner_names=json.loads(row['winner_names']) if row['winner_names'] else None
                    )
                return None
        except sqlite3.Error as e:
            print(f"获取游戏记录失败: {e}")
            return None
    
    def get_recent_games(self, limit: int = 20, offset: int = 0) -> List[GameRecord]:
        """
        获取最近的游戏记录
        
        Args:
            limit: 返回记录数量
            offset: 偏移量（用于分页）
            
        Returns:
            游戏记录列表
        """
        games = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM games 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                for row in cursor.fetchall():
                    games.append(GameRecord(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        date_time=row['date_time'],
                        small_blind=row['small_blind'],
                        big_blind=row['big_blind'],
                        dealer_position=row['dealer_position'],
                        total_pot=row['total_pot'],
                        duration_seconds=row['duration_seconds'],
                        ai_styles=json.loads(row['ai_styles']) if row['ai_styles'] else None,
                        players=json.loads(row['players']) if row['players'] else None,
                        winner_names=json.loads(row['winner_names']) if row['winner_names'] else None
                    ))
        except sqlite3.Error as e:
            print(f"获取游戏记录列表失败: {e}")
        return games
    
    def get_games_count(self) -> int:
        """获取游戏总数"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM games')
                return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0
    
    # ========================================================================
    # 玩家单局记录操作
    # ========================================================================
    
    def save_player_in_game(self, player: PlayerInGame) -> bool:
        """保存玩家单局记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO players_in_game 
                    (game_id, player_name, hole_cards, final_chips, is_winner, hand_rank, winnings)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    player.game_id,
                    player.player_name,
                    json.dumps(player.hole_cards),
                    player.final_chips,
                    player.is_winner,
                    player.hand_rank,
                    player.winnings
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"保存玩家单局记录失败: {e}")
            return False
    
    def get_players_in_game(self, game_id: str) -> List[PlayerInGame]:
        """获取某局游戏的所有玩家记录"""
        players = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM players_in_game WHERE game_id = ?
                ''', (game_id,))
                
                for row in cursor.fetchall():
                    players.append(PlayerInGame(
                        game_id=row['game_id'],
                        player_name=row['player_name'],
                        hole_cards=json.loads(row['hole_cards']) if row['hole_cards'] else [],
                        final_chips=row['final_chips'],
                        is_winner=bool(row['is_winner']),
                        hand_rank=row['hand_rank'] or '',
                        winnings=row['winnings']
                    ))
        except sqlite3.Error as e:
            print(f"获取玩家单局记录失败: {e}")
        return players
    
    # ========================================================================
    # 动作记录操作
    # ========================================================================
    
    def save_action(self, action: ActionRecord) -> bool:
        """保存动作记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO actions 
                    (game_id, phase, player_name, action, amount, timestamp, chips_before, chips_after)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action.game_id,
                    action.phase,
                    action.player_name,
                    action.action,
                    action.amount,
                    action.timestamp,
                    action.chips_before,
                    action.chips_after
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"保存动作记录失败: {e}")
            return False
    
    def save_actions_batch(self, actions: List[ActionRecord]) -> bool:
        """批量保存动作记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO actions 
                    (game_id, phase, player_name, action, amount, timestamp, chips_before, chips_after)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', [
                    (a.game_id, a.phase, a.player_name, a.action, a.amount, 
                     a.timestamp, a.chips_before, a.chips_after)
                    for a in actions
                ])
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"批量保存动作记录失败: {e}")
            return False
    
    def get_actions_for_game(self, game_id: str) -> List[ActionRecord]:
        """获取某局游戏的所有动作"""
        actions = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM actions WHERE game_id = ? ORDER BY timestamp
                ''', (game_id,))
                
                for row in cursor.fetchall():
                    actions.append(ActionRecord(
                        id=row['id'],
                        game_id=row['game_id'],
                        phase=row['phase'],
                        player_name=row['player_name'],
                        action=row['action'],
                        amount=row['amount'],
                        timestamp=row['timestamp'],
                        chips_before=row['chips_before'],
                        chips_after=row['chips_after']
                    ))
        except sqlite3.Error as e:
            print(f"获取动作记录失败: {e}")
        return actions
    
    # ========================================================================
    # 玩家统计操作
    # ========================================================================
    
    def get_player_stats(self, player_name: str) -> Optional[PlayerStats]:
        """获取玩家统计数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM player_stats WHERE player_name = ?', (player_name,))
                row = cursor.fetchone()
                
                if row:
                    return PlayerStats(
                        player_name=row['player_name'],
                        total_hands=row['total_hands'],
                        total_bets=row['total_bets'],
                        total_raises=row['total_raises'],
                        total_calls=row['total_calls'],
                        total_folds=row['total_folds'],
                        total_checks=row['total_checks'],
                        showdowns_won=row['showdowns_won'],
                        showdowns_total=row['showdowns_total'],
                        total_winnings=row['total_winnings'],
                        total_losses=row['total_losses'],
                        updated_at=row['updated_at']
                    )
                return None
        except sqlite3.Error as e:
            print(f"获取玩家统计失败: {e}")
            return None
    
    def save_player_stats(self, stats: PlayerStats) -> bool:
        """保存/更新玩家统计数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO player_stats 
                    (player_name, total_hands, total_bets, total_raises, total_calls,
                     total_folds, total_checks, showdowns_won, showdowns_total,
                     total_winnings, total_losses, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stats.player_name,
                    stats.total_hands,
                    stats.total_bets,
                    stats.total_raises,
                    stats.total_calls,
                    stats.total_folds,
                    stats.total_checks,
                    stats.showdowns_won,
                    stats.showdowns_total,
                    stats.total_winnings,
                    stats.total_losses,
                    time.time()
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"保存玩家统计失败: {e}")
            return False
    
    def update_player_action_stats(self, player_name: str, action: str, amount: int = 0):
        """更新玩家动作统计"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 确保玩家记录存在
                cursor.execute('''
                    INSERT OR IGNORE INTO player_stats (player_name, updated_at)
                    VALUES (?, ?)
                ''', (player_name, time.time()))
                
                # 更新对应的动作计数
                action_column_map = {
                    'bet': 'total_bets',
                    'raise': 'total_raises',
                    'call': 'total_calls',
                    'fold': 'total_folds',
                    'check': 'total_checks'
                }
                
                column = action_column_map.get(action.lower())
                if column:
                    cursor.execute(f'''
                        UPDATE player_stats 
                        SET {column} = {column} + 1, updated_at = ?
                        WHERE player_name = ?
                    ''', (time.time(), player_name))
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"更新玩家动作统计失败: {e}")
    
    def update_player_hand_stats(self, player_name: str, won_showdown: Optional[bool] = None,
                                  winnings: int = 0):
        """更新玩家手牌统计"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 确保玩家记录存在
                cursor.execute('''
                    INSERT OR IGNORE INTO player_stats (player_name, updated_at)
                    VALUES (?, ?)
                ''', (player_name, time.time()))
                
                # 更新手牌数
                cursor.execute('''
                    UPDATE player_stats 
                    SET total_hands = total_hands + 1, updated_at = ?
                    WHERE player_name = ?
                ''', (time.time(), player_name))
                
                # 更新摊牌统计
                if won_showdown is not None:
                    cursor.execute('''
                        UPDATE player_stats 
                        SET showdowns_total = showdowns_total + 1,
                            showdowns_won = showdowns_won + ?,
                            updated_at = ?
                        WHERE player_name = ?
                    ''', (1 if won_showdown else 0, time.time(), player_name))
                
                # 更新盈亏
                if winnings > 0:
                    cursor.execute('''
                        UPDATE player_stats 
                        SET total_winnings = total_winnings + ?, updated_at = ?
                        WHERE player_name = ?
                    ''', (winnings, time.time(), player_name))
                elif winnings < 0:
                    cursor.execute('''
                        UPDATE player_stats 
                        SET total_losses = total_losses + ?, updated_at = ?
                        WHERE player_name = ?
                    ''', (abs(winnings), time.time(), player_name))
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"更新玩家手牌统计失败: {e}")
    
    def get_all_player_stats(self) -> List[PlayerStats]:
        """获取所有玩家统计"""
        stats_list = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM player_stats ORDER BY total_hands DESC')
                
                for row in cursor.fetchall():
                    stats_list.append(PlayerStats(
                        player_name=row['player_name'],
                        total_hands=row['total_hands'],
                        total_bets=row['total_bets'],
                        total_raises=row['total_raises'],
                        total_calls=row['total_calls'],
                        total_folds=row['total_folds'],
                        total_checks=row['total_checks'],
                        showdowns_won=row['showdowns_won'],
                        showdowns_total=row['showdowns_total'],
                        total_winnings=row['total_winnings'],
                        total_losses=row['total_losses'],
                        updated_at=row['updated_at']
                    ))
        except sqlite3.Error as e:
            print(f"获取所有玩家统计失败: {e}")
        return stats_list
    
    # ========================================================================
    # 高级查询
    # ========================================================================
    
    def get_player_game_history(self, player_name: str, limit: int = 50) -> List[Dict]:
        """获取玩家的游戏历史（带详细信息）"""
        history = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT g.*, p.hole_cards, p.final_chips, p.is_winner, 
                           p.hand_rank, p.winnings
                    FROM games g
                    JOIN players_in_game p ON g.id = p.game_id
                    WHERE p.player_name = ?
                    ORDER BY g.timestamp DESC
                    LIMIT ?
                ''', (player_name, limit))
                
                for row in cursor.fetchall():
                    history.append({
                        'game_id': row['id'],
                        'date_time': row['date_time'],
                        'total_pot': row['total_pot'],
                        'hole_cards': json.loads(row['hole_cards']) if row['hole_cards'] else [],
                        'final_chips': row['final_chips'],
                        'is_winner': bool(row['is_winner']),
                        'hand_rank': row['hand_rank'],
                        'winnings': row['winnings'],
                        'winner_names': json.loads(row['winner_names']) if row['winner_names'] else []
                    })
        except sqlite3.Error as e:
            print(f"获取玩家游戏历史失败: {e}")
        return history
    
    def get_player_chip_history(self, player_name: str, limit: int = 50) -> List[Tuple[str, int]]:
        """获取玩家筹码变化历史"""
        chip_history = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT g.date_time, p.final_chips
                    FROM games g
                    JOIN players_in_game p ON g.id = p.game_id
                    WHERE p.player_name = ?
                    ORDER BY g.timestamp ASC
                    LIMIT ?
                ''', (player_name, limit))
                
                for row in cursor.fetchall():
                    chip_history.append((row['date_time'], row['final_chips']))
        except sqlite3.Error as e:
            print(f"获取玩家筹码历史失败: {e}")
        return chip_history
    
    def get_player_position_stats(self, player_name: str) -> Dict[str, Dict]:
        """获取玩家在不同位置的表现统计"""
        # 这需要在动作记录中包含位置信息，暂时返回基础统计
        stats = self.get_player_stats(player_name)
        if not stats:
            return {}
        
        # 计算基础指标
        total_actions = (stats.total_bets + stats.total_raises + 
                        stats.total_calls + stats.total_folds + stats.total_checks)
        
        vpip = 0.0
        pfr = 0.0
        aggression = 0.0
        
        if stats.total_hands > 0:
            vpip = (stats.total_calls + stats.total_bets + stats.total_raises) / stats.total_hands * 100
            pfr = stats.total_raises / stats.total_hands * 100
        
        if stats.total_calls > 0:
            aggression = (stats.total_bets + stats.total_raises) / stats.total_calls
        
        win_rate = 0.0
        if stats.showdowns_total > 0:
            win_rate = stats.showdowns_won / stats.showdowns_total * 100
        
        return {
            'summary': {
                'total_hands': stats.total_hands,
                'vpip': round(vpip, 1),
                'pfr': round(pfr, 1),
                'aggression': round(aggression, 2),
                'showdown_win_rate': round(win_rate, 1),
                'net_profit': stats.total_winnings - stats.total_losses
            }
        }
    
    # ========================================================================
    # 数据迁移
    # ========================================================================
    
    def migrate_from_json(self, json_file: str = "game_history.json", 
                         stats_file: str = "player_stats.json") -> Tuple[int, int]:
        """
        从JSON文件迁移数据到SQLite
        
        Args:
            json_file: 游戏历史JSON文件路径
            stats_file: 玩家统计JSON文件路径
            
        Returns:
            (迁移的游戏数, 迁移的统计数)
        """
        games_migrated = 0
        stats_migrated = 0
        
        # 迁移游戏历史
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)
                
                for game_data in games_data:
                    # 保存游戏基本信息
                    game = GameRecord(
                        id=game_data.get('game_id', f"migrated_{games_migrated}"),
                        timestamp=game_data.get('timestamp', time.time()),
                        date_time=game_data.get('date_time', ''),
                        small_blind=game_data.get('small_blind', 5),
                        big_blind=game_data.get('big_blind', 10),
                        dealer_position=game_data.get('dealer_position', 0),
                        total_pot=game_data.get('total_pot', 0),
                        duration_seconds=game_data.get('duration_seconds', 0),
                        ai_styles=game_data.get('ai_styles'),
                        players=game_data.get('players', []),
                        winner_names=game_data.get('winner_names', [])
                    )
                    
                    if self.save_game(game):
                        games_migrated += 1
                        
                        # 保存玩家单局记录
                        for hand in game_data.get('final_hands', []):
                            player_record = PlayerInGame(
                                game_id=game.id,
                                player_name=hand.get('player_name', ''),
                                hole_cards=hand.get('hole_cards', []),
                                final_chips=hand.get('final_chips', 0),
                                is_winner=hand.get('player_name', '') in game_data.get('winner_names', []),
                                hand_rank=hand.get('hand_rank', ''),
                                winnings=hand.get('winnings', 0)
                            )
                            self.save_player_in_game(player_record)
                        
                        # 保存动作记录
                        for phase_data in game_data.get('phases', []):
                            for action_data in phase_data.get('actions', []):
                                action = ActionRecord(
                                    id=None,
                                    game_id=game.id,
                                    phase=phase_data.get('phase', ''),
                                    player_name=action_data.get('player_name', ''),
                                    action=action_data.get('action', ''),
                                    amount=action_data.get('amount', 0),
                                    timestamp=action_data.get('timestamp', time.time()),
                                    chips_before=action_data.get('chips_before', 0),
                                    chips_after=action_data.get('chips_after', 0)
                                )
                                self.save_action(action)
                
                print(f"✅ 成功迁移 {games_migrated} 局游戏记录")
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"❌ 迁移游戏历史失败: {e}")
        
        # 迁移玩家统计
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats_data = json.load(f)
                
                for player_name, data in stats_data.items():
                    stats = PlayerStats(
                        player_name=player_name,
                        total_hands=data.get('hands_played', 0),
                        total_bets=data.get('total_bets', 0),
                        total_raises=data.get('total_raises', 0),
                        total_calls=data.get('total_calls', 0),
                        total_folds=data.get('total_folds', 0),
                        total_checks=data.get('total_checks', 0),
                        showdowns_won=data.get('showdowns_won', 0),
                        showdowns_total=data.get('showdowns_total', 0)
                    )
                    
                    if self.save_player_stats(stats):
                        stats_migrated += 1
                
                print(f"✅ 成功迁移 {stats_migrated} 个玩家统计")
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"❌ 迁移玩家统计失败: {e}")
        
        return games_migrated, stats_migrated
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None


# ============================================================================
# 全局数据库实例
# ============================================================================

_db_instance: Optional[DatabaseManager] = None


def get_database(db_path: str = "poker_game.db") -> DatabaseManager:
    """获取数据库单例实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance


def reset_database():
    """重置数据库实例（主要用于测试）"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
    _db_instance = None


# ============================================================================
# 命令行工具
# ============================================================================

if __name__ == "__main__":
    import sys
    
    db = get_database()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            # 执行数据迁移
            print("🔄 开始数据迁移...")
            games, stats = db.migrate_from_json()
            print(f"📊 迁移完成: {games} 局游戏, {stats} 个玩家统计")
            
        elif command == "stats":
            # 显示统计信息
            print(f"📊 数据库统计:")
            print(f"   游戏总数: {db.get_games_count()}")
            all_stats = db.get_all_player_stats()
            print(f"   玩家总数: {len(all_stats)}")
            
        elif command == "test":
            # 测试数据库功能
            print("🧪 测试数据库功能...")
            
            # 创建测试游戏
            test_game = GameRecord(
                id=f"test_{int(time.time())}",
                timestamp=time.time(),
                date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                small_blind=5,
                big_blind=10,
                dealer_position=0,
                total_pot=100,
                duration_seconds=60.0,
                players=["Player1", "AI_Alice"],
                winner_names=["Player1"]
            )
            
            if db.save_game(test_game):
                print("✅ 游戏保存成功")
                
                retrieved = db.get_game(test_game.id)
                if retrieved:
                    print(f"✅ 游戏读取成功: {retrieved.id}")
                
            print("🧪 测试完成!")
    else:
        print("用法: python database.py [migrate|stats|test]")


