# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 增强日志系统
提供结构化、分级的日志记录和性能监控
"""

import logging
import logging.handlers
import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from functools import wraps
from texas_holdem.support.enhanced_config_manager import get_global_config


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """日志分类"""
    GAME = "GAME"
    AI = "AI"
    PERFORMANCE = "PERFORMANCE"
    ERROR = "ERROR"
    USER = "USER"
    SYSTEM = "SYSTEM"
    DEBUG = "DEBUG"


class PerformanceTimer:
    """性能计时器"""
    
    def __init__(self, operation_name: str, logger: 'EnhancedLogger'):
        self.operation_name = operation_name
        self.logger = logger
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if exc_type is None:
            self.logger.log_performance(self.operation_name, duration, success=True)
        else:
            self.logger.log_performance(self.operation_name, duration, success=False, 
                                      error=f"{exc_type.__name__}: {exc_val}")


class EnhancedLogger:
    """增强日志记录器"""
    
    def __init__(self, name: str = "PokerGame"):
        """
        初始化增强日志器
        
        Args:
            name: 日志器名称
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.config = get_global_config().config.logging
        
        # 性能统计
        self.performance_stats: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
        
        # 设置日志器
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器配置"""
        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 设置日志级别
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(category)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器
        if self.config.log_to_file:
            self._setup_file_handler(formatter)
        
        # 控制台处理器
        if self.config.log_to_console:
            self._setup_console_handler(formatter)
    
    def _setup_file_handler(self, formatter):
        """设置文件日志处理器"""
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(self.config.log_file) or "."
            os.makedirs(log_dir, exist_ok=True)
            
            # 使用轮转文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                self.config.log_file,
                maxBytes=self.config.max_log_size_mb * 1024 * 1024,
                backupCount=self.config.max_log_files,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"设置文件日志处理器失败: {e}")
    
    def _setup_console_handler(self, formatter):
        """设置控制台日志处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _log(self, level: LogLevel, category: LogCategory, message: str, 
             extra_data: Optional[Dict[str, Any]] = None):
        """内部日志记录方法"""
        # 准备日志数据
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'category': category.value,
            'message': message
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        # 创建LogRecord并添加自定义字段
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=getattr(logging, level.value),
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.category = category.value
        
        # 发送日志
        self.logger.handle(record)
        
        # 更新统计
        if level == LogLevel.ERROR or level == LogLevel.CRITICAL:
            error_key = f"{category.value}_{level.value}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def debug(self, message: str, category: LogCategory = LogCategory.DEBUG, 
              extra_data: Optional[Dict[str, Any]] = None):
        """记录调试信息"""
        self._log(LogLevel.DEBUG, category, message, extra_data)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
             extra_data: Optional[Dict[str, Any]] = None):
        """记录信息"""
        self._log(LogLevel.INFO, category, message, extra_data)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
                extra_data: Optional[Dict[str, Any]] = None):
        """记录警告"""
        self._log(LogLevel.WARNING, category, message, extra_data)
    
    def error(self, message: str, category: LogCategory = LogCategory.ERROR, 
              extra_data: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """记录错误"""
        if exception:
            extra_data = extra_data or {}
            extra_data.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            })
        
        self._log(LogLevel.ERROR, category, message, extra_data)
    
    def critical(self, message: str, category: LogCategory = LogCategory.ERROR, 
                 extra_data: Optional[Dict[str, Any]] = None):
        """记录严重错误"""
        self._log(LogLevel.CRITICAL, category, message, extra_data)
    
    def log_game_event(self, event: str, player: Optional[str] = None, 
                       extra_data: Optional[Dict[str, Any]] = None):
        """记录游戏事件"""
        message = f"游戏事件: {event}"
        if player:
            message += f" (玩家: {player})"
        
        self.info(message, LogCategory.GAME, extra_data)
    
    def log_ai_decision(self, ai_name: str, decision: str, reasoning: str,
                        extra_data: Optional[Dict[str, Any]] = None):
        """记录AI决策"""
        message = f"AI决策 [{ai_name}]: {decision} - {reasoning}"
        
        log_extra = extra_data or {}
        log_extra.update({
            'ai_name': ai_name,
            'decision': decision,
            'reasoning': reasoning
        })
        
        self.debug(message, LogCategory.AI, log_extra)
    
    def log_performance(self, operation: str, duration: float, success: bool = True,
                       extra_data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """记录性能数据"""
        # 更新性能统计
        if operation not in self.performance_stats:
            self.performance_stats[operation] = []
        self.performance_stats[operation].append(duration)
        
        # 记录日志
        status = "成功" if success else "失败"
        message = f"性能监控 [{operation}]: {duration:.3f}s - {status}"
        
        log_extra = extra_data or {}
        log_extra.update({
            'operation': operation,
            'duration': duration,
            'success': success
        })
        
        if error:
            log_extra['error'] = error
            message += f" - 错误: {error}"
        
        level = LogLevel.INFO if success else LogLevel.WARNING
        self._log(level, LogCategory.PERFORMANCE, message, log_extra)
    
    def log_user_action(self, action: str, player: str, 
                        extra_data: Optional[Dict[str, Any]] = None):
        """记录用户行为"""
        message = f"用户行为 [{player}]: {action}"
        
        log_extra = extra_data or {}
        log_extra.update({
            'player': player,
            'action': action
        })
        
        self.info(message, LogCategory.USER, log_extra)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能统计摘要"""
        summary = {}
        
        for operation, durations in self.performance_stats.items():
            if durations:
                summary[operation] = {
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'total_duration': sum(durations)
                }
        
        return summary
    
    def get_error_summary(self) -> Dict[str, int]:
        """获取错误统计摘要"""
        return self.error_counts.copy()
    
    def timer(self, operation_name: str) -> PerformanceTimer:
        """创建性能计时器上下文管理器"""
        return PerformanceTimer(operation_name, self)
    
    def export_logs(self, export_file: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, categories: Optional[List[LogCategory]] = None):
        """导出日志到文件"""
        try:
            # 这里可以实现更复杂的日志导出逻辑
            # 目前只是简单的统计信息导出
            export_data = {
                'export_time': datetime.now().isoformat(),
                'performance_summary': self.get_performance_summary(),
                'error_summary': self.get_error_summary(),
                'config': {
                    'log_level': self.config.log_level,
                    'log_file': self.config.log_file
                }
            }
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.info(f"日志已导出到: {export_file}", LogCategory.SYSTEM)
        except Exception as e:
            self.error(f"导出日志失败: {e}", exception=e)


def log_errors(category: LogCategory = LogCategory.ERROR):
    """错误日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            try:
                with logger.timer(f"{func.__name__}"):
                    return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"函数 {func.__name__} 执行失败",
                    category=category,
                    extra_data={
                        'function': func.__name__,
                        'args': str(args)[:200],  # 限制长度
                        'kwargs': str(kwargs)[:200]
                    },
                    exception=e
                )
                raise
        return wrapper
    return decorator


