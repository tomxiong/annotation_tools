#!/usr/bin/env python3
"""
全景图像标注工具启动脚本
直接启动，避免复杂的导入问题
"""

import sys
import os
from pathlib import Path

# 获取项目根目录并添加到Python路径
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'

# 确保src目录在Python路径中
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 直接启动GUI
if __name__ == '__main__':
    print("启动全景图像标注工具...")
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建主窗口
        root = tk.Tk()
        root.title("全景图像标注工具 - 微生物药敏检测")
        root.geometry("1400x900")
        
        # 创建应用实例
        app = PanoramicAnnotationGUI(root)
        
        print("界面已启动，请在窗口中操作")
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        print(f"启动失败: {str(e)}")
        print(f"错误详情: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)