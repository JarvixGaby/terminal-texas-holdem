# -*- coding: utf-8 -*-
"""
德州扑克游戏 - 增强错误处理系统
提供结构化的错误处理、输入验证和用户友好的错误恢复
"""

import re
import traceback
from typing import Any, Optional, Callable, Dict, List, Union
from enum import Enum
from functools import wraps
from texas_holdem.support.enhanced_logging import get_logger, LogCategory


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 可忽略的错误
    MEDIUM = "medium"     # 需要处理但不影响游戏继续
    HIGH = "high"         # 严重错误，可能影响游戏
    CRITICAL = "critical" # 致命错误，需要终止操作


class ErrorCategory(Enum):
    """错误分类"""
    INPUT_VALIDATION = "input_validation"
    GAME_LOGIC = "game_logic"
    FILE_IO = "file_io"
    NETWORK = "network"
    CALCULATION = "calculation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    USER_ACTION = "user_action"


class GameError(Exception):
    """游戏基础异常类"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 recovery_suggestion: Optional[str] = None,
                 error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.recovery_suggestion = recovery_suggestion
        self.error_code = error_code
        self.timestamp = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'recovery_suggestion': self.recovery_suggestion,
            'error_code': self.error_code,
            'timestamp': self.timestamp
        }


class InputValidationError(GameError):
    """输入验证错误"""
    
    def __init__(self, message: str, input_value: Any = None, 
                 expected_format: Optional[str] = None):
        super().__init__(
            message, 
            ErrorCategory.INPUT_VALIDATION, 
            ErrorSeverity.LOW,
            "请检查输入格式并重新输入"
        )
        self.input_value = input_value
        self.expected_format = expected_format


class GameLogicError(GameError):
    """游戏逻辑错误"""
    
    def __init__(self, message: str, game_state: Optional[Dict] = None):
        super().__init__(
            message, 
            ErrorCategory.GAME_LOGIC, 
            ErrorSeverity.HIGH,
            "游戏状态异常，建议重新开始游戏"
        )
        self.game_state = game_state


class FileIOError(GameError):
    """文件IO错误"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 operation: Optional[str] = None):
        super().__init__(
            message, 
            ErrorCategory.FILE_IO, 
            ErrorSeverity.MEDIUM,
            "请检查文件权限和磁盘空间"
        )
        self.file_path = file_path
        self.operation = operation


class CalculationError(GameError):
    """计算错误"""
    
    def __init__(self, message: str, calculation_type: Optional[str] = None,
                 input_parameters: Optional[Dict] = None):
        super().__init__(
            message, 
            ErrorCategory.CALCULATION, 
            ErrorSeverity.MEDIUM,
            "计算参数可能有误，建议使用默认设置"
        )
        self.calculation_type = calculation_type
        self.input_parameters = input_parameters


class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_integer(value: Any, min_val: Optional[int] = None, 
                        max_val: Optional[int] = None, field_name: str = "值") -> int:
        """验证整数输入"""
        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise InputValidationError(
                f"{field_name}必须是有效的整数",
                input_value=value,
                expected_format="整数"
            )
        
        if min_val is not None and int_val < min_val:
            raise InputValidationError(
                f"{field_name}不能小于{min_val}",
                input_value=value,
                expected_format=f"≥{min_val}的整数"
            )
        
        if max_val is not None and int_val > max_val:
            raise InputValidationError(
                f"{field_name}不能大于{max_val}",
                input_value=value,
                expected_format=f"≤{max_val}的整数"
            )
        
        return int_val
    
    @staticmethod
    def validate_float(value: Any, min_val: Optional[float] = None, 
                      max_val: Optional[float] = None, field_name: str = "值") -> float:
        """验证浮点数输入"""
        try:
            float_val = float(value)
        except (ValueError, TypeError):
            raise InputValidationError(
                f"{field_name}必须是有效的数字",
                input_value=value,
                expected_format="浮点数"
            )
        
        if min_val is not None and float_val < min_val:
            raise InputValidationError(
                f"{field_name}不能小于{min_val}",
                input_value=value,
                expected_format=f"≥{min_val}的数字"
            )
        
        if max_val is not None and float_val > max_val:
            raise InputValidationError(
                f"{field_name}不能大于{max_val}",
                input_value=value,
                expected_format=f"≤{max_val}的数字"
            )
        
        return float_val
    
    @staticmethod
    def validate_string(value: Any, min_length: int = 0, max_length: Optional[int] = None,
                       pattern: Optional[str] = None, field_name: str = "字符串") -> str:
        """验证字符串输入"""
        if not isinstance(value, str):
            try:
                str_val = str(value).strip()
            except Exception:
                raise InputValidationError(
                    f"{field_name}必须是有效的字符串",
                    input_value=value,
                    expected_format="字符串"
                )
        else:
            str_val = value.strip()
        
        if len(str_val) < min_length:
            raise InputValidationError(
                f"{field_name}长度不能少于{min_length}个字符",
                input_value=value,
                expected_format=f"至少{min_length}个字符"
            )
        
        if max_length is not None and len(str_val) > max_length:
            raise InputValidationError(
                f"{field_name}长度不能超过{max_length}个字符",
                input_value=value,
                expected_format=f"最多{max_length}个字符"
            )
        
        if pattern and not re.match(pattern, str_val):
            raise InputValidationError(
                f"{field_name}格式不正确",
                input_value=value,
                expected_format=f"符合模式: {pattern}"
            )
        
        return str_val
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any], field_name: str = "选择") -> Any:
        """验证选择输入"""
        if value not in choices:
            raise InputValidationError(
                f"{field_name}必须是以下选项之一: {', '.join(map(str, choices))}",
                input_value=value,
                expected_format=f"选项: {choices}"
            )
        return value
    
    @staticmethod
    def validate_yes_no(value: Any, field_name: str = "确认") -> bool:
        """验证是/否输入"""
        if isinstance(value, bool):
            return value
        
        str_val = str(value).strip().lower()
        
        yes_values = ['y', 'yes', '是', '1', 'true', 'ok']
        no_values = ['n', 'no', '否', '0', 'false', 'cancel']
        
        if str_val in yes_values:
            return True
        elif str_val in no_values:
            return False
        else:
            raise InputValidationError(
                f"{field_name}请输入 y/n 或 是/否",
                input_value=value,
                expected_format="y/n, 是/否"
            )


