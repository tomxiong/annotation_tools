#!/usr/bin/env python3
"""
批量标注工具演示脚本
展示MVP核心功能，无需复杂导入
"""

import sys
import os
from pathlib import Path
import json
import yaml
from datetime import datetime

def create_sample_config():
    """创建示例配置"""
    config = {
        'logging': {
            'level': 'INFO',
            'file_path': 'logs/batch_annotation.log',
            'max_file_size': 10485760,
            'backup_count': 5
        },
        'processing': {
            'batch_size': 32,
            'max_workers': 4,
            'confidence_threshold': 0.5
        },
        'models': {
            'default_model': 'yolo_v8',
            'model_path': 'models/'
        },
        'output': {
            'format': 'coco',
            'output_dir': 'output/'
        }
    }
    return config

def create_sample_annotation():
    """创建示例标注"""
    annotation = {
        'id': 1,
        'image_id': 'sample_image.jpg',
        'label': 'person',
        'bbox': [100, 200, 50, 100],  # x, y, width, height
        'confidence': 0.95,
        'created_at': datetime.now().isoformat()
    }
    return annotation

def create_sample_dataset():
    """创建示例数据集"""
    dataset = {
        'name': 'sample_dataset',
        'description': '批量标注工具示例数据集',
        'created_at': datetime.now().isoformat(),
        'annotations': [
            create_sample_annotation(),
            {
                'id': 2,
                'image_id': 'sample_image.jpg',
                'label': 'car',
                'bbox': [300, 150, 80, 60],
                'confidence': 0.88,
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 3,
                'image_id': 'sample_image2.jpg',
                'label': 'dog',
                'bbox': [50, 80, 40, 45],
                'confidence': 0.92,
                'created_at': datetime.now().isoformat()
            }
        ],
        'statistics': {
            'total_images': 2,
            'total_annotations': 3,
            'labels': ['person', 'car', 'dog']
        }
    }
    return dataset

def export_to_coco(dataset):
    """导出为COCO格式"""
    coco_format = {
        'info': {
            'description': dataset['description'],
            'version': '1.0',
            'year': 2024,
            'contributor': 'Batch Annotation Tool',
            'date_created': dataset['created_at']
        },
        'licenses': [],
        'images': [],
        'annotations': [],
        'categories': []
    }
    
    # 添加图像信息
    image_ids = set()
    for ann in dataset['annotations']:
        if ann['image_id'] not in image_ids:
            image_ids.add(ann['image_id'])
            coco_format['images'].append({
                'id': len(coco_format['images']) + 1,
                'file_name': ann['image_id'],
                'width': 640,  # 默认尺寸
                'height': 480
            })
    
    # 添加类别信息
    categories = {}
    for i, label in enumerate(dataset['statistics']['labels']):
        categories[label] = i + 1
        coco_format['categories'].append({
            'id': i + 1,
            'name': label,
            'supercategory': 'object'
        })
    
    # 添加标注信息
    for ann in dataset['annotations']:
        image_id = next(img['id'] for img in coco_format['images'] 
                       if img['file_name'] == ann['image_id'])
        
        coco_format['annotations'].append({
            'id': ann['id'],
            'image_id': image_id,
            'category_id': categories[ann['label']],
            'bbox': ann['bbox'],
            'area': ann['bbox'][2] * ann['bbox'][3],
            'iscrowd': 0,
            'score': ann.get('confidence', 1.0)
        })
    
    return coco_format

def init_project(project_dir):
    """初始化项目"""
    project_path = Path(project_dir)
    project_path.mkdir(parents=True, exist_ok=True)
    
    # 创建目录结构
    dirs = ['config', 'data', 'models', 'output', 'logs']
    for dir_name in dirs:
        (project_path / dir_name).mkdir(exist_ok=True)
    
    # 创建配置文件
    config = create_sample_config()
    config_file = project_path / 'config' / 'config.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ 项目初始化完成: {project_path}")
    print(f"📝 配置文件: {config_file}")
    
    for dir_name in dirs:
        print(f"📁 {dir_name}/ 目录已创建")
    
    return project_path

def demonstrate_functionality():
    """演示核心功能"""
    print("🎯 批量标注工具MVP - 功能演示")
    print("=" * 50)
    
    # 1. 创建示例数据集
    print("\n🚀 创建示例数据集...")
    dataset = create_sample_dataset()
    
    print(f"📊 数据集统计:")
    stats = dataset['statistics']
    print(f"   - 总图像数: {stats['total_images']}")
    print(f"   - 总标注数: {stats['total_annotations']}")
    print(f"   - 标签类别: {stats['labels']}")
    
    # 2. 演示导出功能
    print("\n📤 演示导出功能...")
    
    # 创建输出目录
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    # 导出为JSON
    json_file = output_dir / "sample_dataset.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON导出: {json_file}")
    
    # 导出为COCO格式
    coco_data = export_to_coco(dataset)
    coco_file = output_dir / "sample_dataset.coco"
    with open(coco_file, 'w', encoding='utf-8') as f:
        json.dump(coco_data, f, indent=2)
    print(f"✅ COCO导出: {coco_file}")
    
    # 导出为CSV
    csv_file = output_dir / "sample_dataset.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("image_id,label,bbox_x,bbox_y,bbox_w,bbox_h,confidence\n")
        for ann in dataset['annotations']:
            bbox = ann['bbox']
            f.write(f"{ann['image_id']},{ann['label']},{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},{ann['confidence']}\n")
    print(f"✅ CSV导出: {csv_file}")
    
    # 3. 显示配置示例
    print("\n⚙️  配置示例:")
    config = create_sample_config()
    print("```yaml")
    print(yaml.dump(config, default_flow_style=False))
    print("```")
    
    print("\n🎉 演示完成!")
    print("\n📋 下一步:")
    print("1. 运行 'python demo.py init my_project' 创建项目")
    print("2. 将图像文件放入 data/ 目录")
    print("3. 查看 README.md 了解完整功能")
    print("4. 运行单元测试: python -m pytest tests/ -v")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量标注工具MVP演示")
    parser.add_argument('command', nargs='?', choices=['init', 'demo'], 
                       default='demo', help='命令类型')
    parser.add_argument('project_dir', nargs='?', default='my_annotation_project',
                       help='项目目录（仅用于init命令）')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_project(args.project_dir)
    else:
        demonstrate_functionality()

if __name__ == '__main__':
    main()