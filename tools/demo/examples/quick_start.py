#!/usr/bin/env python3
"""
批量标注工具快速开始示例
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.core.config import Config
from src.core.logger import Logger
from src.models.dataset import Dataset
from src.models.annotation import Annotation
from src.services.image_processor import ImageProcessor


def create_sample_dataset():
    """创建示例数据集"""
    print("🚀 创建示例数据集...")
    
    # 创建数据集
    dataset = Dataset(
        name="sample_dataset",
        description="批量标注工具示例数据集"
    )
    
    # 添加示例标注
    sample_annotations = [
        Annotation(
            image_id="image1.jpg",
            label="person",
            bbox=[100, 200, 50, 100],
            confidence=0.95
        ),
        Annotation(
            image_id="image1.jpg", 
            label="car",
            bbox=[300, 150, 80, 60],
            confidence=0.88
        ),
        Annotation(
            image_id="image2.jpg",
            label="dog",
            bbox=[50, 80, 40, 45],
            confidence=0.92
        )
    ]
    
    for ann in sample_annotations:
        dataset.add_annotation(ann)
    
    # 显示统计信息
    stats = dataset.get_statistics()
    print(f"📊 数据集统计:")
    print(f"   - 总图像数: {stats['total_images']}")
    print(f"   - 总标注数: {stats['total_annotations']}")
    print(f"   - 标签类别: {stats['labels']}")
    
    return dataset


def demonstrate_image_processing():
    """演示图像处理功能"""
    print("\n🖼️  演示图像处理功能...")
    
    try:
        # 使用默认配置
        config = Config()
        processor = ImageProcessor(config)
        
        print(f"✅ 图像处理器初始化成功")
        print(f"📋 支持的格式: {processor.supported_formats}")
        
        # 演示格式检查
        test_files = ["test.jpg", "test.png", "test.gif", "test.txt"]
        for file in test_files:
            is_supported = processor.is_supported_format(file)
            status = "✅" if is_supported else "❌"
            print(f"   {status} {file}")
            
    except Exception as e:
        print(f"⚠️  图像处理器演示失败: {e}")


def demonstrate_export_formats(dataset):
    """演示导出功能"""
    print("\n📤 演示导出功能...")
    
    # 创建输出目录
    output_dir = Path("demo_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 导出为JSON
        json_file = output_dir / "sample_dataset.json"
        dataset.save_to_json(str(json_file))
        print(f"✅ JSON导出: {json_file}")
        
        # 导出为COCO格式
        coco_file = output_dir / "sample_dataset.coco"
        dataset.export_to_coco(str(coco_file))
        print(f"✅ COCO导出: {coco_file}")
        
        # 简单CSV导出
        csv_file = output_dir / "sample_dataset.csv"
        import csv
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'label', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h', 'confidence'])
            for ann in dataset.annotations:
                writer.writerow([
                    ann.image_id, ann.label,
                    ann.bbox[0], ann.bbox[1], ann.bbox[2], ann.bbox[3],
                    ann.confidence or 0.0
                ])
        print(f"✅ CSV导出: {csv_file}")
        
    except Exception as e:
        print(f"⚠️  导出演示失败: {e}")


def main():
    """主函数"""
    print("🎯 批量标注工具MVP - 快速开始示例")
    print("=" * 50)
    
    try:
        # 1. 创建示例数据集
        dataset = create_sample_dataset()
        
        # 2. 演示图像处理
        demonstrate_image_processing()
        
        # 3. 演示导出功能
        demonstrate_export_formats(dataset)
        
        print("\n🎉 示例演示完成!")
        print("\n📋 下一步:")
        print("1. 使用 'python -m cli.main init my_project' 创建项目")
        print("2. 将图像文件放入 data/ 目录")
        print("3. 运行 'python -m cli.main process data/ output/' 开始处理")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()