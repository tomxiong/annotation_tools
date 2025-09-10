"""
日志配置模块
提供统一的日志管理功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# 日志配置
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class AnnotationLogger:
    """标注工具日志管理器"""

    def __init__(self, name: str = "annotation_tool", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVELS.get(level, logging.INFO))

        # 调试模式开关 - 默认关闭
        self.debug_enabled = False

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器 - 根据调试开关决定级别
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.debug_enabled else logging.ERROR)

        # 文件处理器 - 始终保留所有调试信息用于调试
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "annotation.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 控制台格式化器 - 简洁格式
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )

        # 文件格式化器 - 详细格式
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        # 保存处理器引用以便动态调整
        self.console_handler = console_handler
        self.file_handler = file_handler
    
    def debug(self, msg: str, category: str = ""):
        """调试日志"""
        if category:
            msg = f"[{category}] {msg}"
        self.logger.debug(msg)
    
    def info(self, msg: str, category: str = ""):
        """信息日志"""
        if category:
            msg = f"[{category}] {msg}"
        self.logger.info(msg)
    
    def warning(self, msg: str, category: str = ""):
        """警告日志"""
        if category:
            msg = f"[{category}] {msg}"
        self.logger.warning(msg)
    
    def error(self, msg: str, category: str = ""):
        """错误日志"""
        if category:
            msg = f"[{category}] {msg}"
        self.logger.error(msg)
    
    def critical(self, msg: str, category: str = ""):
        """严重错误日志"""
        if category:
            msg = f"[{category}] {msg}"
        self.logger.critical(msg)

    def enable_debug(self):
        """启用调试日志"""
        self.debug_enabled = True
        if hasattr(self, 'console_handler'):
            self.console_handler.setLevel(logging.DEBUG)
        self.logger.info("调试日志已启用")

    def disable_debug(self):
        """禁用调试日志"""
        self.debug_enabled = False
        if hasattr(self, 'console_handler'):
            self.console_handler.setLevel(logging.ERROR)
        self.logger.info("调试日志已禁用")

    def is_debug_enabled(self) -> bool:
        """检查调试日志是否启用"""
        return self.debug_enabled

# 全局日志实例
logger = AnnotationLogger()

# 快捷函数
def log_debug(msg: str, category: str = ""):
    logger.debug(msg, category)

def log_info(msg: str, category: str = ""):
    logger.info(msg, category)

def log_warning(msg: str, category: str = ""):
    logger.warning(msg, category)

def log_error(msg: str, category: str = ""):
    logger.error(msg, category)

def log_critical(msg: str, category: str = ""):
    logger.critical(msg, category)

# 调试控制函数
def enable_debug_logging():
    """启用调试日志"""
    logger.enable_debug()

def disable_debug_logging():
    """禁用调试日志"""
    logger.disable_debug()

def is_debug_logging_enabled() -> bool:
    """检查调试日志是否启用"""
    return logger.is_debug_enabled()

def toggle_debug_logging():
    """切换调试日志开关"""
    if logger.is_debug_enabled():
        logger.disable_debug()
    else:
        logger.enable_debug()
