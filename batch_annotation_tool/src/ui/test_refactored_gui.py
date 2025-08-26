#!/usr/bin/env python3
"""
测试重构后的全景标注GUI
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    import tkinter as tk
    from batch_annotation_tool.src.ui.panoramic_annotation_gui_refactored import PanoramicAnnotationGUI
    
    def main():
        """主函数"""
        print("启动重构后的全景标注工具...")
        
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("GUI初始化成功，启动主循环...")
        root.mainloop()
        
        print("程序正常退出")

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的模块都已正确创建")
    sys.exit(1)
except Exception as e:
    print(f"启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)