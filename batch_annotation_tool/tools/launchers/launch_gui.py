#!/usr/bin/env python3
"""
全景图像标注工具启动脚本
专门用于微生物药敏检测的图像标注
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
src_dir = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        ('tkinter', 'tkinter'),
        ('PIL', 'Pillow'),
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy')
    ]
    
    missing_packages = []
    
    for package_name, install_name in required_packages:
        try:
            if package_name == 'tkinter':
                import tkinter
            elif package_name == 'PIL':
                from PIL import Image, ImageTk
            elif package_name == 'cv2':
                import cv2
            elif package_name == 'numpy':
                import numpy
        except ImportError:
            missing_packages.append(install_name)
    
    if missing_packages:
        error_msg = f"缺少以下依赖包: {', '.join(missing_packages)}\n\n"
        error_msg += "请运行以下命令安装:\n"
        error_msg += f"pip install {' '.join(missing_packages)}"
        
        print(error_msg)
        
        # 尝试显示图形错误对话框
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("依赖包缺失", error_msg)
            root.destroy()
        except:
            pass
        
        return False
    
    return True


def main():
    """主函数"""
    print("启动全景图像标注工具...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # 导入GUI模块
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
        
    except ImportError as e:
        error_msg = f"模块导入失败: {str(e)}\n请检查项目结构是否完整"
        print(error_msg)
        
        try:
            messagebox.showerror("导入错误", error_msg)
        except:
            pass
        
        sys.exit(1)
        
    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        print(error_msg)
        
        try:
            messagebox.showerror("启动错误", error_msg)
        except:
            pass
        
        sys.exit(1)


if __name__ == '__main__':
    main()