#!/usr/bin/env python3
"""
测试时间戳保存和加载功能
验证JSON保存和加载过程中时间戳是否正确保持
"""

import os
import sys
import json
import tempfile
import datetime
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / 'src'

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from models.panoramic_annotation import PanoramicAnnotation, PanoramicDataset


def test_timestamp_preservation():
    """测试时间戳保存和加载功能"""
    print("=== 测试时间戳保存和加载功能 ===")
    
    # 创建测试标注对象
    original_time = datetime.datetime(2025, 8, 28, 10, 30, 45)  # 特定的测试时间
    test_annotation = PanoramicAnnotation(
        image_path="test_slice.png",
        label="positive",
        bbox=[0, 0, 70, 70],
        confidence=0.95,
        panoramic_image_id="EB10000026",
        hole_number=25,
        hole_row=3,
        hole_col=1,
        microbe_type="bacteria",
        growth_level="positive",
        interference_factors=[],
        annotation_source="enhanced_manual",
        is_confirmed=True
    )
    
    # 设置时间戳
    test_annotation.timestamp = original_time.isoformat()
    print(f"✓ 创建测试标注，原始时间戳: {original_time.strftime('%m-%d %H:%M:%S')}")
    
    # 创建数据集并添加标注
    dataset = PanoramicDataset("测试数据集", "时间戳保存测试")
    dataset.add_annotation(test_annotation)
    
    # 保存到临时JSON文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_filename = f.name
    
    try:
        dataset.save_to_json(temp_filename, confirmed_only=False)
        print(f"✓ 保存到JSON文件: {temp_filename}")
        
        # 验证JSON文件中是否包含时间戳
        with open(temp_filename, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        saved_annotation = json_data['annotations'][0]
        has_timestamp_in_json = 'timestamp' in saved_annotation
        print(f"✓ JSON文件包含时间戳: {has_timestamp_in_json}")
        
        if has_timestamp_in_json:
            json_timestamp = saved_annotation['timestamp']
            print(f"✓ JSON中的时间戳: {json_timestamp}")
            
            # 从JSON文件加载
            loaded_dataset = PanoramicDataset.load_from_json(temp_filename)
            loaded_annotation = loaded_dataset.annotations[0]
            
            has_loaded_timestamp = hasattr(loaded_annotation, 'timestamp') and loaded_annotation.timestamp
            print(f"✓ 加载的标注包含时间戳: {has_loaded_timestamp}")
            
            if has_loaded_timestamp:
                # 比较时间戳是否一致
                if isinstance(loaded_annotation.timestamp, str):
                    loaded_time_str = loaded_annotation.timestamp
                    loaded_time = datetime.datetime.fromisoformat(loaded_time_str.replace('Z', '+00:00'))
                else:
                    loaded_time = loaded_annotation.timestamp
                    loaded_time_str = loaded_time.isoformat()
                
                timestamp_preserved = loaded_time_str == original_time.isoformat()
                print(f"✓ 时间戳通过JSON循环保持: {timestamp_preserved}")
                print(f"  原始: {original_time.isoformat()}")
                print(f"  加载: {loaded_time_str}")
                
                if timestamp_preserved:
                    print("🎉 时间戳保存和加载测试通过！")
                    return True
                else:
                    print("❌ 时间戳在JSON循环中丢失！")
                    return False
            else:
                print("❌ 加载的标注没有时间戳属性！")
                return False
        else:
            print("❌ JSON文件中没有保存时间戳！")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_filename)
        except:
            pass


def test_memory_timestamp_sync():
    """测试内存时间戳同步功能"""
    print("\n=== 测试内存时间戳同步功能 ===")
    
    # 创建带时间戳的标注
    test_time = datetime.datetime(2025, 8, 28, 15, 45, 30)
    annotation = PanoramicAnnotation(
        image_path="test_slice_2.png",
        label="weak_growth",
        bbox=[0, 0, 70, 70],
        confidence=0.85,
        panoramic_image_id="EB10000027", 
        hole_number=10,
        hole_row=1,
        hole_col=10,
        microbe_type="bacteria",
        growth_level="weak_growth",
        interference_factors=[],
        annotation_source="enhanced_manual",
        is_confirmed=True
    )
    annotation.timestamp = test_time.isoformat()
    
    # 模拟内存同步逻辑（来自load_existing_annotation方法）
    annotation_key = f"{annotation.panoramic_image_id}_{annotation.hole_number}"
    last_annotation_time = {}  # 模拟类实例变量
    
    try:
        if isinstance(annotation.timestamp, str):
            dt = datetime.datetime.fromisoformat(annotation.timestamp.replace('Z', '+00:00'))
        else:
            dt = annotation.timestamp
        last_annotation_time[annotation_key] = dt
        
        synced_time = last_annotation_time[annotation_key]
        sync_successful = synced_time == test_time
        
        print(f"✓ 原始时间: {test_time.strftime('%m-%d %H:%M:%S')}")
        print(f"✓ 同步时间: {synced_time.strftime('%m-%d %H:%M:%S')}")
        print(f"✓ 同步成功: {sync_successful}")
        
        if sync_successful:
            print("🎉 内存时间戳同步测试通过！")
            return True
        else:
            print("❌ 内存时间戳同步失败！")
            return False
            
    except Exception as e:
        print(f"❌ 内存同步测试失败: {e}")
        return False


if __name__ == "__main__":
    print("开始时间戳保存和加载测试...")
    
    test1_passed = test_timestamp_preservation()
    test2_passed = test_memory_timestamp_sync()
    
    print(f"\n=== 测试总结 ===")
    print(f"时间戳保存/加载测试: {'通过' if test1_passed else '失败'}")
    print(f"内存时间戳同步测试: {'通过' if test2_passed else '失败'}")
    
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！时间戳功能正常工作。")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，需要检查时间戳处理逻辑。")
        sys.exit(1)