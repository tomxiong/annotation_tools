#!/usr/bin/env python3
"""
批量标注工具CLI主入口
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.logger import Logger
from core.exceptions import ValidationError, FileProcessingError
from models.dataset import Dataset
from models.batch_job import BatchJob, JobStatus
from services.image_processor import ImageProcessor
from services.annotation_engine import AnnotationEngine, ModelType


class BatchAnnotationCLI:
    """批量标注工具命令行接口"""
    
    def __init__(self):
        self.config: Optional[Config] = None
        self.logger: Optional[Logger] = None
        
    def setup_logging(self, config_path: str = "config/config.yaml"):
        """设置日志系统"""
        try:
            self.config = Config(config_path)
            self.logger = Logger(self.config)
        except Exception as e:
            print(f"错误：无法初始化配置和日志系统: {e}")
            sys.exit(1)
    
    def cmd_init(self, args):
        """初始化项目配置"""
        project_dir = Path(args.project_dir)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建配置目录
        config_dir = project_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # 创建默认配置文件
        config_file = config_dir / "config.yaml"
        if config_file.exists() and not args.force:
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
        
    def cmd_process(self, args):
        """处理图像批量标注"""
        self.setup_logging(args.config)
        
        try:
            # 验证输入目录
            input_dir = Path(args.input_dir)
            if not input_dir.exists():
                raise ValidationError(f"输入目录不存在: {input_dir}")
            
            # 创建输出目录
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 初始化服务
            image_processor = ImageProcessor(self.config)
            annotation_engine = AnnotationEngine(self.config)
            
            # 加载模型
            model_name = args.model or self.config.get('models.default_model', 'yolo_v8')
            model_path = args.model_path or self.config.get('models.model_path', 'models/')
            
            print(f"🤖 加载模型: {model_name}")
            try:
                annotation_engine.load_model(model_name, ModelType.YOLO, model_path)
            except Exception as e:
                print(f"⚠️  模型加载失败: {e}")
                print("继续处理图像（仅图像处理，无AI标注）")
            
            # 扫描图像文件
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                image_files.extend(input_dir.glob(f"**/*{ext}"))
                image_files.extend(input_dir.glob(f"**/*{ext.upper()}"))
            
            if not image_files:
                print("❌ 未找到支持的图像文件")
                return
            
            print(f"📸 找到 {len(image_files)} 个图像文件")
            
            # 创建数据集
            dataset = Dataset(
                name=args.dataset_name or f"batch_{len(image_files)}",
                description=f"批量处理 {len(image_files)} 个图像"
            )
            
            # 创建批处理任务
            batch_job = BatchJob(
                job_id=f"job_{dataset.name}",
                dataset_name=dataset.name,
                model_name=model_name,
                total_images=len(image_files)
            )
            
            batch_job.start()
            
            # 处理图像
            processed_count = 0
            for i, image_file in enumerate(image_files):
                try:
                    print(f"处理 ({i+1}/{len(image_files)}): {image_file.name}")
                    
                    # 加载图像
                    image = image_processor.load_image(str(image_file))
                    
                    # AI标注（如果模型已加载）
                    annotations = []
                    if annotation_engine.current_model:
                        try:
                            annotations = annotation_engine.predict_single_image(
                                str(image_file), model_name
                            )
                        except Exception as e:
                            self.logger.warning(f"标注失败 {image_file}: {e}")
                    
                    # 添加到数据集
                    for ann in annotations:
                        dataset.add_annotation(ann)
                    
                    processed_count += 1
                    batch_job.update_progress(processed_count / len(image_files) * 100)
                    
                except Exception as e:
                    self.logger.error(f"处理图像失败 {image_file}: {e}")
                    batch_job.add_result(str(image_file), False, str(e))
            
            batch_job.complete()
            
            # 保存结果
            output_format = args.format or self.config.get('output.format', 'json')
            output_file = output_dir / f"{dataset.name}.{output_format}"
            
            if output_format == 'json':
                dataset.save_to_json(str(output_file))
            elif output_format == 'coco':
                dataset.export_to_coco(str(output_file))
            else:
                print(f"⚠️  不支持的输出格式: {output_format}")
                dataset.save_to_json(str(output_dir / f"{dataset.name}.json"))
            
            print(f"✅ 处理完成!")
            print(f"📊 统计信息:")
            stats = dataset.get_statistics()
            print(f"   - 总图像数: {stats['total_images']}")
            print(f"   - 总标注数: {stats['total_annotations']}")
            print(f"   - 标签类别: {len(stats['labels'])}")
            print(f"📁 输出文件: {output_file}")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            if self.logger:
                self.logger.error(f"批处理失败: {e}")
            sys.exit(1)
    
    def cmd_export(self, args):
        """导出标注结果"""
        try:
            input_file = Path(args.input_file)
            if not input_file.exists():
                raise ValidationError(f"输入文件不存在: {input_file}")
            
            # 加载数据集
            dataset = Dataset.load_from_json(str(input_file))
            
            output_file = Path(args.output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 根据格式导出
            if args.format == 'coco':
                dataset.export_to_coco(str(output_file))
            elif args.format == 'json':
                dataset.save_to_json(str(output_file))
            elif args.format == 'csv':
                # 简单CSV导出
                import csv
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['image_id', 'label', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h', 'confidence'])
                    for ann in dataset.annotations:
                        writer.writerow([
                            ann.image_id, ann.label,
                            ann.bbox[0], ann.bbox[1], ann.bbox[2], ann.bbox[3],
                            ann.confidence or 0.0
                        ])
            else:
                raise ValidationError(f"不支持的导出格式: {args.format}")
            
            print(f"✅ 导出完成: {output_file}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            sys.exit(1)
    
    def cmd_status(self, args):
        """查看项目状态"""
        try:
            project_dir = Path(args.project_dir)
            
            print(f"📁 项目目录: {project_dir}")
            print(f"📝 配置文件: {project_dir / 'config/config.yaml'}")
            
            # 检查目录结构
            dirs_to_check = ['data', 'models', 'output', 'logs']
            for dir_name in dirs_to_check:
                dir_path = project_dir / dir_name
                status = "✅" if dir_path.exists() else "❌"
                print(f"{status} {dir_name}/ 目录")
            
            # 统计文件数量
            data_dir = project_dir / 'data'
            if data_dir.exists():
                image_count = len(list(data_dir.glob("**/*.jpg"))) + \
                             len(list(data_dir.glob("**/*.png"))) + \
                             len(list(data_dir.glob("**/*.jpeg")))
                print(f"📸 数据目录图像数: {image_count}")
            
            output_dir = project_dir / 'output'
            if output_dir.exists():
                result_files = list(output_dir.glob("*.json")) + list(output_dir.glob("*.coco"))
                print(f"📤 输出文件数: {len(result_files)}")
            
        except Exception as e:
            print(f"❌ 状态检查失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量标注工具 - 基于AI的图像批量标注解决方案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 初始化新项目
  python -m cli.main init my_project
  
  # 批量处理图像
  python -m cli.main process data/images/ output/ --model yolo_v8
  
  # 导出为COCO格式
  python -m cli.main export output/dataset.json output/dataset.coco --format coco
  
  # 查看项目状态
  python -m cli.main status my_project
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init命令
    init_parser = subparsers.add_parser('init', help='初始化项目')
    init_parser.add_argument('project_dir', help='项目目录路径')
    init_parser.add_argument('--force', action='store_true', help='强制覆盖现有配置')
    
    # process命令
    process_parser = subparsers.add_parser('process', help='批量处理图像')
    process_parser.add_argument('input_dir', help='输入图像目录')
    process_parser.add_argument('output_dir', help='输出结果目录')
    process_parser.add_argument('--config', default='config/config.yaml', help='配置文件路径')
    process_parser.add_argument('--model', help='使用的模型名称')
    process_parser.add_argument('--model-path', help='模型文件路径')
    process_parser.add_argument('--format', choices=['json', 'coco', 'csv'], help='输出格式')
    process_parser.add_argument('--dataset-name', help='数据集名称')
    
    # export命令
    export_parser = subparsers.add_parser('export', help='导出标注结果')
    export_parser.add_argument('input_file', help='输入JSON文件')
    export_parser.add_argument('output_file', help='输出文件')
    export_parser.add_argument('--format', choices=['json', 'coco', 'csv'], 
                              default='coco', help='导出格式')
    
    # status命令
    status_parser = subparsers.add_parser('status', help='查看项目状态')
    status_parser.add_argument('project_dir', help='项目目录路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = BatchAnnotationCLI()
    
    # 执行对应命令
    if args.command == 'init':
        cli.cmd_init(args)
    elif args.command == 'process':
        cli.cmd_process(args)
    elif args.command == 'export':
        cli.cmd_export(args)
    elif args.command == 'status':
        cli.cmd_status(args)


if __name__ == '__main__':
    main()