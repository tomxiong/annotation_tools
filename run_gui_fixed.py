#!/usr/bin/env python3
"""
修复后的GUI启动脚本
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def clear_module_cache():
    """清除相关模块的缓存"""
    modules_to_clear = [
        'models.enhanced_annotation',
        'ui.enhanced_annotation_panel',
        'ui.panoramic_annotation_gui',
        'models.panoramic_annotation',
        'models.simple_panoramic_annotation'
    ]
    
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

def main():
    """主函数"""
    print("启动全景图像标注工具（修复版）...")
    
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.absolute()
        
        # 添加src目录到Python路径
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 清除模块缓存
        clear_module_cache()
        
        # 预导入并验证InterferenceType
        print("验证干扰因素定义...")
        from models.enhanced_annotation import InterferenceType
        
        # 验证ARTIFACTS是否存在
        if not hasattr(InterferenceType, 'ARTIFACTS'):
            raise AttributeError(f"InterferenceType缺少ARTIFACTS属性。可用属性: {[attr for attr in dir(InterferenceType) if not attr.startswith('_')]}")
        
        print(f"✓ InterferenceType定义正确: {[attr for attr in dir(InterferenceType) if not attr.startswith('_')]}")
        
        # 验证UI面板的InterferenceType
        from ui.enhanced_annotation_panel import InterferenceType as PanelInterferenceType
        
        if not hasattr(PanelInterferenceType, 'ARTIFACTS'):
            raise AttributeError(f"Panel InterferenceType缺少ARTIFACTS属性")
        
        print("✓ UI面板InterferenceType定义正确")
        
        # 直接导入GUI模块
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建主窗口
        root = tk.Tk()
        
        # 设置窗口属性
        root.title("全景图像标注工具 - 微生物药敏检测")
        root.geometry("1400x900")
        
        # 创建应用实例
        app = PanoramicAnnotationGUI(root)
        
        print("界面已启动，请在窗口中操作")
        print("✓ 支持的干扰因素: 气孔, 气孔重叠, 杂质, 污染")
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        print(error_msg)
        print(f"错误详情: {type(e).__name__}: {e}")
        
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