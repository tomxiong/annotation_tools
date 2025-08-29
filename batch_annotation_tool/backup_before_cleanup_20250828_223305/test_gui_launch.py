#!/usr/bin/env python3
"""
测试GUI启动
"""
import sys
import os
import tkinter as tk

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_gui():
    """测试GUI启动"""
    try:
        print("正在创建Tkinter根窗口...")
        root = tk.Tk()
        
        print("正在导入PanoramicAnnotationGUI...")
        from ui.panoramic_annotation_gui_mixin import PanoramicAnnotationGUI
        
        print("正在初始化GUI...")
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI初始化成功！")
        print("界面已启动，请检查窗口是否正常显示...")
        
        # 启动主循环
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试重构版本GUI启动...")
    success = test_gui()
    
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败")
        input("按Enter键退出...")