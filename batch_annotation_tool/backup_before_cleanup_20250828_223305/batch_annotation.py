#!/usr/bin/env python3
"""
批量标注工具启动脚本
解决相对导入问题的入口点
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

# 导入并运行CLI主函数
from cli.main import main

if __name__ == '__main__':
    main()