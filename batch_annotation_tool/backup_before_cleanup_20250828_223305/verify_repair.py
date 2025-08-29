
import sys
import os
from pathlib import Path

current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import tkinter as tk
from ui.panoramic_annotation_gui import PanoramicAnnotationGUI

def run_verification():
    print("🔍 验证修复结果...")
    root = tk.Tk()
    app = PanoramicAnnotationGUI(root)
    
    print("✅ GUI启动成功，请测试以下功能：")
    print("1. 加载数据集")
    print("2. 进行标注并保存")
    print("3. 观察统计是否立即更新")
    print("4. 切换到其他切片再切换回来")
    print("5. 观察状态是否正确更新")
    print("\n如果看到DEBUG输出，说明修复生效")
    
    root.mainloop()

if __name__ == '__main__':
    run_verification()
