"""
导航面板组件

提供图像导航和视图控制功能
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, List
import logging

from src.ui.utils.base_components import BaseFrameView, ComponentMixin
from src.ui.utils.event_bus import EventBus, EventType, Event, get_event_bus
from src.ui.models.ui_state import UIStateManager, get_ui_state_manager, NavigationMode

logger = logging.getLogger(__name__)


class NavigationPanel(BaseFrameView, ComponentMixin):
    """导航面板组件"""
    
    def __init__(self, parent: tk.Widget, controller=None):
        super().__init__(parent, controller)
        self.image_canvas = None
        
        # 控制组件
        self.zoom_var = tk.DoubleVar(value=100.0)
        self.nav_mode_var = tk.StringVar(value=NavigationMode.CENTERED.value)
        
        # 图像列表
        self.image_listbox: Optional[tk.Listbox] = None
        self.current_images: List[str] = []
        
        # 绑定事件总线
        self.event_bus = get_event_bus()
        self.ui_state_manager = get_ui_state_manager()
        
        # 订阅事件
        self.event_bus.subscribe(EventType.IMAGE_LOADED, self._on_image_loaded)
    
    def build_ui(self) -> tk.Widget:
        """构建UI界面"""
        self.widget = ttk.Frame(self.parent)
        
        # 创建主框架
        main_frame = ttk.Frame(self.widget, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建图像列表部分
        self._create_image_list(main_frame)
        
        # 创建分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # 创建导航控制部分
        self._create_navigation_controls(main_frame)
        
        # 创建分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # 创建视图控制部分
        self._create_view_controls(main_frame)
        
        return self.widget
    
    def _create_image_list(self, parent):
        """创建图像列表"""
        # 标题
        title_label = ttk.Label(parent, text="图像列表", font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 列表框架
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 列表框
        self.image_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=8,
            selectmode=tk.SINGLE
        )
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.image_listbox.yview)
        
        # 绑定选择事件
        self.image_listbox.bind('<<ListboxSelect>>', self._on_image_selected)
        
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 添加图像按钮
        add_button = ttk.Button(
            button_frame,
            text="添加图像",
            command=self._add_images
        )
        add_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 移除图像按钮
        remove_button = ttk.Button(
            button_frame,
            text="移除图像",
            command=self._remove_image
        )
        remove_button.pack(side=tk.LEFT)
    
    def _create_navigation_controls(self, parent):
        """创建导航控制"""
        # 标题
        title_label = ttk.Label(parent, text="导航控制", font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 导航模式
        mode_frame = ttk.Frame(parent)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mode_frame, text="导航模式:").pack(side=tk.LEFT)
        
        centered_radio = ttk.Radiobutton(
            mode_frame,
            text="居中导航",
            variable=self.nav_mode_var,
            value=NavigationMode.CENTERED.value,
            command=self._on_nav_mode_changed
        )
        centered_radio.pack(side=tk.LEFT, padx=(10, 5))
        
        traditional_radio = ttk.Radiobutton(
            mode_frame,
            text="传统导航",
            variable=self.nav_mode_var,
            value=NavigationMode.TRADITIONAL.value,
            command=self._on_nav_mode_changed
        )
        traditional_radio.pack(side=tk.LEFT)
        
        # 快速导航按钮
        nav_frame = ttk.Frame(parent)
        nav_frame.pack(fill=tk.X)
        
        # 第一行
        row1_frame = ttk.Frame(nav_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(row1_frame, text="A1", command=lambda: self._navigate_to_hole("0000")).pack(side=tk.LEFT, padx=2)
        ttk.Button(row1_frame, text="A12", command=lambda: self._navigate_to_hole("0011")).pack(side=tk.LEFT, padx=2)
        ttk.Button(row1_frame, text="H1", command=lambda: self._navigate_to_hole("0700")).pack(side=tk.LEFT, padx=2)
        ttk.Button(row1_frame, text="H12", command=lambda: self._navigate_to_hole("0711")).pack(side=tk.LEFT, padx=2)
        
        # 第二行
        row2_frame = ttk.Frame(nav_frame)
        row2_frame.pack(fill=tk.X)
        
        ttk.Button(row2_frame, text="D6", command=lambda: self._navigate_to_hole("0305")).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2_frame, text="G7", command=lambda: self._navigate_to_hole("0606")).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2_frame, text="居中", command=self._navigate_to_center).pack(side=tk.LEFT, padx=2)
    
    def _create_view_controls(self, parent):
        """创建视图控制"""
        # 标题
        title_label = ttk.Label(parent, text="视图控制", font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 缩放控制
        zoom_frame = ttk.Frame(parent)
        zoom_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(zoom_frame, text="缩放:").pack(side=tk.LEFT)
        
        # 缩放滑块
        zoom_scale = ttk.Scale(
            zoom_frame,
            from_=10,
            to=500,
            variable=self.zoom_var,
            orient=tk.HORIZONTAL,
            command=self._on_zoom_changed
        )
        zoom_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        # 缩放标签
        self.zoom_label = ttk.Label(zoom_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT)
        
        # 缩放按钮
        zoom_button_frame = ttk.Frame(parent)
        zoom_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(zoom_button_frame, text="放大", command=self._zoom_in).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(zoom_button_frame, text="缩小", command=self._zoom_out).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(zoom_button_frame, text="适应", command=self._zoom_fit).pack(side=tk.LEFT)
        
        # 显示选项
        display_frame = ttk.LabelFrame(parent, text="显示选项", padding="5")
        display_frame.pack(fill=tk.X)
        
        # 网格显示
        self.show_grid_var = tk.BooleanVar(value=self.ui_state_manager.get_state().show_grid)
        grid_check = ttk.Checkbutton(
            display_frame,
            text="显示网格",
            variable=self.show_grid_var,
            command=self._on_grid_toggle
        )
        grid_check.pack(anchor=tk.W)
        
        # 孔位编号显示
        self.show_numbers_var = tk.BooleanVar(value=self.ui_state_manager.get_state().show_hole_numbers)
        numbers_check = ttk.Checkbutton(
            display_frame,
            text="显示孔位编号",
            variable=self.show_numbers_var,
            command=self._on_numbers_toggle
        )
        numbers_check.pack(anchor=tk.W)
        
        # 标注显示
        self.show_annotations_var = tk.BooleanVar(value=self.ui_state_manager.get_state().show_annotations)
        annotations_check = ttk.Checkbutton(
            display_frame,
            text="显示标注",
            variable=self.show_annotations_var,
            command=self._on_annotations_toggle
        )
        annotations_check.pack(anchor=tk.W)
    
    def setup_layout(self) -> None:
        """设置布局"""
        pass
    
    def bind_events(self) -> None:
        """绑定事件"""
        pass
    
    def set_image_canvas(self, canvas):
        """设置图像画布引用"""
        self.image_canvas = canvas
    
    def add_image_to_list(self, image_path: str):
        """添加图像到列表"""
        if image_path not in self.current_images:
            self.current_images.append(image_path)
            self.image_listbox.insert(tk.END, image_path.split('/')[-1].split('\\')[-1])
    
    def remove_image_from_list(self, image_path: str):
        """从列表中移除图像"""
        if image_path in self.current_images:
            index = self.current_images.index(image_path)
            self.current_images.remove(image_path)
            self.image_listbox.delete(index)
    
    def _on_image_selected(self, event):
        """图像选择事件"""
        selection = self.image_listbox.curselection()
        if selection:
            index = selection[0]
            image_path = self.current_images[index]
            
            # 发布图像选择事件
            self.event_bus.publish(EventType.FILE_OPENED, {
                'file_path': image_path,
                'file_type': 'image'
            })
    
    def _add_images(self):
        """添加图像"""
        # 这里应该实现文件选择对话框
        # 暂时发布事件让控制器处理
        self.event_bus.publish(EventType.FILE_OPENED, {
            'action': 'add_images'
        })
    
    def _remove_image(self):
        """移除图像"""
        selection = self.image_listbox.curselection()
        if selection:
            index = selection[0]
            image_path = self.current_images[index]
            
            # 从列表中移除
            self.remove_image_from_list(image_path)
            
            # 发布移除事件
            self.event_bus.publish(EventType.FILE_OPENED, {
                'action': 'remove_image',
                'file_path': image_path
            })
    
    def _navigate_to_hole(self, hole_id: str):
        """导航到指定孔位"""
        if self.image_canvas:
            self.image_canvas.select_hole(hole_id)
            
            # 发布导航事件
            self.event_bus.publish(EventType.NAVIGATION_CHANGED, {
                'target': 'hole',
                'hole_id': hole_id
            })
    
    def _navigate_to_center(self):
        """导航到中心"""
        if self.image_canvas:
            # 计算中心孔位
            center_row = self.image_canvas.grid_rows // 2
            center_col = self.image_canvas.grid_cols // 2
            center_hole = f"{center_row:02d}{center_col:02d}"
            
            self._navigate_to_hole(center_hole)
    
    def _on_zoom_changed(self, value):
        """缩放改变事件"""
        zoom_percent = float(value)
        self.zoom_label.config(text=f"{zoom_percent:.0f}%")
        
        if self.image_canvas:
            self.image_canvas.zoom_level = zoom_percent / 100.0
            self.image_canvas._redraw_image()
    
    def _zoom_in(self):
        """放大"""
        current_zoom = self.zoom_var.get()
        new_zoom = min(500, current_zoom * 1.2)
        self.zoom_var.set(new_zoom)
    
    def _zoom_out(self):
        """缩小"""
        current_zoom = self.zoom_var.get()
        new_zoom = max(10, current_zoom / 1.2)
        self.zoom_var.set(new_zoom)
    
    def _zoom_fit(self):
        """适应窗口"""
        if self.image_canvas:
            self.image_canvas._fit_image_to_canvas()
            
            # 更新缩放显示
            zoom_percent = self.image_canvas.zoom_level * 100
            self.zoom_var.set(zoom_percent)
    
    def _on_nav_mode_changed(self):
        """导航模式改变"""
        mode = self.nav_mode_var.get()
        self.ui_state_manager.set_navigation_mode(NavigationMode(mode))
        
        # 发布导航模式变更事件
        self.event_bus.publish(EventType.NAVIGATION_CHANGED, {
            'mode': mode
        })
    
    def _on_grid_toggle(self):
        """网格显示切换"""
        show_grid = self.show_grid_var.get()
        self.ui_state_manager.toggle_grid()
    
    def _on_numbers_toggle(self):
        """孔位编号显示切换"""
        show_numbers = self.show_numbers_var.get()
        self.ui_state_manager.update_state(show_hole_numbers=show_numbers)
    
    def _on_annotations_toggle(self):
        """标注显示切换"""
        show_annotations = self.show_annotations_var.get()
        self.ui_state_manager.toggle_annotations()
    
    def _on_image_loaded(self, event: Event):
        """图像加载事件"""
        data = event.data
        if data and 'image_path' in data:
            self.add_image_to_list(data['image_path'])
    
    def update_zoom_display(self, zoom_level: float):
        """更新缩放显示"""
        zoom_percent = zoom_level * 100
        self.zoom_var.set(zoom_percent)
    
    def get_current_image_path(self) -> Optional[str]:
        """获取当前选中的图像路径"""
        selection = self.image_listbox.curselection()
        if selection:
            index = selection[0]
            return self.current_images[index]
        return None
    
    def set_current_image(self, image_path: str):
        """设置当前图像"""
        if image_path in self.current_images:
            index = self.current_images.index(image_path)
            self.image_listbox.selection_clear(0, tk.END)
            self.image_listbox.selection_set(index)
            self.image_listbox.see(index)
    
    def clear_image_list(self):
        """清空图像列表"""
        self.current_images.clear()
        self.image_listbox.delete(0, tk.END)
    
    def get_navigation_mode(self) -> NavigationMode:
        """获取导航模式"""
        return NavigationMode(self.nav_mode_var.get())
    
    def set_navigation_mode(self, mode: NavigationMode):
        """设置导航模式"""
        self.nav_mode_var.set(mode.value)
        self._on_nav_mode_changed()