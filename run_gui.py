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

        # 启动主循环
        root.mainloop()

    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        print(f"启动错误: {error_msg}")

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
