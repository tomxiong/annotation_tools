#!/usr/bin/env python3
"""
测试坐标不一致问题
验证两种不同的坐标计算方式
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.ui.hole_manager import HoleManager

def test_coordinate_inconsistency():
    """测试坐标不一致问题"""
    print("=== 测试坐标不一致问题 ===")
    
    # 创建HoleManager实例
    hole_manager = HoleManager()
    
    print(f"初始状态:")
    print(f"  original_first_hole_x: {hole_manager.original_first_hole_x}")
    print(f"  original_first_hole_y: {hole_manager.original_first_hole_y}")
    print(f"  first_hole_x: {hole_manager.first_hole_x}")
    print(f"  first_hole_y: {hole_manager.first_hole_y}")
    print(f"  current_scale: {hole_manager.current_scale}")
    
    # 模拟用户修改起始位置
    print(f"\n=== 用户修改起始位置 ===")
    new_x, new_y = 800, 450
    hole_manager.update_positioning_params(
        first_hole_x=new_x,
        first_hole_y=new_y
    )
    
    print(f"修改后状态:")
    print(f"  original_first_hole_x: {hole_manager.original_first_hole_x}")
    print(f"  original_first_hole_y: {hole_manager.original_first_hole_y}")
    print(f"  first_hole_x: {hole_manager.first_hole_x}")
    print(f"  first_hole_y: {hole_manager.first_hole_y}")
    
    # 获取第1个孔位的坐标（方式一：原始坐标）
    hole_center_original = hole_manager.get_hole_center_coordinates(1)
    print(f"\n第1个孔位中心坐标（原始）: {hole_center_original}")
    
    # 模拟画布调整
    print(f"\n=== 模拟画布调整 ===")
    canvas_width, canvas_height = 1200, 800
    img_width, img_height = 3088, 2064
    
    hole_manager.adjust_coordinates_for_canvas(
        canvas_width, canvas_height, img_width, img_height
    )
    
    print(f"画布调整后状态:")
    print(f"  original_first_hole_x: {hole_manager.original_first_hole_x}")
    print(f"  original_first_hole_y: {hole_manager.original_first_hole_y}")
    print(f"  first_hole_x: {hole_manager.first_hole_x}")
    print(f"  first_hole_y: {hole_manager.first_hole_y}")
    print(f"  current_scale: {hole_manager.current_scale}")
    
    # 再次获取第1个孔位的坐标
    hole_center_adjusted = hole_manager.get_hole_center_coordinates(1)
    print(f"\n第1个孔位中心坐标（调整后）: {hole_center_adjusted}")
    
    # 计算两种方式的最终坐标
    scale_factor = hole_manager.current_scale
    offset_x, offset_y = 100, 50  # 模拟偏移
    
    print(f"\n=== 两种坐标计算方式对比 ===")
    print(f"缩放因子: {scale_factor}")
    print(f"偏移: ({offset_x}, {offset_y})")
    
    # 方式一：原始坐标 * 缩放因子
    method1_x = offset_x + int(hole_center_original[0] * scale_factor)
    method1_y = offset_y + int(hole_center_original[1] * scale_factor)
    print(f"方式一（手动缩放）: ({method1_x}, {method1_y})")
    
    # 方式二：直接使用调整后的坐标
    method2_x = offset_x + hole_center_adjusted[0]
    method2_y = offset_y + hole_center_adjusted[1]
    print(f"方式二（直接使用）: ({method2_x}, {method2_y})")
    
    # 计算差异
    diff_x = abs(method1_x - method2_x)
    diff_y = abs(method1_y - method2_y)
    print(f"坐标差异: ({diff_x}, {diff_y})")
    
    if diff_x > 0 or diff_y > 0:
        print(f"❌ 发现坐标不一致问题！")
        return False
    else:
        print(f"✅ 坐标一致")
        return True

def test_scale_update_timing():
    """测试缩放更新时序问题"""
    print(f"\n=== 测试缩放更新时序问题 ===")
    
    hole_manager = HoleManager()
    
    # 场景1：先画布调整，再用户修改
    print(f"\n场景1：先画布调整，再用户修改")
    hole_manager.adjust_coordinates_for_canvas(1200, 800, 3088, 2064)
    scale1 = hole_manager.current_scale
    print(f"  画布调整后 scale: {scale1}")
    
    hole_manager.update_positioning_params(first_hole_x=800, first_hole_y=450)
    coord1 = hole_manager.get_hole_center_coordinates(1)
    print(f"  用户修改后坐标: {coord1}")
    
    # 场景2：先用户修改，再画布调整
    print(f"\n场景2：先用户修改，再画布调整")
    hole_manager2 = HoleManager()
    
    hole_manager2.update_positioning_params(first_hole_x=800, first_hole_y=450)
    print(f"  用户修改后 original: ({hole_manager2.original_first_hole_x}, {hole_manager2.original_first_hole_y})")
    
    hole_manager2.adjust_coordinates_for_canvas(1200, 800, 3088, 2064)
    scale2 = hole_manager2.current_scale
    coord2 = hole_manager2.get_hole_center_coordinates(1)
    print(f"  画布调整后 scale: {scale2}")
    print(f"  最终坐标: {coord2}")
    
    # 对比结果
    print(f"\n结果对比:")
    print(f"  场景1最终坐标: {coord1}")
    print(f"  场景2最终坐标: {coord2}")
    
    if coord1 == coord2:
        print(f"✅ 时序无影响")
        return True
    else:
        print(f"❌ 时序有影响！")
        return False

if __name__ == "__main__":
    try:
        result1 = test_coordinate_inconsistency()
        result2 = test_scale_update_timing()
        
        print(f"\n=== 测试总结 ===")
        print(f"坐标一致性测试: {'通过' if result1 else '失败'}")
        print(f"时序问题测试: {'通过' if result2 else '失败'}")
        
        if not result1 or not result2:
            print(f"\n❌ 发现问题，需要修复坐标不一致问题")
        else:
            print(f"\n✅ 所有测试通过")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
