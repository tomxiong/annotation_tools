"""
异常处理模块

提供统一的异常处理机制，支持：
- 自定义异常类型
- 异常链管理
- 异常日志记录
- 异常恢复策略
- 错误代码管理
"""

import sys
import traceback
import functools
import threading
from typing import Any, Dict, Optional, Union, List, Callable, Type, Tuple
from datetime import datetime
from enum import Enum
import json

import logging

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """错误代码枚举"""
    # 系统错误 (1000-1999)
    SYSTEM_ERROR = 1000
    CONFIG_ERROR = 1001
    LOG_ERROR = 1002
    FILE_ERROR = 1003
    NETWORK_ERROR = 1004
    DATABASE_ERROR = 1005
    
    # 业务错误 (2000-2999)
    VALIDATION_ERROR = 2000
    NOT_FOUND_ERROR = 2001
    PERMISSION_ERROR = 2002
    BUSINESS_LOGIC_ERROR = 2003
    TIMEOUT_ERROR = 2004
    
    # UI错误 (3000-3999)
    UI_ERROR = 3000
    INPUT_ERROR = 3001
    RENDER_ERROR = 3002
    
    # 图像处理错误 (4000-4999)
    IMAGE_ERROR = 4000
    IMAGE_LOAD_ERROR = 4001
    IMAGE_PROCESS_ERROR = 4002
    IMAGE_FORMAT_ERROR = 4003
    
    # 标注错误 (5000-5999)
    ANNOTATION_ERROR = 5000
    ANNOTATION_SAVE_ERROR = 5001
    ANNOTATION_LOAD_ERROR = 5002
    ANNOTATION_FORMAT_ERROR = 5003


