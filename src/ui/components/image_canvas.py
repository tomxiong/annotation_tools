"""
图像画布组件

负责显示全景图像和处理用户交互
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple, List, Dict, Any
import logging
from PIL import Image, ImageTk, ImageDraw
import math

from src.ui.utils.base_components import BaseFrameView, ComponentMixin
from src.ui.utils.event_bus import EventBus, EventType, Event, get_event_bus
from src.ui.models.ui_state import UIStateManager, get_ui_state_manager

logger = logging.getLogger(__name__)


class ImageCanvas(BaseFrameView, ComponentMixin):
    """图像画布组件"""
    
    def __init__(self, parent: tk.Widget, controller=None):
        super().__init__(parent, controller)
        self.canvas: Optional[tk.Canvas] = None
        self.current_image: Optional[Image.Image] = None
        self.photo_image: Optional[ImageTk.PhotoImage] = None
        
        # 显示状态
        self.zoom_level = 1.0
        self.pan_offset = [0, 0]
        self.is_panning = False
        self.pan_start = [0, 0]
        
        # 孔位信息
        self.holes: Dict[str, Dict[str, Any]] = {}
        self.selected_hole: Optional[str] = None
        self.hovered_hole: Optional[str] = None
        
        # 网格设置
        self.grid_rows = 10
        self.grid_cols = 12
        self.show_grid = True
        self.show_hole_numbers = True
        
        # 绑定事件总线
        self.event_bus = get_event_bus()
        self.ui_state_manager = get_ui_state_manager()
        
        # 订阅状态变更
        self.ui_state_manager.register_state_listener('show_grid', self._on_grid_toggle)
        self.ui_state_manager.register_state_listener('show_hole_numbers', self._on_hole_numbers_toggle)
    
    def build_ui(self) -> tk.Widget:
        """构建UI界面"""
        self.widget = ttk.Frame(self.parent)
        
        # 创建画布
        self.canvas = tk.Canvas(
            self.widget,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        h_scrollbar = ttk.Scrollbar(self.widget, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(self.widget, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        return self.widget
    
    def setup_layout(self) -> None:
        """设置布局"""
        # 滚动条布局将在父容器中处理
        pass
    
    def bind_events(self) -> None:
        """绑定事件"""
        # 鼠标事件
        self.canvas.bind('<Button-1>', self._on_mouse_down)
        self.canvas.bind('<B1-Motion>', self._on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_mouse_up)
        self.canvas.bind('<Motion>', self._on_mouse_move)
        self.canvas.bind('<MouseWheel>', self._on_mouse_wheel)
        self.canvas.bind('<Button-4>', self._on_mouse_wheel)  # Linux
        self.canvas.bind('<Button-5>', self._on_mouse_wheel)  # Linux
        
        # 键盘事件
        self.canvas.bind('<Control-plus>', self._on_zoom_in)
        self.canvas.bind('<Control-minus>', self._on_zoom_out)
        self.canvas.bind('<Control-0>', self._on_zoom_reset)
    
    def load_image(self, image_path: str) -> bool:
        """加载图像"""
        try:
            # 加载图像
            self.current_image = Image.open(image_path)
            
            # 调整图像大小以适应画布
            self._fit_image_to_canvas()
            
            # 发布图像加载事件
            self.event_bus.publish(EventType.IMAGE_LOADED, {
                'image_path': image_path,
                'image_size': self.current_image.size
            })
            
            logger.info(f"Image loaded: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return False
    
    def _fit_image_to_canvas(self):
        """调整图像大小以适应画布"""
        if not self.current_image:
            return
        
        # 获取画布大小
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # 画布尚未完全初始化
            self.widget.after(100, self._fit_image_to_canvas)
            return
        
        # 计算缩放比例
        img_width, img_height = self.current_image.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.zoom_level = min(scale_x, scale_y) * 0.9  # 留10%边距
        
        # 重置偏移
        self.pan_offset = [0, 0]
        
        # 重绘图像
        self._redraw_image()
    
    def _redraw_image(self):
        """重绘图像"""
        if not self.current_image or not self.canvas:
            return
        
        # 清除画布
        self.canvas.delete('all')
        
        # 计算显示大小
        img_width, img_height = self.current_image.size
        display_width = int(img_width * self.zoom_level)
        display_height = int(img_height * self.zoom_level)
        
        # 调整图像大小
        resized_image = self.current_image.resize(
            (display_width, display_height),
            Image.Resampling.LANCZOS
        )
        
        # 创建PhotoImage
        self.photo_image = ImageTk.PhotoImage(resized_image)
        
        # 计算显示位置（居中）
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = (canvas_width - display_width) // 2 + self.pan_offset[0]
        y = (canvas_height - display_height) // 2 + self.pan_offset[1]
        
        # 绘制图像
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo_image)
        
        # 更新滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        
        # 绘制网格和孔位
        self._draw_grid()
        self._draw_holes()
    
    def _draw_grid(self):
        """绘制网格"""
        if not self.show_grid or not self.canvas:
            return
        
        # 获取图像显示区域
        if not self.photo_image:
            return
        
        # 计算网格间距
        img_width, img_height = self.current_image.size
        cell_width = (img_width * self.zoom_level) / self.grid_cols
        cell_height = (img_height * self.zoom_level) / self.grid_rows
        
        # 获取图像位置
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_x = (canvas_width - img_width * self.zoom_level) // 2 + self.pan_offset[0]
        img_y = (canvas_height - img_height * self.zoom_level) // 2 + self.pan_offset[1]
        
        # 绘制垂直线
        for i in range(self.grid_cols + 1):
            x = img_x + i * cell_width
            self.canvas.create_line(
                x, img_y, x, img_y + img_height * self.zoom_level,
                fill='gray', width=1, tags='grid'
            )
        
        # 绘制水平线
        for i in range(self.grid_rows + 1):
            y = img_y + i * cell_height
            self.canvas.create_line(
                img_x, y, img_x + img_width * self.zoom_level, y,
                fill='gray', width=1, tags='grid'
            )
    
    def _draw_holes(self):
        """绘制孔位"""
        if not self.canvas:
            return
        
        # 获取图像显示区域
        if not self.photo_image:
            return
        
        # 计算孔位大小和位置
        img_width, img_height = self.current_image.size
        cell_width = (img_width * self.zoom_level) / self.grid_cols
        cell_height = (img_height * self.zoom_level) / self.grid_rows
        
        # 获取图像位置
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_x = (canvas_width - img_width * self.zoom_level) // 2 + self.pan_offset[0]
        img_y = (canvas_height - img_height * self.zoom_level) // 2 + self.pan_offset[1]
        
        # 绘制每个孔位
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                hole_id = f"{row:02d}{col:02d}"
                
                # 计算孔位中心
                center_x = img_x + (col + 0.5) * cell_width
                center_y = img_y + (row + 0.5) * cell_height
                
                # 孔位半径
                radius = min(cell_width, cell_height) * 0.3
                
                # 确定颜色
                color = self._get_hole_color(hole_id)
                outline_color = 'yellow' if hole_id == self.selected_hole else 'white'
                outline_width = 3 if hole_id == self.selected_hole else 1
                
                # 绘制孔位
                hole = self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    fill=color, outline=outline_color, width=outline_width,
                    tags=f'hole_{hole_id}'
                )
                
                # 绘制孔位编号
                if self.show_hole_numbers:
                    self.canvas.create_text(
                        center_x, center_y,
                        text=hole_id, fill='white',
                        font=('Arial', int(8 * self.zoom_level)),
                        tags=f'hole_text_{hole_id}'
                    )
                
                # 存储孔位信息
                self.holes[hole_id] = {
                    'id': hole_id,
                    'row': row,
                    'col': col,
                    'center': (center_x, center_y),
                    'radius': radius,
                    'widget': hole
                }
    
    def _get_hole_color(self, hole_id: str) -> str:
        """获取孔位颜色"""
        # 这里可以根据标注状态返回不同颜色
        # 默认为深蓝色
        return '#0066cc'
    
    def _on_mouse_down(self, event):
        """鼠标按下事件"""
        # 检查是否点击了孔位
        clicked_hole = self._get_hole_at_position(event.x, event.y)
        
        if clicked_hole:
            # 选择孔位
            self.select_hole(clicked_hole)
        else:
            # 开始拖拽
            self.is_panning = True
            self.pan_start = [event.x, event.y]
    
    def _on_mouse_drag(self, event):
        """鼠标拖拽事件"""
        if self.is_panning:
            # 计算拖拽偏移
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            
            # 更新偏移
            self.pan_offset[0] += dx
            self.pan_offset[1] += dy
            
            # 更新起始位置
            self.pan_start = [event.x, event.y]
            
            # 重绘图像
            self._redraw_image()
    
    def _on_mouse_up(self, event):
        """鼠标释放事件"""
        self.is_panning = False
    
    def _on_mouse_move(self, event):
        """鼠标移动事件"""
        # 检查悬停的孔位
        hovered_hole = self._get_hole_at_position(event.x, event.y)
        
        if hovered_hole != self.hovered_hole:
            self.hovered_hole = hovered_hole
            
            # 发布悬停事件
            self.event_bus.publish(EventType.HOLE_HOVERED, {
                'hole_id': hovered_hole
            })
            
            # 更新鼠标样式
            if hovered_hole:
                self.canvas.configure(cursor='hand2')
            else:
                self.canvas.configure(cursor='arrow')
    
    def _on_mouse_wheel(self, event):
        """鼠标滚轮事件"""
        # 计算缩放
        if event.delta:
            # Windows
            scale_factor = 1.1 if event.delta > 0 else 0.9
        else:
            # Linux
            scale_factor = 1.1 if event.num == 4 else 0.9
        
        # 限制缩放范围
        new_zoom = self.zoom_level * scale_factor
        if 0.1 <= new_zoom <= 10.0:
            self.zoom_level = new_zoom
            self._redraw_image()
    
    def _on_zoom_in(self, event):
        """放大"""
        if self.zoom_level < 10.0:
            self.zoom_level *= 1.2
            self._redraw_image()
    
    def _on_zoom_out(self, event):
        """缩小"""
        if self.zoom_level > 0.1:
            self.zoom_level /= 1.2
            self._redraw_image()
    
    def _on_zoom_reset(self, event):
        """重置缩放"""
        self._fit_image_to_canvas()
    
    def _get_hole_at_position(self, x: float, y: float) -> Optional[str]:
        """获取指定位置的孔位"""
        for hole_id, hole_info in self.holes.items():
            center_x, center_y = hole_info['center']
            radius = hole_info['radius']
            
            # 计算距离
            distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
            
            if distance <= radius:
                return hole_id
        
        return None
    
    def select_hole(self, hole_id: str):
        """选择孔位"""
        if self.selected_hole == hole_id:
            return
        
        self.selected_hole = hole_id
        
        # 重绘以更新选择状态
        self._redraw_image()
        
        # 发布选择事件
        self.event_bus.publish(EventType.HOLE_SELECTED, {
            'hole_id': hole_id,
            'hole_info': self.holes.get(hole_id, {})
        })
    
    def _on_grid_toggle(self, show_grid: bool):
        """网格显示切换"""
        self.show_grid = show_grid
        self._redraw_image()
    
    def _on_hole_numbers_toggle(self, show_numbers: bool):
        """孔位编号显示切换"""
        self.show_hole_numbers = show_numbers
        self._redraw_image()
    
    def get_selected_hole(self) -> Optional[str]:
        """获取当前选中的孔位"""
        return self.selected_hole
    
    def get_hole_info(self, hole_id: str) -> Optional[Dict[str, Any]]:
        """获取孔位信息"""
        return self.holes.get(hole_id)
    
    def update_hole_annotation(self, hole_id: str, annotation_data: Dict[str, Any]):
        """更新孔位标注"""
        if hole_id in self.holes:
            self.holes[hole_id].update(annotation_data)
            self._redraw_image()
    
    def clear_selection(self):
        """清除选择"""
        self.selected_hole = None
        self._redraw_image()
    
    def set_grid_size(self, rows: int, cols: int):
        """设置网格大小"""
        self.grid_rows = rows
        self.grid_cols = cols
        self.holes.clear()
        self._redraw_image()
    
    def get_current_view_info(self) -> Dict[str, Any]:
        """获取当前视图信息"""
        return {
            'zoom_level': self.zoom_level,
            'pan_offset': self.pan_offset.copy(),
            'selected_hole': self.selected_hole,
            'grid_size': (self.grid_rows, self.grid_cols),
            'image_size': self.current_image.size if self.current_image else None
        }