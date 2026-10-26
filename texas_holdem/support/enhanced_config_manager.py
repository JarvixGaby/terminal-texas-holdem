# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 增强配置管理系统
统一管理所有游戏配置，提供验证和默认值
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from enum import Enum


class ConfigVersion(Enum):
    """配置版本"""
    V1_0 = "1.0"
    V1_1 = "1.1"  # 当前版本
    CURRENT = V1_1


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 胜率计算配置
    odds_simulation_count: int = 3000
    fast_mode_simulation_count: int = 1000
    cache_enabled: bool = True
    cache_max_size: int = 1000
    
    # AI思考时间
    ai_thinking_time: float = 1.0
    ai_decision_variance: float = 0.1
    
    # 界面响应
    animation_speed: float = 1.0
    show_calculation_progress: bool = True


@dataclass
class GameplayConfig:
    """游戏玩法配置"""
    # 基础设置
    small_blind: int = 5
    big_blind: int = 10
    initial_chips: int = 1000
    min_players: int = 2
    max_players: int = 6
    
    # 游戏规则
    enable_side_pots: bool = True
    enable_all_in_protection: bool = True
    auto_muck_losing_hands: bool = True
    
    # 盲注设置
    tournament_mode: bool = False
    blind_increase_interval: int = 0  # 0表示不增加


@dataclass
class AIConfig:
    """AI配置"""
    # AI技能等级
    skill_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    
    # AI行为配置
    enable_bluffing: bool = True
    enable_learning: bool = True
    enable_position_awareness: bool = True
    
    # 风格分布权重
    style_weights: Dict[str, float] = field(default_factory=lambda: {
        "tight_aggressive": 0.3,
        "loose_aggressive": 0.2,
        "tight_passive": 0.2,
        "loose_passive": 0.15,
        "calling_station": 0.1,
        "maniac": 0.05
    })


@dataclass
class UIConfig:
    """界面配置"""
    # 显示设置
    show_odds_in_game: bool = False
    show_opponent_strength: bool = False
    confirm_simple_actions: bool = False
    
    # 学习辅助
    highlight_mistakes: bool = False
    enable_hints: bool = False
    show_ai_thinking: bool = False
    
    # 语言设置
    language: str = "zh_CN"
    use_emoji: bool = True


@dataclass
class DataConfig:
    """数据管理配置"""
    # 历史记录
    track_statistics: bool = True
    max_history_records: int = 10000
    auto_backup_frequency: int = 100  # 每100局自动备份
    
    # 文件管理
    history_file: str = "game_history.json"
    stats_file: str = "player_stats.json"
    backup_directory: str = "backups"
    
    # 压缩设置
    compress_old_data: bool = True
    data_retention_days: int = 365


@dataclass
class LoggingConfig:
    """日志配置"""
    # 日志等级
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    # 日志输出
    log_to_file: bool = True
    log_to_console: bool = False
    log_file: str = "poker_game.log"
    
    # 日志轮转
    max_log_size_mb: int = 10
    max_log_files: int = 5


@dataclass
class DeveloperConfig:
    """开发者配置"""
    # 调试模式
    debug_mode: bool = False
    enable_profiling: bool = False
    
    # 测试配置
    enable_test_mode: bool = False
    seed_random: Optional[int] = None
    
    # 性能监控
    track_performance: bool = False
    performance_log_interval: int = 1000


