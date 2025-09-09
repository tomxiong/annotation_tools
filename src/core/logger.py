"""
日志系统模块

提供统一的日志管理功能，支持：
- 多级别日志记录
- 文件和控制台输出
- 日志轮转
- 结构化日志
- 异步日志记录
- 日志格式化
"""

import os
import sys
import logging
import logging.handlers
import threading
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union, List, Callable
from pathlib import Path
from functools import wraps
from contextlib import contextmanager
import traceback

# 全局日志器字典
_loggers: Dict[str, logging.Logger] = {}
_loggers_lock = threading.RLock()
_initialized = False
_init_lock = threading.RLock()


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        self._default_formatter = logging.Formatter(fmt, datefmt, style)
    
    def format(self, record):
        """格式化日志记录为JSON格式"""
        if not hasattr(record, 'structured'):
            return self._default_formatter.format(record)
        
        # 创建结构化日志
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # 添加额外字段
        if hasattr(record, 'extra') and record.extra:
            log_entry.update(record.extra)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        """格式化日志记录为彩色格式"""
        # 添加颜色
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # 格式化消息
        formatted_message = super().format(record)
        
        # 应用颜色
        if level_color and sys.stdout.isatty():
            return f"{level_color}{formatted_message}{reset_color}"
        
        return formatted_message


class AsyncLogHandler(logging.Handler):
    """异步日志处理器"""
    
    def __init__(self, handler: logging.Handler, queue_size: int = 1000):
        """
        初始化异步日志处理器
        
        Args:
            handler: 实际的日志处理器
            queue_size: 队列大小
        """
        super().__init__()
        self.handler = handler
        self.queue_size = queue_size
        self._queue = []
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
    
    def emit(self, record):
        """异步发送日志记录"""
        try:
            with self._lock:
                if len(self._queue) >= self.queue_size:
                    # 队列满，丢弃最旧的日志
                    self._queue.pop(0)
                self._queue.append(record)
        except Exception:
            pass
    
    def _worker(self):
        """工作线程"""
        while not self._stop_event.is_set():
            records = []
            with self._lock:
                if self._queue:
                    records = self._queue.copy()
                    self._queue.clear()
            
            for record in records:
                try:
                    self.handler.emit(record)
                except Exception:
                    pass
            
            time.sleep(0.1)  # 避免CPU占用过高
    
    def close(self):
        """关闭处理器"""
        self._stop_event.set()
        self._worker_thread.join(timeout=1.0)
        self.handler.close()


class PerformanceLogger:
    """性能日志器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    @contextmanager
    def timer(self, operation: str, threshold: float = None):
        """
        计时上下文管理器
        
        Args:
            operation: 操作名称
            threshold: 性能阈值（秒），超过则记录警告
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            if threshold and elapsed > threshold:
                self.logger.warning(f"性能警告: {operation} 耗时 {elapsed:.3f}s (阈值: {threshold}s)")
            else:
                self.logger.debug(f"性能统计: {operation} 耗时 {elapsed:.3f}s")
    
    def log_timing(self, operation: str, elapsed_time: float, threshold: float = None):
        """
        记录性能统计
        
        Args:
            operation: 操作名称
            elapsed_time: 耗时（秒）
            threshold: 性能阈值（秒）
        """
        if threshold and elapsed_time > threshold:
            self.logger.warning(f"性能警告: {operation} 耗时 {elapsed_time:.3f}s (阈值: {threshold}s)")
        else:
            self.logger.debug(f"性能统计: {operation} 耗时 {elapsed_time:.3f}s")


