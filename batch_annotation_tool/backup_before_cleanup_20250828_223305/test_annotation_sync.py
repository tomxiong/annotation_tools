#!/usr/bin/env python3
"""
测试标注同步功能的修复
验证切片切换时标注结果是否正确显示
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import tkinter as tk
from ui.panoramic_annotation_gui import PanoramicAnnotationGUI


def test_annotation_sync():
    """测试标注同步功能"""
    print("启动标注同步测试...")
    
    try:
        # 创建GUI实例
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("GUI初始化成功")
        print("请手动测试以下功能：")
        print("1. 加载数据集")
        print("2. 在多个切片之间进行标注")
        print("3. 切换到其他切片，然后返回已标注的切片")
        print("4. 验证标注结果是否正确显示")
        print("5. 验证标注日期时间是否显示")
        print("6. 验证标注统计是否更新")
        print("7. 验证全景图预览是否显示已标注孔位")
        print("\n关键修复点：")
        print("- load_current_slice() 现在调用 update_statistics() 和 update_slice_info_display()")
        print("- 新增 update_slice_info_display() 方法确保注释状态实时更新")
        print("- 所有导航方法现在都会刷新显示")
        print("- 批量操作和导入操作后会刷新显示")
        print("- 清除标注后会刷新显示")
        
        # 启动GUI
        root.mainloop()
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_annotation_sync()