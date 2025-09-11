#!/usr/bin/env python3
"""
全景图像标注工具 - 模块化版本启动脚本
按照正确的模块化设计重新组织的启动器
"""

import sys
import os
from pathlib import Path

# 添加src路径到Python路径
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def main():
    """主函数"""
    try:
        print("启动模块化全景图像标注工具...")
        
        # 导入并运行模块化GUI
        from ui.modular_annotation_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保所有依赖都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
