"""
GUI应用启动脚本

用于启动全景标注工具的GUI界面
使用直接模块启动方式
"""

import sys
import os
from pathlib import Path

# 添加项目根目录和src目录到Python路径
project_root = Path(__file__).parent
src_dir = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

try:
    # 导入直接的GUI模块
    from src.ui.panoramic_annotation_gui import main as gui_main

except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保已安装所有依赖包：pip install -r requirements.txt")
    sys.exit(1)


def main():
    """主函数"""
    try:
        print("正在启动全景标注工具GUI...")
        print("使用直接模块启动方式")

        # 直接调用GUI模块的主函数
        gui_main()

    except KeyboardInterrupt:
        print("用户中断应用启动")
    except Exception as e:
        print(f"应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()