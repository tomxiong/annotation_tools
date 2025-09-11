#!/usr/bin/env python3
"""
标注工具日志级别初始化配置
在应用启动时调用，设置生产环境优化的日志级别
"""

from src.utils.logger import set_performance_mode, set_debug_mode, log_startup

def initialize_production_logging():
    """初始化生产环境日志配置"""
    # 启用性能模式，最小化控制台输出
    set_performance_mode(True)
    
    # 记录启动信息
    log_startup("标注工具启动 - 性能模式已启用（控制台仅显示错误，详细日志保存到文件）")

def initialize_development_logging():
    """初始化开发环境日志配置"""
    # 启用信息级别日志
    set_debug_mode("info")
    
    # 记录启动信息
    log_startup("标注工具启动 - 开发模式已启用（显示信息级别日志）")

def initialize_debug_logging():
    """初始化调试环境日志配置"""
    # 启用详细调试日志
    set_debug_mode("verbose")
    
    # 记录启动信息
    log_startup("标注工具启动 - 调试模式已启用（显示所有级别日志）")

# 默认配置：生产环境
def init_default_logging():
    """默认日志初始化 - 生产环境配置"""
    initialize_production_logging()

if __name__ == "__main__":
    # 如果直接运行此文件，显示不同模式的示例
    print("📋 日志级别配置说明:")
    print("1. 生产模式（默认）: 控制台只显示错误，详细日志保存到文件")
    print("2. 开发模式: 控制台显示信息级别日志")  
    print("3. 调试模式: 控制台显示所有级别日志")
    print()
    print("🔧 在代码中使用:")
    print("from src.config.logging_config import init_default_logging")
    print("init_default_logging()  # 在main()函数开始时调用")