def initialize_logging(config: Optional[Any] = None) -> None:
    """
    初始化日志系统
    
    Args:
        config: 日志配置，如果为None则使用默认配置
    """
    global _initialized
    
    with _init_lock:
        if _initialized:
            return
        
        try:
            # 默认配置
            default_config = type('DefaultConfig', (), {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': 'logs/app.log',
                'max_file_size': 10 * 1024 * 1024,
                'backup_count': 5,
                'console_output': True
            })()
            
            if config is None:
                config = default_config
            elif hasattr(config, 'logging'):
                config = config.logging
            
            # 确保日志目录存在
            log_dir = Path(config.file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 配置根日志器
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, config.level.upper()))
            
            # 清除现有处理器
            root_logger.handlers.clear()
            
            # 创建文件处理器
            if config.file_path:
                file_handler = logging.handlers.RotatingFileHandler(
                    config.file_path,
                    maxBytes=config.max_file_size,
                    backupCount=config.backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, config.level.upper()))
                file_formatter = JSONFormatter(config.format)
                file_handler.setFormatter(file_formatter)
                
                # 使用异步处理器
                async_file_handler = AsyncLogHandler(file_handler)
                root_logger.addHandler(async_file_handler)
            
            # 创建控制台处理器
            if config.console_output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(getattr(logging, config.level.upper()))
                console_formatter = ColoredFormatter(config.format)
                console_handler.setFormatter(console_formatter)
                root_logger.addHandler(console_handler)
            
            # 设置错误处理器
            def handle_exception(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                
                root_logger.critical(
                    "未捕获的异常",
                    exc_info=(exc_type, exc_value, exc_traceback)
                )
            
            sys.excepthook = handle_exception
            
            _initialized = True
            logging.info("日志系统初始化成功")
            
        except Exception as e:
            print(f"初始化日志系统失败: {e}")
            # 延迟导入避免循环依赖
            from .exceptions import LoggerError
            raise LoggerError(f"初始化日志系统失败: {e}")


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称，如果为None则使用根日志器
        
    Returns:
        日志器实例
    """
    if not _initialized:
        initialize_logging()
    
    if name is None:
        return logging.getLogger()
    
    with _loggers_lock:
        if name not in _loggers:
            _loggers[name] = logging.getLogger(name)
        return _loggers[name]


def set_level(level: Union[str, int]) -> None:
    """
    设置日志级别
    
    Args:
        level: 日志级别
    """
    try:
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        
        logging.getLogger().setLevel(level)
        logging.info(f"日志级别已设置为: {logging.getLevelName(level)}")
    except Exception as e:
        logging.error(f"设置日志级别失败: {e}")


def add_file_handler(file_path: str, level: str = 'INFO', format: str = None) -> None:
    """
    添加文件处理器
    
    Args:
        file_path: 文件路径
        level: 日志级别
        format: 日志格式
    """
    try:
        logger = logging.getLogger()
        
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建处理器
        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.setLevel(getattr(logging, level.upper()))
        
        # 设置格式
        if format is None:
            format = logging.getLogger().handlers[0].formatter._fmt if logging.getLogger().handlers else None
        
        if format:
            formatter = JSONFormatter(format)
            handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logging.info(f"文件处理器已添加: {file_path}")
        
    except Exception as e:
        logging.error(f"添加文件处理器失败: {e}")


def remove_handler(handler: logging.Handler) -> None:
    """
    移除日志处理器
    
    Args:
        handler: 要移除的处理器
    """
    try:
        logging.getLogger().removeHandler(handler)
        handler.close()
    except Exception as e:
        logging.error(f"移除处理器失败: {e}")


def log_function_call(logger: logging.Logger = None, level: str = 'DEBUG', include_args: bool = True):
    """
    函数调用日志装饰器
    
    Args:
        logger: 日志器，如果为None则使用调用者的日志器
        level: 日志级别
        include_args: 是否包含参数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if logger is None:
                # 获取调用者的日志器
                frame = sys._getframe(1)
                module_name = frame.f_globals.get('__name__', '')
                func_logger = logging.getLogger(module_name)
            else:
                func_logger = logger
            
            # 记录函数调用
            if include_args:
                func_logger.log(
                    getattr(logging, level.upper()),
                    f"调用函数: {func.__name__} (args: {args}, kwargs: {kwargs})"
                )
            else:
                func_logger.log(
                    getattr(logging, level.upper()),
                    f"调用函数: {func.__name__}"
                )
            
            try:
                result = func(*args, **kwargs)
                func_logger.log(
                    getattr(logging, level.upper()),
                    f"函数返回: {func.__name__} -> {type(result).__name__}"
                )
                return result
            except Exception as e:
                func_logger.error(
                    f"函数异常: {func.__name__} -> {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def structured_log_msg(logger: logging.Logger, level: str, message: str, **extra):
    """
    记录结构化日志
    
    Args:
        logger: 日志器
        level: 日志级别
        message: 日志消息
        **extra: 额外字段
    """
    try:
        # 创建日志记录
        record = logger.makeRecord(
            logger.name,
            getattr(logging, level.upper()),
            '(unknown file)',
            0,
            message,
            (),
            None
        )
        
        # 添加结构化标记和额外字段
        record.structured = True
        record.extra = extra
        
        # 处理日志记录
        logger.handle(record)
        
    except Exception as e:
        logger.error(f"记录结构化日志失败: {e}")


def get_performance_logger(name: str = None) -> PerformanceLogger:
    """
    获取性能日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        性能日志器实例
    """
    logger = get_logger(name)
    return PerformanceLogger(logger)


def create_audit_logger(name: str, file_path: str) -> logging.Logger:
    """
    创建审计日志器
    
    Args:
        name: 日志器名称
        file_path: 审计日志文件路径
        
    Returns:
        审计日志器实例
    """
    try:
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建日志器
        audit_logger = logging.getLogger(f"audit.{name}")
        audit_logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        audit_logger.handlers.clear()
        
        # 创建文件处理器
        handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        handler.setLevel(logging.INFO)
        
        # 设置JSON格式
        formatter = JSONFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        audit_logger.addHandler(handler)
        
        # 防止传播到根日志器
        audit_logger.propagate = False
        
        return audit_logger
        
    except Exception as e:
        logging.error(f"创建审计日志器失败: {e}")
        # 延迟导入避免循环依赖
        from .exceptions import LoggerError
        raise LoggerError(f"创建审计日志器失败: {e}")


def setup_logger() -> None:
    """设置日志系统（向后兼容）"""
    initialize_logging()


def shutdown_logging() -> None:
    """关闭日志系统"""
    try:
        logging.info("正在关闭日志系统...")

        # 关闭所有处理器
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        # 清理日志器字典
        with _loggers_lock:
            _loggers.clear()

        global _initialized
        _initialized = False

        print("日志系统已关闭")

    except Exception as e:
        print(f"关闭日志系统失败: {e}")


# 便捷函数
def debug(message: str, *args, **kwargs):
    """记录DEBUG级别日志"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """记录INFO级别日志"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """记录WARNING级别日志"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """记录ERROR级别日志"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """记录CRITICAL级别日志"""
    get_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """记录异常日志"""
    get_logger().exception(message, *args, **kwargs)