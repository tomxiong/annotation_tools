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
    
    def __init__(self, name: str = "annotation_tool", level: str = "DEBUG"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVELS.get(level, logging.INFO))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器 - 只显示警告和错误，保持控制台简洁
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)

        # 文件处理器 - 保留所有调试信息用于调试
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "annotation.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
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
