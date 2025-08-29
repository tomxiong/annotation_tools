#!/usr/bin/env python3
"""
启动重构后的全景标注GUI
这是推荐的启动方式，使用模块化的重构版本
"""

import sys
import os
import tkinter as tk

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def main():
    """主函数"""
    print("=" * 60)
    print("启动重构后的全景标注工具")
    print("=" * 60)
    
    try:
        # 导入重构后的GUI
        from batch_annotation_tool.src.ui.panoramic_annotation_gui_refactored import PanoramicAnnotationGUI
        
        print("✓ 成功导入重构版GUI模块")
        
        # 创建主窗口
        root = tk.Tk()
        print("✓ 创建主窗口")
        
        # 初始化GUI
        app = PanoramicAnnotationGUI(root)
        print("✓ GUI初始化成功")
        
        # 验证全景图导航功能
        navigation_methods = [
            'go_prev_panoramic',
            'go_next_panoramic', 
            'go_to_panoramic',
            'update_panoramic_list'
        ]
        
        print("\n检查全景图导航功能:")
        for method in navigation_methods:
            if hasattr(app, method):
                print(f"✓ {method}")
            else:
                print(f"✗ {method} - 缺失")
        
        # 检查UI组件
        ui_components = [
            'panoramic_combobox',
            'navigation_controller',
            'annotation_manager',
            'image_display_controller'
        ]
        
        print("\n检查UI组件:")
        for component in ui_components:
            if hasattr(app, component):
                print(f"✓ {component}")
            else:
                print(f"✗ {component} - 缺失")
        
        print("\n" + "=" * 60)
        print("启动主循环...")
        print("=" * 60)
        
        # 启动主循环
        root.mainloop()
        
        print("程序正常退出")
        
    except ImportError as e:
        print(f"✗ 导入错误: {e}")
        print("\n请确保以下文件存在:")
        print("- panoramic_annotation_gui_refactored.py")
        print("- navigation_controller.py")
        print("- annotation_manager.py")
        print("- image_display_controller.py")
        print("- event_handlers.py")
        print("- ui_components.py")
        sys.exit(1)
        
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()