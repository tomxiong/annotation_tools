"""
事件处理模块
处理键盘快捷键和界面事件
"""

import tkinter as tk
from typing import Optional


class EventHandlers:
    """事件处理器"""
    
    def __init__(self, gui_instance):
        """初始化事件处理器"""
        self.gui = gui_instance
    
    def setup_bindings(self):
        """设置键盘快捷键"""
        # 只在非输入控件获得焦点时响应快捷键
        self.gui.root.bind('<Key-1>', self.on_key_1)
        self.gui.root.bind('<Key-2>', self.on_key_2)
        self.gui.root.bind('<Key-3>', self.on_key_3)
        self.gui.root.bind('<Left>', self.on_key_left)
        self.gui.root.bind('<Right>', self.on_key_right)
        self.gui.root.bind('<Up>', self.on_key_up)
        self.gui.root.bind('<Down>', self.on_key_down)
        self.gui.root.bind('<space>', self.on_key_space)
        self.gui.root.bind('<Return>', self.on_key_return)
        self.gui.root.bind('<Escape>', self.on_key_escape)
        self.gui.root.bind('<Delete>', self.on_key_delete)
        
        # 设置焦点以接收键盘事件
        self.gui.root.focus_set()
    
    def is_input_widget_focused(self) -> bool:
        """检查当前焦点是否在输入控件上"""
        focused_widget = self.gui.root.focus_get()
        if focused_widget is None:
            return False
        
        # 检查是否是Entry或Text控件
        widget_class = focused_widget.__class__.__name__
        return widget_class in ['Entry', 'Text', 'Spinbox', 'Combobox']
    
    def on_key_1(self, event):
        """数字键1事件处理 - 设置为阴性"""
        if not self.is_input_widget_focused():
            self.set_growth_level('negative')
    
    def on_key_2(self, event):
        """数字键2事件处理 - 设置为弱生长"""
        if not self.is_input_widget_focused():
            self.set_growth_level('weak_growth')
    
    def on_key_3(self, event):
        """数字键3事件处理 - 设置为阳性"""
        if not self.is_input_widget_focused():
            self.set_growth_level('positive')
    
    def on_key_left(self, event):
        """左箭头键事件处理"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'navigation_controller'):
            self.gui.navigation_controller.go_left()
    
    def on_key_right(self, event):
        """右箭头键事件处理"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'navigation_controller'):
            self.gui.navigation_controller.go_right()
    
    def on_key_up(self, event):
        """上箭头键事件处理"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'navigation_controller'):
            self.gui.navigation_controller.go_up()
    
    def on_key_down(self, event):
        """下箭头键事件处理"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'navigation_controller'):
            self.gui.navigation_controller.go_down()
    
    def on_key_space(self, event):
        """空格键事件处理 - 保存当前标注"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'annotation_manager'):
            self.gui.annotation_manager.save_current_annotation()
    
    def on_key_return(self, event):
        """回车键事件处理 - 下一个孔位"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'navigation_controller'):
            self.gui.navigation_controller.go_next_hole()
    
    def on_key_escape(self, event):
        """ESC键事件处理 - 跳过当前"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'annotation_manager'):
            self.gui.annotation_manager.skip_current()
    
    def on_key_delete(self, event):
        """Delete键事件处理 - 清除当前标注"""
        if not self.is_input_widget_focused() and hasattr(self.gui, 'annotation_manager'):
            self.gui.annotation_manager.clear_current_annotation()
    
    def set_growth_level(self, level: str):
        """设置生长级别（快捷键使用）"""
        self.gui.current_growth_level.set(level)
        
        # 如果有增强标注面板，也更新它
        if hasattr(self.gui, 'enhanced_annotation_panel') and self.gui.enhanced_annotation_panel:
            try:
                # 获取当前特征组合
                current_combination = self.gui.enhanced_annotation_panel.get_current_feature_combination()
                
                # 更新生长级别
                from models.enhanced_annotation import GrowthLevel
                if level == 'negative':
                    current_combination.growth_level = GrowthLevel.NEGATIVE
                elif level == 'weak_growth':
                    current_combination.growth_level = GrowthLevel.WEAK_GROWTH
                elif level == 'positive':
                    current_combination.growth_level = GrowthLevel.POSITIVE
                
                # 设置回增强标注面板
                self.gui.enhanced_annotation_panel.set_feature_combination(current_combination)
                
            except Exception as e:
                print(f"更新增强标注面板失败: {e}")
        
        # 标记当前标注已修改
        self.gui.current_annotation_modified = True
        
        # 触发生长级别改变事件
        self.on_growth_level_change()
    
    def on_growth_level_change(self):
        """生长级别改变时的处理"""
        # 标记当前标注已修改
        self.gui.current_annotation_modified = True
        
        # 可以在这里添加自动保存逻辑或其他处理
        pass
    
    def on_enhanced_annotation_change(self, annotation_data=None):
        """增强标注变化回调"""
        # 标记当前标注已修改
        self.gui.current_annotation_modified = True
        # 可以在这里添加实时预览或验证逻辑
        pass
    
    def on_canvas_configure(self, event):
        """画布配置改变事件处理"""
        if hasattr(self.gui, 'image_display_controller'):
            self.gui.image_display_controller.resize_canvas(event)
    
    def on_window_closing(self):
        """窗口关闭事件处理"""
        # 检查是否有未保存的标注
        if self.gui.current_annotation_modified:
            from tkinter import messagebox
            result = messagebox.askyesnocancel(
                "确认退出", 
                "当前标注尚未保存，是否保存后退出？"
            )
            
            if result is True:  # 保存后退出
                try:
                    if hasattr(self.gui, 'annotation_manager'):
                        self.gui.annotation_manager.save_current_annotation_internal()
                    self.gui.root.destroy()
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败: {str(e)}")
                    return
            elif result is False:  # 不保存直接退出
                self.gui.root.destroy()
            # result is None 表示取消，不做任何操作
        else:
            # 没有未保存的标注，直接退出
            self.gui.root.destroy()
    
    def on_microbe_type_change(self, *args):
        """微生物类型改变事件处理"""
        # 标记当前标注已修改
        self.gui.current_annotation_modified = True
    
    def on_interference_factor_change(self, factor_name: str):
        """干扰因素改变事件处理"""
        # 标记当前标注已修改
        self.gui.current_annotation_modified = True
        
        # 可以在这里添加特定的干扰因素处理逻辑
        pass
    
    def on_auto_save_toggle(self):
        """自动保存开关切换事件处理"""
        if hasattr(self.gui, 'auto_save_enabled'):
            status = "启用" if self.gui.auto_save_enabled.get() else "禁用"
            self.gui.update_status(f"自动保存已{status}")
    
    def on_enhanced_mode_toggle(self):
        """增强模式开关切换事件处理"""
        if hasattr(self.gui, 'use_enhanced_mode'):
            # 切换标注面板显示
            if hasattr(self.gui, 'toggle_annotation_mode'):
                self.gui.toggle_annotation_mode()
            
            mode = "增强模式" if self.gui.use_enhanced_mode.get() else "基础模式"
            self.gui.update_status(f"已切换到{mode}")
    
    def on_subdirectory_mode_toggle(self):
        """子目录模式开关切换事件处理"""
        if hasattr(self.gui, 'use_subdirectory_mode'):
            mode = "子目录模式" if self.gui.use_subdirectory_mode.get() else "独立路径模式"
            self.gui.update_status(f"已切换到{mode}")
    
    def on_centered_navigation_toggle(self):
        """居中导航开关切换事件处理"""
        if hasattr(self.gui, 'use_centered_navigation'):
            mode = "居中导航" if self.gui.use_centered_navigation.get() else "传统导航"
            self.gui.update_status(f"已切换到{mode}")
    
    def bind_canvas_events(self):
        """绑定画布事件"""
        if hasattr(self.gui, 'panoramic_canvas'):
            self.gui.panoramic_canvas.bind('<Button-1>', self.on_panoramic_click)
            self.gui.panoramic_canvas.bind('<Configure>', self.on_canvas_configure)
        
        if hasattr(self.gui, 'slice_canvas'):
            self.gui.slice_canvas.bind('<Configure>', self.on_canvas_configure)
    
    def on_panoramic_click(self, event):
        """全景图点击事件处理"""
        if hasattr(self.gui, 'image_display_controller'):
            self.gui.image_display_controller.on_panoramic_click(event)