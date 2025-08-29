#!/usr/bin/env python3
"""
全面测试标注同步功能的修复
测试统计和状态更新是否正常工作
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

def run_comprehensive_sync_test():
    """运行全面的同步测试"""
    print("启动全面标注同步测试...")
    print("=" * 60)
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建GUI实例
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✓ GUI初始化成功")
        print("\n测试计划:")
        print("1. 手动加载数据集")
        print("2. 进行标注 → 保存并下一个")
        print("3. 切换回上一个，验证以下内容:")
        print("   - 统计数据是否更新")
        print("   - 状态是否显示时间戳")
        print("   - 标注结果是否正确显示")
        
        print("\n关键修复点验证:")
        print("- _immediate_refresh_after_save() 方法已添加")
        print("- _force_navigation_refresh() 方法已添加")
        print("- _delayed_sync_after_load() 增强了多重刷新")
        print("- save_current_annotation_internal() 使用更强的UI刷新")
        print("- 导航方法添加了延迟强制刷新")
        
        print("\n期望的修复效果:")
        print("✓ 保存标注后统计立即更新")
        print("✓ 切换切片时统计正确反映状态")
        print("✓ 手动标注显示时间戳而非'配置导入'")
        print("✓ 界面完全同步，无延迟问题")
        
        print(f"\n测试方法:")
        print("1. 选择包含全景图的目录")
        print("2. 加载数据")
        print("3. 进行以下操作序列:")
        print("   a) 对孔位进行标注")
        print("   b) 点击'保存并下一个'")
        print("   c) 观察统计是否立即更新")
        print("   d) 点击'上一个'返回")
        print("   e) 验证状态显示和统计数据")
        
        print(f"\n启动GUI测试界面...")
        
        # 启动GUI主循环
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("标注同步修复验证 - 第三轮增强")
    print("修复内容：多重强制UI刷新 + 延迟验证刷新")
    print()
    
    success = run_comprehensive_sync_test()
    
    if success:
        print("\n✅ 测试环境启动成功")
        print("请按照上述测试计划进行手动验证")
    else:
        print("\n❌ 测试环境启动失败")
    
    sys.exit(0 if success else 1)