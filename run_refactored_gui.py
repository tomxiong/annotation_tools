"""
重构后GUI应用启动脚本

用于启动重构后的全景标注工具GUI界面
使用模块化架构的新版本
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
    # 首先初始化日志配置
    from src.config.logging_config import init_default_logging
    
    # 导入重构后的GUI模块
    from ui.annotation_tools_gui import create_main_app

except ImportError as e:
    print(f"导入重构模块失败: {e}")
    print("请确保重构后的模块文件存在")
    sys.exit(1)


def main():
    """主函数"""
    try:
        # 初始化生产环境日志配置（最小化控制台输出）
        init_default_logging()
        print("正在启动全景标注工具GUI（重构版）...")
        print("使用模块化架构启动方式")

        # 创建并启动重构后的GUI应用
        root, app = create_main_app()
        
        print("GUI应用已启动，窗口显示中...")
        
        # 启动主循环
        root.mainloop()
        
        print("GUI应用正常退出")

    except KeyboardInterrupt:
        print("用户中断应用启动")
    except Exception as e:
        print(f"重构版GUI启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
