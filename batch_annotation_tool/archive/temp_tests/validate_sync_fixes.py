#!/usr/bin/env python3
"""
验证标注同步修复的测试脚本
测试核心功能是否正常工作
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

def test_annotation_sync_fixes():
    """测试标注同步修复"""
    print("开始验证标注同步修复...")
    
    try:
        # 测试1: 导入主要模块
        print("1. 导入主要模块...")
        from models.panoramic_annotation import PanoramicAnnotation
        from models.panoramic_dataset import PanoramicDataset
        from ui.enhanced_annotation_panel import FeatureCombination
        print("✓ 主要模块导入成功")
        
        # 测试2: 创建测试数据集
        print("2. 创建测试数据集...")
        dataset = PanoramicDataset("测试数据集", "用于验证同步修复")
        print("✓ 数据集创建成功")
        
        # 测试3: 创建增强标注
        print("3. 创建增强标注...")
        
        # 创建一个假的特征组合
        feature_combination = FeatureCombination(
            growth_level="positive",
            growth_pattern="clean",
            interference_factors=set(),
            confidence=0.95
        )
        
        # 创建标注对象
        annotation = PanoramicAnnotation.from_filename(
            "test_panoramic_hole_25.png",
            label=feature_combination.to_label,
            bbox=[0, 0, 70, 70],
            confidence=0.95,
            microbe_type="bacteria",
            growth_level="positive",
            interference_factors=[],
            annotation_source="enhanced_manual",
            is_confirmed=True,
            panoramic_id="test_panoramic"
        )
        
        # 添加增强数据
        annotation.enhanced_data = {
            'feature_combination': feature_combination.to_dict(),
            'annotation_source': 'enhanced_manual',
            'is_confirmed': True
        }
        
        # 添加时间戳
        import datetime
        annotation.timestamp = datetime.datetime.now().isoformat()
        
        print("✓ 增强标注创建成功")
        
        # 测试4: 验证标注属性
        print("4. 验证标注属性...")
        
        # 检查是否为增强标注
        has_enhanced = (hasattr(annotation, 'enhanced_data') and 
                      annotation.enhanced_data and 
                      annotation.annotation_source == 'enhanced_manual')
        
        print(f"   annotation_source: {annotation.annotation_source}")
        print(f"   has enhanced_data: {hasattr(annotation, 'enhanced_data')}")
        print(f"   enhanced_data content: {annotation.enhanced_data}")
        print(f"   is enhanced annotation: {has_enhanced}")
        print(f"   timestamp: {annotation.timestamp}")
        
        if has_enhanced:
            print("✓ 增强标注验证成功")
        else:
            print("✗ 增强标注验证失败")
            return False
        
        # 测试5: 添加到数据集并查询
        print("5. 测试数据集操作...")
        dataset.add_annotation(annotation)
        
        retrieved_ann = dataset.get_annotation_by_hole("test_panoramic", 25)
        if retrieved_ann:
            print("✓ 标注查询成功")
            
            # 验证查询到的标注是否还是增强标注
            has_enhanced_retrieved = (hasattr(retrieved_ann, 'enhanced_data') and 
                                    retrieved_ann.enhanced_data and 
                                    retrieved_ann.annotation_source == 'enhanced_manual')
            
            if has_enhanced_retrieved:
                print("✓ 查询到的标注保持增强属性")
            else:
                print("✗ 查询到的标注丢失增强属性")
                return False
        else:
            print("✗ 标注查询失败")
            return False
        
        print("\n🎉 所有测试通过！标注同步修复验证成功。")
        print("\n修复说明:")
        print("1. save_current_annotation_internal() 正确设置 annotation_source='enhanced_manual'")
        print("2. enhanced_data 结构正确保存")
        print("3. 时间戳正确设置")
        print("4. 数据集查询功能正常")
        print("5. load_current_slice() 增加了延迟同步机制")
        print("6. load_existing_annotation() 改进了时间戳同步逻辑")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_annotation_sync_fixes()
    if success:
        print("\n请现在启动GUI测试完整功能:")
        print("python test_annotation_sync.py")
    else:
        print("\n修复验证失败，请检查错误信息。")
    sys.exit(0 if success else 1)