"""
导航控制器模块
负责处理全景图导航、方向导航和序列导航
"""

import tkinter as tk
from tkinter import messagebox


class NavigationController:
    """导航控制器类"""
    
    def __init__(self, gui):
        """初始化导航控制器"""
        self.gui = gui
        self.panoramic_ids = []  # 全景图ID列表
        self.current_panoramic_index = 0  # 当前全景图索引
    
    def update_panoramic_list(self):
        """更新全景图列表"""
        try:
            # 从切片文件中提取唯一的全景图ID
            panoramic_ids = set()
            for slice_file in self.gui.slice_files:
                panoramic_ids.add(slice_file['panoramic_id'])
            
            self.panoramic_ids = sorted(list(panoramic_ids))
            
            # 更新下拉列表
            if hasattr(self.gui, 'panoramic_combobox'):
                self.gui.panoramic_combobox['values'] = self.panoramic_ids
                
                # 设置当前选中项
                if self.gui.current_panoramic_id in self.panoramic_ids:
                    self.current_panoramic_index = self.panoramic_ids.index(self.gui.current_panoramic_id)
                    self.gui.panoramic_combobox.set(self.gui.current_panoramic_id)
                elif self.panoramic_ids:
                    self.current_panoramic_index = 0
                    self.gui.panoramic_combobox.set(self.panoramic_ids[0])
            
            
        except Exception as e:
            print(f"更新全景图列表失败: {e}")
    
    def on_panoramic_selected(self, event=None):
        """处理全景图选择事件"""
        if hasattr(self.gui, 'panoramic_id_var'):
            selected_panoramic_id = self.gui.panoramic_id_var.get()
            if selected_panoramic_id and selected_panoramic_id != self.gui.current_panoramic_id:
                self.go_to_panoramic(selected_panoramic_id)
    
    def go_prev_panoramic(self):
        """导航到上一个全景图"""
        if not self.panoramic_ids:
            return
        
        # 保存当前标注
        self.gui.annotation_manager.save_current_annotation()
        
        # 计算上一个全景图索引（循环）
        self.current_panoramic_index = (self.current_panoramic_index - 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[self.current_panoramic_index]
        
        # 导航到目标全景图
        self.go_to_panoramic(target_panoramic_id)
    
    def go_next_panoramic(self):
        """导航到下一个全景图"""
        if not self.panoramic_ids:
            return
        
        # 保存当前标注
        self.gui.annotation_manager.save_current_annotation()
        
        # 计算下一个全景图索引（循环）
        self.current_panoramic_index = (self.current_panoramic_index + 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[self.current_panoramic_index]
        
        # 导航到目标全景图
        self.go_to_panoramic(target_panoramic_id)
    
    def go_to_panoramic(self, panoramic_id):
        """导航到指定全景图"""
        if panoramic_id not in self.panoramic_ids:
            messagebox.showerror("错误", f"全景图 {panoramic_id} 不存在")
            return
        
        # 保存当前标注
        self.gui.annotation_manager.save_current_annotation()
        
        # 查找目标全景图的第一个孔位
        target_slice_index = None
        for i, slice_file in enumerate(self.gui.slice_files):
            if slice_file['panoramic_id'] == panoramic_id:
                target_slice_index = i
                break
        
        if target_slice_index is not None:
            # 更新当前索引和全景图ID
            self.gui.current_slice_index = target_slice_index
            self.gui.current_panoramic_id = panoramic_id
            self.current_panoramic_index = self.panoramic_ids.index(panoramic_id)
            
            # 更新下拉列表选中项
            if hasattr(self.gui, 'panoramic_combobox'):
                self.gui.panoramic_combobox.set(panoramic_id)
            
            # 加载新的切片
            self.gui.load_current_slice()
            self.gui.update_progress()
            self.gui.update_statistics()
            
            self.gui.update_status(f"已切换到全景图: {panoramic_id}")
        else:
            messagebox.showerror("错误", f"未找到全景图 {panoramic_id} 的切片文件")
    
    def go_up(self):
        """向上导航"""
        if self.gui.use_centered_navigation.get():
            self.navigate_to_middle('up')
        else:
            self._navigate_direction('up')
    
    def go_down(self):
        """向下导航"""
        if self.gui.use_centered_navigation.get():
            self.navigate_to_middle('down')
        else:
            self._navigate_direction('down')
    
    def go_left(self):
        """向左导航"""
        if self.gui.use_centered_navigation.get():
            self.navigate_to_middle('left')
        else:
            self._navigate_direction('left')
    
    def go_right(self):
        """向右导航"""
        if self.gui.use_centered_navigation.get():
            self.navigate_to_middle('right')
        else:
            self._navigate_direction('right')
    
    def _navigate_direction(self, direction):
        """基础方向导航"""
        current_row, current_col = self._get_current_position()
        
        if direction == 'up' and current_row > 1:
            target_hole = self._get_hole_number(current_row - 1, current_col)
        elif direction == 'down' and current_row < 10:
            target_hole = self._get_hole_number(current_row + 1, current_col)
        elif direction == 'left' and current_col > 1:
            target_hole = self._get_hole_number(current_row, current_col - 1)
        elif direction == 'right' and current_col < 12:
            target_hole = self._get_hole_number(current_row, current_col + 1)
        else:
            return  # 边界情况，不导航
        
        self.go_to_hole(target_hole)
    
    def navigate_to_middle(self, direction):
        """导航到指定方向的中间位置"""
        current_row, current_col = self._get_current_position()
        
        if direction == 'up':
            # 向上导航到第1行的中间列（第6列）
            target_hole = self._get_hole_number(1, 6)
        elif direction == 'down':
            # 向下导航到第10行的中间列（第6列）
            target_hole = self._get_hole_number(10, 6)
        elif direction == 'left':
            # 向左导航到第1列的中间行（第5行）
            target_hole = self._get_hole_number(5, 1)
        elif direction == 'right':
            # 向右导航到第12列的中间行（第5行）
            target_hole = self._get_hole_number(5, 12)
        else:
            return
        
        self.go_to_hole(target_hole)
    
    def _get_current_position(self):
        """获取当前孔位的行列位置"""
        hole_number = self.gui.current_hole_number
        row = ((hole_number - 1) // 12) + 1
        col = ((hole_number - 1) % 12) + 1
        return row, col
    
    def _get_hole_number(self, row, col):
        """根据行列位置计算孔位编号"""
        return (row - 1) * 12 + col
    
    def go_first_hole(self):
        """导航到首个孔位"""
        if self.gui.slice_files:
            # 找到当前全景图的第一个孔位
            for i, slice_file in enumerate(self.gui.slice_files):
                if slice_file['panoramic_id'] == self.gui.current_panoramic_id:
                    self.gui.current_slice_index = i
                    self.gui.load_current_slice()
                    self.gui.update_progress()
                    break
    
    def go_last_hole(self):
        """导航到最后孔位"""
        if self.gui.slice_files:
            # 找到当前全景图的最后一个孔位
            last_index = None
            for i, slice_file in enumerate(self.gui.slice_files):
                if slice_file['panoramic_id'] == self.gui.current_panoramic_id:
                    last_index = i
            
            if last_index is not None:
                self.gui.current_slice_index = last_index
                self.gui.load_current_slice()
                self.gui.update_progress()
    
    def go_prev_hole(self):
        """导航到上一个孔位"""
        if self.gui.current_slice_index > 0:
            self.gui.current_slice_index -= 1
            self.gui.load_current_slice()
            self.gui.update_progress()
    
    def go_next_hole(self):
        """导航到下一个孔位"""
        if self.gui.current_slice_index < len(self.gui.slice_files) - 1:
            self.gui.current_slice_index += 1
            self.gui.load_current_slice()
            self.gui.update_progress()
    
    def go_to_hole(self, hole_number=None):
        """导航到指定孔位"""
        if hole_number is None:
            # 从输入框获取孔位编号
            try:
                hole_number = int(self.gui.hole_number_var.get())
            except ValueError:
                messagebox.showerror("错误", "请输入有效的孔位编号")
                return
        
        # 查找指定孔位的切片索引
        target_index = None
        for i, slice_file in enumerate(self.gui.slice_files):
            if (slice_file['panoramic_id'] == self.gui.current_panoramic_id and 
                slice_file['hole_number'] == hole_number):
                target_index = i
                break
                
        if target_index is not None:
            self.gui.current_slice_index = target_index
            self.gui.load_current_slice()
            self.gui.update_progress()
        
    def navigate_to_hole(self, hole_number):
        """导航到指定孔位（别名方法）"""
        self.go_to_hole(hole_number)
