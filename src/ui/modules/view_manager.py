"""
视图管理模块
负责所有图像显示、画布管理、视觉效果绘制等视图相关功能
专注于"怎么显示"而不是"做什么"

职责：
1. 图像加载和显示 (全景图/切片)
2. 画布管理和操作 (缩放/偏移/清理)
3. 视觉效果绘制 (孔位框/高亮/标记)
4. 配置数据可视化 (颜色映射/状态显示)

不负责：
- 导航逻辑 (交给SliceController)
- 事件处理 (交给SliceController)
- 业务逻辑 (交给其他服务)
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import os
from typing import Optional, Dict, Any, Callable, List

# 日志导入
try:
    from src.utils.logger import log_debug, log_info, log_warning, log_error
except ImportError:
    def log_debug(msg, category=""): print(f"[DEBUG] {msg}")
    def log_info(msg, category=""): print(f"[INFO] {msg}")
    def log_warning(msg, category=""): print(f"[WARNING] {msg}")
    def log_error(msg, category=""): print(f"[ERROR] {msg}")

class ViewManager:
    """视图管理器 - 负责图像显示和画布管理"""
    
    def __init__(self, gui_instance):
        """
        初始化视图管理器
        
        Args:
            gui_instance: 主GUI实例，用于访问其他组件
        """
        self.gui = gui_instance
        
        # 画布引用
        self.panoramic_canvas = None
        self.slice_canvas = None
        
        # 图像相关
        self.panoramic_image = None
        self.slice_image = None
        self.panoramic_photo = None
        self.slice_photo = None
        
        # 视图状态
        self.current_panoramic_id = None
        self.current_hole_number = None
        
        # 缩放和显示状态
        self.zoom_factor = 1.0
        self.display_width = 0
        self.display_height = 0
        self.offset_x = 0
        self.offset_y = 0
        self.scale_factor = 1.0
        
        # 配置数据缓存
        self._config_data_cache = {}
        
        # 全景图加载重试计数
        self._panoramic_load_retry_count = 0
        self._last_panoramic_load_time = 0
        self._last_panoramic_load_id = None
        
        log_debug("视图管理器初始化完成", "VIEW_MANAGER")
    
    def set_canvas_references(self, panoramic_canvas: tk.Canvas, slice_canvas: tk.Canvas):
        """设置画布引用"""
        self.panoramic_canvas = panoramic_canvas
        self.slice_canvas = slice_canvas
        log_debug("画布引用设置完成", "VIEW_MANAGER")
    
    def update_current_info(self, panoramic_id: str, hole_number: int):
        """更新当前视图信息"""
        self.current_panoramic_id = panoramic_id
        self.current_hole_number = hole_number
    
    def load_panoramic_image(self):
        """加载全景图"""
        if not self.current_panoramic_id:
            return
        
        # 检查画布是否准备就绪
        if not self._is_canvas_ready():
            if not hasattr(self, '_panoramic_load_retry_count'):
                self._panoramic_load_retry_count = 0
            
            if self._panoramic_load_retry_count < 5:
                self._panoramic_load_retry_count += 1
                log_debug(f"画布未准备就绪，延迟重试 ({self._panoramic_load_retry_count}/5)", "LOAD_PANORAMIC")
                self.gui.root.after(100, self.load_panoramic_image)
                return
            else:
                log_debug("画布重试次数已达上限，使用默认尺寸", "LOAD_PANORAMIC")
        
        # 重置重试计数器
        self._reset_panoramic_load_retry()
        
        try:
            # 查找全景图文件
            panoramic_file = None
            if hasattr(self.gui, 'image_processor') and self.gui.image_processor:
                panoramic_file = self.gui.image_processor.find_panoramic_image(
                    f"{self.current_panoramic_id}_hole_1.png", 
                    getattr(self.gui, 'panoramic_directory', '')
                )
            
            if not panoramic_file:
                # 尝试直接从data_manager获取
                if hasattr(self.gui, 'data_manager'):
                    panoramic_file = self.gui.data_manager.get_panoramic_file_path(self.current_panoramic_id)
            
            if not panoramic_file:
                # 更新全景图信息标签 - 适配模块化架构
                self._update_panoramic_info_label(f"未找到全景图: {self.current_panoramic_id}")
                log_debug(f"未找到全景图文件: {self.current_panoramic_id}", "VIEW_MANAGER")
                return
            
            # 加载全景图
            try:
                from PIL import Image
                self.panoramic_image = Image.open(panoramic_file)
            except Exception as e:
                log_error(f"加载全景图文件失败: {e}", "VIEW_MANAGER")
                return
                
            if self.panoramic_image:
                # 获取已标注孔位信息
                annotated_holes = {}
                if hasattr(self.gui, 'current_dataset'):
                    try:
                        for ann in self.gui.current_dataset.get_annotations_by_panoramic_id(self.current_panoramic_id):
                            annotated_holes[ann.hole_number] = {
                                'growth_level': ann.growth_level,
                                'annotation_source': getattr(ann, 'annotation_source', 'unknown')
                            }
                    except Exception as e:
                        log_debug(f"获取标注信息失败: {e}", "VIEW_MANAGER")
                
                # 使用原始图像（暂时不创建覆盖层）
                overlay_image = self.panoramic_image
                
                # 调整尺寸适应显示
                canvas_width = self.panoramic_canvas.winfo_width() if self.panoramic_canvas else 1220
                canvas_height = self.panoramic_canvas.winfo_height() if self.panoramic_canvas else 750
                
                if canvas_width <= 1 or canvas_height <= 1:
                    canvas_width, canvas_height = 1220, 750
                
                # 计算缩放比例以适应画布（减少边距以更好利用空间）
                img_width, img_height = overlay_image.size
                margin = 10  # 统一使用较小的边距
                scale_w = (canvas_width - margin * 2) / img_width
                scale_h = (canvas_height - margin * 2) / img_height
                scale = min(scale_w, scale_h)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                display_panoramic = overlay_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.panoramic_photo = ImageTk.PhotoImage(display_panoramic)
                
                # 显示在画布上
                if self.panoramic_canvas:
                    self.panoramic_canvas.delete("all")
                    canvas_width = self.panoramic_canvas.winfo_width()
                    canvas_height = self.panoramic_canvas.winfo_height()
                    if canvas_width > 1 and canvas_height > 1:
                        self.panoramic_canvas.create_image(
                            canvas_width//2, canvas_height//2, 
                            image=self.panoramic_photo
                        )
                
                # 更新全景图信息 - 适配模块化架构
                self._update_panoramic_info_label(
                    f"全景图: {self.current_panoramic_id} ({self.panoramic_image.width}×{self.panoramic_image.height})"
                )
            
        except Exception as e:
            log_error(f"加载全景图失败: {str(e)}", "LOAD_PANORAMIC")
            # 更新全景图信息标签 - 适配模块化架构
            self._update_panoramic_info_label(f"加载全景图失败: {self.current_panoramic_id}")
        
        # 绘制孔位指示器
        self.draw_current_hole_indicator()
        
        # 清除配置数据缓存
        self._config_data_cache.clear()
    
    def _update_panoramic_info_label(self, text: str):
        """更新全景图信息标签 - 适配不同的GUI架构"""
        try:
            # 尝试不同的GUI架构
            if hasattr(self.gui, 'panoramic_info_label'):
                # 直接在主GUI对象中
                self.gui.panoramic_info_label.config(text=text)
            elif hasattr(self.gui, 'ui_builder') and hasattr(self.gui.ui_builder, 'panoramic_info_label'):
                # 在UIBuilder中
                self.gui.ui_builder.panoramic_info_label.config(text=text)
            elif hasattr(self.gui, 'ui_manager') and hasattr(self.gui.ui_manager, 'panoramic_info_label'):
                # 在UIManager中
                self.gui.ui_manager.panoramic_info_label.config(text=text)
            else:
                log_debug(f"未找到panoramic_info_label，无法更新文本: {text}", "VIEW_MANAGER")
        except Exception as e:
            log_error(f"更新全景图信息标签失败: {e}", "VIEW_MANAGER")
    
    def draw_current_hole_indicator(self):
        """更新当前孔位的外框颜色状态"""
        log_debug(f"draw_current_hole_indicator 调用 - panoramic_image: {self.panoramic_image is not None}, current_hole_number: {self.current_hole_number}", "DISPLAY")
        
        if not self.panoramic_image or not self.current_hole_number:
            log_debug("draw_current_hole_indicator 早期退出: 缺少panoramic_image或current_hole_number", "DISPLAY")
            return
            
        # 直接调用绘制所有配置框的方法，会自动高亮当前孔位
        self.draw_all_config_hole_boxes()
    
    def draw_all_config_hole_boxes(self):
        """在全景图上绘制所有孔位的配置状态框，当前孔位用特殊样式高亮，并显示人工确认状态"""
        if not self.panoramic_image or not self.current_panoramic_id:
            return

        try:
            # 获取画布尺寸
            if not self.panoramic_canvas:
                log_debug("绘制所有配置孔位框失败: 全景图画布未设置", "DISPLAY")
                return
                
            canvas_width = self.panoramic_canvas.winfo_width()
            canvas_height = self.panoramic_canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                return

            # 计算显示图像的实际尺寸（保持宽高比）
            original_width = self.panoramic_image.width
            original_height = self.panoramic_image.height

            # 计算缩放比例（保持宽高比，适应画布）
            margin = 10  # 统一使用较小的边距以更好利用空间
            scale_w = (canvas_width - margin * 2) / original_width
            scale_h = (canvas_height - margin * 2) / original_height
            scale_factor = min(scale_w, scale_h)

            # 计算显示尺寸
            display_width = int(original_width * scale_factor)
            display_height = int(original_height * scale_factor)

            # 计算图像在画布中的偏移（居中显示）
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2

            # 保存显示参数供其他组件使用
            self.display_width = display_width
            self.display_height = display_height
            self.offset_x = offset_x
            self.offset_y = offset_y
            self.scale_factor = scale_factor

            # 关键修正：调整HoleManager的坐标参数以匹配当前画布
            if hasattr(self.gui, 'hole_manager'):
                self.gui.hole_manager.adjust_coordinates_for_canvas(
                    canvas_width, canvas_height, original_width, original_height
                )

            # 删除之前的所有配置框
            self.panoramic_canvas.delete("config_hole_boxes")
            self.panoramic_canvas.delete("config_hole_boxes_current")
            self.panoramic_canvas.delete("current_hole_indicator")
            self.panoramic_canvas.delete("manual_annotation_markers")

            # 获取当前全景图的所有配置数据
            config_data = self.get_current_panoramic_config()
            if not config_data:
                log_debug("没有配置数据可绘制", "DISPLAY")
                return

            # 定义颜色方案
            color_map = {
                'positive': '#CC0000',        # 阳性：深红色
                'negative': '#00AA00',        # 阴性：深绿色
                'weak_growth': '#FF8C00',     # 弱生长：深橙色
                'uncertain': '#9932CC',       # 不确定：深紫色
                'default': '#708090'          # 默认：石板灰
            }

            # 当前孔位的特殊高亮颜色
            current_color_map = {
                'positive': '#FF0000',        # 阳性当前：亮红色
                'negative': '#00FF00',        # 阴性当前：亮绿色
                'weak_growth': '#FFA500',     # 弱生长当前：亮橙色
                'uncertain': '#DA70D6',       # 不确定当前：亮紫色
                'default': '#C0C0C0'          # 默认当前：银色
            }

            # 人工确认状态的视觉标记颜色
            manual_confirm_color = '#FFFF00'  # 亮黄色

            # 绘制每个有配置的孔位
            drawn_count = 0
            manual_confirmed_count = 0

            for hole_number, hole_data in config_data.items():
                try:
                    # 确保孔位编号是整数类型，跳过非数字键（如元数据字段）
                    try:
                        hole_number_int = int(hole_number) if isinstance(hole_number, str) else hole_number
                    except ValueError:
                        # 跳过非数字的键（如 'format', 'filename' 等元数据）
                        log_debug(f"跳过非数字孔位键: {hole_number}", "DISPLAY")
                        continue
                    
                    # 从孔位数据字典中提取生长级别
                    if isinstance(hole_data, dict):
                        growth_level = self._extract_growth_level_from_hole_data(hole_data)
                    else:
                        # 如果不是字典，可能是直接的生长级别值
                        growth_level = str(hole_data)
                    
                    if not growth_level or growth_level == 'unannotated':
                        continue
                    
                    # 获取孔位中心坐标（HoleManager已经调整为适合画布的坐标）
                    hole_center = self.gui.hole_manager.get_hole_center_coordinates(hole_number_int)

                    # 直接使用调整后的坐标，不需要再次缩放
                    # HoleManager.adjust_coordinates_for_canvas()已经处理了缩放
                    hole_x = offset_x + hole_center[0]
                    hole_y = offset_y + hole_center[1]

                    # 计算框的大小
                    box_size = max(20, int(90 * scale_factor))

                    # 判断是否为当前孔位
                    is_current = (hole_number_int == self.current_hole_number)

                    # 检查是否已人工确认
                    is_manual_confirmed = False
                    if hasattr(self.gui, 'current_dataset'):
                        manual_annotation = self.gui.current_dataset.get_annotation_by_hole(
                            self.current_panoramic_id, hole_number
                        )
                        if manual_annotation and hasattr(manual_annotation, 'annotation_source'):
                            is_manual_confirmed = manual_annotation.annotation_source in ['enhanced_manual', 'manual']

                    # 确定显示的生长级别和颜色
                    if is_manual_confirmed:
                        display_growth_level = manual_annotation.growth_level
                    else:
                        display_growth_level = growth_level

                    # 选择颜色和线宽
                    if is_current:
                        color = current_color_map.get(display_growth_level, current_color_map['default'])
                        width = 3
                        tags = "config_hole_boxes_current"
                    else:
                        color = color_map.get(display_growth_level, color_map['default'])
                        width = 1
                        tags = "config_hole_boxes"

                    # 绘制配置状态框
                    self.panoramic_canvas.create_rectangle(
                        hole_x - box_size//2, hole_y - box_size//2,
                        hole_x + box_size//2, hole_y + box_size//2,
                        outline=color, width=width, tags=tags
                    )

                    # 如果已人工确认，绘制醒目的黄色三角标记
                    if is_manual_confirmed:
                        triangle_size = max(12, int(25 * scale_factor))
                        
                        triangle_points = [
                            hole_x + box_size//2, hole_y - box_size//2,
                            hole_x + box_size//2 - triangle_size, hole_y - box_size//2,
                            hole_x + box_size//2, hole_y - box_size//2 + triangle_size
                        ]

                        self.panoramic_canvas.create_polygon(
                            triangle_points,
                            fill=manual_confirm_color,
                            outline='black',
                            width=1,
                            tags="manual_annotation_markers"
                        )

                        manual_confirmed_count += 1

                    drawn_count += 1

                except Exception as e:
                    log_debug(f"绘制孔位{hole_number}配置框失败: {e}", "DISPLAY")
                    continue

            log_debug(f"绘制了 {drawn_count} 个配置孔位框，其中 {manual_confirmed_count} 个已人工确认，当前孔位: {self.current_hole_number}", "DISPLAY")

            # 确保当前孔位框在最顶层
            self.panoramic_canvas.tag_raise("config_hole_boxes_current")
            self.panoramic_canvas.tag_raise("manual_annotation_markers")

        except Exception as e:
            log_debug(f"绘制所有配置孔位框失败: {e}", "DISPLAY")
    
    def get_current_panoramic_config(self):
        """获取当前全景图的配置数据"""
        if not self.current_panoramic_id:
            return {}
        
        # 检查缓存
        cache_key = f"{self.current_panoramic_id}_config_data"
        if cache_key in self._config_data_cache:
            return self._config_data_cache[cache_key]
        
        try:
            # 查找全景图文件
            panoramic_filename = f"{self.current_panoramic_id}_hole_1.png"
            panoramic_file = None
            
            if hasattr(self.gui, 'image_processor') and self.gui.image_processor:
                try:
                    panoramic_file = self.gui.image_processor.find_panoramic_image(
                        panoramic_filename, 
                        getattr(self.gui, 'panoramic_directory', '')
                    )
                except Exception:
                    pass
            
            if not panoramic_file and hasattr(self.gui, 'data_manager'):
                try:
                    panoramic_file = self.gui.data_manager.get_panoramic_file_path(self.current_panoramic_id)
                except Exception:
                    pass
            
            if not panoramic_file:
                return {}
            
            # 从DataManager获取配置数据
            config_annotations = {}
            if hasattr(self.gui, 'data_manager') and self.gui.data_manager:
                try:
                    raw_config_data = self.gui.data_manager.get_panoramic_config_data(self.current_panoramic_id)
                    # 只提取 'holes' 字段中的孔位数据，过滤掉元数据字段
                    if raw_config_data and 'holes' in raw_config_data:
                        config_annotations = raw_config_data['holes']
                        log_debug(f"从DataManager获取配置数据: {len(config_annotations)}个孔位", "CONFIG")
                    else:
                        log_debug(f"配置数据中未找到holes字段: {raw_config_data.keys() if raw_config_data else 'None'}", "CONFIG")
                except Exception as e:
                    log_debug(f"DataManager获取配置失败: {e}", "CONFIG")
            
            # 缓存配置数据
            if config_annotations:
                self._config_data_cache[cache_key] = config_annotations
            return config_annotations
            
        except Exception as e:
            log_debug(f"获取当前全景图配置失败: {e}", "CONFIG")
            return {}
    
    def load_slice_image(self, slice_file_path: str):
        """
        加载切片图像
        
        Args:
            slice_file_path: 切片文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if not slice_file_path or not os.path.exists(slice_file_path):
                log_debug(f"切片文件不存在: {slice_file_path}", "VIEW_MANAGER")
                return False
            
            # 缓存当前切片路径
            self._current_slice_path = slice_file_path
            
            # 加载切片图像
            if hasattr(self.gui, 'image_processor') and self.gui.image_processor:
                self.slice_image = self.gui.image_processor.load_slice_image(slice_file_path)
            else:
                # 直接使用PIL加载
                from PIL import Image
                self.slice_image = Image.open(slice_file_path)
                
            if self.slice_image:
                # 使用新的显示方法（支持缩放）
                self._update_slice_display()
                log_debug(f"成功加载切片: {slice_file_path}", "VIEW_MANAGER")
                return True
            
            return False
            
        except Exception as e:
            log_error(f"加载切片图像失败: {str(e)}", "VIEW_MANAGER")
            return False
    
    def draw_slice_annotation_indicator(self, canvas_width, canvas_height):
        """在切片预览画布上绘制标注状态指示器"""
        if not self.current_panoramic_id or not self.current_hole_number:
            return
            
        try:
            # 检查当前孔位是否已人工标注
            is_manual_confirmed = False
            if hasattr(self.gui, 'current_dataset'):
                manual_annotation = self.gui.current_dataset.get_annotation_by_hole(
                    self.current_panoramic_id, self.current_hole_number
                )
                if manual_annotation and hasattr(manual_annotation, 'annotation_source'):
                    is_manual_confirmed = manual_annotation.annotation_source in ['enhanced_manual', 'manual']
            
            # 如果已标注，在右上角绘制亮黄色标记
            if is_manual_confirmed:
                indicator_size = 20
                margin = 5
                
                x = canvas_width - margin - indicator_size // 2
                y = margin + indicator_size // 2
                
                # 绘制圆形标记
                self.slice_canvas.create_oval(
                    x - indicator_size // 2, y - indicator_size // 2,
                    x + indicator_size // 2, y + indicator_size // 2,
                    fill='#FFFF00',
                    outline='black',
                    width=2,
                    tags="annotation_indicator"
                )
                
                # 在圆形中央添加"✓"符号
                self.slice_canvas.create_text(
                    x, y,
                    text="✓",
                    font=('Arial', 10, 'bold'),
                    fill='black',
                    tags="annotation_indicator"
                )
                
                log_debug(f"已在切片预览添加标注状态指示器", "DISPLAY")
                
        except Exception as e:
            log_debug(f"绘制切片标注指示器失败: {e}", "DISPLAY")
    
    def _is_canvas_ready(self):
        """检查画布是否准备就绪"""
        try:
            if not self.panoramic_canvas:
                log_debug("全景图画布未设置", "LOAD_PANORAMIC")
                return False
                
            canvas_width = self.panoramic_canvas.winfo_width()
            canvas_height = self.panoramic_canvas.winfo_height()
            return canvas_width > 1 and canvas_height > 1
        except Exception as e:
            log_debug(f"检查画布状态失败: {e}", "LOAD_PANORAMIC")
            return False
    
    def _reset_panoramic_load_retry(self):
        """重置全景图加载重试计数器"""
        if hasattr(self, '_panoramic_load_retry_count'):
            self._panoramic_load_retry_count = 0
    
    def clear_canvas(self, canvas_type="both"):
        """清除画布内容"""
        try:
            if canvas_type in ["both", "panoramic"] and self.panoramic_canvas:
                self.panoramic_canvas.delete("all")
            
            if canvas_type in ["both", "slice"] and self.slice_canvas:
                self.slice_canvas.delete("all")
                
            log_debug(f"已清除{canvas_type}画布", "VIEW_MANAGER")
            
        except Exception as e:
            log_error(f"清除画布失败: {e}", "VIEW_MANAGER")
    
    def refresh_view(self):
        """刷新当前视图"""
        try:
            # 重新加载全景图
            self.load_panoramic_image()
            
            # 重新绘制孔位指示器
            self.draw_current_hole_indicator()
            
            log_debug("视图刷新完成", "VIEW_MANAGER")
            
        except Exception as e:
            log_error(f"刷新视图失败: {e}", "VIEW_MANAGER")
    
    def set_zoom(self, zoom_factor: float):
        """
        设置缩放比例
        
        Args:
            zoom_factor: 缩放因子 (0.1 - 3.0)
        """
        self.zoom_factor = max(0.1, min(3.0, zoom_factor))
        # 刷新切片显示
        if self.slice_image:
            self._update_slice_display()
        log_debug(f"设置缩放比例: {self.zoom_factor}", "VIEW_MANAGER")
    
    def on_window_resize(self):
        """
        窗口大小变化时的处理
        """
        # 延迟更新显示，避免频繁刷新
        if hasattr(self, '_resize_timer'):
            self.gui.root.after_cancel(self._resize_timer)
            
        self._resize_timer = self.gui.root.after(200, self._delayed_resize_update)
        
    def _delayed_resize_update(self):
        """延迟的窗口大小变化更新"""
        try:
            # 重新加载和调整显示
            if self.current_panoramic_id:
                self.load_panoramic_image()
            
            # 如果有切片图像，也重新显示
            if self.slice_image and hasattr(self, '_current_slice_path'):
                self.load_slice_image(self._current_slice_path)
                
            log_debug("窗口大小调整处理完成", "VIEW_MANAGER")
        except Exception as e:
            log_error(f"窗口大小调整处理失败: {e}", "VIEW_MANAGER")
    
    def _extract_growth_level_from_hole_data(self, hole_data: dict) -> str:
        """
        从孔位数据字典中提取生长级别
        
        Args:
            hole_data: CFG中的孔位数据字典
            
        Returns:
            str: 生长级别 ('negative', 'weak_growth', 'positive', 'unannotated')
        """
        # 检查直接的growth字段
        if 'growth' in hole_data:
            growth_value = hole_data['growth']
            
            # 处理字符串类型的生长级别
            if isinstance(growth_value, str):
                growth_lower = growth_value.lower()
                if growth_lower in ['positive', '+', '阳性']:
                    return 'positive'
                elif growth_lower in ['negative', '-', '阴性']:
                    return 'negative'
                elif growth_lower in ['weak_growth', 'weak', '弱生长']:
                    return 'weak_growth'
                elif growth_lower in ['uncertain', '不确定']:
                    return 'uncertain'
            
            # 处理数值类型
            elif isinstance(growth_value, (int, float)):
                if growth_value > 0.7:
                    return 'positive'
                elif growth_value > 0.3:
                    return 'weak_growth'
                elif growth_value >= 0:
                    return 'negative'
        
        # 检查其他可能的字段名
        for field in ['level', 'status', 'result', 'classification']:
            if field in hole_data:
                value = str(hole_data[field]).lower()
                if value in ['positive', '+', '阳性']:
                    return 'positive'
                elif value in ['negative', '-', '阴性']:
                    return 'negative'
                elif value in ['weak_growth', 'weak', '弱生长']:
                    return 'weak_growth'
        
        # 默认返回未标注
        return 'unannotated'
    
    def _update_slice_display(self):
        """
        更新切片显示（支持缩放）
        """
        if not self.slice_image or not self.slice_canvas:
            return
            
        try:
            canvas_width = self.slice_canvas.winfo_width()
            canvas_height = self.slice_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # 画布尺寸未初始化，延迟更新
                self.gui.root.after(100, self._update_slice_display)
                return
            
            # 计算缩放以填充画布
            img_width, img_height = self.slice_image.size
            
            # 计算缩放比例，优先填充画布
            canvas_padding = 10  # 画布边距
            target_width = canvas_width - canvas_padding * 2
            target_height = canvas_height - canvas_padding * 2
            
            scale_w = target_width / img_width
            scale_h = target_height / img_height
            
            # 选择较大的缩放比例以填充画布，然后应用用户缩放
            base_scale = max(scale_w, scale_h)  # 改为max以放大填充
            final_scale = base_scale * self.zoom_factor
            
            new_width = int(img_width * final_scale)
            new_height = int(img_height * final_scale)
                
            # 调整图像大小
            resized_image = self.slice_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter图像
            self.slice_photo = ImageTk.PhotoImage(resized_image)
            
            # 清空画布并显示图像
            self.slice_canvas.delete("all")
            
            # 居中显示
            x = canvas_width // 2
            y = canvas_height // 2
            self.slice_canvas.create_image(x, y, image=self.slice_photo, anchor='center')
            
            # 绘制标注状态指示器
            self.draw_slice_annotation_indicator(canvas_width, canvas_height)
            
        except Exception as e:
            log_error(f"更新切片显示失败: {e}", "VIEW_MANAGER")
