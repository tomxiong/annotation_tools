"""
事件分发器模块
负责处理鼠标事件、键盘事件、窗口事件的分发和处理
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Any


class EventDispatcher:
    """事件分发器 - 负责所有事件的处理和分发"""
    
    def __init__(self, parent_gui):
        """
        初始化事件分发器
        
        Args:
            parent_gui: 主GUI实例
        """
        self.gui = parent_gui
        self.root = parent_gui.root
        self.event_handlers = {}
        
    def setup_bindings(self):
        """设置所有事件绑定"""
        self.setup_keyboard_bindings()
        self.setup_mouse_bindings()
        self.setup_window_bindings()
        
    def setup_keyboard_bindings(self):
        """设置键盘事件绑定"""
        # 数字键 - 生长级别快捷设置
        self.root.bind('<Key-1>', self.on_key_1)
        self.root.bind('<Key-2>', self.on_key_2)  
        self.root.bind('<Key-3>', self.on_key_3)
        
        # 方向键 - 孔位导航
        self.root.bind('<Left>', self.on_key_left)
        self.root.bind('<Right>', self.on_key_right)
        self.root.bind('<Up>', self.on_key_up)
        self.root.bind('<Down>', self.on_key_down)
        
        # 导航键
        self.root.bind('<Home>', self.on_key_home)      # 第一个孔位
        self.root.bind('<End>', self.on_key_end)        # 最后一个孔位
        self.root.bind('<Prior>', self.on_key_page_up)  # 上一个全景图
        self.root.bind('<Next>', self.on_key_page_down) # 下一个全景图
        
        # 功能键
        self.root.bind('<space>', self.on_key_space)    # 保存标注
        self.root.bind('<Return>', self.on_key_return)  # 下一个孔位
        self.root.bind('<F1>', self.on_key_f1)          # 帮助
        
        # 组合键
        self.root.bind('<Control-s>', self.on_ctrl_s)   # 保存
        self.root.bind('<Control-o>', self.on_ctrl_o)   # 打开
        self.root.bind('<Control-l>', self.on_ctrl_l)   # 日志分析
        
        # 设置焦点以接收键盘事件
        self.root.focus_set()
        
    def setup_mouse_bindings(self):
        """设置鼠标事件绑定"""
        # 全景图点击事件将在UI构建完成后绑定
        pass
        
    def setup_window_bindings(self):
        """设置窗口事件绑定"""
        self.root.bind('<Configure>', self.on_window_resize)
        
    def bind_panoramic_click(self, canvas):
        """绑定全景图点击事件"""
        canvas.bind('<Button-1>', self.on_panoramic_click)
        
    def bind_slice_click(self, canvas):
        """绑定切片点击事件"""
        canvas.bind('<Button-1>', self.on_slice_click)
        
    # === 键盘事件处理 ===
    
    def on_key_1(self, event):
        """数字键1 - 设置为阴性"""
        if not self._is_input_focused():
            self.gui.set_growth_level('negative')
            self.gui.log_info("快捷键1: 设置生长级别为阴性", "EVENT")
            
    def on_key_2(self, event):
        """数字键2 - 设置为弱生长"""
        if not self._is_input_focused():
            self.gui.set_growth_level('weak_growth')
            self.gui.log_info("快捷键2: 设置生长级别为弱生长", "EVENT")
            
    def on_key_3(self, event):
        """数字键3 - 设置为阳性"""
        if not self._is_input_focused():
            self.gui.set_growth_level('positive')
            self.gui.log_info("快捷键3: 设置生长级别为阳性", "EVENT")
            
    def on_key_left(self, event):
        """左箭头键 - 向左导航"""
        if not self._is_input_focused():
            self.gui.go_left()
            self.gui.log_info("快捷键←: 向左导航", "EVENT")
            
    def on_key_right(self, event):
        """右箭头键 - 向右导航"""
        if not self._is_input_focused():
            self.gui.go_right()
            self.gui.log_info("快捷键→: 向右导航", "EVENT")
            
    def on_key_up(self, event):
        """上箭头键 - 向上导航"""
        if not self._is_input_focused():
            self.gui.go_up()
            self.gui.log_info("快捷键↑: 向上导航", "EVENT")
            
    def on_key_down(self, event):
        """下箭头键 - 向下导航"""
        if not self._is_input_focused():
            self.gui.go_down()
            self.gui.log_info("快捷键↓: 向下导航", "EVENT")
            
    def on_key_home(self, event):
        """Home键 - 跳转到第一个孔位"""
        if not self._is_input_focused():
            self.gui.go_first_hole()
            self.gui.log_info("快捷键Home: 跳转到第一个孔位", "EVENT")
            
    def on_key_end(self, event):
        """End键 - 跳转到最后一个孔位"""
        if not self._is_input_focused():
            self.gui.go_last_hole()
            self.gui.log_info("快捷键End: 跳转到最后一个孔位", "EVENT")
            
    def on_key_page_up(self, event):
        """PageUp键 - 上一个全景图"""
        if not self._is_input_focused():
            self.gui.go_prev_panoramic()
            self.gui.log_info("快捷键PageUp: 上一个全景图", "EVENT")
            
    def on_key_page_down(self, event):
        """PageDown键 - 下一个全景图"""
        if not self._is_input_focused():
            self.gui.go_next_panoramic()
            self.gui.log_info("快捷键PageDown: 下一个全景图", "EVENT")
            
    def on_key_space(self, event):
        """空格键 - 保存当前标注"""
        if not self._is_input_focused():
            self.gui.save_current_annotation()
            self.gui.log_info("快捷键Space: 保存当前标注", "EVENT")
            
    def on_key_return(self, event):
        """回车键 - 下一个孔位"""
        if not self._is_input_focused():
            self.gui.go_next_hole()
            self.gui.log_info("快捷键Enter: 下一个孔位", "EVENT")
            
    def on_key_f1(self, event):
        """F1键 - 显示帮助"""
        self.gui.show_help_dialog()
        self.gui.log_info("快捷键F1: 显示帮助", "EVENT")
        
    def on_ctrl_s(self, event):
        """Ctrl+S - 保存"""
        self.gui.save_current_annotation()
        self.gui.log_info("快捷键Ctrl+S: 保存", "EVENT")
        
    def on_ctrl_o(self, event):
        """Ctrl+O - 打开目录"""
        self.gui.open_directory()
        self.gui.log_info("快捷键Ctrl+O: 打开目录", "EVENT")
        
    def on_ctrl_l(self, event):
        """Ctrl+L - 日志分析"""
        self.gui.analyze_window_resize_log()
        self.gui.log_info("快捷键Ctrl+L: 日志分析", "EVENT")
        
    # === 鼠标事件处理 ===
    
    def on_panoramic_click(self, event):
        """全景图点击事件处理"""
        try:
            # 委托给切片控制器处理孔位定位
            if hasattr(self.gui, 'slice_controller'):
                self.gui.slice_controller.handle_panoramic_click(event)
            self.gui.log_info(f"全景图点击: ({event.x}, {event.y})", "EVENT")
        except Exception as e:
            self.gui.log_error(f"全景图点击处理失败: {e}", "EVENT")
            
    def on_slice_click(self, event):
        """切片点击事件处理"""
        try:
            # 可以在这里添加切片点击相关逻辑
            self.gui.log_info(f"切片点击: ({event.x}, {event.y})", "EVENT")
        except Exception as e:
            self.gui.log_error(f"切片点击处理失败: {e}", "EVENT")
            
    # === 窗口事件处理 ===
    
    def on_window_resize(self, event):
        """窗口大小变化事件处理"""
        try:
            if event.widget == self.root:
                geometry = self.root.geometry()
                self.gui.log_debug(f"窗口大小变化: {geometry}", "EVENT")
                
                # 通知其他模块更新显示
                if hasattr(self.gui, 'slice_controller'):
                    self.gui.slice_controller.on_window_resize()
                    
        except Exception as e:
            self.gui.log_error(f"窗口大小变化处理失败: {e}", "EVENT")
            
    # === 工具方法 ===
    
    def _is_input_focused(self):
        """检查当前焦点是否在输入控件上"""
        try:
            focused_widget = self.root.focus_get()
            if focused_widget is None:
                return False
                
            # 检查是否为输入类控件
            input_types = (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox)
            return isinstance(focused_widget, input_types)
            
        except Exception:
            return False
            
    def register_event_handler(self, event_name: str, handler: Callable):
        """注册事件处理器"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
        
    def unregister_event_handler(self, event_name: str, handler: Callable):
        """注销事件处理器"""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                pass
                
    def dispatch_event(self, event_name: str, *args, **kwargs):
        """分发自定义事件"""
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    self.gui.log_error(f"事件处理器执行失败 {event_name}: {e}", "EVENT")