class SafeInput:
    """安全输入处理器"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.logger = get_logger()
    
    def get_integer(self, prompt: str, min_val: Optional[int] = None, 
                   max_val: Optional[int] = None, default: Optional[int] = None) -> int:
        """安全获取整数输入"""
        for attempt in range(self.max_retries):
            try:
                user_input = input(prompt).strip()
                
                # 处理默认值
                if not user_input and default is not None:
                    return default
                
                return InputValidator.validate_integer(user_input, min_val, max_val)
                
            except InputValidationError as e:
                self.logger.warning(f"输入验证失败: {e.message}", LogCategory.USER)
                if attempt < self.max_retries - 1:
                    print(f"❌ {e.message}")
                    if e.recovery_suggestion:
                        print(f"💡 {e.recovery_suggestion}")
                else:
                    print(f"❌ 尝试次数过多，将使用默认值")
                    if default is not None:
                        return default
                    raise
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.error(f"获取整数输入时发生未知错误", exception=e)
                raise GameError("输入处理失败", ErrorCategory.USER_ACTION, ErrorSeverity.HIGH)
    
    def get_string(self, prompt: str, min_length: int = 0, max_length: Optional[int] = None,
                  pattern: Optional[str] = None, default: Optional[str] = None) -> str:
        """安全获取字符串输入"""
        for attempt in range(self.max_retries):
            try:
                user_input = input(prompt)
                
                # 处理默认值
                if not user_input.strip() and default is not None:
                    return default
                
                return InputValidator.validate_string(user_input, min_length, max_length, pattern)
                
            except InputValidationError as e:
                self.logger.warning(f"输入验证失败: {e.message}", LogCategory.USER)
                if attempt < self.max_retries - 1:
                    print(f"❌ {e.message}")
                    if e.recovery_suggestion:
                        print(f"💡 {e.recovery_suggestion}")
                else:
                    print(f"❌ 尝试次数过多，将使用默认值")
                    if default is not None:
                        return default
                    raise
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.error(f"获取字符串输入时发生未知错误", exception=e)
                raise GameError("输入处理失败", ErrorCategory.USER_ACTION, ErrorSeverity.HIGH)
    
    def get_choice(self, prompt: str, choices: List[Any], 
                  default: Optional[Any] = None) -> Any:
        """安全获取选择输入"""
        for attempt in range(self.max_retries):
            try:
                user_input = input(prompt).strip()
                
                # 处理默认值
                if not user_input and default is not None:
                    return default
                
                # 尝试转换为整数索引
                try:
                    index = int(user_input) - 1
                    if 0 <= index < len(choices):
                        return choices[index]
                except ValueError:
                    pass
                
                return InputValidator.validate_choice(user_input, choices)
                
            except InputValidationError as e:
                self.logger.warning(f"输入验证失败: {e.message}", LogCategory.USER)
                if attempt < self.max_retries - 1:
                    print(f"❌ {e.message}")
                    print(f"💡 可以输入选项内容或序号(1-{len(choices)})")
                else:
                    print(f"❌ 尝试次数过多，将使用默认值")
                    if default is not None:
                        return default
                    raise
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.error(f"获取选择输入时发生未知错误", exception=e)
                raise GameError("输入处理失败", ErrorCategory.USER_ACTION, ErrorSeverity.HIGH)
    
    def get_confirmation(self, prompt: str, default: Optional[bool] = None) -> bool:
        """安全获取确认输入"""
        for attempt in range(self.max_retries):
            try:
                user_input = input(prompt).strip()
                
                # 处理默认值
                if not user_input and default is not None:
                    return default
                
                return InputValidator.validate_yes_no(user_input)
                
            except InputValidationError as e:
                self.logger.warning(f"输入验证失败: {e.message}", LogCategory.USER)
                if attempt < self.max_retries - 1:
                    print(f"❌ {e.message}")
                    print(f"💡 请输入 y(是) 或 n(否)")
                else:
                    print(f"❌ 尝试次数过多，将使用默认值")
                    if default is not None:
                        return default
                    raise
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.logger.error(f"获取确认输入时发生未知错误", exception=e)
                raise GameError("输入处理失败", ErrorCategory.USER_ACTION, ErrorSeverity.HIGH)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.logger = get_logger()
        self.error_counts: Dict[str, int] = {}
    
    def handle_error(self, error: Exception, context: Optional[str] = None,
                    user_friendly: bool = True) -> bool:
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            user_friendly: 是否显示用户友好的错误信息
            
        Returns:
            bool: 是否可以继续执行
        """
        # 统计错误
        error_key = f"{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # 记录错误日志
        if isinstance(error, GameError):
            self._handle_game_error(error, context, user_friendly)
            return error.severity != ErrorSeverity.CRITICAL
        else:
            self._handle_system_error(error, context, user_friendly)
            return True
    
    def _handle_game_error(self, error: GameError, context: Optional[str] = None,
                          user_friendly: bool = True):
        """处理游戏错误"""
        log_message = f"游戏错误: {error.message}"
        if context:
            log_message += f" (上下文: {context})"
        
        # 根据严重程度选择日志级别
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, LogCategory.ERROR, error.to_dict())
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, LogCategory.ERROR, error.to_dict())
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, LogCategory.ERROR, error.to_dict())
        else:
            self.logger.debug(log_message, LogCategory.ERROR, error.to_dict())
        
        # 显示用户友好信息
        if user_friendly:
            severity_icon = {
                ErrorSeverity.LOW: "⚠️",
                ErrorSeverity.MEDIUM: "❗",
                ErrorSeverity.HIGH: "🚨",
                ErrorSeverity.CRITICAL: "💥"
            }
            
            icon = severity_icon.get(error.severity, "❓")
            print(f"\n{icon} {error.message}")
            
            if error.recovery_suggestion:
                print(f"💡 建议: {error.recovery_suggestion}")
    
    def _handle_system_error(self, error: Exception, context: Optional[str] = None,
                           user_friendly: bool = True):
        """处理系统错误"""
        log_message = f"系统错误: {str(error)}"
        if context:
            log_message += f" (上下文: {context})"
        
        self.logger.error(log_message, LogCategory.ERROR, exception=error)
        
        # 显示用户友好信息
        if user_friendly:
            print(f"\n🚨 系统发生未预期的错误")
            print(f"错误类型: {type(error).__name__}")
            print(f"错误信息: {str(error)}")
            print(f"💡 建议: 请尝试重新操作，如果问题持续存在，请联系开发者")
    
    def get_error_statistics(self) -> Dict[str, int]:
        """获取错误统计"""
        return self.error_counts.copy()


