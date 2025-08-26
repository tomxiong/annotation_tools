#!/usr/bin/env python3
"""
全景图像标注工具启动脚本
使用绝对导入避免相对导入问题
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def main():
    """主函数"""
    print("启动全景图像标注工具...")
    
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.absolute()
        
        # 添加项目根目录到Python路径
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # 添加src目录到Python路径
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 导入必要的模块
        from src.ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建主窗口
        root = tk.Tk()
        
        # 设置窗口属性
        root.title("全景图像标注工具 - 微生物药敏检测")
        root.geometry("1400x900")
        
        # 创建应用实例
        app = PanoramicAnnotationGUI(root)
        
        print("界面已启动，请在窗口中操作")
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        print(error_msg)
        print(f"错误详情: {type(e).__name__}: {e}")
        
        try:
            messagebox.showerror("启动错误", error_msg)
        except:
            pass
        
        sys.exit(1)

if __name__ == '__main__':
    main()