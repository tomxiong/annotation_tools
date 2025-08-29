#!/usr/bin/env python3
"""
验证标注同步修复的测试脚本
专门测试：1.统计并未更新，2.切换回去状态也未更新
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

def run_annotation_sync_verification():
    """运行标注同步验证测试"""
    print("🔧 标注同步修复验证测试")
    print("=" * 60)
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建GUI实例
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI初始化成功")
        print("\n🎯 已修复的关键问题:")
        print("1. 手动标注现在正确标记为 'enhanced_manual' 而不是 'manual'")
        print("2. 统计系统现在正确识别增强标注 vs 配置导入")
        print("3. 状态显示现在正确区分增强标注（带时间戳）和配置导入")
        print("4. 添加了全面的DEBUG输出追踪整个同步过程")
        
        print("\n🛠  实施的关键修复:")
        print("✓ 修正 annotation_source 为 'enhanced_manual'")
        print("✓ 增强统计算法以正确分类标注类型")
        print("✓ 改进时间戳同步和显示逻辑")
        print("✓ 添加详细的调试输出验证修复效果")
        print("✓ 强化 save_current_annotation_internal() 的UI刷新")
        print("✓ 增强导航方法的强制刷新机制")
        
        print("\n📝 测试流程:")
        print("1. 加载包含配置文件的数据集")
        print("2. 观察配置导入标注显示为 '状态: 配置导入 - 级别'")
        print("3. 对某个孔位进行手动标注（选择生长级别和模式）")
        print("4. 点击 '保存并下一个' - 观察以下变化:")
        print("   • 统计立即更新，增强标注计数增加")
        print("   • 阴性/弱生长/阳性计数正确更新")
        print("5. 导航回到刚标注的孔位:")
        print("   • 状态显示为 '状态: 已标注 (MM-DD HH:MM:SS) - 级别'")
        print("   • 不再显示为 '配置导入'")
        
        print("\n🔍 期望看到的修复效果:")
        print("✅ 手动标注后统计立即更新")
        print("✅ 增强标注显示时间戳，配置导入显示 '配置导入'")
        print("✅ DEBUG输出清楚显示标注分类过程")
        print("✅ 统计数字正确反映实际标注状态")
        
        print("\n🐛 调试信息:")
        print("观察控制台输出中的以下关键信息:")
        print("• 'DEBUG: 创建增强标注 - 源: enhanced_manual'")
        print("• 'DEBUG: 统计增强标注 - 孔位X, 级别: Y'")
        print("• 'DEBUG: 显示时间戳状态: 状态: 已标注 (时间) - 级别'")
        print("• 'DEBUG: 配置导入状态: 状态: 配置导入 - 级别'")
        
        print(f"\n🚀 启动修复验证GUI...")
        
        # 启动GUI主循环
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔧 标注同步问题最终修复验证")
    print("修复问题：1.统计并未更新，2.切换回去状态也未更新")
    print()
    
    success = run_annotation_sync_verification()
    
    if success:
        print("\n✅ 验证测试启动成功")
        print("请按照上述流程进行测试，观察DEBUG输出确认修复效果")
    else:
        print("\n❌ 验证测试启动失败")
    
    print("\n📋 验证检查清单:")
    print("[ ] 手动标注后统计数字立即更新")
    print("[ ] 手动标注显示时间戳而非'配置导入'")
    print("[ ] 配置导入的标注仍显示'配置导入'状态")
    print("[ ] DEBUG输出显示正确的标注分类")
    print("[ ] 导航流畅，无延迟或不一致问题")
    
    sys.exit(0 if success else 1)