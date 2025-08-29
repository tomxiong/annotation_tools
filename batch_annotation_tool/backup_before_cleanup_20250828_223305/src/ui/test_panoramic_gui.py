#!/usr/bin/env python3
"""
测试修改后的全景标注GUI
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
try:
    import tkinter as tk
    
    def test_original_gui():
        """测试原始GUI（带全景图导航集成）"""
        print("\n=== 测试原始GUI ===")
        try:
            from batch_annotation_tool.src.ui.panoramic_annotation_gui import PanoramicAnnotationGUI
            
            root = tk.Tk()
            app = PanoramicAnnotationGUI(root)
            
            print("✓ 原始GUI初始化成功")
            print("全景图导航功能检查:")
            methods = ['go_prev_panoramic', 'go_next_panoramic', 'go_to_panoramic', 'update_panoramic_list']
            for method in methods:
                status = "✓" if hasattr(app, method) else "✗"
                print(f"  {status} {method}")
            
            root.destroy()
            return True
        except Exception as e:
            print(f"✗ 原始GUI测试失败: {e}")
            return False
    
    def test_refactored_gui():
        """测试重构后的GUI"""
        print("\n=== 测试重构后的GUI ===")
        try:
            from batch_annotation_tool.src.ui.panoramic_annotation_gui_refactored import PanoramicAnnotationGUI
            
            root = tk.Tk()
            app = PanoramicAnnotationGUI(root)
            
            print("✓ 重构GUI初始化成功")
            print("模块检查:")
            modules = ['navigation_controller', 'annotation_manager', 'image_display_controller', 'event_handlers', 'ui_components']
            for module in modules:
                status = "✓" if hasattr(app, module) else "✗"
                print(f"  {status} {module}")
            
            print("全景图导航功能检查:")
            methods = ['go_prev_panoramic', 'go_next_panoramic', 'go_to_panoramic']
            for method in methods:
                status = "✓" if hasattr(app, method) else "✗"
                print(f"  {status} {method}")
            
            root.destroy()
            return True
        except Exception as e:
            print(f"✗ 重构GUI测试失败: {e}")
            return False
    
    def main():
        """主函数"""
        print("全景标注GUI测试工具")
        print("=" * 50)
        
        # 测试两个版本
        original_ok = test_original_gui()
        refactored_ok = test_refactored_gui()
        
        print("\n" + "=" * 50)
        print("测试结果:")
        print(f"原始GUI: {'✓ 通过' if original_ok else '✗ 失败'}")
        print(f"重构GUI: {'✓ 通过' if refactored_ok else '✗ 失败'}")
        
        # 启动推荐版本
        if refactored_ok:
            print("\n启动重构版本GUI...")
            from batch_annotation_tool.src.ui.panoramic_annotation_gui_refactored import PanoramicAnnotationGUI
            root = tk.Tk()
            app = PanoramicAnnotationGUI(root)
            root.mainloop()
        elif original_ok:
            print("\n启动原始版本GUI...")
            from batch_annotation_tool.src.ui.panoramic_annotation_gui import PanoramicAnnotationGUI
            root = tk.Tk()
            app = PanoramicAnnotationGUI(root)
            root.mainloop()
        else:
            print("\n✗ 两个版本都无法正常工作")

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