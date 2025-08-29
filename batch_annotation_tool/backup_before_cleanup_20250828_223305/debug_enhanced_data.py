#!/usr/bin/env python3
"""
调试增强数据保存和加载问题
专门测试为什么 positive_clustered 标注没有被正确保存和恢复
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

def debug_enhanced_data_issue():
    """调试增强数据问题"""
    print("🔍 调试增强数据保存和加载问题")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from models.enhanced_annotation import FeatureCombination, GrowthLevel, GrowthPattern
        from models.enhanced_annotation import EnhancedPanoramicAnnotation
        from models.panoramic_annotation import PanoramicAnnotation
        
        print("✅ 模块导入成功")
        
        # 测试1: 创建一个 positive_clustered 特征组合
        print("\n📝 测试1: 创建 positive_clustered 特征组合")
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.CLUSTERED,
            interference_factors=set(),
            confidence=1.0
        )
        print(f"✓ 特征组合创建: {feature_combination.growth_level}, {feature_combination.growth_pattern}")
        
        # 测试2: 创建增强标注对象
        print("\n📝 测试2: 创建增强标注对象")
        enhanced_annotation = EnhancedPanoramicAnnotation(
            image_path="test_hole_25.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="TEST001",
            hole_number=25,
            microbe_type="bacteria",
            feature_combination=feature_combination,
            annotation_source="enhanced_manual",
            is_confirmed=True
        )
        print(f"✓ 增强标注对象创建成功")
        
        # 测试3: 转换为字典
        print("\n📝 测试3: 转换为字典")
        enhanced_dict = enhanced_annotation.to_dict()
        print(f"✓ 增强数据字典:")
        print(f"  - growth_level: {enhanced_dict.get('growth_level')}")
        print(f"  - feature_combination: {enhanced_dict.get('feature_combination')}")
        if 'feature_combination' in enhanced_dict:
            fc_dict = enhanced_dict['feature_combination']
            print(f"    - growth_level: {fc_dict.get('growth_level')}")
            print(f"    - growth_pattern: {fc_dict.get('growth_pattern')}")
            print(f"    - confidence: {fc_dict.get('confidence')}")
        
        # 测试4: 创建兼容的标注对象
        print("\n📝 测试4: 创建兼容的标注对象")
        training_label = enhanced_annotation.get_training_label()
        print(f"✓ 训练标签: {training_label}")
        
        annotation = PanoramicAnnotation.from_filename(
            "test_hole_25.png",
            label=training_label,
            bbox=[0, 0, 70, 70],
            confidence=feature_combination.confidence,
            microbe_type="bacteria",
            growth_level=feature_combination.growth_level.value,
            interference_factors=[],
            annotation_source="enhanced_manual",
            is_confirmed=True,
            panoramic_id="TEST001"
        )
        
        # 关键: 设置增强数据
        annotation.enhanced_data = enhanced_dict
        print(f"✓ 设置 annotation.enhanced_data")
        print(f"  - enhanced_data 类型: {type(annotation.enhanced_data)}")
        print(f"  - enhanced_data 是否为空: {not annotation.enhanced_data}")
        print(f"  - 包含 feature_combination: {'feature_combination' in annotation.enhanced_data}")
        
        # 测试5: 模拟恢复过程
        print("\n📝 测试5: 模拟恢复过程")
        print(f"✓ 检查条件:")
        print(f"  - hasattr(annotation, 'enhanced_data'): {hasattr(annotation, 'enhanced_data')}")
        print(f"  - annotation.enhanced_data: {bool(annotation.enhanced_data)}")
        print(f"  - annotation.annotation_source: {annotation.annotation_source}")
        print(f"  - 源在允许列表中: {annotation.annotation_source in ['enhanced_manual', 'manual']}")
        
        condition_met = (
            hasattr(annotation, 'enhanced_data') and 
            annotation.enhanced_data and 
            annotation.annotation_source in ['enhanced_manual', 'manual']
        )
        print(f"✓ 条件是否满足: {condition_met}")
        
        if condition_met:
            print("\n📝 测试6: 执行恢复过程")
            enhanced_data = annotation.enhanced_data
            
            if isinstance(enhanced_data, dict):
                if 'feature_combination' in enhanced_data:
                    combination_data = enhanced_data['feature_combination']
                    print(f"✓ 提取 feature_combination 数据: {combination_data}")
                else:
                    combination_data = enhanced_data
                    print(f"✓ 直接使用 enhanced_data: {combination_data}")
                
                # 尝试恢复特征组合
                restored_combination = FeatureCombination.from_dict(combination_data)
                print(f"✓ 恢复的特征组合:")
                print(f"  - growth_level: {restored_combination.growth_level}")
                print(f"  - growth_pattern: {restored_combination.growth_pattern}")
                print(f"  - confidence: {restored_combination.confidence}")
                
                # 检查值的类型
                print(f"✓ 类型检查:")
                print(f"  - growth_level 类型: {type(restored_combination.growth_level)}")
                print(f"  - growth_pattern 类型: {type(restored_combination.growth_pattern)}")
                
                # 提取字符串值
                growth_level_str = restored_combination.growth_level
                if hasattr(growth_level_str, 'value'):
                    growth_level_str = growth_level_str.value
                    
                growth_pattern_str = restored_combination.growth_pattern
                if growth_pattern_str and hasattr(growth_pattern_str, 'value'):
                    growth_pattern_str = growth_pattern_str.value
                
                print(f"✓ 提取的字符串值:")
                print(f"  - growth_level: '{growth_level_str}'")
                print(f"  - growth_pattern: '{growth_pattern_str}'")
                
                print("\n🎯 结论: 如果上述过程成功，说明修复有效!")
                print("如果在实际应用中仍有问题，可能是:")
                print("1. 保存时 enhanced_data 没有正确设置")
                print("2. 加载时条件判断有问题")
                print("3. UI 设置过程中的问题")
        else:
            print("\n❌ 条件不满足，无法进入恢复流程")
            print("需要检查保存过程是否正确设置了 enhanced_data")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔍 增强数据保存和加载调试")
    print("目标：理解为什么 positive_clustered 没有被正确恢复")
    print()
    
    success = debug_enhanced_data_issue()
    
    if success:
        print("\n✅ 调试测试完成")
        print("请查看上述输出，分析问题所在")
    else:
        print("\n❌ 调试测试失败")
    
    sys.exit(0 if success else 1)