#!/usr/bin/env python3
"""
启动重构版本的全景图标注工具
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def main():
    """主函数"""
    try:
        # 创建根窗口
        root = tk.Tk()
        
        # 导入并启动重构版本的GUI
        from ui.panoramic_annotation_gui_mixin import PanoramicAnnotationGUI
        
        print("正在启动重构版本的全景图标注工具...")
        app = PanoramicAnnotationGUI(root)
        
        print("重构版本启动成功！")
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"导入模块失败: {e}"
        print(f"错误: {error_msg}")
        if 'root' in locals():
            messagebox.showerror("导入错误", error_msg)
        return False
        
    except Exception as e:
        error_msg = f"启动重构版本失败: {e}"
        print(f"错误: {error_msg}")
        if 'root' in locals():
            messagebox.showerror("启动错误", error_msg)
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("重构版本启动失败，请检查错误信息")
        input("按Enter键退出...")