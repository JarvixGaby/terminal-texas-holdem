#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克游戏配置系统
专业级游戏参数和设置管理
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any
from texas_holdem.ai.smart_ai_system import AISkillLevel


@dataclass
class GameConfig:
    """游戏配置类"""
    
    # 基础游戏设置
    small_blind: int = 5
    big_blind: int = 10
    initial_chips: int = 1000
    min_players: int = 2
    max_players: int = 6
    
    # AI设置
    ai_skill_level: str = "intermediate"
    ai_thinking_time: float = 1.0
    ai_decision_variance: float = 0.1
    
    # 界面设置
    show_odds_in_game: bool = False
    auto_muck_losing_hands: bool = True
    confirm_simple_actions: bool = False
    animation_speed: float = 1.0
    
    # 高级设置
    enable_side_pots: bool = True
    enable_all_in_protection: bool = True
    tournament_mode: bool = False
    blind_increase_interval: int = 0  # 0表示不增加
    
    # 训练设置
    show_opponent_strength: bool = False
    highlight_mistakes: bool = False
    enable_hints: bool = False
    track_statistics: bool = True


class GameConfigManager:
    """游戏配置管理器"""
    
    def __init__(self, config_file: str = "game_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> GameConfig:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return GameConfig(**data)
            else:
                # 创建默认配置
                config = GameConfig()
                self.save_config(config)
                return config
        except Exception as e:
            print(f"配置加载失败，使用默认配置: {e}")
            return GameConfig()
    
    def save_config(self, config: GameConfig = None):
        """保存配置"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"配置保存失败: {e}")
    
    def get_ai_skill_level(self) -> AISkillLevel:
        """获取AI技能等级枚举"""
        level_map = {
            "beginner": AISkillLevel.BEGINNER,
            "intermediate": AISkillLevel.INTERMEDIATE,
            "advanced": AISkillLevel.ADVANCED,
            "expert": AISkillLevel.EXPERT
        }
        return level_map.get(self.config.ai_skill_level, AISkillLevel.INTERMEDIATE)
    
    def set_ai_skill_level(self, level: AISkillLevel):
        """设置AI技能等级"""
        level_names = {
            AISkillLevel.BEGINNER: "beginner",
            AISkillLevel.INTERMEDIATE: "intermediate",
            AISkillLevel.ADVANCED: "advanced",
            AISkillLevel.EXPERT: "expert"
        }
        self.config.ai_skill_level = level_names[level]
        self.save_config()
    
    def get_display_settings(self) -> Dict[str, Any]:
        """获取显示相关设置"""
        return {
            "show_odds": self.config.show_odds_in_game,
            "auto_muck": self.config.auto_muck_losing_hands,
            "confirm_actions": self.config.confirm_simple_actions,
            "animation_speed": self.config.animation_speed
        }
    
    def get_training_settings(self) -> Dict[str, Any]:
        """获取训练相关设置"""
        return {
            "show_strength": self.config.show_opponent_strength,
            "highlight_mistakes": self.config.highlight_mistakes,
            "enable_hints": self.config.enable_hints,
            "track_stats": self.config.track_statistics
        }
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 检查基础参数
            if self.config.big_blind <= self.config.small_blind:
                return False
            if self.config.initial_chips < self.config.big_blind * 20:
                return False
            if not (2 <= self.config.min_players <= self.config.max_players <= 10):
                return False
            
            # 检查AI参数
            if not (0.5 <= self.config.ai_thinking_time <= 5.0):
                return False
            if not (0.0 <= self.config.ai_decision_variance <= 0.5):
                return False
            
            return True
        except:
            return False
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config = GameConfig()
        self.save_config()
    
    def export_config(self, filename: str):
        """导出配置到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def import_config(self, filename: str) -> bool:
        """从文件导入配置"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证导入的配置
            temp_config = GameConfig(**data)
            old_config = self.config
            self.config = temp_config
            
            if self.validate_config():
                self.save_config()
                return True
            else:
                self.config = old_config
                return False
        except:
            return False


# 全局配置管理器实例
game_config_manager = GameConfigManager()


# 预设配置模板
PRESET_CONFIGS = {
    "beginner_friendly": GameConfig(
        small_blind=1,
        big_blind=2,
        initial_chips=200,
        ai_skill_level="beginner",
        ai_thinking_time=1.5,
        show_odds_in_game=True,
        enable_hints=True,
        highlight_mistakes=True
    ),
    
    "intermediate_practice": GameConfig(
        small_blind=5,
        big_blind=10,
        initial_chips=1000,
        ai_skill_level="intermediate",
        ai_thinking_time=1.0,
        show_odds_in_game=False,
        enable_hints=False,
        highlight_mistakes=False
    ),
    
    "advanced_training": GameConfig(
        small_blind=10,
        big_blind=20,
        initial_chips=2000,
        ai_skill_level="advanced",
        ai_thinking_time=0.8,
        ai_decision_variance=0.05,
        show_odds_in_game=False,
        track_statistics=True
    ),
    
    "expert_challenge": GameConfig(
        small_blind=25,
        big_blind=50,
        initial_chips=5000,
        ai_skill_level="expert",
        ai_thinking_time=0.5,
        ai_decision_variance=0.02,
        show_opponent_strength=False,
        enable_all_in_protection=False
    ),
    
    "tournament_style": GameConfig(
        small_blind=10,
        big_blind=20,
        initial_chips=1500,
        ai_skill_level="advanced",
        tournament_mode=True,
        blind_increase_interval=10,
        enable_side_pots=True
    )
}


def apply_preset_config(preset_name: str) -> bool:
    """应用预设配置"""
    if preset_name in PRESET_CONFIGS:
        game_config_manager.config = PRESET_CONFIGS[preset_name]
        game_config_manager.save_config()
        return True
    return False


def get_available_presets() -> Dict[str, str]:
    """获取可用的预设配置"""
    return {
        "beginner_friendly": "🎓 新手友好 - 慢节奏，提示丰富",
        "intermediate_practice": "🎯 中级练习 - 平衡挑战",
        "advanced_training": "🏆 高级训练 - 专业对手",
        "expert_challenge": "🚀 专家挑战 - 终极考验",
        "tournament_style": "🏅 锦标赛模式 - 盲注递增"
    }