class BaseException(Exception):
    """基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.SYSTEM_ERROR,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        初始化异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            cause: 原始异常
            context: 异常上下文
            user_message: 用户友好消息
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.cause = cause
        self.context = context or {}
        self.user_message = user_message or message
        self.timestamp = datetime.now()
        
        # 记录异常
        self._log_exception()
    
    def _log_exception(self):
        """记录异常日志"""
        log_data = {
            'error_code': self.error_code.value,
            'error_name': self.error_code.name,
            'message': self.message,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }
        
        if self.cause:
            log_data['cause'] = str(self.cause)
            log_data['cause_type'] = type(self.cause).__name__
        
        log_data['message'] = f"异常发生: {self.message}"
        structured_log_entry(logger, 'ERROR', **log_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'error_code': self.error_code.value,
            'error_name': self.error_code.name,
            'message': self.message,
            'user_message': self.user_message,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'cause': str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code.name}] {self.message}"


class SystemError(BaseException):
    """系统异常"""
    def __init__(self, message: str, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.SYSTEM_ERROR, cause, **kwargs)


class ConfigError(BaseException):
    """配置异常"""
    def __init__(self, message: str, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.CONFIG_ERROR, cause, **kwargs)


class ConfigValidationError(ConfigError):
    """配置验证异常"""
    def __init__(self, message: str, validation_errors: List[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []


class LoggerError(BaseException):
    """日志异常"""
    def __init__(self, message: str, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.LOG_ERROR, cause, **kwargs)


class FileError(BaseException):
    """文件异常"""
    def __init__(self, message: str, file_path: str = None, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.FILE_ERROR, cause, **kwargs)
        self.file_path = file_path


class NetworkError(BaseException):
    """网络异常"""
    def __init__(self, message: str, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.NETWORK_ERROR, cause, **kwargs)


class DatabaseError(BaseException):
    """数据库异常"""
    def __init__(self, message: str, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.DATABASE_ERROR, cause, **kwargs)


class ValidationError(BaseException):
    """验证异常"""
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, **kwargs)
        self.field = field
        self.value = value


class NotFoundError(BaseException):
    """未找到异常"""
    def __init__(self, message: str, resource_type: str = None, resource_id: Any = None, **kwargs):
        super().__init__(message, ErrorCode.NOT_FOUND_ERROR, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class PermissionError(BaseException):
    """权限异常"""
    def __init__(self, message: str, required_permission: str = None, **kwargs):
        super().__init__(message, ErrorCode.PERMISSION_ERROR, **kwargs)
        self.required_permission = required_permission


class BusinessLogicError(BaseException):
    """业务逻辑异常"""
    def __init__(self, message: str, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.BUSINESS_LOGIC_ERROR, cause, **kwargs)


class TimeoutError(BaseException):
    """超时异常"""
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        super().__init__(message, ErrorCode.TIMEOUT_ERROR, **kwargs)
        self.timeout_seconds = timeout_seconds


class ServiceError(BaseException):
    """服务异常"""
    def __init__(self, message: str, service_name: str = None, **kwargs):
        super().__init__(message, ErrorCode.SYSTEM_ERROR, **kwargs)
        self.service_name = service_name


class UIError(BaseException):
    """UI异常"""
    def __init__(self, message: str, component: str = None, **kwargs):
        super().__init__(message, ErrorCode.UI_ERROR, **kwargs)
        self.component = component


class InputError(BaseException):
    """输入异常"""
    def __init__(self, message: str, field: str = None, input_value: Any = None, **kwargs):
        super().__init__(message, ErrorCode.INPUT_ERROR, **kwargs)
        self.field = field
        self.input_value = input_value


class RenderError(BaseException):
    """渲染异常"""
    def __init__(self, message: str, component: str = None, **kwargs):
        super().__init__(message, ErrorCode.RENDER_ERROR, **kwargs)
        self.component = component


class ImageError(BaseException):
    """图像异常"""
    def __init__(self, message: str, image_path: str = None, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, ErrorCode.IMAGE_ERROR, cause, **kwargs)
        self.image_path = image_path


class ImageLoadError(ImageError):
    """图像加载异常"""
    def __init__(self, message: str, image_path: str = None, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, image_path, cause, error_code=ErrorCode.IMAGE_LOAD_ERROR, **kwargs)


class ImageProcessError(ImageError):
    """图像处理异常"""
    def __init__(self, message: str, operation: str = None, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, cause=cause, error_code=ErrorCode.IMAGE_PROCESS_ERROR, **kwargs)
        self.operation = operation


class ImageFormatError(ImageError):
    """图像格式异常"""
    def __init__(self, message: str, file_format: str = None, **kwargs):
        super().__init__(message, error_code=ErrorCode.IMAGE_FORMAT_ERROR, **kwargs)
        self.file_format = file_format


class AnnotationError(BaseException):
    """标注异常"""
    def __init__(self, message: str, annotation_id: str = None, **kwargs):
        super().__init__(message, ErrorCode.ANNOTATION_ERROR, **kwargs)
        self.annotation_id = annotation_id


class AnnotationSaveError(AnnotationError):
    """标注保存异常"""
    def __init__(self, message: str, annotation_id: str = None, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, annotation_id, cause=cause, error_code=ErrorCode.ANNOTATION_SAVE_ERROR, **kwargs)


class AnnotationLoadError(AnnotationError):
    """标注加载异常"""
    def __init__(self, message: str, file_path: str = None, cause: Optional[Exception] = None, **kwargs):
        super().__init__(message, cause=cause, error_code=ErrorCode.ANNOTATION_LOAD_ERROR, **kwargs)
        self.file_path = file_path


class AnnotationFormatError(AnnotationError):
    """标注格式异常"""
    def __init__(self, message: str, expected_format: str = None, actual_format: str = None, **kwargs):
        super().__init__(message, error_code=ErrorCode.ANNOTATION_FORMAT_ERROR, **kwargs)
        self.expected_format = expected_format
        self.actual_format = actual_format


class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self):
        self._handlers: Dict[Type[Exception], Callable] = {}
        self._default_handler: Optional[Callable] = None
        self._lock = threading.RLock()
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """
        注册异常处理器
        
        Args:
            exception_type: 异常类型
            handler: 处理函数
        """
        with self._lock:
            self._handlers[exception_type] = handler
    
    def register_default_handler(self, handler: Callable):
        """
        注册默认异常处理器
        
        Args:
            handler: 默认处理函数
        """
        with self._lock:
            self._default_handler = handler
    
    def handle(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        处理异常
        
        Args:
            exception: 异常实例
            context: 上下文信息
            
        Returns:
            处理结果
        """
        try:
            # 查找匹配的处理器
            handler = None
            for exc_type in type(exception).__mro__:
                if exc_type in self._handlers:
                    handler = self._handlers[exc_type]
                    break
            
            if handler:
                return handler(exception, context)
            elif self._default_handler:
                return self._default_handler(exception, context)
            else:
                # 默认处理：重新抛出异常
                raise exception
                
        except Exception as e:
            # 避免无限递归，直接抛出原始异常
            raise exception


