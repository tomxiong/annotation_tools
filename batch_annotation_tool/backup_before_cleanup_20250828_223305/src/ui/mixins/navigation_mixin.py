"""
导航功能Mixin
包含所有导航相关的方法
"""

class NavigationMixin:
    """导航功能混入类"""
    
    def go_up(self):
        """向上导航"""
        if not self.slice_files:
            return
        
        current_file = self.slice_files[self.current_slice_index]
        current_hole = current_file['hole_number']
        
        # 计算目标孔位
        if self.use_centered_navigation.get():
            # 居中导航模式：移动到上方的中间位置
            target_hole = self.get_middle_hole_in_direction(current_hole, 'up')
        else:
            # 普通模式：向上移动一行
            target_hole = current_hole - 12
        
        if target_hole >= 1:
            self.go_to_hole(target_hole)
    
    def go_down(self):
        """向下导航"""
        if not self.slice_files:
            return
        
        current_file = self.slice_files[self.current_slice_index]
        current_hole = current_file['hole_number']
        
        # 计算目标孔位
        if self.use_centered_navigation.get():
            # 居中导航模式：移动到下方的中间位置
            target_hole = self.get_middle_hole_in_direction(current_hole, 'down')
        else:
            # 普通模式：向下移动一行
            target_hole = current_hole + 12
        
        if target_hole <= 120:
            self.go_to_hole(target_hole)
    
    def go_left(self):
        """向左导航"""
        if not self.slice_files:
            return
        
        current_file = self.slice_files[self.current_slice_index]
        current_hole = current_file['hole_number']
        
        # 计算目标孔位
        if self.use_centered_navigation.get():
            # 居中导航模式：移动到左侧的中间位置
            target_hole = self.get_middle_hole_in_direction(current_hole, 'left')
        else:
            # 普通模式：向左移动一列
            target_hole = current_hole - 1
        
        # 检查是否在同一行
        current_row = (current_hole - 1) // 12
        target_row = (target_hole - 1) // 12
        
        if target_hole >= 1 and current_row == target_row:
            self.go_to_hole(target_hole)
    
    def go_right(self):
        """向右导航"""
        if not self.slice_files:
            return
        
        current_file = self.slice_files[self.current_slice_index]
        current_hole = current_file['hole_number']
        
        # 计算目标孔位
        if self.use_centered_navigation.get():
            # 居中导航模式：移动到右侧的中间位置
            target_hole = self.get_middle_hole_in_direction(current_hole, 'right')
        else:
            # 普通模式：向右移动一列
            target_hole = current_hole + 1
        
        # 检查是否在同一行
        current_row = (current_hole - 1) // 12
        target_row = (target_hole - 1) // 12
        
        if target_hole <= 120 and current_row == target_row:
            self.go_to_hole(target_hole)
    
    def get_middle_hole_in_direction(self, current_hole, direction):
        """计算指定方向上的中间孔位"""
        current_row = (current_hole - 1) // 12
        current_col = (current_hole - 1) % 12
        
        if direction == 'up':
            if current_row > 0:
                # 移动到上一行的中间列（第6列，索引5）
                target_row = current_row - 1
                target_col = 5  # 中间列
                return target_row * 12 + target_col + 1
        elif direction == 'down':
            if current_row < 9:
                # 移动到下一行的中间列（第6列，索引5）
                target_row = current_row + 1
                target_col = 5  # 中间列
                return target_row * 12 + target_col + 1
        elif direction == 'left':
            if current_col > 0:
                # 移动到左一列的中间行（第5行，索引4）
                target_row = 4  # 中间行
                target_col = current_col - 1
                return target_row * 12 + target_col + 1
        elif direction == 'right':
            if current_col < 11:
                # 移动到右一列的中间行（第5行，索引4）
                target_row = 4  # 中间行
                target_col = current_col + 1
                return target_row * 12 + target_col + 1
        
        return current_hole
    
    def navigate_to_middle(self, direction):
        """导航到指定方向的中间位置"""
        if not self.slice_files:
            return
        
        current_file = self.slice_files[self.current_slice_index]
        current_hole = current_file['hole_number']
        target_hole = self.get_middle_hole_in_direction(current_hole, direction)
        
        if target_hole != current_hole:
            self.go_to_hole(target_hole)
    
    def go_to_hole(self, hole_number):
        """跳转到指定孔位"""
        try:
            hole_number = int(hole_number)
            if not (1 <= hole_number <= 120):
                self.update_status("孔位编号必须在1-120之间")
                return
            
            # 查找对应的切片文件
            for i, file_info in enumerate(self.slice_files):
                if (file_info['panoramic_id'] == self.current_panoramic_id and 
                    file_info['hole_number'] == hole_number):
                    self.current_slice_index = i
                    self.load_current_slice()
                    return
            
            self.update_status(f"未找到孔位 {hole_number} 的切片文件")
        except ValueError:
            self.update_status("请输入有效的孔位编号")
    
    def go_first_hole(self):
        """跳转到第一个孔位"""
        if not self.slice_files:
            return
        
        # 找到第一个全景图的第一个孔位
        first_panoramic_id = None
        for i, file_info in enumerate(self.slice_files):
            if first_panoramic_id is None:
                first_panoramic_id = file_info['panoramic_id']
                self.current_slice_index = i
                break
            elif file_info['panoramic_id'] != first_panoramic_id:
                break
        
        self.load_current_slice()
    
    def go_last_hole(self):
        """跳转到最后一个孔位"""
        if not self.slice_files:
            return
        
        # 找到最后一个全景图的最后一个孔位
        last_panoramic_id = None
        last_index = 0
        
        for i, file_info in enumerate(self.slice_files):
            if file_info['panoramic_id'] != last_panoramic_id:
                last_panoramic_id = file_info['panoramic_id']
                last_index = i
        
        # 找到该全景图的最后一个孔位
        for i in range(last_index, len(self.slice_files)):
            if self.slice_files[i]['panoramic_id'] == last_panoramic_id:
                self.current_slice_index = i
        
        self.load_current_slice()
    
    def go_prev_hole(self):
        """跳转到上一个孔位"""
        if self.current_slice_index > 0:
            self.current_slice_index -= 1
            self.load_current_slice()
    
    def go_next_hole(self):
        """跳转到下一个孔位"""
        if self.current_slice_index < len(self.slice_files) - 1:
            self.current_slice_index += 1
            self.load_current_slice()
    
    def update_panoramic_list(self):
        """更新全景图列表"""
        if not self.slice_files:
            return
        
        # 从切片文件中提取唯一的全景图ID
        panoramic_ids = set()
        for slice_file in self.slice_files:
            panoramic_ids.add(slice_file['panoramic_id'])
        
        self.panoramic_ids = sorted(list(panoramic_ids))
        
        if hasattr(self, 'panoramic_combobox'):
            self.panoramic_combobox['values'] = self.panoramic_ids
            
            # 设置当前选中项
            if self.current_panoramic_id in self.panoramic_ids:
                self.panoramic_combobox.set(self.current_panoramic_id)
            elif self.panoramic_ids:
                self.panoramic_combobox.set(self.panoramic_ids[0])
    
    def on_panoramic_selected(self, event=None):
        """处理全景图选择事件"""
        selected_panoramic_id = self.panoramic_id_var.get()
        if selected_panoramic_id and selected_panoramic_id != self.current_panoramic_id:
            self.go_to_panoramic(selected_panoramic_id)
    
    def go_prev_panoramic(self):
        """导航到上一个全景图"""
        if not self.panoramic_ids:
            return
        
        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)
        
        # 计算上一个全景图的索引（循环）
        prev_index = (current_index - 1) % len(self.panoramic_ids)
        prev_panoramic_id = self.panoramic_ids[prev_index]
        
        # 导航到上一个全景图
        self.go_to_panoramic(prev_panoramic_id)
        self.update_status(f"已导航到上一个全景图: {prev_panoramic_id}")
    
    def go_next_panoramic(self):
        """导航到下一个全景图"""
        if not self.panoramic_ids:
            return
        
        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)
        
        # 计算下一个全景图的索引（循环）
        next_index = (current_index + 1) % len(self.panoramic_ids)
        next_panoramic_id = self.panoramic_ids[next_index]
        
        # 导航到下一个全景图
        self.go_to_panoramic(next_panoramic_id)
        self.update_status(f"已导航到下一个全景图: {next_panoramic_id}")
    
    def go_to_panoramic(self, panoramic_id):
        """导航到指定的全景图"""
        if not panoramic_id or panoramic_id == self.current_panoramic_id:
            return
        
        # 保存当前标注
        if hasattr(self, 'save_current_annotation_internal'):
            self.save_current_annotation_internal()
        
        # 查找目标全景图的第一个孔位
        first_index = None
        for i, file_info in enumerate(self.slice_files):
            if file_info.get('panoramic_id') == panoramic_id:
                first_index = i
                break
        
        if first_index is not None:
            self.current_slice_index = first_index
            self.load_current_slice()
            
            # 更新下拉列表选中项
            self.panoramic_id_var.set(panoramic_id)
        else:
            self.current_slice_index = 0
            messagebox.showwarning("警告", f"未找到全景图 {panoramic_id} 的切片文件")