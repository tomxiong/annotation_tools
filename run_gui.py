#!/usr/bin/env python3
"""
全景图像标注工具GUI启动脚本
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# 日志导入
try:
    from src.utils.logger import log_info, log_error
except ImportError:
    # 如果日志模块不可用，使用print作为后备
    def log_info(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_error(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)

def main():
    """主函数"""
    log_info("启动全景图像标注工具...", "STARTUP")
    
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.absolute()
        
        # 添加src目录到Python路径
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 直接导入GUI模块
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建主窗口
        root = tk.Tk()
        
        # 设置窗口属性
        root.title("全景图像标注工具 - 微生物药敏检测")
        root.geometry("1400x900")
        
        # 创建应用实例
        app = PanoramicAnnotationGUI(root)
        
        log_info("界面已启动，请在窗口中操作", "STARTUP")
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        log_error(error_msg, "STARTUP")
        log_error(f"错误详情: {type(e).__name__}: {e}", "STARTUP")
        
        # 打印更详细的调试信息
        import traceback
        traceback.print_exc()
        
        try:
            messagebox.showerror("启动错误", error_msg)
        except:
            pass
        
        sys.exit(1)

if __name__ == '__main__':
    main()
