#!/usr/bin/env python3
"""
日志配置管理工具
用于动态调整日志级别和查看日志状态
"""

import sys
import argparse
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / 'src'

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def show_log_status():
    """显示当前日志状态"""
    try:
        from src.utils.logger import (
            logger, is_debug_logging_enabled, is_verbose_debug_enabled, is_performance_mode
        )
        
        print("📋 当前日志配置状态:")
        print(f"  性能模式: {'启用' if is_performance_mode() else '禁用'}")
        print(f"  调试日志: {'启用' if is_debug_logging_enabled() else '禁用'}")
        print(f"  详细模式: {'启用' if is_verbose_debug_enabled() else '禁用'}")
        print(f"  控制台级别: {logger.console_handler.level}")
        print(f"  文件级别: {logger.file_handler.level}")
        
        # 显示级别说明
        level_names = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}
        console_level_name = level_names.get(logger.console_handler.level, "未知")
        file_level_name = level_names.get(logger.file_handler.level, "未知")
        print(f"  控制台显示: {console_level_name} 及以上")
        print(f"  文件记录: {file_level_name} 及以上")
        
        return True
    except Exception as e:
        print(f"❌ 获取日志状态失败: {e}")
        return False

def set_log_level(mode: str):
    """设置日志级别"""
    try:
        from src.utils.logger import set_debug_mode
        
        set_debug_mode(mode)
        print(f"✅ 日志模式已设置为: {mode}")
        
        # 显示更新后的状态
        show_log_status()
        return True
        
    except Exception as e:
        print(f"❌ 设置日志级别失败: {e}")
        return False

def test_log_levels():
    """测试不同的日志级别输出"""
    try:
        from src.utils.logger import (
            log_debug, log_info, log_warning, log_error,
            log_strategy, log_perf, log_nav, log_ann,
            log_debug_detail, log_ui_detail, log_timing
        )
        
        print("🧪 测试不同日志级别的输出:")
        print("-" * 50)
        
        # 基础日志级别
        log_error("这是一个错误日志示例", "TEST")
        log_warning("这是一个警告日志示例", "TEST")
        log_info("这是一个信息日志示例", "TEST")
        log_debug("这是一个调试日志示例", "TEST")
        
        print("\n便捷日志函数测试:")
        log_strategy("智能继承策略已选择策略2")
        log_perf("性能监控: 保存并下一个操作耗时 125ms")
        log_nav("导航: 从孔位1跳转到孔位2")
        log_ann("标注: 已保存增强标注数据")
        
        print("\n详细调试日志测试:")
        log_debug_detail("变量值: current_hole=1, next_hole=2")
        log_ui_detail("UI组件更新: 按钮状态=禁用")
        log_timing("时序: 按钮禁用->5ms, 设置收集->12ms")
        
        print("-" * 50)
        print("✅ 日志级别测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 日志级别测试失败: {e}")
        return False

def show_log_categories():
    """显示可用的日志分类"""
    from src.utils.logger import LOG_CATEGORIES
    
    print("📚 可用的日志分类:")
    print("-" * 40)
    
    categories = {
        "系统级别": ["SYSTEM", "CONFIG", "STARTUP"],
        "功能级别": ["NAVIGATION", "ANNOTATION", "PERFORMANCE", "STRATEGY"], 
        "调试级别": ["DEBUG_DETAIL", "UI_DETAIL", "DATA_DETAIL", "TIMING_DETAIL"]
    }
    
    for group_name, group_cats in categories.items():
        print(f"\n{group_name}:")
        for cat in group_cats:
            short_name = LOG_CATEGORIES.get(cat, cat)
            print(f"  {cat:<15} -> [{short_name}]")

def clear_logs():
    """清理日志文件"""
    try:
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                for log_file in log_files:
                    # 备份当前日志
                    backup_name = f"{log_file.stem}_backup.log"
                    backup_path = log_dir / backup_name
                    if backup_path.exists():
                        backup_path.unlink()
                    log_file.rename(backup_path)
                    print(f"  已备份: {log_file.name} -> {backup_name}")
                
                print(f"✅ 已清理 {len(log_files)} 个日志文件")
            else:
                print("ℹ️  没有找到日志文件")
        else:
            print("ℹ️  日志目录不存在")
        return True
        
    except Exception as e:
        print(f"❌ 清理日志失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="日志配置管理工具")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 状态命令
    subparsers.add_parser("status", help="显示当前日志状态")
    
    # 设置级别命令
    level_parser = subparsers.add_parser("set", help="设置日志级别")
    level_parser.add_argument(
        "mode", 
        choices=["off", "info", "verbose", "performance"], 
        help="日志模式: off(关闭), info(信息), verbose(详细), performance(性能模式)"
    )
    
    # 测试命令
    subparsers.add_parser("test", help="测试不同日志级别的输出")
    
    # 分类命令
    subparsers.add_parser("categories", help="显示可用的日志分类")
    
    # 清理命令
    subparsers.add_parser("clear", help="清理日志文件")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🔧 日志配置管理工具")
    print("=" * 50)
    
    if args.command == "status":
        show_log_status()
    elif args.command == "set":
        set_log_level(args.mode)
    elif args.command == "test":
        test_log_levels()
    elif args.command == "categories":
        show_log_categories()
    elif args.command == "clear":
        clear_logs()
    
    print("=" * 50)

if __name__ == '__main__':
    main()
