#!/usr/bin/env python3
"""
测试不考虑画布调整时的坐标一致性
验证两种场景下如果不调用adjust_coordinates_for_canvas是否一致
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.ui.hole_manager import HoleManager

def test_without_canvas_adjustment():
    """测试不进行画布调整时的坐标一致性"""
    print("=== 测试不进行画布调整时的坐标一致性 ===")
    
    # 场景1：只进行用户修改，不调用画布调整
    print(f"\n场景1：只进行用户修改")
    hole_manager1 = HoleManager()
    
    print(f"初始状态:")
    print(f"  original_first_hole_x: {hole_manager1.original_first_hole_x}")
    print(f"  original_first_hole_y: {hole_manager1.original_first_hole_y}")
    print(f"  first_hole_x: {hole_manager1.first_hole_x}")
    print(f"  first_hole_y: {hole_manager1.first_hole_y}")
    print(f"  current_scale: {hole_manager1.current_scale}")
    
    # 用户修改起始位置
    new_x, new_y = 800, 450
    hole_manager1.update_positioning_params(
        first_hole_x=new_x,
        first_hole_y=new_y
    )
    
    print(f"\n用户修改后:")
    print(f"  original_first_hole_x: {hole_manager1.original_first_hole_x}")
    print(f"  original_first_hole_y: {hole_manager1.original_first_hole_y}")
    print(f"  first_hole_x: {hole_manager1.first_hole_x}")
    print(f"  first_hole_y: {hole_manager1.first_hole_y}")
    
    coord1 = hole_manager1.get_hole_center_coordinates(1)
    print(f"  第1个孔位中心坐标: {coord1}")
    
    # 场景2：相同的用户修改（验证一致性）
    print(f"\n场景2：相同的用户修改")
    hole_manager2 = HoleManager()
    
    hole_manager2.update_positioning_params(
        first_hole_x=new_x,
        first_hole_y=new_y
    )
    
    coord2 = hole_manager2.get_hole_center_coordinates(1)
    print(f"  第1个孔位中心坐标: {coord2}")
    
    # 对比结果
    print(f"\n=== 结果对比 ===")
    print(f"场景1坐标: {coord1}")
    print(f"场景2坐标: {coord2}")
    
    if coord1 == coord2:
        print(f"✅ 不进行画布调整时坐标一致")
        return True
    else:
        print(f"❌ 坐标不一致！")
        return False

def test_original_coordinates_consistency():
    """测试原始坐标的一致性"""
    print(f"\n=== 测试原始坐标的一致性 ===")
    
    hole_manager = HoleManager()
    
    # 测试多次设置相同的坐标
    test_coords = [(800, 450), (750, 392), (900, 500)]
    
    for i, (x, y) in enumerate(test_coords):
        print(f"\n测试坐标 {i+1}: ({x}, {y})")
        
        # 设置坐标
        hole_manager.update_positioning_params(first_hole_x=x, first_hole_y=y)
        
        print(f"  设置后 original: ({hole_manager.original_first_hole_x}, {hole_manager.original_first_hole_y})")
        print(f"  设置后 current: ({hole_manager.first_hole_x}, {hole_manager.first_hole_y})")
        
        # 获取孔位坐标
        coord = hole_manager.get_hole_center_coordinates(1)
        print(f"  第1个孔位坐标: {coord}")
        
        # 验证原始坐标是否正确设置
        expected_coord = (x, y)
        if (hole_manager.original_first_hole_x, hole_manager.original_first_hole_y) == expected_coord:
            print(f"  ✅ 原始坐标设置正确")
        else:
            print(f"  ❌ 原始坐标设置错误")
            return False
            
        # 在没有缩放的情况下，当前坐标应该等于原始坐标
        if (hole_manager.first_hole_x, hole_manager.first_hole_y) == expected_coord:
            print(f"  ✅ 当前坐标正确")
        else:
            print(f"  ❌ 当前坐标错误")
            return False
    
    return True

def test_get_hole_coordinates_logic():
    """测试get_hole_coordinates的计算逻辑"""
    print(f"\n=== 测试get_hole_coordinates的计算逻辑 ===")
    
    hole_manager = HoleManager()
    
    # 设置测试参数
    test_x, test_y = 800, 450
    hole_manager.update_positioning_params(first_hole_x=test_x, first_hole_y=test_y)
    
    print(f"测试参数:")
    print(f"  first_hole_x: {hole_manager.first_hole_x}")
    print(f"  first_hole_y: {hole_manager.first_hole_y}")
    print(f"  hole_diameter: {hole_manager.hole_diameter}")
    print(f"  horizontal_spacing: {hole_manager.horizontal_spacing}")
    print(f"  vertical_spacing: {hole_manager.vertical_spacing}")
    
    # 测试前几个孔位的坐标计算
    test_holes = [1, 2, 13, 25]  # 第1个、第2个、第二行第一个、第三行第一个
    
    for hole_num in test_holes:
        row, col = hole_manager.number_to_position(hole_num)
        print(f"\n孔位 {hole_num} (行{row}, 列{col}):")
        
        # 手动计算预期坐标
        expected_x = (test_x - hole_manager.hole_diameter // 2) + col * hole_manager.horizontal_spacing
        expected_y = (test_y - hole_manager.hole_diameter // 2) + row * hole_manager.vertical_spacing
        expected_center_x = expected_x + hole_manager.hole_diameter // 2
        expected_center_y = expected_y + hole_manager.hole_diameter // 2
        
        print(f"  预期矩形坐标: ({expected_x}, {expected_y})")
        print(f"  预期中心坐标: ({expected_center_x}, {expected_center_y})")
        
        # 实际计算坐标
        actual_rect = hole_manager.get_hole_coordinates(hole_num)
        actual_center = hole_manager.get_hole_center_coordinates(hole_num)
        
        print(f"  实际矩形坐标: {actual_rect}")
        print(f"  实际中心坐标: {actual_center}")
        
        # 验证计算是否正确
        if (actual_rect[0], actual_rect[1]) == (expected_x, expected_y):
            print(f"  ✅ 矩形坐标计算正确")
        else:
            print(f"  ❌ 矩形坐标计算错误")
            return False
            
        if actual_center == (expected_center_x, expected_center_y):
            print(f"  ✅ 中心坐标计算正确")
        else:
            print(f"  ❌ 中心坐标计算错误")
            return False
    
    return True

if __name__ == "__main__":
    try:
        result1 = test_without_canvas_adjustment()
        result2 = test_original_coordinates_consistency()
        result3 = test_get_hole_coordinates_logic()
        
        print(f"\n=== 测试总结 ===")
        print(f"不调整画布坐标一致性: {'通过' if result1 else '失败'}")
        print(f"原始坐标设置一致性: {'通过' if result2 else '失败'}")
        print(f"坐标计算逻辑验证: {'通过' if result3 else '失败'}")
        
        if result1 and result2 and result3:
            print(f"\n✅ 所有测试通过 - 不考虑画布调整时坐标是一致的")
        else:
            print(f"\n❌ 测试失败")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
