#!/usr/bin/env python3
"""
Simple test to understand the annotation_source issue
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_annotation_source():
    """Test annotation_source handling"""
    print("🔍 测试 annotation_source 处理")
    print("=" * 50)
    
    try:
        from models.panoramic_annotation import PanoramicAnnotation
        
        # 测试1: 直接创建带enhanced_manual源的标注
        print("\n📝 测试1: 直接创建标注")
        annotation = PanoramicAnnotation.from_filename(
            "EB10000026_hole_25.png",
            label="positive",
            bbox=[0, 0, 70, 70],
            confidence=1.0,
            microbe_type="bacteria",
            growth_level="positive",
            interference_factors=[],
            annotation_source="enhanced_manual",
            is_confirmed=True,
            panoramic_id="EB10000026"
        )
        
        print(f"✓ 创建的标注:")
        print(f"  - annotation_source: {annotation.annotation_source}")
        print(f"  - growth_level: {annotation.growth_level}")
        print(f"  - hole_number: {annotation.hole_number}")
        
        # 测试2: 转换为字典并重新创建
        print("\n📝 测试2: 序列化和反序列化")
        data_dict = annotation.to_dict()
        print(f"✓ 字典中的 annotation_source: {data_dict.get('annotation_source')}")
        
        # 从字典重新创建
        restored_annotation = PanoramicAnnotation.from_dict(data_dict)
        print(f"✓ 恢复的标注:")
        print(f"  - annotation_source: {restored_annotation.annotation_source}")
        print(f"  - growth_level: {restored_annotation.growth_level}")
        
        # 测试3: 模拟数据集操作
        print("\n📝 测试3: 数据集操作")
        from models.panoramic_annotation import PanoramicDataset
        
        dataset = PanoramicDataset("测试数据集")
        dataset.add_annotation(annotation)
        
        # 查找标注
        found_annotation = dataset.get_annotation_by_hole("EB10000026", 25)
        if found_annotation:
            print(f"✓ 从数据集找到的标注:")
            print(f"  - annotation_source: {found_annotation.annotation_source}")
            print(f"  - growth_level: {found_annotation.growth_level}")
        else:
            print("❌ 未在数据集中找到标注")
        
        # 测试4: 检查默认值行为
        print("\n📝 测试4: 默认值行为")
        default_annotation = PanoramicAnnotation.from_filename(
            "EB10000026_hole_26.png",
            # 不提供annotation_source参数
        )
        print(f"✓ 默认标注:")
        print(f"  - annotation_source: {default_annotation.annotation_source}")
        
        print("\n🎯 结论:")
        if annotation.annotation_source == "enhanced_manual":
            print("✅ annotation_source 参数处理正常")
            print("问题可能在于:")
            print("1. 实际调用时参数传递有误")
            print("2. 某处代码修改了annotation_source")
            print("3. 数据保存/加载过程中的问题")
        else:
            print("❌ annotation_source 参数处理有问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_annotation_source()
    sys.exit(0 if success else 1)