# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 优化数据管理系统
实现分页存储、压缩、缓存和高效的历史数据管理
"""

import json
import gzip
import os
import shutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Iterator, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import defaultdict, deque
from game_history import GameRecord, PlayerAction, GamePhase, PlayerHand
from enhanced_config_manager import get_global_config
from enhanced_logging import get_logger, LogCategory
from enhanced_error_handling import FileIOError, safe_execute


@dataclass
class DataPage:
    """数据页"""
    page_id: str
    start_date: str
    end_date: str
    record_count: int
    file_path: str
    compressed: bool = False
    last_access: float = 0.0


@dataclass
class DataIndex:
    """数据索引"""
    game_id: str
    timestamp: float
    page_id: str
    player_names: List[str]
    winner_names: List[str]
    total_pot: int
    duration: float


class MemoryCache:
    """内存缓存管理器"""
    
    def __init__(self, max_size: int = 100, max_age_seconds: int = 3600):
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_order = deque()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                
                # 检查是否过期
                if time.time() - timestamp > self.max_age_seconds:
                    self._remove_key(key)
                    return None
                
                # 更新访问顺序
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                
                return data
        return None
    
    def put(self, key: str, data: Any):
        """存储缓存数据"""
        with self.lock:
            # 如果缓存已满，移除最久未访问的项
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_oldest()
            
            self.cache[key] = (data, time.time())
            
            # 更新访问顺序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def _remove_key(self, key: str):
        """移除指定键"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def _evict_oldest(self):
        """移除最久未访问的项"""
        if self.access_order:
            oldest_key = self.access_order.popleft()
            if oldest_key in self.cache:
                del self.cache[oldest_key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            active_count = 0
            expired_count = 0
            current_time = time.time()
            
            for _, (_, timestamp) in self.cache.items():
                if current_time - timestamp > self.max_age_seconds:
                    expired_count += 1
                else:
                    active_count += 1
            
            return {
                'total_items': len(self.cache),
                'active_items': active_count,
                'expired_items': expired_count,
                'max_size': self.max_size,
                'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
            }


class OptimizedDataManager:
    """优化数据管理器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化优化数据管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 子目录
        self.pages_dir = self.data_dir / "pages"
        self.compressed_dir = self.data_dir / "compressed"
        self.backup_dir = self.data_dir / "backups"
        self.index_dir = self.data_dir / "indexes"
        
        for dir_path in [self.pages_dir, self.compressed_dir, self.backup_dir, self.index_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # 配置和日志
        self.config = get_global_config().config.data
        self.logger = get_logger()
        
        # 索引和缓存
        self.pages_index: Dict[str, DataPage] = {}
        self.data_index: Dict[str, DataIndex] = {}
        self.memory_cache = MemoryCache(max_size=50, max_age_seconds=1800)
        
        # 当前数据页
        self.current_page_id: Optional[str] = None
        self.current_page_records: List[GameRecord] = []
        
        # 性能统计
        self.stats = {
            'total_reads': 0,
            'cache_hits': 0,
            'total_writes': 0,
            'compressions': 0,
            'decompressions': 0
        }
        
        # 加载索引
        self._load_indexes()
        
        # 定期任务锁
        self._maintenance_lock = threading.Lock()
    
    def _load_indexes(self):
        """加载索引数据"""
        try:
            # 加载页面索引
            pages_index_file = self.index_dir / "pages_index.json"
            if pages_index_file.exists():
                with open(pages_index_file, 'r', encoding='utf-8') as f:
                    pages_data = json.load(f)
                    for page_id, page_data in pages_data.items():
                        self.pages_index[page_id] = DataPage(**page_data)
            
            # 加载数据索引
            data_index_file = self.index_dir / "data_index.json"
            if data_index_file.exists():
                with open(data_index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    for game_id, index_item in index_data.items():
                        self.data_index[game_id] = DataIndex(**index_item)
            
            self.logger.info(f"已加载 {len(self.pages_index)} 个数据页和 {len(self.data_index)} 条记录索引")
            
        except Exception as e:
            self.logger.error(f"加载索引失败: {e}", exception=e)
    
    def _save_indexes(self):
        """保存索引数据"""
        try:
            # 保存页面索引
            pages_index_file = self.index_dir / "pages_index.json"
            with open(pages_index_file, 'w', encoding='utf-8') as f:
                pages_data = {page_id: asdict(page) for page_id, page in self.pages_index.items()}
                json.dump(pages_data, f, ensure_ascii=False, indent=2)
            
            # 保存数据索引
            data_index_file = self.index_dir / "data_index.json"
            with open(data_index_file, 'w', encoding='utf-8') as f:
                index_data = {game_id: asdict(index) for game_id, index in self.data_index.items()}
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"保存索引失败: {e}", exception=e)
            raise FileIOError(f"保存索引失败: {e}", operation="save_indexes")
    
    def _generate_page_id(self) -> str:
        """生成数据页ID"""
        return f"page_{int(time.time() * 1000)}"
    
    def _get_current_page(self) -> str:
        """获取当前数据页ID"""
        if self.current_page_id is None:
            # 查找最新的页面或创建新页面
            latest_page = None
            latest_timestamp = 0
            
            for page_id, page in self.pages_index.items():
                if not page.compressed and page.record_count < self.config.max_history_records // 10:
                    page_timestamp = float(page.page_id.split('_')[1]) / 1000
                    if page_timestamp > latest_timestamp:
                        latest_timestamp = page_timestamp
                        latest_page = page_id
            
            if latest_page:
                self.current_page_id = latest_page
                self._load_current_page()
            else:
                self.current_page_id = self._generate_page_id()
                self.current_page_records = []
        
        return self.current_page_id
    
    def _load_current_page(self):
        """加载当前页面数据"""
        if self.current_page_id and self.current_page_id in self.pages_index:
            page = self.pages_index[self.current_page_id]
            
            # 检查缓存
            cache_key = f"page_{self.current_page_id}"
            cached_data = self.memory_cache.get(cache_key)
            if cached_data:
                self.current_page_records = cached_data
                self.stats['cache_hits'] += 1
                return
            
            try:
                file_path = Path(page.file_path)
                
                if page.compressed:
                    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                    self.stats['decompressions'] += 1
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                
                # 转换为GameRecord对象
                self.current_page_records = self._deserialize_records(data)
                
                # 更新缓存
                self.memory_cache.put(cache_key, self.current_page_records)
                
                # 更新访问时间
                page.last_access = time.time()
                
                self.stats['total_reads'] += 1
                
            except Exception as e:
                self.logger.error(f"加载页面数据失败: {e}", exception=e)
                self.current_page_records = []
    
    def _save_current_page(self):
        """保存当前页面数据"""
        if not self.current_page_id or not self.current_page_records:
            return
        
        try:
            page_file = self.pages_dir / f"{self.current_page_id}.json"
            
            # 序列化数据
            serialized_data = self._serialize_records(self.current_page_records)
            
            with open(page_file, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, ensure_ascii=False, indent=2)
            
            # 更新页面索引
            if self.current_page_records:
                start_date = min(record.date_time for record in self.current_page_records)
                end_date = max(record.date_time for record in self.current_page_records)
            else:
                start_date = end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.pages_index[self.current_page_id] = DataPage(
                page_id=self.current_page_id,
                start_date=start_date,
                end_date=end_date,
                record_count=len(self.current_page_records),
                file_path=str(page_file),
                compressed=False,
                last_access=time.time()
            )
            
            # 更新缓存
            cache_key = f"page_{self.current_page_id}"
            self.memory_cache.put(cache_key, self.current_page_records.copy())
            
            self.stats['total_writes'] += 1
            
        except Exception as e:
            self.logger.error(f"保存页面数据失败: {e}", exception=e)
            raise FileIOError(f"保存页面数据失败: {e}", operation="save_page")
    
    def _serialize_records(self, records: List[GameRecord]) -> List[Dict]:
        """序列化游戏记录"""
        return [asdict(record) for record in records]
    
    def _deserialize_records(self, data: List[Dict]) -> List[GameRecord]:
        """反序列化游戏记录"""
        records = []
        for record_data in data:
            # 转换phases
            phases = []
            for phase_data in record_data.get('phases', []):
                actions = [PlayerAction(**action_data) for action_data in phase_data.get('actions', [])]
                phase = GamePhase(
                    phase=phase_data['phase'],
                    community_cards=phase_data['community_cards'],
                    pot_size=phase_data['pot_size'],
                    current_bet=phase_data['current_bet'],
                    actions=actions
                )
                phases.append(phase)
            
            # 转换final_hands
            final_hands = [PlayerHand(**hand_data) for hand_data in record_data.get('final_hands', [])]
            
            # 创建GameRecord
            record = GameRecord(
                game_id=record_data['game_id'],
                timestamp=record_data['timestamp'],
                date_time=record_data['date_time'],
                players=record_data['players'],
                small_blind=record_data['small_blind'],
                big_blind=record_data['big_blind'],
                dealer_position=record_data['dealer_position'],
                phases=phases,
                final_hands=final_hands,
                total_pot=record_data['total_pot'],
                winner_names=record_data['winner_names'],
                duration_seconds=record_data.get('duration_seconds', 0.0),
                ai_styles=record_data.get('ai_styles', {})
            )
            records.append(record)
        
        return records
    
    @safe_execute("添加游戏记录")
    def add_game_record(self, record: GameRecord):
        """添加游戏记录"""
        current_page_id = self._get_current_page()
        self.current_page_records.append(record)
        
        # 添加到数据索引
        self.data_index[record.game_id] = DataIndex(
            game_id=record.game_id,
            timestamp=record.timestamp,
            page_id=current_page_id,
            player_names=record.players,
            winner_names=record.winner_names,
            total_pot=record.total_pot,
            duration=record.duration_seconds
        )
        
        # 检查是否需要创建新页面
        if len(self.current_page_records) >= self.config.max_history_records // 10:
            self._save_current_page()
            self._save_indexes()
            
            # 创建新页面
            self.current_page_id = None
            self.current_page_records = []
        else:
            # 定期保存
            if len(self.current_page_records) % 10 == 0:
                self._save_current_page()
                self._save_indexes()
        
        self.logger.debug(f"添加游戏记录: {record.game_id}", LogCategory.SYSTEM)
    
    @safe_execute("获取游戏记录")
    def get_game_record(self, game_id: str) -> Optional[GameRecord]:
        """获取指定游戏记录"""
        if game_id not in self.data_index:
            return None
        
        index = self.data_index[game_id]
        
        # 检查是否在当前页面
        if index.page_id == self.current_page_id:
            for record in self.current_page_records:
                if record.game_id == game_id:
                    return record
        
        # 从对应页面加载
        return self._load_record_from_page(game_id, index.page_id)
    
    def _load_record_from_page(self, game_id: str, page_id: str) -> Optional[GameRecord]:
        """从指定页面加载记录"""
        if page_id not in self.pages_index:
            return None
        
        page = self.pages_index[page_id]
        
        # 检查缓存
        cache_key = f"page_{page_id}"
        cached_records = self.memory_cache.get(cache_key)
        if cached_records:
            for record in cached_records:
                if record.game_id == game_id:
                    self.stats['cache_hits'] += 1
                    return record
        
        try:
            file_path = Path(page.file_path)
            
            if page.compressed:
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                self.stats['decompressions'] += 1
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            records = self._deserialize_records(data)
            
            # 更新缓存
            self.memory_cache.put(cache_key, records)
            
            # 更新访问时间
            page.last_access = time.time()
            
            self.stats['total_reads'] += 1
            
            # 查找目标记录
            for record in records:
                if record.game_id == game_id:
                    return record
            
        except Exception as e:
            self.logger.error(f"从页面加载记录失败: {e}", exception=e)
        
        return None
    
    def list_recent_games(self, limit: int = 20, player_filter: Optional[str] = None) -> List[GameRecord]:
        """获取最近的游戏列表"""
        # 从索引中获取最近的游戏
        sorted_indexes = sorted(
            self.data_index.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        # 应用玩家过滤
        if player_filter:
            sorted_indexes = [
                idx for idx in sorted_indexes
                if player_filter in idx.player_names
            ]
        
        # 限制数量
        selected_indexes = sorted_indexes[:limit]
        
        # 加载完整记录
        records = []
        for index in selected_indexes:
            record = self.get_game_record(index.game_id)
            if record:
                records.append(record)
        
        return records
    
    def get_player_statistics(self, player_name: str) -> Dict[str, Any]:
        """获取玩家统计数据"""
        player_games = [
            idx for idx in self.data_index.values()
            if player_name in idx.player_names
        ]
        
        if not player_games:
            return {
                'player_name': player_name,
                'total_games': 0,
                'wins': 0,
                'total_winnings': 0,
                'recent_games': []
            }
        
        # 计算统计数据
        wins = sum(1 for game in player_games if player_name in game.winner_names)
        
        # 加载详细数据计算盈亏
        total_winnings = 0
        recent_games = []
        
        for game_idx in sorted(player_games, key=lambda x: x.timestamp, reverse=True)[:20]:
            record = self.get_game_record(game_idx.game_id)
            if record:
                # 查找玩家手牌信息
                for hand in record.final_hands:
                    if hand.player_name == player_name:
                        total_winnings += hand.winnings
                        recent_games.append({
                            'game_id': record.game_id,
                            'date_time': record.date_time,
                            'is_winner': hand.is_winner,
                            'winnings': hand.winnings,
                            'hand_rank': hand.hand_rank
                        })
                        break
        
        return {
            'player_name': player_name,
            'total_games': len(player_games),
            'wins': wins,
            'win_rate': (wins / len(player_games)) * 100 if player_games else 0,
            'total_winnings': total_winnings,
            'recent_games': recent_games
        }
    
    @safe_execute("压缩旧数据")
    def compress_old_data(self, days_old: int = 7):
        """压缩旧数据"""
        if not self.config.compress_old_data:
            return
        
        cutoff_time = time.time() - (days_old * 24 * 3600)
        compressed_count = 0
        
        for page_id, page in list(self.pages_index.items()):
            if page.compressed or page.last_access > cutoff_time:
                continue
            
            if page_id == self.current_page_id:
                continue  # 不压缩当前页面
            
            try:
                # 读取原文件
                with open(page.file_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                
                # 压缩保存
                compressed_file = self.compressed_dir / f"{page_id}.json.gz"
                with gzip.open(compressed_file, 'wt', encoding='utf-8') as f:
                    f.write(data)
                
                # 删除原文件
                os.remove(page.file_path)
                
                # 更新索引
                page.file_path = str(compressed_file)
                page.compressed = True
                
                compressed_count += 1
                self.stats['compressions'] += 1
                
            except Exception as e:
                self.logger.error(f"压缩页面 {page_id} 失败: {e}", exception=e)
        
        if compressed_count > 0:
            self._save_indexes()
            self.logger.info(f"已压缩 {compressed_count} 个数据页")
    
    @safe_execute("清理过期数据")
    def cleanup_expired_data(self):
        """清理过期数据"""
        if self.config.data_retention_days <= 0:
            return
        
        cutoff_time = time.time() - (self.config.data_retention_days * 24 * 3600)
        deleted_count = 0
        
        for game_id, index in list(self.data_index.items()):
            if index.timestamp < cutoff_time:
                # 删除记录索引
                del self.data_index[game_id]
                deleted_count += 1
        
        # 清理空页面
        for page_id, page in list(self.pages_index.items()):
            # 检查页面是否还有有效记录
            has_valid_records = any(
                idx.page_id == page_id for idx in self.data_index.values()
            )
            
            if not has_valid_records and page_id != self.current_page_id:
                try:
                    # 删除文件
                    if os.path.exists(page.file_path):
                        os.remove(page.file_path)
                    
                    # 删除索引
                    del self.pages_index[page_id]
                    
                except Exception as e:
                    self.logger.error(f"删除页面文件失败: {e}", exception=e)
        
        if deleted_count > 0:
            self._save_indexes()
            self.logger.info(f"已清理 {deleted_count} 条过期记录")
    
    @safe_execute("创建备份")
    def create_backup(self, backup_name: Optional[str] = None):
        """创建数据备份"""
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # 备份页面数据
            pages_backup = backup_path / "pages"
            pages_backup.mkdir(exist_ok=True)
            
            for page_id, page in self.pages_index.items():
                if os.path.exists(page.file_path):
                    backup_file = pages_backup / os.path.basename(page.file_path)
                    shutil.copy2(page.file_path, backup_file)
            
            # 备份索引
            shutil.copy2(self.index_dir / "pages_index.json", backup_path)
            shutil.copy2(self.index_dir / "data_index.json", backup_path)
            
            # 保存当前页面
            if self.current_page_id and self.current_page_records:
                self._save_current_page()
            
            self.logger.info(f"备份已创建: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}", exception=e)
            raise FileIOError(f"创建备份失败: {e}", operation="create_backup")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据管理统计信息"""
        total_records = len(self.data_index)
        compressed_pages = sum(1 for page in self.pages_index.values() if page.compressed)
        
        return {
            'total_records': total_records,
            'total_pages': len(self.pages_index),
            'compressed_pages': compressed_pages,
            'current_page_records': len(self.current_page_records),
            'cache_stats': self.memory_cache.get_stats(),
            'performance_stats': self.stats.copy()
        }
    
    def maintenance(self):
        """定期维护任务"""
        with self._maintenance_lock:
            try:
                # 保存当前数据
                if self.current_page_records:
                    self._save_current_page()
                
                # 压缩旧数据
                self.compress_old_data()
                
                # 清理过期数据
                self.cleanup_expired_data()
                
                # 清理缓存中的过期项
                self.memory_cache.clear()
                
                # 保存索引
                self._save_indexes()
                
                self.logger.info("数据维护任务完成")
                
            except Exception as e:
                self.logger.error(f"数据维护失败: {e}", exception=e)
    
    def shutdown(self):
        """关闭数据管理器"""
        try:
            # 保存当前数据
            if self.current_page_records:
                self._save_current_page()
            
            # 保存索引
            self._save_indexes()
            
            # 清空缓存
            self.memory_cache.clear()
            
            self.logger.info("数据管理器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭数据管理器失败: {e}", exception=e)


# 全局数据管理器实例
_global_data_manager: Optional[OptimizedDataManager] = None


def get_data_manager() -> OptimizedDataManager:
    """获取全局数据管理器实例"""
    global _global_data_manager
    if _global_data_manager is None:
        _global_data_manager = OptimizedDataManager()
    return _global_data_manager


def shutdown_data_manager():
    """关闭全局数据管理器"""
    global _global_data_manager
    if _global_data_manager:
        _global_data_manager.shutdown()
        _global_data_manager = None
