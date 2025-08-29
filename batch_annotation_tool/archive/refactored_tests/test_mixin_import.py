#!/usr/bin/env python3
"""
测试Mixin导入
"""
import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

print("Python路径:", sys.path[:3])
print("当前目录:", current_dir)
print("src目录:", src_dir)
print("src目录存在:", os.path.exists(src_dir))

try:
    print("\n1. 测试导入Mixin类...")
    from ui.mixins.navigation_mixin import NavigationMixin
    print("✓ NavigationMixin导入成功")
    
    from ui.mixins.annotation_mixin import AnnotationMixin
    print("✓ AnnotationMixin导入成功")
    
    from ui.mixins.image_mixin import ImageMixin
    print("✓ ImageMixin导入成功")
    
    from ui.mixins.event_mixin import EventMixin
    print("✓ EventMixin导入成功")
    
    from ui.mixins.ui_mixin import UIMixin
    print("✓ UIMixin导入成功")
    
    print("\n2. 测试导入依赖类...")
    from ui.hole_manager import HoleManager
    print("✓ HoleManager导入成功")
    
    from ui.enhanced_annotation_panel import EnhancedAnnotationPanel
    print("✓ EnhancedAnnotationPanel导入成功")
    
    from services.config_file_service import ConfigFileService
    print("✓ ConfigFileService导入成功")
    
    print("\n3. 测试导入主GUI类...")
    from ui.panoramic_annotation_gui_mixin import PanoramicAnnotationGUI
    print("✓ PanoramicAnnotationGUI导入成功")
    
    print("\n✅ 所有导入测试通过！")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()