@dataclass
class FullGameConfig:
    """完整游戏配置"""
    version: str = ConfigVersion.CURRENT.value
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    gameplay: GameplayConfig = field(default_factory=GameplayConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    data: DataConfig = field(default_factory=DataConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    developer: DeveloperConfig = field(default_factory=DeveloperConfig)


class EnhancedConfigManager:
    """增强配置管理器"""
    
    def __init__(self, config_file: str = "enhanced_game_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self._validation_errors: List[str] = []
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self) -> FullGameConfig:
        """加载或创建配置"""
        if os.path.exists(self.config_file):
            try:
                return self._load_config()
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _load_config(self) -> FullGameConfig:
        """从文件加载配置"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查版本兼容性
        if data.get('version') != ConfigVersion.CURRENT.value:
            print(f"配置版本不匹配，从 {data.get('version')} 升级到 {ConfigVersion.CURRENT.value}")
            data = self._migrate_config(data)
        
        # 重建配置对象
        config = FullGameConfig(
            version=data.get('version', ConfigVersion.CURRENT.value),
            performance=PerformanceConfig(**data.get('performance', {})),
            gameplay=GameplayConfig(**data.get('gameplay', {})),
            ai=AIConfig(**data.get('ai', {})),
            ui=UIConfig(**data.get('ui', {})),
            data=DataConfig(**data.get('data', {})),
            logging=LoggingConfig(**data.get('logging', {})),
            developer=DeveloperConfig(**data.get('developer', {}))
        )
        
        # 验证配置
        if not self._validate_config(config):
            print("配置验证失败，使用默认值修复")
            config = self._fix_invalid_config(config)
        
        return config
    
    def _create_default_config(self) -> FullGameConfig:
        """创建默认配置"""
        config = FullGameConfig()
        self.config = config  # 设置config属性
        self.save_config()
        return config
    
    def _migrate_config(self, old_data: Dict) -> Dict:
        """迁移旧版本配置"""
        # 这里实现配置版本迁移逻辑
        # 目前只是简单的保留兼容字段
        migrated = {
            'version': ConfigVersion.CURRENT.value,
            'performance': {},
            'gameplay': {},
            'ai': {},
            'ui': {},
            'data': {},
            'logging': {},
            'developer': {}
        }
        
        # 从旧配置中迁移兼容的字段
        if 'small_blind' in old_data:
            migrated['gameplay']['small_blind'] = old_data['small_blind']
        if 'big_blind' in old_data:
            migrated['gameplay']['big_blind'] = old_data['big_blind']
        if 'initial_chips' in old_data:
            migrated['gameplay']['initial_chips'] = old_data['initial_chips']
        
        return migrated
    
    def _validate_config(self, config: FullGameConfig) -> bool:
        """验证配置有效性"""
        self._validation_errors.clear()
        
        # 验证游戏玩法配置
        if config.gameplay.small_blind <= 0:
            self._validation_errors.append("小盲注必须大于0")
        
        if config.gameplay.big_blind <= config.gameplay.small_blind:
            self._validation_errors.append("大盲注必须大于小盲注")
        
        if config.gameplay.initial_chips < config.gameplay.big_blind * 10:
            self._validation_errors.append("初始筹码应该至少是大盲注的10倍")
        
        if not (2 <= config.gameplay.min_players <= config.gameplay.max_players <= 10):
            self._validation_errors.append("玩家数量范围无效")
        
        # 验证性能配置
        if config.performance.odds_simulation_count < 100:
            self._validation_errors.append("模拟次数太少，至少需要100次")
        
        if config.performance.cache_max_size < 10:
            self._validation_errors.append("缓存大小太小")
        
        # 验证AI配置
        valid_skill_levels = ["beginner", "intermediate", "advanced", "expert"]
        if config.ai.skill_level not in valid_skill_levels:
            self._validation_errors.append(f"AI技能等级无效，必须是: {valid_skill_levels}")
        
        # 验证数据配置
        if config.data.max_history_records < 100:
            self._validation_errors.append("历史记录数量太少")
        
        return len(self._validation_errors) == 0
    
    def _fix_invalid_config(self, config: FullGameConfig) -> FullGameConfig:
        """修复无效配置"""
        # 创建新的默认配置，但保留有效的用户设置
        default_config = FullGameConfig()
        
        # 保留有效的用户配置
        if config.gameplay.small_blind > 0:
            default_config.gameplay.small_blind = config.gameplay.small_blind
        
        if config.gameplay.big_blind > config.gameplay.small_blind:
            default_config.gameplay.big_blind = config.gameplay.big_blind
        
        if config.gameplay.initial_chips >= config.gameplay.big_blind * 10:
            default_config.gameplay.initial_chips = config.gameplay.initial_chips
        
        return default_config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_validation_errors(self) -> List[str]:
        """获取验证错误列表"""
        return self._validation_errors.copy()
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config = FullGameConfig()
        self.save_config()
    
    def update_performance_level(self, level: str):
        """更新性能等级"""
        level_configs = {
            "fast": {"odds_simulation_count": 1000, "cache_enabled": True},
            "normal": {"odds_simulation_count": 3000, "cache_enabled": True},
            "accurate": {"odds_simulation_count": 8000, "cache_enabled": True},
            "precise": {"odds_simulation_count": 15000, "cache_enabled": True}
        }
        
        if level in level_configs:
            for key, value in level_configs[level].items():
                setattr(self.config.performance, key, value)
            self.save_config()
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置字典"""
        return asdict(self.config.performance)
    
    def get_gameplay_config(self) -> Dict[str, Any]:
        """获取游戏配置字典"""
        return asdict(self.config.gameplay)
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI配置字典"""
        return asdict(self.config.ai)
    
    def export_config(self, export_file: str):
        """导出配置到指定文件"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
            print(f"配置已导出到: {export_file}")
        except Exception as e:
            print(f"导出配置失败: {e}")
    
    def import_config(self, import_file: str) -> bool:
        """从指定文件导入配置"""
        try:
            old_config_file = self.config_file
            self.config_file = import_file
            new_config = self._load_config()
            self.config_file = old_config_file
            self.config = new_config
            self.save_config()
            print(f"配置已从 {import_file} 导入")
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False


# 全局配置管理器实例
_global_config_manager: Optional[EnhancedConfigManager] = None


def get_global_config() -> EnhancedConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = EnhancedConfigManager()
    return _global_config_manager


def reload_global_config():
    """重新加载全局配置"""
    global _global_config_manager
    _global_config_manager = None
    return get_global_config()


# 便捷访问函数
def get_performance_config() -> Dict[str, Any]:
    """获取性能配置"""
    return get_global_config().get_performance_config()


def get_gameplay_config() -> Dict[str, Any]:
    """获取游戏配置"""
    return get_global_config().get_gameplay_config()


def get_ai_config() -> Dict[str, Any]:
    """获取AI配置"""
    return get_global_config().get_ai_config()