def log_performance(operation_name: Optional[str] = None, 
                   category: LogCategory = LogCategory.PERFORMANCE):
    """性能日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            op_name = operation_name or func.__name__
            
            with logger.timer(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# 全局日志器实例
_global_logger: Optional[EnhancedLogger] = None


def get_logger(name: str = "PokerGame") -> EnhancedLogger:
    """获取全局日志器实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = EnhancedLogger(name)
    return _global_logger


def reload_logger():
    """重新加载日志器配置"""
    global _global_logger
    if _global_logger:
        _global_logger._setup_logger()


# 便捷日志函数
def log_debug(message: str, category: LogCategory = LogCategory.DEBUG, **kwargs):
    """便捷调试日志"""
    get_logger().debug(message, category, kwargs)


def log_info(message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
    """便捷信息日志"""
    get_logger().info(message, category, kwargs)


def log_warning(message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
    """便捷警告日志"""
    get_logger().warning(message, category, kwargs)


def log_error(message: str, exception: Optional[Exception] = None, 
              category: LogCategory = LogCategory.ERROR, **kwargs):
    """便捷错误日志"""
    get_logger().error(message, category, kwargs, exception)


def log_game_event(event: str, player: Optional[str] = None, **kwargs):
    """便捷游戏事件日志"""
    get_logger().log_game_event(event, player, kwargs)


def log_ai_decision(ai_name: str, decision: str, reasoning: str, **kwargs):
    """便捷AI决策日志"""
    get_logger().log_ai_decision(ai_name, decision, reasoning, kwargs)


def log_user_action(action: str, player: str, **kwargs):
    """便捷用户行为日志"""
    get_logger().log_user_action(action, player, kwargs)
