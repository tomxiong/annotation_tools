# 已禁用的坐标调整功能 - 移到此处以减少主文件长度
# 由于坐标调整功能不是核心需求且存在时序问题，已被禁用

"""
原始的坐标调整功能代码
包含：
1. HoleManager.adjust_coordinates_for_canvas()
2. MainController坐标调整相关方法
3. 相关的坐标变换逻辑

这些功能被移到这里是因为：
- 存在坐标不一致问题
- 时序依赖导致的bug
- 非核心功能，优先级较低
"""

def adjust_coordinates_for_canvas_deprecated(self, canvas_width: int, canvas_height: int,
                               original_img_width: int, original_img_height: int):
    """
    已禁用：根据画布和原始图像尺寸调整坐标
    
    原始逻辑：
    - 计算缩放比例
    - 调整孔位坐标以适应画布显示
    - 更新内部坐标状态
    
    问题：
    - 与用户修改坐标的时序冲突
    - 导致两种坐标计算方法不一致
    - 复杂的坐标转换逻辑难以维护
    """
    from ..log_manager import log_debug

    # 计算缩放比例
    scale_x = canvas_width / original_img_width
    scale_y = canvas_height / original_img_height
    scale = min(scale_x, scale_y)
    
    log_debug(f"计算缩放比例: scale_x={scale_x:.4f}, scale_y={scale_y:.4f}, final_scale={scale:.4f}")
    
    # 存储当前缩放比例
    self.current_scale = scale
    
    # 如果有原始坐标，根据缩放比例调整显示坐标
    if hasattr(self, 'original_first_hole_x') and self.original_first_hole_x is not None:
        self.first_hole_x = int(self.original_first_hole_x * scale)
        log_debug(f"调整第一个孔X坐标: {self.original_first_hole_x} -> {self.first_hole_x}")
        
    if hasattr(self, 'original_first_hole_y') and self.original_first_hole_y is not None:
        self.first_hole_y = int(self.original_first_hole_y * scale)
        log_debug(f"调整第一个孔Y坐标: {self.original_first_hole_y} -> {self.first_hole_y}")
    
    # 调整间距（如果设置了的话）
    if hasattr(self, 'original_horizontal_spacing') and self.original_horizontal_spacing is not None:
        self.horizontal_spacing = int(self.original_horizontal_spacing * scale)
        
    if hasattr(self, 'original_vertical_spacing') and self.original_vertical_spacing is not None:
        self.vertical_spacing = int(self.original_vertical_spacing * scale)
        
    # 调整孔径
    if hasattr(self, 'original_hole_diameter') and self.original_hole_diameter is not None:
        self.hole_diameter = int(self.original_hole_diameter * scale)


def reset_coordinate_adjustments_deprecated(self):
    """已禁用：重置所有坐标调整参数"""
    self.coordinate_offset_x = 0.0
    self.coordinate_offset_y = 0.0
    self.coordinate_scale_adjust = 1.0
    print("重置所有坐标调整参数")


def _apply_coordinate_adjustments_deprecated(self, x: float, y: float, scale: float) -> tuple:
    """已禁用：应用坐标调整参数"""
    if not getattr(self, 'debug_coordinate_offset', False):
        return x * scale, y * scale

    # 应用缩放调整
    adjusted_scale = scale * getattr(self, 'coordinate_scale_adjust', 1.0)

    # 应用偏移调整
    adjusted_x = x * adjusted_scale + getattr(self, 'coordinate_offset_x', 0.0)
    adjusted_y = y * adjusted_scale + getattr(self, 'coordinate_offset_y', 0.0)

    return adjusted_x, adjusted_y


# 原始的复杂坐标转换逻辑
COORDINATE_ADJUSTMENT_NOTES = """
坐标调整功能的设计思路：

1. 用户输入坐标基于原始图像（如3088x2064）
2. 界面显示需要根据画布大小缩放
3. 需要在两种坐标系之间转换

问题分析：
1. 时序问题：adjust_coordinates_for_canvas和用户输入的调用顺序不确定
2. 状态管理：original_*和current_*坐标的同步问题  
3. 复杂性：两套坐标计算逻辑在不同文件中

解决方案：
直接禁用坐标调整功能，使用统一的坐标系
- 简化代码逻辑
- 避免坐标不一致问题
- 专注核心功能
"""
