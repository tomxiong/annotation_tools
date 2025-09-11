"""
日志配置模块
提供统一的日志管理功能

日志级别说明：
- DEBUG: 详细的调试信息，包括变量值、执行流程等
- INFO: 关键操作信息，如策略选择、状态变化等  
- WARNING: 警告信息，如性能问题、配置缺失等
- ERROR: 错误信息，程序可以继续运行
- CRITICAL: 严重错误，程序可能无法继续运行
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

# 日志分类配置
LOG_CATEGORIES = {
    # 系统级别
    'SYSTEM': 'SYS',
    'CONFIG': 'CFG', 
    'STARTUP': 'START',
    
    # 功能级别
    'NAVIGATION': 'NAV',
    'ANNOTATION': 'ANN',
    'PERFORMANCE': 'PERF',
    'STRATEGY': 'STRAT',
    
    # 调试级别
    'DEBUG_DETAIL': 'DEBUG',
    'UI_DETAIL': 'UI',
    'DATA_DETAIL': 'DATA',
    'TIMING_DETAIL': 'TIME'
}

class AnnotationLogger:
    """标注工具日志管理器"""

    def __init__(self, name: str = "annotation_tool", level: str = "WARNING"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVELS.get(level, logging.WARNING))  # 默认设为WARNING级别

        # 运行时日志级别控制 - 默认关闭调试和信息输出
        self.runtime_console_level = logging.WARNING  # 控制台默认只显示WARNING及以上
        self.runtime_file_level = logging.INFO        # 文件记录INFO及以上
        
        # 调试模式开关 - 默认关闭
        self.debug_enabled = False
        
        # 详细调试模式 - 显示更多细节
        self.verbose_debug = False
        
        # 性能模式 - 最小化日志输出
        self.performance_mode = True  # 默认启用性能模式

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器 - 根据性能模式和调试开关决定级别
        console_handler = logging.StreamHandler(sys.stdout)
        
        if self.verbose_debug:
            console_handler.setLevel(logging.DEBUG)
        elif self.debug_enabled:
            console_handler.setLevel(logging.INFO)
        elif self.performance_mode:
            console_handler.setLevel(logging.ERROR)  # 性能模式下只显示错误
        else:
            console_handler.setLevel(self.runtime_console_level)

        # 文件处理器 - 根据设置记录不同级别
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "annotation.log", encoding='utf-8')
        file_handler.setLevel(self.runtime_file_level)

        # 控制台格式化器 - 根据模式使用不同格式
        if self.verbose_debug:
            console_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s][%(name)s] %(message)s',
                datefmt='%H:%M:%S'
            )
        elif self.performance_mode:
            console_formatter = logging.Formatter(
                '[%(levelname)s] %(message)s'  # 性能模式下使用最简格式
            )
        else:
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
    
    def _format_message(self, msg: str, category: str = "") -> str:
        """格式化日志消息"""
        if category:
            # 使用缩写提高可读性
            short_category = LOG_CATEGORIES.get(category, category[:8])
            return f"[{short_category}] {msg}"
        return msg
    
    def debug(self, msg: str, category: str = ""):
        """调试日志 - 详细的执行流程和变量值 (默认不在控制台显示)"""
        if not self.debug_enabled and not self.verbose_debug:
            return  # 性能优化：调试关闭时直接返回
        formatted_msg = self._format_message(msg, category)
        self.logger.debug(formatted_msg)
    
    def info(self, msg: str, category: str = ""):
        """信息日志 - 重要的操作和状态变化"""
        formatted_msg = self._format_message(msg, category)
        self.logger.info(formatted_msg)
    
    def warning(self, msg: str, category: str = ""):
        """警告日志 - 需要注意但不影响功能的问题"""
        formatted_msg = self._format_message(msg, category)
        self.logger.warning(formatted_msg)
    
    def error(self, msg: str, category: str = ""):
        """错误日志 - 功能异常但程序可以继续"""
        formatted_msg = self._format_message(msg, category)
        self.logger.error(formatted_msg)
    
    def critical(self, msg: str, category: str = ""):
        """严重错误日志 - 可能导致程序崩溃"""
        formatted_msg = self._format_message(msg, category)
        self.logger.critical(formatted_msg)

    def set_performance_mode(self, enabled: bool = True):
        """设置性能模式 - 最小化日志输出"""
        self.performance_mode = enabled
        if enabled:
            # 性能模式：控制台只显示ERROR及以上
            if hasattr(self, 'console_handler'):
                self.console_handler.setLevel(logging.ERROR)
            # 文件仍记录WARNING及以上
            if hasattr(self, 'file_handler'):
                self.file_handler.setLevel(logging.WARNING)
        else:
            # 普通模式：恢复正常级别
            if hasattr(self, 'console_handler'):
                self.console_handler.setLevel(self.runtime_console_level)
            if hasattr(self, 'file_handler'):
                self.file_handler.setLevel(self.runtime_file_level)

    def enable_debug(self, verbose: bool = False):
        """启用调试日志
        Args:
            verbose: 是否启用详细模式，显示DEBUG级别信息
        """
        self.debug_enabled = True
        self.verbose_debug = verbose
        self.performance_mode = False  # 调试时禁用性能模式
        
        if hasattr(self, 'console_handler'):
            if verbose:
                self.console_handler.setLevel(logging.DEBUG)
                # 更新格式化器
                verbose_formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s][%(name)s] %(message)s',
                    datefmt='%H:%M:%S'
                )
                self.console_handler.setFormatter(verbose_formatter)
            else:
                self.console_handler.setLevel(logging.INFO)
        
        # 文件始终记录DEBUG信息以便调试
        if hasattr(self, 'file_handler'):
            self.file_handler.setLevel(logging.DEBUG)
        
        level_str = "详细调试" if verbose else "信息"
        self.logger.info(f"调试日志已启用 - 级别: {level_str}")

    def disable_debug(self):
        """禁用调试日志，恢复性能模式"""
        self.debug_enabled = False
        self.verbose_debug = False
        self.performance_mode = True
        
        if hasattr(self, 'console_handler'):
            self.console_handler.setLevel(logging.ERROR)
            # 恢复简洁格式
            simple_formatter = logging.Formatter('[%(levelname)s] %(message)s')
            self.console_handler.setFormatter(simple_formatter)
        
        if hasattr(self, 'file_handler'):
            self.file_handler.setLevel(logging.WARNING)
        
        self.logger.warning("调试日志已禁用，恢复性能模式")

    def is_debug_enabled(self) -> bool:
        """检查调试日志是否启用"""
        return self.debug_enabled
    
    def is_verbose_debug_enabled(self) -> bool:
        """检查详细调试日志是否启用"""
        return self.verbose_debug

# 全局日志实例 - 默认性能模式
logger = AnnotationLogger()

# 快捷函数 - 增加性能优化
def log_debug(msg: str, category: str = ""):
    """调试日志 - 在性能模式下会被跳过"""
    if logger.performance_mode and not logger.debug_enabled:
        return  # 性能优化：直接返回
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
def enable_debug_logging(verbose: bool = False):
    """启用调试日志
    Args:
        verbose: 是否启用详细模式
    """
    logger.enable_debug(verbose)

def disable_debug_logging():
    """禁用调试日志，恢复性能模式"""
    logger.disable_debug()

def set_performance_mode(enabled: bool = True):
    """设置性能模式 - 最小化日志输出影响
    Args:
        enabled: True=性能模式(控制台只显示ERROR), False=普通模式
    """
    logger.set_performance_mode(enabled)

def is_debug_logging_enabled() -> bool:
    """检查调试日志是否启用"""
    return logger.is_debug_enabled()

def is_verbose_debug_enabled() -> bool:
    """检查详细调试日志是否启用"""
    return logger.is_verbose_debug_enabled()

def is_performance_mode() -> bool:
    """检查是否为性能模式"""
    return logger.performance_mode

def toggle_debug_logging():
    """切换调试日志开关"""
    if logger.is_debug_enabled():
        logger.disable_debug()
    else:
        logger.enable_debug()

def set_debug_mode(mode: str = "off"):
    """设置调试模式
    Args:
        mode: "off" | "info" | "verbose" | "performance"
    """
    if mode == "off" or mode == "performance":
        logger.disable_debug()
        if mode == "performance":
            logger.set_performance_mode(True)
    elif mode == "info":
        logger.enable_debug(verbose=False)
    elif mode == "verbose":
        logger.enable_debug(verbose=True)
    else:
        raise ValueError(f"无效的调试模式: {mode}，支持: off, info, verbose, performance")

# 便捷的日志函数别名 - 按重要性分类
def log_strategy(msg: str):
    """策略相关日志 - INFO级别"""
    log_info(msg, "STRATEGY")

def log_perf(msg: str):
    """性能相关日志 - INFO级别"""
    log_info(msg, "PERFORMANCE")

def log_nav(msg: str):
    """导航相关日志 - INFO级别"""
    log_info(msg, "NAVIGATION")

def log_ann(msg: str):
    """标注相关日志 - INFO级别"""
    log_info(msg, "ANNOTATION")

# 调试级别的便捷函数 - 在性能模式下会被优化跳过
def log_debug_detail(msg: str):
    """详细调试日志 - DEBUG级别 (性能模式下跳过)"""
    if logger.performance_mode and not logger.debug_enabled:
        return
    log_debug(msg, "DEBUG_DETAIL")

def log_ui_detail(msg: str):
    """UI详细日志 - DEBUG级别 (性能模式下跳过)"""
    if logger.performance_mode and not logger.debug_enabled:
        return
    log_debug(msg, "UI_DETAIL")

def log_timing(msg: str):
    """时序详细日志 - DEBUG级别 (性能模式下跳过)"""
    if logger.performance_mode and not logger.debug_enabled:
        return
    log_debug(msg, "TIMING_DETAIL")

# 系统级别日志函数 - 总是记录
def log_config(msg: str):
    """配置相关日志 - INFO级别"""
    log_info(msg, "CONFIG")

def log_startup(msg: str):
    """启动相关日志 - INFO级别"""
    log_info(msg, "STARTUP")

def log_system(msg: str):
    """系统级别日志 - WARNING级别"""
    log_warning(msg, "SYSTEM")
