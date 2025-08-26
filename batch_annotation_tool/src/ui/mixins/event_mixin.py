"""
事件处理功能Mixin
包含所有事件处理相关的方法
"""

class EventMixin:
    """事件处理功能混入类"""
    
    def setup_keyboard_bindings(self):
        """设置键盘快捷键"""
        # 绑定键盘事件
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()  # 确保窗口可以接收键盘事件
        
        # 方向键导航
        self.root.bind('<Up>', lambda e: self.go_up())
        self.root.bind('<Down>', lambda e: self.go_down())
        self.root.bind('<Left>', lambda e: self.go_left())
        self.root.bind('<Right>', lambda e: self.go_right())
        
        # 切片导航
        self.root.bind('<Prior>', lambda e: self.go_prev_hole())  # Page Up
        self.root.bind('<Next>', lambda e: self.go_next_hole())   # Page Down
        self.root.bind('<Home>', lambda e: self.go_first_hole())
        self.root.bind('<End>', lambda e: self.go_last_hole())
        
        # 全景图导航
        self.root.bind('<Control-Left>', lambda e: self.go_prev_panoramic())
        self.root.bind('<Control-Right>', lambda e: self.go_next_panoramic())
        
        # 功能快捷键
        self.root.bind('<Control-s>', lambda e: self.save_current_annotation())
        self.root.bind('<Control-o>', lambda e: self.load_slice_directory())
        self.root.bind('<Delete>', lambda e: self.clear_current_annotation())
        self.root.bind('<F5>', lambda e: self.load_current_slice())
    
    def on_key_press(self, event):
        """处理键盘按键事件"""
        key = event.keysym
        
        # 数字键快速跳转到孔位
        if key.isdigit():
            if hasattr(self, 'hole_entry'):
                # 将数字添加到孔位输入框
                current_text = self.hole_entry.get()
                if len(current_text) < 3:  # 限制最多3位数
                    self.hole_entry.delete(0, 'end')
                    self.hole_entry.insert(0, current_text + key)
        
        # Enter键确认孔位跳转
        elif key == 'Return':
            if hasattr(self, 'hole_entry'):
                hole_number = self.hole_entry.get()
                if hole_number:
                    self.go_to_hole(hole_number)
        
        # Escape键清空孔位输入框
        elif key == 'Escape':
            if hasattr(self, 'hole_entry'):
                self.hole_entry.delete(0, 'end')
    
    def on_mouse_wheel(self, event):
        """处理鼠标滚轮事件"""
        # 滚轮向上滚动，切换到上一个切片
        if event.delta > 0:
            self.go_prev_hole()
        # 滚轮向下滚动，切换到下一个切片
        else:
            self.go_next_hole()
    
    def on_window_close(self):
        """处理窗口关闭事件"""
        try:
            # 保存当前标注
            if hasattr(self, 'save_current_annotation_internal'):
                self.save_current_annotation_internal()
            
            # 保存窗口状态
            self.save_window_state()
            
            # 销毁窗口
            self.root.destroy()
            
        except Exception as e:
            print(f"关闭窗口时发生错误: {e}")
            self.root.destroy()
    
    def on_window_resize(self, event):
        """处理窗口大小改变事件"""
        # 只处理主窗口的大小改变
        if event.widget == self.root:
            # 重新调整图像显示
            if hasattr(self, 'canvas'):
                self.root.after(100, self.on_canvas_resize, event)
    
    def save_window_state(self):
        """保存窗口状态"""
        try:
            # 获取窗口位置和大小
            geometry = self.root.geometry()
            
            # 保存到配置文件
            if hasattr(self, 'config_service'):
                self.config_service.save_window_state({
                    'geometry': geometry,
                    'subdirectory_mode': self.use_subdirectory_mode.get(),
                    'centered_navigation': self.use_centered_navigation.get()
                })
                
        except Exception as e:
            print(f"保存窗口状态失败: {e}")
    
    def load_window_state(self):
        """加载窗口状态"""
        try:
            if hasattr(self, 'config_service') and hasattr(self.config_service, 'load_window_state'):
                state = self.config_service.load_window_state()
                
                if state:
                    # 恢复窗口位置和大小
                    if 'geometry' in state:
                        self.root.geometry(state['geometry'])
                    
                    # 恢复选项状态
                    if 'subdirectory_mode' in state:
                        self.use_subdirectory_mode.set(state['subdirectory_mode'])
                    
                    if 'centered_navigation' in state:
                        self.use_centered_navigation.set(state['centered_navigation'])
            else:
                print("ConfigFileService不支持窗口状态保存功能")
                        
        except Exception as e:
            print(f"加载窗口状态失败: {e}")
    
    def on_annotation_change(self, feature_combination=None):
        """处理标注改变事件"""
        if feature_combination:
            # 处理特征组合数据
            pass
        # 标注发生改变时的处理（如果状态栏存在）
        if hasattr(self, 'status_bar') and self.status_bar:
            self.update_status("标注已修改")
    
    def on_directory_change(self):
        """处理目录改变事件"""
        # 目录改变时重新扫描文件
        if hasattr(self, 'slice_directory') and self.slice_directory:
            self.scan_slice_files()
    
    def on_panoramic_change(self):
        """处理全景图改变事件"""
        # 全景图改变时更新相关显示
        self.update_panoramic_list()