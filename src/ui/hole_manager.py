"""
孔位管理模块
处理12×10孔位布局的管理和导航
"""

from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class HolePosition:
    """孔位信息"""
    number: int  # 孔位编号 1-120
    row: int     # 行号 0-9
    col: int     # 列号 0-11
    x: int       # 在全景图中的X坐标
    y: int       # 在全景图中的Y坐标
    width: int   # 孔位宽度
    height: int  # 孔位高度


class HoleManager:
    """
    孔位管理器
    负责孔位编号、坐标转换、导航等功能
    """
    
    def __init__(self, rows: int = 10, cols: int = 12):
        self.rows = rows
        self.cols = cols
        self.total_holes = rows * cols
        
        # 默认孔位尺寸（可根据实际全景图调整）
        self.hole_width = 90
        self.hole_height = 90
        self.hole_spacing_x = 80  # 孔位间距
        self.hole_spacing_y = 80
        self.start_x = 50  # 起始坐标
        self.start_y = 50
        
        # 动态配置参数 - 用于实时调整
        self.first_hole_x = 750  # 第一个孔位的X坐标
        self.first_hole_y = 392  # 第一个孔位的Y坐标
        self.horizontal_spacing = 145  # 水平间距
        self.vertical_spacing = 145  # 垂直间距
        self.hole_diameter = 90  # 孔位外框直径
        
        # 起始孔位设置 - 默认从25号孔开始标注
        self.start_hole_number = 25
        
    def update_positioning_params(self, first_hole_x=None, first_hole_y=None, 
                                horizontal_spacing=None, vertical_spacing=None, 
                                hole_diameter=None, start_hole=None):
        """更新孔位定位参数"""
        if first_hole_x is not None:
            self.first_hole_x = first_hole_x
        if first_hole_y is not None:
            self.first_hole_y = first_hole_y
        if horizontal_spacing is not None:
            self.horizontal_spacing = horizontal_spacing
        if vertical_spacing is not None:
            self.vertical_spacing = vertical_spacing
        if hole_diameter is not None:
            self.hole_diameter = hole_diameter
            self.hole_width = hole_diameter
            self.hole_height = hole_diameter
        if start_hole is not None:
            self.start_hole_number = start_hole
        
        # 更新相关参数
        self.hole_spacing_x = self.horizontal_spacing
        self.hole_spacing_y = self.vertical_spacing
        self.start_x = self.first_hole_x - self.hole_diameter // 2
        self.start_y = self.first_hole_y - self.hole_diameter // 2
    
    def set_layout_params(self, panoramic_width: int, panoramic_height: int, 
                         margin_x: int = 50, margin_y: int = 50):
        """
        根据全景图尺寸设置孔位布局参数
        针对3088×2064全景图优化
        注意：现在使用动态配置参数，不会覆盖用户设置的值
        """
        # 针对实际全景图的精确参数
        if panoramic_width == 3088 and panoramic_height == 2064:
            # 如果是首次初始化（动态参数还是默认值），则设置优化参数
            # 否则保持用户已设置的参数不变
            if (self.first_hole_x == 750 and self.first_hole_y == 392 and 
                self.horizontal_spacing == 145 and self.vertical_spacing == 145):
                
                # 使用用户在__init__中设置的参数，或者设置为优化后的默认值
                # 这些参数已经在__init__中设置，这里不再覆盖
                pass
            
            # 更新相关的旧参数以保持兼容性
            self.hole_spacing_x = self.horizontal_spacing
            self.hole_spacing_y = self.vertical_spacing
            self.hole_width = self.hole_diameter
            self.hole_height = self.hole_diameter
            self.start_x = self.first_hole_x - self.hole_diameter // 2
            self.start_y = self.first_hole_y - self.hole_diameter // 2
            
        else:
            # 通用参数计算（仅在非标准尺寸时使用）
            available_width = panoramic_width - 2 * margin_x
            available_height = panoramic_height - 2 * margin_y
            
            self.hole_spacing_x = available_width // self.cols
            self.hole_spacing_y = available_height // self.rows
            
            # 孔位实际尺寸稍小于间距
            self.hole_width = int(self.hole_spacing_x * 0.8)
            self.hole_height = int(self.hole_spacing_y * 0.8)
            
            self.start_x = margin_x + (self.hole_spacing_x - self.hole_width) // 2
            self.start_y = margin_y + (self.hole_spacing_y - self.hole_height) // 2
            
            # 同步更新动态配置参数
            self.first_hole_x = self.start_x + self.hole_width // 2
            self.first_hole_y = self.start_y + self.hole_height // 2
            self.horizontal_spacing = self.hole_spacing_x
            self.vertical_spacing = self.hole_spacing_y
            self.hole_diameter = min(self.hole_width, self.hole_height)
    
    def number_to_position(self, hole_number: int) -> Tuple[int, int]:
        """
        孔位编号转换为行列坐标
        编号从1开始，按行优先排列
        """
        if not (1 <= hole_number <= self.total_holes):
            raise ValueError(f"孔位编号必须在1-{self.total_holes}之间")
        
        # 转换为0基索引
        index = hole_number - 1
        row = index // self.cols
        col = index % self.cols
        
        return (row, col)
    
    def position_to_number(self, row: int, col: int) -> int:
        """
        行列坐标转换为孔位编号
        """
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"行列坐标超出范围: ({row}, {col})")
        
        return row * self.cols + col + 1
    
    def get_row_from_hole_number(self, hole_number: int) -> int:
        """
        从孔位编号获取行号
        """
        row, col = self.number_to_position(hole_number)
        return row
    
    def get_col_from_hole_number(self, hole_number: int) -> int:
        """
        从孔位编号获取列号
        """
        row, col = self.number_to_position(hole_number)
        return col
        
    def get_hole_coordinates(self, hole_number: int) -> Tuple[int, int, int, int]:
        """
        获取孔位在全景图中的坐标 (x, y, width, height)
        使用动态配置参数
        """
        row, col = self.number_to_position(hole_number)
        
        # 使用动态配置参数计算坐标
        x = (self.first_hole_x - self.hole_diameter // 2) + col * self.horizontal_spacing
        y = (self.first_hole_y - self.hole_diameter // 2) + row * self.vertical_spacing
        
        return (x, y, self.hole_diameter, self.hole_diameter)
    
    def get_hole_center_coordinates(self, hole_number: int) -> Tuple[int, int]:
        """
        获取孔位中心坐标
        """
        x, y, width, height = self.get_hole_coordinates(hole_number)
        center_x = x + width // 2
        center_y = y + height // 2
        return (center_x, center_y)
    
    def get_hole_info(self, hole_number: int) -> HolePosition:
        """获取完整的孔位信息"""
        row, col = self.number_to_position(hole_number)
        x, y, width, height = self.get_hole_coordinates(hole_number)
        
        return HolePosition(
            number=hole_number,
            row=row,
            col=col,
            x=x,
            y=y,
            width=width,
            height=height
        )
    
    def get_adjacent_holes(self, hole_number: int) -> List[int]:
        """获取相邻孔位编号"""
        row, col = self.number_to_position(hole_number)
        adjacent = []
        
        # 上下左右四个方向
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.rows and 0 <= new_col < self.cols:
                adjacent.append(self.position_to_number(new_row, new_col))
        
        return adjacent
    
    def get_gradient_sequence(self, hole_number: int, direction: str = 'horizontal') -> List[int]:
        """
        获取梯度序列（同行或同列的孔位）
        用于药敏梯度分析
        """
        row, col = self.number_to_position(hole_number)
        sequence = []
        
        if direction == 'horizontal':
            # 同行的所有孔位
            for c in range(self.cols):
                sequence.append(self.position_to_number(row, c))
        elif direction == 'vertical':
            # 同列的所有孔位
            for r in range(self.rows):
                sequence.append(self.position_to_number(r, col))
        else:
            raise ValueError("方向必须是 'horizontal' 或 'vertical'")
        
        return sequence
    
    def find_hole_by_coordinates(self, x: int, y: int, scale_factor: float = 1.0, 
                               offset_x: int = 0, offset_y: int = 0) -> Optional[int]:
        """
        根据坐标查找对应的孔位编号
        用于鼠标点击定位 - 考虑图像缩放和偏移
        
        Args:
            x, y: 点击坐标（相对于画布）
            scale_factor: 图像缩放比例
            offset_x, offset_y: 图像在画布中的偏移
        """
        # 将画布坐标转换为原始图像坐标
        original_x = (x - offset_x) / scale_factor
        original_y = (y - offset_y) / scale_factor
        
        # 遍历所有孔位，找到最近的
        min_distance = float('inf')
        closest_hole = None
        
        for hole_num in range(1, self.total_holes + 1):
            # 获取孔位中心坐标（原始图像坐标）
            hx, hy, hw, hh = self.get_hole_coordinates(hole_num)
            center_x = hx + hw // 2
            center_y = hy + hh // 2
            
            # 计算距离
            distance = ((original_x - center_x) ** 2 + (original_y - center_y) ** 2) ** 0.5
            
            # 检查是否在孔位范围内
            radius = min(hw, hh) // 2
            if distance <= radius * 1.3:  # 放宽容差以提升用户体验
                if distance < min_distance:
                    min_distance = distance
                    closest_hole = hole_num
        
        return closest_hole
    
    def get_navigation_info(self, current_hole: int) -> Dict[str, Any]:
        """
        获取导航信息
        """
        row, col = self.number_to_position(current_hole)
        
        navigation = {
            'current': current_hole,
            'row': row,
            'col': col,
            'total': self.total_holes,
            'can_go_up': row > 0,
            'can_go_down': row < self.rows - 1,
            'can_go_left': col > 0,
            'can_go_right': col < self.cols - 1,
            'can_go_prev': current_hole > 1,
            'can_go_next': current_hole < self.total_holes
        }
        
        # 计算导航目标
        if navigation['can_go_up']:
            navigation['up_hole'] = self.position_to_number(row - 1, col)
        if navigation['can_go_down']:
            navigation['down_hole'] = self.position_to_number(row + 1, col)
        if navigation['can_go_left']:
            navigation['left_hole'] = self.position_to_number(row, col - 1)
        if navigation['can_go_right']:
            navigation['right_hole'] = self.position_to_number(row, col + 1)
        
        navigation['prev_hole'] = current_hole - 1 if navigation['can_go_prev'] else None
        navigation['next_hole'] = current_hole + 1 if navigation['can_go_next'] else None
        
        return navigation
    
    def get_all_holes_layout(self) -> List[List[int]]:
        """
        获取所有孔位的二维布局
        返回10×12的二维数组
        """
        layout = []
        for row in range(self.rows):
            row_holes = []
            for col in range(self.cols):
                hole_number = self.position_to_number(row, col)
                row_holes.append(hole_number)
            layout.append(row_holes)
        
        return layout
        
    def validate_hole_number(self, hole_number: int) -> bool:
        """验证孔位编号是否有效（考虑起始孔位限制）"""
        return self.start_hole_number <= hole_number <= self.total_holes
    
    def is_hole_available_for_annotation(self, hole_number: int) -> bool:
        """检查孔位是否可用于标注"""
        return hole_number >= self.start_hole_number
    
    def get_hole_label(self, hole_number: int) -> str:
        """
        获取孔位标签（如 A1, B2 等）
        """
        row, col = self.number_to_position(hole_number)
        row_label = chr(ord('A') + row)  # A-J
        col_label = str(col + 1)  # 1-12
        return f"{row_label}{col_label}"
    
    def parse_hole_label(self, label: str) -> int:
        """
        解析孔位标签为编号
        """
        if len(label) < 2:
            raise ValueError(f"无效的孔位标签: {label}")
        
        row_char = label[0].upper()
        col_str = label[1:]
        
        if not ('A' <= row_char <= 'J'):
            raise ValueError(f"行标签必须在A-J之间: {row_char}")
        
        try:
            col_num = int(col_str)
            if not (1 <= col_num <= 12):
                raise ValueError(f"列标签必须在1-12之间: {col_num}")
        except ValueError:
            raise ValueError(f"无效的列标签: {col_str}")
        
        row = ord(row_char) - ord('A')
        col = col_num - 1
        
        return self.position_to_number(row, col)