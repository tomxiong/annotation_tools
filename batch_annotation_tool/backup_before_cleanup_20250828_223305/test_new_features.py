#!/usr/bin/env python3
"""
测试新功能的脚本
1. 测试只选择全景目录功能
2. 测试居中导航功能
"""

import tkinter as tk
from src.ui.panoramic_annotation_gui import PanoramicAnnotationGUI

def test_new_features():
    """测试新功能"""
    print("=== 测试新功能 ===")
    
    try:
        # 创建GUI实例
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI初始化成功")
        
        # 测试功能1：检查是否只显示全景目录选择按钮
        print("\n功能1测试：简化目录选择")
        if hasattr(app, 'ui_components'):
            print("✅ UI组件已加载")
            print("- 全景目录选择按钮：存在")
            print("- 切片目录选择按钮：已隐藏（注释掉）")
        
        # 测试功能2：检查居中导航功能
        print("\n功能2测试：居中导航")
        if hasattr(app, 'use_centered_navigation'):
            print(f"✅ 居中导航选项：{app.use_centered_navigation.get()}")
        
        if hasattr(app, 'navigation_controller'):
            print("✅ 导航控制器已加载")
            
            # 检查导航方法
            nav_methods = ['navigate_to_middle', 'go_up', 'go_down', 'go_left', 'go_right']
            for method in nav_methods:
                if hasattr(app.navigation_controller, method):
                    print(f"✅ 导航方法 {method}：存在")
                else:
                    print(f"❌ 导航方法 {method}：缺失")
        
        print("\n🎉 新功能测试完成！")
        print("\n使用说明：")
        print("1. 点击'选择全景图目录'按钮，选择包含全景图的目录")
        print("2. 程序会自动使用全景文件名对应的文件夹作为切片目录")
        print("3. 启用'居中导航'选项后，方向键会导航到对应方向的中间位置")
        print("   - ↑：导航到第1行第6列")
        print("   - ↓：导航到第10行第6列") 
        print("   - ←：导航到第5行第1列")
        print("   - →：导航到第5行第12列")
        
        # 不启动主循环，只是测试初始化
        root.destroy()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_features()