#!/usr/bin/env python3
"""
全景标注工具启动器
启动原始版本GUI
"""

import sys
import os
import traceback

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def start_original_version():
    """启动原始版本"""
    try:
        print("启动全景标注工具...")
        
        # 导入原始版本
        from ui.panoramic_annotation_gui import main
        
        # 直接调用main函数启动
        main()
        
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        print("\n错误详情:")
        traceback.print_exc()
        return False

def main():
    """主启动函数"""
    print("全景标注工具")
    print("=" * 40)
    
    start_original_version()

if __name__ == "__main__":
    main()