def safe_execute(operation_name: str = "操作", show_errors: bool = True,
                default_return: Any = None, reraise: bool = False):
    """安全执行装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                can_continue = error_handler.handle_error(e, operation_name, show_errors)
                
                if reraise or not can_continue:
                    raise
                else:
                    return default_return
        return wrapper
    return decorator


def validate_input(validation_func: Callable, error_message: str = "输入无效"):
    """输入验证装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 假设第一个参数是需要验证的输入
                if args:
                    validation_func(args[0])
                return func(*args, **kwargs)
            except Exception as e:
                raise InputValidationError(error_message, args[0] if args else None)
        return wrapper
    return decorator


# 全局错误处理器实例
_global_error_handler: Optional[ErrorHandler] = None
_global_safe_input: Optional[SafeInput] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def get_safe_input() -> SafeInput:
    """获取全局安全输入处理器"""
    global _global_safe_input
    if _global_safe_input is None:
        _global_safe_input = SafeInput()
    return _global_safe_input


# 便捷函数
def safe_int_input(prompt: str, min_val: Optional[int] = None, 
                  max_val: Optional[int] = None, default: Optional[int] = None) -> int:
    """安全整数输入"""
    return get_safe_input().get_integer(prompt, min_val, max_val, default)


def safe_str_input(prompt: str, min_length: int = 0, max_length: Optional[int] = None,
                  default: Optional[str] = None) -> str:
    """安全字符串输入"""
    return get_safe_input().get_string(prompt, min_length, max_length, None, default)


def safe_choice_input(prompt: str, choices: List[Any], default: Optional[Any] = None) -> Any:
    """安全选择输入"""
    return get_safe_input().get_choice(prompt, choices, default)


def safe_confirm_input(prompt: str, default: Optional[bool] = None) -> bool:
    """安全确认输入"""
    return get_safe_input().get_confirmation(prompt, default)
