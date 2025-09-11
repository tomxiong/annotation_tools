"""
事件处理模块
负责处理所有用户交互事件
从原panoramic_annotation_gui.py中拆分出来
"""

import tkinter as tk
from tkinter import messagebox


class EventHandlers:
    """事件处理管理类"""
    
    def __init__(self, parent_gui):
        """
        初始化事件处理管理器
        
        Args:
            parent_gui: 主GUI实例，用于访问必要的属性和方法
        """
        self.gui = parent_gui
        self.root = parent_gui.root

    def setup_bindings(self):
        """设置键盘快捷键和窗口事件"""
        try:
            # 窗口尺寸变化事件
            self.root.bind('<Configure>', self.on_window_resize)

            # 方向导航快捷键
            self.root.bind('<Key-1>', self.on_key_1)
            self.root.bind('<Key-2>', self.on_key_2)
            self.root.bind('<Key-3>', self.on_key_3)
            self.root.bind('<Left>', self.on_key_left)
            self.root.bind('<Right>', self.on_key_right)
            self.root.bind('<Up>', self.on_key_up)
            self.root.bind('<Down>', self.on_key_down)

            # 保存快捷键
            self.root.bind('<Control-s>', self.on_ctrl_s)
            
            # 让根窗口可以接收键盘事件
            self.root.focus_set()
            
            self.gui.log_info("事件绑定设置完成", "EVENT")
            
        except Exception as e:
            self.gui.log_error(f"事件绑定设置失败: {e}", "EVENT")
            raise

    def on_window_resize(self, event):
        """窗口大小变化事件处理"""
        if event.widget == self.root:
            # 记录窗口大小变化
            geometry = self.root.geometry()
            self.gui.log_debug(f"窗口大小变化: {geometry}", "EVENT")

    def on_key_1(self, event):
        """按键1事件处理"""
        try:
            self.gui.log_info("按键1被按下", "EVENT")
            # TODO: 实现按键1的具体功能
        except Exception as e:
            self.gui.log_error(f"按键1处理失败: {e}", "EVENT")

    def on_key_2(self, event):
        """按键2事件处理"""
        try:
            self.gui.log_info("按键2被按下", "EVENT")
            # TODO: 实现按键2的具体功能
        except Exception as e:
            self.gui.log_error(f"按键2处理失败: {e}", "EVENT")

    def on_key_3(self, event):
        """按键3事件处理"""
        try:
            self.gui.log_info("按键3被按下", "EVENT")
            # TODO: 实现按键3的具体功能
        except Exception as e:
            self.gui.log_error(f"按键3处理失败: {e}", "EVENT")

    def on_key_left(self, event):
        """左箭头键事件处理"""
        try:
            self.gui.log_info("左箭头键被按下", "EVENT")
            # TODO: 实现向左导航功能
        except Exception as e:
            self.gui.log_error(f"左箭头键处理失败: {e}", "EVENT")

    def on_key_right(self, event):
        """右箭头键事件处理"""
        try:
            self.gui.log_info("右箭头键被按下", "EVENT")
            # TODO: 实现向右导航功能
        except Exception as e:
            self.gui.log_error(f"右箭头键处理失败: {e}", "EVENT")

    def on_key_up(self, event):
        """上箭头键事件处理"""
        try:
            self.gui.log_info("上箭头键被按下", "EVENT")
            # TODO: 实现向上导航功能
        except Exception as e:
            self.gui.log_error(f"上箭头键处理失败: {e}", "EVENT")

    def on_key_down(self, event):
        """下箭头键事件处理"""
        try:
            self.gui.log_info("下箭头键被按下", "EVENT")
            # TODO: 实现向下导航功能
        except Exception as e:
            self.gui.log_error(f"下箭头键处理失败: {e}", "EVENT")

    def on_ctrl_s(self, event):
        """Ctrl+S保存快捷键事件处理"""
        try:
            self.gui.log_info("Ctrl+S被按下，执行保存", "EVENT")
            if hasattr(self.gui, 'data_operations'):
                self.gui.data_operations.save_annotations()
            else:
                self.gui.log_warning("数据操作模块未初始化", "EVENT")
        except Exception as e:
            self.gui.log_error(f"Ctrl+S处理失败: {e}", "EVENT")

    def on_mouse_click(self, event):
        """鼠标点击事件处理"""
        try:
            x, y = event.x, event.y
            self.gui.log_debug(f"鼠标点击位置: ({x}, {y})", "EVENT")
            # TODO: 实现鼠标点击的具体功能
        except Exception as e:
            self.gui.log_error(f"鼠标点击处理失败: {e}", "EVENT")

    def on_mouse_drag(self, event):
        """鼠标拖拽事件处理"""
        try:
            x, y = event.x, event.y
            self.gui.log_debug(f"鼠标拖拽位置: ({x}, {y})", "EVENT")
            # TODO: 实现鼠标拖拽的具体功能
        except Exception as e:
            self.gui.log_error(f"鼠标拖拽处理失败: {e}", "EVENT")
