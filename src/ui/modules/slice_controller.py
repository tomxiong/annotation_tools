"""
切片控制器模块
负责导航控制、事件处理和业务逻辑协调
专注于"做什么"而不是"怎么显示"
"""

import tkinter as tk
from typing import Optional, Tuple, Dict, Any


class SliceController:
    """
    切片控制器 - 负责导航控制和业务逻辑
    
    职责：
    1. 导航控制 (孔位/全景图切换)
    2. 事件处理 (键盘/鼠标事件)
    3. 状态管理 (当前位置、索引等)
    4. 业务逻辑协调 (调用其他服务)
    
    不负责：
    - 图像加载和显示 (交给ViewManager)
    - 画布操作 (交给ViewManager)
    - 视觉效果绘制 (交给ViewManager)
    """
    
    def __init__(self, parent_gui):
        """
        初始化切片控制器
        
        Args:
            parent_gui: 主GUI实例
        """
        self.gui = parent_gui
        
        # 当前状态
        self.current_panoramic_id = None
        self.current_hole_number = None
        self.current_slice_index = 0
        self.zoom_factor = 1.0
        
        # 孔位网格配置 (10行12列)
        self.grid_rows = 10
        self.grid_cols = 12
        self.hole_positions = self._generate_hole_positions()
        
    def update_panoramic_list(self):
        """更新全景图列表显示"""
        try:
            if not hasattr(self.gui.ui_builder, 'panoramic_id_var'):
                return
                
            # 获取全景图列表
            panoramic_ids = list(self.gui.data_manager.get_panoramic_ids())
            
            if panoramic_ids:
                # 设置第一个全景图为当前
                first_panoramic = panoramic_ids[0]
                self.gui.ui_builder.panoramic_id_var.set(first_panoramic)
                self.current_panoramic_id = first_panoramic
                
                # 同步给 ViewManager
                if hasattr(self.gui, 'view_manager'):
                    self.gui.view_manager.current_panoramic_id = first_panoramic
                
                self.gui.log_info(f"更新全景图列表，共 {len(panoramic_ids)} 个", "SLICE")
            else:
                self.gui.log_warning("未找到全景图", "SLICE")
                
        except Exception as e:
            self.gui.log_error(f"更新全景图列表失败: {e}", "SLICE")
            
    def load_first_slice(self):
        """加载第一个切片"""
        try:
            slice_files = self.gui.data_manager.slice_files
            if not slice_files:
                self.gui.log_warning("没有可用的切片文件", "SLICE")
                return
                
            # 加载第一个切片
            first_slice = slice_files[0]
            panoramic_id = first_slice.get('panoramic_id')
            hole_number = first_slice.get('hole_number')
            
            if panoramic_id and hole_number:
                self.current_slice_index = 0
                self.navigate_to_hole(panoramic_id, hole_number)
                
        except Exception as e:
            self.gui.log_error(f"加载第一个切片失败: {e}", "SLICE")
            
    def navigate_to_hole(self, panoramic_id: str, hole_number: int):
        """
        导航到指定孔位
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 孔位号
        """
        try:
            # 更新当前状态
            self.current_panoramic_id = panoramic_id
            self.current_hole_number = hole_number
            
            # 委托ViewManager处理图像显示
            if hasattr(self.gui, 'view_manager'):
                self.gui.view_manager.update_current_info(panoramic_id, hole_number)
                self.gui.view_manager.load_panoramic_image()
                
                # 加载切片图像
                slice_file_path = self._get_slice_file_path(panoramic_id, hole_number)
                if slice_file_path:
                    self.gui.view_manager.load_slice_image(slice_file_path)
            
            # 更新界面显示信息
            self._update_navigation_display()
            
            self.gui.log_debug(f"导航到孔位: {panoramic_id}_{hole_number}", "NAV")
            
        except Exception as e:
            self.gui.log_error(f"导航失败: {e}", "NAV")
    
    def _get_slice_file_path(self, panoramic_id: str, hole_number: int) -> Optional[str]:
        """
        获取切片文件路径
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 孔位号
            
        Returns:
            切片文件路径，如果未找到返回None
        """
        try:
            slice_files = self.gui.data_manager.get_slice_files_by_panoramic(panoramic_id)
            for file_info in slice_files:
                if file_info['hole_number'] == hole_number:
                    return file_info['filepath']
            return None
        except Exception as e:
            self.gui.log_error(f"获取切片文件路径失败: {e}", "NAV")
            return None
    
    def _get_panoramic_image_size(self) -> Optional[Tuple[int, int]]:
        """
        获取当前全景图的尺寸
        
        Returns:
            (width, height) 或 None
        """
        try:
            if hasattr(self.gui, 'view_manager') and self.gui.view_manager.panoramic_image:
                return (self.gui.view_manager.panoramic_image.width, 
                       self.gui.view_manager.panoramic_image.height)
            return None
        except Exception as e:
            self.gui.log_error(f"获取全景图尺寸失败: {e}", "NAV")
            return None
            
    def _update_navigation_display(self):
        """更新导航显示信息"""
        try:
            # 更新孔位号显示
            if hasattr(self.gui.ui_builder, 'hole_number_var'):
                self.gui.ui_builder.hole_number_var.set(str(self.current_hole_number))
                
            # 更新全景图ID显示
            if hasattr(self.gui.ui_builder, 'panoramic_id_var'):
                self.gui.ui_builder.panoramic_id_var.set(self.current_panoramic_id)
                
            # 更新进度显示
            self._update_progress_display()
            
        except Exception as e:
            self.gui.log_error(f"更新导航显示失败: {e}", "UI")
            
    def _update_progress_display(self):
        """更新进度显示"""
        try:
            if not hasattr(self.gui.ui_builder, 'progress_label'):
                return
                
            total_slices = len(self.gui.data_manager.slice_files)
            if total_slices > 0:
                progress_text = f"{self.current_slice_index + 1}/{total_slices}"
                self.gui.ui_builder.progress_label.config(text=progress_text)
            else:
                self.gui.ui_builder.progress_label.config(text="0/0")
                
        except Exception as e:
            self.gui.log_error(f"更新进度显示失败: {e}", "UI")
            

        
    def _generate_hole_positions(self) -> Dict[int, Tuple[int, int]]:
        """生成孔位坐标映射"""
        positions = {}
        hole_number = 1
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                positions[hole_number] = (row, col)
                hole_number += 1
                
        return positions

            

            


        
    def _update_info_display(self):
        """更新信息显示"""
        if not hasattr(self.gui, 'ui_builder'):
            return
            
        try:
            # 获取当前标注状态
            annotation = self.gui.data_manager.get_annotation(
                self.current_panoramic_id, self.current_hole_number
            )
            
            status = annotation.growth_level if annotation else "未标注"
            
            # 更新UI显示
            self.gui.ui_builder.update_info_display(
                self.current_panoramic_id,
                self.current_hole_number,
                status
            )
            
            # 更新统计信息
            stats = self.gui.data_manager.get_statistics()
            self.gui.ui_builder.update_stats_display(
                stats['total_annotations'],
                stats['total_slices']
            )
            
        except Exception as e:
            self.gui.log_error(f"更新信息显示失败: {e}", "SLICE")
            
    def navigate_to_hole_simple(self, hole_number: int) -> bool:
        """
        导航到指定孔位（简化版，仅孔位号）
        
        Args:
            hole_number: 孔位号
            
        Returns:
            bool: 导航是否成功
        """
        if not self.current_panoramic_id:
            return False
            
        try:
            self.navigate_to_hole(self.current_panoramic_id, hole_number)
            return True
        except Exception as e:
            self.gui.log_error(f"简单导航失败: {e}", "NAV")
            return False
        
    def navigate_to_panoramic(self, panoramic_id: str, hole_number: int = 1) -> bool:
        """
        导航到指定全景图和孔位
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 孔位号，默认为1
            
        Returns:
            bool: 导航是否成功
        """
        try:
            self.navigate_to_hole(panoramic_id, hole_number)
            return True
        except Exception as e:
            self.gui.log_error(f"导航到全景图失败: {e}", "NAV")
            return False
        
    def go_next_hole(self) -> bool:
        """下一个孔位"""
        if not self.current_hole_number:
            return False
            
        next_hole = self.current_hole_number + 1
        max_holes = self.grid_rows * self.grid_cols
        
        if next_hole <= max_holes:
            return self.navigate_to_hole_simple(next_hole)
        else:
            # 跳转到下一个全景图的第一个孔位
            return self.go_next_panoramic()
            
    def go_prev_hole(self) -> bool:
        """上一个孔位"""
        if not self.current_hole_number:
            return False
            
        prev_hole = self.current_hole_number - 1
        
        if prev_hole >= 1:
            return self.navigate_to_hole_simple(prev_hole)
        else:
            # 跳转到上一个全景图的最后一个孔位
            return self.go_prev_panoramic(last_hole=True)
            
    def go_next_panoramic(self) -> bool:
        """下一个全景图"""
        panoramic_ids = self.gui.data_manager.get_panoramic_ids()
        if not panoramic_ids or not self.current_panoramic_id:
            return False
            
        try:
            current_index = panoramic_ids.index(self.current_panoramic_id)
            next_index = (current_index + 1) % len(panoramic_ids)
            next_panoramic_id = panoramic_ids[next_index]
            
            return self.navigate_to_panoramic(next_panoramic_id, 1)
            
        except ValueError:
            return False
            
    def go_prev_panoramic(self, last_hole: bool = False) -> bool:
        """上一个全景图"""
        panoramic_ids = self.gui.data_manager.get_panoramic_ids()
        if not panoramic_ids or not self.current_panoramic_id:
            return False
            
        try:
            current_index = panoramic_ids.index(self.current_panoramic_id)
            prev_index = (current_index - 1) % len(panoramic_ids)
            prev_panoramic_id = panoramic_ids[prev_index]
            
            hole_number = self.grid_rows * self.grid_cols if last_hole else 1
            return self.navigate_to_panoramic(prev_panoramic_id, hole_number)
            
        except ValueError:
            return False
            
    def go_left(self) -> bool:
        """向左导航"""
        if not self.current_hole_number:
            return False
            
        row, col = self.hole_positions[self.current_hole_number]
        
        if col > 0:
            new_col = col - 1
            new_hole = self._position_to_number(row, new_col)
            return self.navigate_to_hole_simple(new_hole)
            
        return False
        
    def go_right(self) -> bool:
        """向右导航"""
        if not self.current_hole_number:
            return False
            
        row, col = self.hole_positions[self.current_hole_number]
        
        if col < self.grid_cols - 1:
            new_col = col + 1
            new_hole = self._position_to_number(row, new_col)
            return self.navigate_to_hole_simple(new_hole)
            
        return False
        
    def go_up(self) -> bool:
        """向上导航"""
        if not self.current_hole_number:
            return False
            
        row, col = self.hole_positions[self.current_hole_number]
        
        if row > 0:
            new_row = row - 1
            new_hole = self._position_to_number(new_row, col)
            return self.navigate_to_hole_simple(new_hole)
            
        return False
        
    def go_down(self) -> bool:
        """向下导航"""
        if not self.current_hole_number:
            return False
            
        row, col = self.hole_positions[self.current_hole_number]
        
        if row < self.grid_rows - 1:
            new_row = row + 1
            new_hole = self._position_to_number(new_row, col)
            return self.navigate_to_hole_simple(new_hole)
            
        return False
        
    def go_first_hole(self) -> bool:
        """跳转到第一个孔位"""
        return self.navigate_to_hole_simple(1)
        
    def go_last_hole(self) -> bool:
        """跳转到最后一个孔位"""
        max_holes = self.grid_rows * self.grid_cols
        return self.navigate_to_hole_simple(max_holes)
        
    def _position_to_number(self, row: int, col: int) -> int:
        """将行列位置转换为孔位号"""
        return row * self.grid_cols + col + 1
        
    def set_zoom(self, zoom_factor: float):
        """设置缩放比例"""
        self.zoom_factor = max(0.1, min(3.0, zoom_factor))
        self._update_slice_display()
        
    def handle_panoramic_click(self, event):
        """
        处理全景图点击事件
        
        Args:
            event: 鼠标点击事件
        """
        if not self.current_panoramic_id or not hasattr(self.gui, 'ui_builder'):
            return
            
        try:
            canvas = self.gui.ui_builder.panoramic_canvas
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # 获取全景图尺寸（从ViewManager或数据管理器）
            panoramic_image_size = self._get_panoramic_image_size()
            if not panoramic_image_size:
                return
                
            img_width, img_height = panoramic_image_size
            
            # 计算显示参数
            scale_w = (canvas_width - 20) / img_width
            scale_h = (canvas_height - 20) / img_height
            scale_factor = min(scale_w, scale_h)
            
            display_width = int(img_width * scale_factor)
            display_height = int(img_height * scale_factor)
            
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2
            
            # 使用HoleManager进行孔位检测
            hole_number = self._find_hole_by_coordinates(
                event.x, event.y, scale_factor, offset_x, offset_y
            )
            
            if hole_number:
                self.navigate_to_hole_simple(hole_number)
                if hasattr(self.gui.ui_builder, 'update_status'):
                    self.gui.ui_builder.update_status(f"点击定位到孔位 {hole_number}")
            else:
                if hasattr(self.gui.ui_builder, 'update_status'):
                    self.gui.ui_builder.update_status("点击位置未找到有效孔位")
                
        except Exception as e:
            self.gui.log_error(f"处理全景图点击失败: {e}", "NAV")
            
    def _find_hole_by_coordinates(self, x: int, y: int, scale_factor: float, offset_x: int, offset_y: int) -> Optional[int]:
        """根据坐标查找孔位"""
        if not self.current_panoramic_id or not hasattr(self.gui, 'hole_manager'):
            return None
            
        try:
            # 使用HoleManager的坐标计算方法，与原始代码保持一致
            return self.gui.hole_manager.find_hole_by_coordinates(
                x, y, scale_factor, offset_x, offset_y
            )
                
        except Exception as e:
            self.gui.log_error(f"坐标转换失败: {e}", "SLICE")
            
        return None
        
    def on_window_resize(self):
        """处理窗口大小变化事件 - 委托给ViewManager"""
        try:
            if hasattr(self.gui, 'view_manager'):
                self.gui.view_manager.on_window_resize()
        except Exception as e:
            self.gui.log_error(f"窗口调整大小处理失败: {e}", "NAV")
        
    def set_zoom(self, zoom_factor: float):
        """
        设置缩放比例
        
        Args:
            zoom_factor: 缩放因子
        """
        self.zoom_factor = max(0.1, min(3.0, zoom_factor))
        # 委托ViewManager处理显示更新
        if hasattr(self.gui, 'view_manager'):
            # ViewManager需要实现zoom相关方法
            pass
