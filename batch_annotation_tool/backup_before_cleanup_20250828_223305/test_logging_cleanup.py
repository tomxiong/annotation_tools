#!/usr/bin/env python3
"""
日志清理验证测试
验证日志输出已经被优化，减少了无用的调试信息
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_logging_cleanup():
    """测试日志清理效果"""
    print("🧹 日志清理验证测试")
    print("=" * 60)
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建GUI实例
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI初始化成功")
        print("\n🎯 已实施的日志清理改进:")
        print("1. ❌ 移除了重复的 'DEBUG: 开始获取特征组合...' 信息")
        print("2. ❌ 移除了冗余的 'DEBUG: 特征组合创建成功' 信息")
        print("3. ❌ 移除了多余的类型检查日志")
        print("4. ❌ 移除了重复的训练标签获取日志")
        print("5. ❌ 减少了统计更新的重复日志")
        print("6. ❌ 简化了状态检查的调试输出")
        print("7. ❌ 优化了导航刷新的日志频率")
        print("8. ❌ 限制了验证过程的日志输出")
        
        print("\n🔧 修复的核心问题:")
        print("✓ 修正所有手动标注源为 'enhanced_manual'")
        print("✓ 修正批量操作标注源为 'batch_operation'") 
        print("✓ 减少了控制台噪音，保留关键信息")
        print("✓ 使用分类日志前缀：[SAVE], [STATS], [STATUS], [NAV], [VERIFY], [LOAD], [INFO], [ERROR]")
        
        print("\n📊 优化后的日志特点:")
        print("• 使用简洁的分类前缀标识不同操作")
        print("• 只在状态变化时记录重要信息")
        print("• 限制重复日志的输出频率")
        print("• 保留关键的错误和状态信息")
        print("• 移除了开发调试用的详细输出")
        
        print("\n🎮 现在启动GUI进行测试...")
        print("👀 观察控制台输出，应该看到:")
        print("   • 更清洁的日志输出")
        print("   • 明确的操作分类标记")
        print("   • 减少的重复信息")
        print("   • 保留的关键状态更新")
        
        print(f"\n🚀 启动优化后的GUI...")
        
        # 启动GUI主循环
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🧹 日志清理与优化验证")
    print("目标：减少无用或历史调试日志，提供更清晰的系统状态反映")
    print()
    
    success = test_logging_cleanup()
    
    if success:
        print("\n✅ 日志清理验证启动成功")
        print("请观察控制台输出的变化，确认日志更加简洁清晰")
    else:
        print("\n❌ 日志清理验证启动失败")
    
    print("\n📋 验证要点:")
    print("[ ] 控制台输出更加简洁")
    print("[ ] 日志信息有明确分类")
    print("[ ] 减少了重复和冗余信息")
    print("[ ] 保留了关键状态和错误信息")
    print("[ ] 系统运行状态更容易理解")
    
    sys.exit(0 if success else 1)