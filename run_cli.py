#!/usr/bin/env python3
"""
批量标注工具CLI运行器
简化版本，避免相对导入问题
"""

import sys
import os
import argparse
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

# 直接导入所需模块，避免相对导入
from core.config import Config
from core.logger import Logger
from core.exceptions import ValidationError, FileProcessingError
from models.dataset import Dataset
from models.batch_job import BatchJob, JobStatus
from models.annotation import Annotation
from services.image_processor import ImageProcessor


def cmd_init(project_dir, force=False):
    """初始化项目配置"""
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建配置目录
    config_dir = project_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # 创建默认配置文件
    config_file = config_dir / "config.yaml"
    if config_file.exists() and not force:
        print(f"配置文件已存在: {config_file}")
        print("使用 --force 参数覆盖现有配置")
        return
    
    default_config = """# 批量标注工具配置文件
logging:
  level: INFO
  file_path: logs/batch_annotation.log
  max_file_size: 10485760  # 10MB
  backup_count: 5

processing:
  batch_size: 32
  max_workers: 4
  confidence_threshold: 0.5

models:
  default_model: yolo_v8
  model_path: models/

output:
  format: coco  # json, coco, csv
  output_dir: output/
"""
    
    config_file.write_text(default_config, encoding='utf-8')
    
    # 创建其他必要目录
    for dir_name in ['data', 'models', 'output', 'logs']:
        (project_dir / dir_name).mkdir(exist_ok=True)
    
    print(f"✅ 项目初始化完成: {project_dir}")
    print(f"📝 配置文件: {config_file}")
    print(f"📁 数据目录: {project_dir / 'data'}")
    print(f"🤖 模型目录: {project_dir / 'models'}")
    print(f"📤 输出目录: {project_dir / 'output'}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量标注工具 - 基于AI的图像批量标注解决方案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 初始化新项目
  python run_cli.py init my_project
  
  # 运行快速示例
  python examples/quick_start.py
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init命令
    init_parser = subparsers.add_parser('init', help='初始化项目')
    init_parser.add_argument('project_dir', help='项目目录路径')
    init_parser.add_argument('--force', action='store_true', help='强制覆盖现有配置')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应命令
    if args.command == 'init':
        cmd_init(args.project_dir, args.force)


if __name__ == '__main__':
    main()