class ExceptionManager:
    """异常管理器"""
    
    _instance: Optional['ExceptionManager'] = None
    _lock = threading.RLock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._handler = ExceptionHandler()
            self._exception_counts: Dict[ErrorCode, int] = {}
            self._recent_exceptions: List[BaseException] = []
            self._max_recent_exceptions = 100
            self._initialized = True
    
    def handle_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        处理异常
        
        Args:
            exception: 异常实例
            context: 上下文信息
            
        Returns:
            处理结果
        """
        # 统计异常
        if isinstance(exception, BaseException):
            self._count_exception(exception.error_code)
            self._add_recent_exception(exception)
        
        # 处理异常
        return self._handler.handle(exception, context)
    
    def _count_exception(self, error_code: ErrorCode):
        """统计异常次数"""
        with self._lock:
            self._exception_counts[error_code] = self._exception_counts.get(error_code, 0) + 1
    
    def _add_recent_exception(self, exception: BaseException):
        """添加到最近异常列表"""
        with self._lock:
            self._recent_exceptions.append(exception)
            if len(self._recent_exceptions) > self._max_recent_exceptions:
                self._recent_exceptions.pop(0)
    
    def get_exception_stats(self) -> Dict[str, Any]:
        """获取异常统计信息"""
        with self._lock:
            return {
                'total_exceptions': sum(self._exception_counts.values()),
                'exception_counts': {code.name: count for code, count in self._exception_counts.items()},
                'recent_exceptions': [exc.to_dict() for exc in self._recent_exceptions[-10:]]
            }
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """注册异常处理器"""
        self._handler.register_handler(exception_type, handler)
    
    def register_default_handler(self, handler: Callable):
        """注册默认异常处理器"""
        self._handler.register_default_handler(handler)


def exception_handler(
    exception_types: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    reraise: bool = False,
    default_return: Any = None,
    log_exception: bool = True
):
    """
    异常处理装饰器
    
    Args:
        exception_types: 要捕获的异常类型
        reraise: 是否重新抛出异常
        default_return: 默认返回值
        log_exception: 是否记录异常日志
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_exception:
                    logger.error(f"函数 {func.__name__} 执行异常: {e}", exc_info=True)
                
                if reraise:
                    raise
                return default_return
        
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数
        exceptions: 要重试的异常类型
        on_retry: 重试回调函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试，抛出异常
                        raise e
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{current_delay}s 后重试")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # 不应该到达这里
            raise last_exception
        
        return wrapper
    return decorator


def validate_input(**validators):
    """
    输入验证装饰器
    
    Args:
        validators: 验证器字典，键为参数名，值为验证函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数参数
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 验证参数
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    try:
                        validator(bound_args.arguments[param_name])
                    except Exception as e:
                        raise ValidationError(f"参数 {param_name} 验证失败: {e}", field=param_name)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def structured_log_entry(logger, level: str, **extra):
    """记录结构化日志（简化版本，避免循环导入）"""
    try:
        message = extra.pop('message', 'Unknown message')
        log_entry = {
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat(),
            **extra
        }
        logger.log(getattr(logging, level.upper()), json.dumps(log_entry, ensure_ascii=False))
    except Exception:
        message = extra.get('message', 'Unknown message')
        logger.log(getattr(logging, level.upper()), message)


def get_exception_manager() -> ExceptionManager:
    """获取异常管理器实例"""
    return ExceptionManager()


def handle_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
    """
    处理异常的便捷函数
    
    Args:
        exception: 异常实例
        context: 上下文信息
        
    Returns:
        处理结果
    """
    return get_exception_manager().handle_exception(exception, context)


def create_user_message(exception: Exception) -> str:
    """
    创建用户友好的错误消息
    
    Args:
        exception: 异常实例
        
    Returns:
        用户友好的错误消息
    """
    if isinstance(exception, BaseException):
        return exception.user_message
    else:
        return f"系统错误: {str(exception)}"


def format_exception_for_display(exception: Exception) -> str:
    """
    格式化异常用于显示
    
    Args:
        exception: 异常实例
        
    Returns:
        格式化的异常信息
    """
    if isinstance(exception, BaseException):
        return f"[{exception.error_code.name}] {exception.user_message}"
    else:
        return f"错误: {str(exception)}"


def get_exception_traceback(exception: Exception) -> str:
    """
    获取异常堆栈跟踪
    
    Args:
        exception: 异常实例
        
    Returns:
        堆栈跟踪字符串
    """
    return ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        default_return: 默认返回值
        log_errors: 是否记录错误
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"安全执行函数失败: {func.__name__} - {e}", exc_info=True)
        return default_return