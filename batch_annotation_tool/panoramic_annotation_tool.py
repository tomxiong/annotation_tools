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

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

try:
    # 尝试绝对导入
    from src.ui.panoramic_annotation_gui import PanoramicAnnotationGUI
    from src.core.config import Config
    from src.core.logger import Logger
except ImportError as e:
    try:
        # 如果绝对导入失败，尝试相对导入
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        from core.config import Config
        from core.logger import Logger
    except ImportError as e2:
        print(f"导入错误: {e}")
        print(f"相对导入也失败: {e2}")
        print("请确保所有依赖包已正确安装")
        sys.exit(1)
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

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

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

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

try:
    from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
    from core.config import Config
    from core.logger import Logger
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖包已正确安装")
    sys.exit(1)


def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'tkinter',
        'PIL',
        'cv2',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'PIL':
                from PIL import Image, ImageTk
            elif package == 'cv2':
                import cv2
            elif package == 'numpy':
                import numpy
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        error_msg = f"缺少以下依赖包: {', '.join(missing_packages)}\n\n"
        error_msg += "请运行以下命令安装:\n"
        if 'PIL' in missing_packages:
            error_msg += "pip install Pillow\n"
        if 'cv2' in missing_packages:
            error_msg += "pip install opencv-python\n"
        if 'numpy' in missing_packages:
            error_msg += "pip install numpy\n"
        
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
        
        try:
            messagebox.showerror("启动错误", error_msg)
        except:
            pass
        
        sys.exit(1)


if __name__ == '__main__':
    main()