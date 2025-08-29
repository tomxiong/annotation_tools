def update_panoramic_list(self):
    """更新全景图下拉列表"""
    # 提取所有唯一的全景图ID
    self.panoramic_ids = []
    seen_ids = set()
    
    for file_info in self.slice_files:
        panoramic_id = file_info.get('panoramic_id')
        if panoramic_id and panoramic_id not in seen_ids:
            seen_ids.add(panoramic_id)
            self.panoramic_ids.append(panoramic_id)
    
    # 更新下拉列表
    self.panoramic_combobox['values'] = self.panoramic_ids
    
    # 设置当前选中项
    if self.current_panoramic_id and self.current_panoramic_id in self.panoramic_ids:
        self.panoramic_id_var.set(self.current_panoramic_id)
    elif self.panoramic_ids:
        self.panoramic_id_var.set(self.panoramic_ids[0])

def on_panoramic_selected(self, event=None):
    """处理全景图选择事件"""
    selected_id = self.panoramic_id_var.get()
    if selected_id and selected_id != self.current_panoramic_id:
        self.go_to_panoramic(selected_id)

def go_prev_panoramic(self):
    """导航到上一个全景图"""
    if not self.panoramic_ids:
        return
    
    # 找到当前全景图在列表中的索引
    try:
        current_index = self.panoramic_ids.index(self.current_panoramic_id)
    except ValueError:
        current_index = 0
    
    # 计算上一个全景图的索引
    prev_index = (current_index - 1) % len(self.panoramic_ids)
    prev_panoramic_id = self.panoramic_ids[prev_index]
    
    # 导航到上一个全景图
    self.go_to_panoramic(prev_panoramic_id)
    self.update_status(f"已导航到上一个全景图: {prev_panoramic_id}")

def go_next_panoramic(self):
    """导航到下一个全景图"""
    if not self.panoramic_ids:
        return
    
    # 找到当前全景图在列表中的索引
    try:
        current_index = self.panoramic_ids.index(self.current_panoramic_id)
    except ValueError:
        current_index = 0
    
    # 计算下一个全景图的索引
    next_index = (current_index + 1) % len(self.panoramic_ids)
    next_panoramic_id = self.panoramic_ids[next_index]
    
    # 导航到下一个全景图
    self.go_to_panoramic(next_panoramic_id)
    self.update_status(f"已导航到下一个全景图: {next_panoramic_id}")

def go_to_panoramic(self, panoramic_id):
    """导航到指定的全景图"""
    if not panoramic_id or panoramic_id == self.current_panoramic_id:
        return
    
    # 自动保存当前标注
    self.auto_save_current_annotation()
    
    # 查找目标全景图的第一个孔位
    first_index = None
    for i, file_info in enumerate(self.slice_files):
        if file_info.get('panoramic_id') == panoramic_id:
            first_index = i
            break
    
    if first_index is not None:
        # 切换到目标全景图的第一个孔位
        self.current_slice_index = first_index
        self.load_current_slice()
        self.update_progress()
        
        # 更新下拉列表选中项
        self.panoramic_id_var.set(panoramic_id)
    else:
        messagebox.showwarning("警告", f"未找到全景图 {panoramic_id} 的切片文件")