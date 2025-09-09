"""
图像控制器模块

负责图像处理和显示相关逻辑
"""

import tkinter as tk
from typing import Optional, Dict, Any, Tuple
import logging
from PIL import Image, ImageEnhance, ImageFilter

from src.ui.utils.base_components import BaseController
from src.ui.utils.event_bus import EventBus, EventType, Event, get_event_bus
from src.ui.components import ImageCanvas
from src.services.panoramic_image_service import PanoramicImageService

logger = logging.getLogger(__name__)


class ImageController(BaseController):
    """图像控制器"""
    
    def __init__(self, image_service: Optional[PanoramicImageService] = None):
        super().__init__()
        self.image_service = image_service
        
        # UI组件
        self.image_canvas: Optional[ImageCanvas] = None
        
        # 图像处理参数
        self.brightness = 1.0
        self.contrast = 1.0
        self.sharpness = 1.0
        self.auto_enhance = True
        
        # 当前图像信息
        self.current_image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.image_path: Optional[str] = None
        
    def initialize(self) -> None:
        """初始化控制器"""
        try:
            logger.info("Initializing ImageController...")
            
            # 订阅事件
            self._subscribe_events()
            
            self._mark_initialized()
            logger.info("ImageController initialized successfully")
            
        except Exception as e:
            self.handle_error(e, "ImageController initialization")
            raise
    
    def cleanup(self) -> None:
        """清理资源"""
        logger.info("Cleaning up ImageController...")
        self.cleanup_listeners()
    
    def set_image_canvas(self, canvas: ImageCanvas):
        """设置图像画布"""
        self.image_canvas = canvas
    
    def _subscribe_events(self):
        """订阅事件"""
        self.subscribe(EventType.IMAGE_LOADED, self._on_image_loaded)
        self.subscribe(EventType.IMAGE_PROCESSED, self._on_image_processed)
    
    def _on_image_loaded(self, event: Event):
        """图像加载事件"""
        data = event.data
        if data and 'image_path' in data:
            self.image_path = data['image_path']
            self._load_image_data()
    
    def _on_image_processed(self, event: Event):
        """图像处理事件"""
        data = event.data
        if data:
            logger.debug(f"Image processed: {data}")
    
    def _load_image_data(self):
        """加载图像数据"""
        if not self.image_path:
            return
        
        try:
            # 使用图像服务加载
            if self.image_service:
                self.current_image = self.image_service.get_current_image()
                self.original_image = self.current_image.copy() if self.current_image else None
            else:
                # 直接加载
                self.current_image = Image.open(self.image_path)
                self.original_image = self.current_image.copy()
            
            # 应用图像增强
            if self.auto_enhance:
                self._apply_auto_enhance()
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            logger.info(f"Image data loaded: {self.image_path}")
            
        except Exception as e:
            self.handle_error(e, f"Failed to load image data from {self.image_path}")
    
    def _apply_auto_enhance(self):
        """应用自动增强"""
        if not self.current_image:
            return
        
        try:
            # 自动对比度
            enhancer = ImageEnhance.Contrast(self.current_image)
            self.current_image = enhancer.enhance(1.2)
            
            # 自动锐化
            enhancer = ImageEnhance.Sharpness(self.current_image)
            self.current_image = enhancer.enhance(1.1)
            
            logger.debug("Auto enhancement applied")
            
        except Exception as e:
            logger.warning(f"Failed to apply auto enhancement: {e}")
    
    def adjust_brightness(self, factor: float):
        """调整亮度"""
        if not self.current_image:
            return
        
        try:
            self.brightness = max(0.1, min(3.0, factor))
            
            # 从原始图像开始处理
            image = self.original_image.copy() if self.original_image else self.current_image.copy()
            
            # 应用亮度调整
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(self.brightness)
            
            # 应用其他调整
            if self.contrast != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(self.contrast)
            
            if self.sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(self.sharpness)
            
            self.current_image = image
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            # 发布处理事件
            self.publish(EventType.IMAGE_PROCESSED, {
                'operation': 'brightness',
                'factor': self.brightness
            })
            
        except Exception as e:
            self.handle_error(e, "Failed to adjust brightness")
    
    def adjust_contrast(self, factor: float):
        """调整对比度"""
        if not self.current_image:
            return
        
        try:
            self.contrast = max(0.1, min(3.0, factor))
            
            # 从原始图像开始处理
            image = self.original_image.copy() if self.original_image else self.current_image.copy()
            
            # 应用对比度调整
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(self.contrast)
            
            # 应用其他调整
            if self.brightness != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(self.brightness)
            
            if self.sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(self.sharpness)
            
            self.current_image = image
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            # 发布处理事件
            self.publish(EventType.IMAGE_PROCESSED, {
                'operation': 'contrast',
                'factor': self.contrast
            })
            
        except Exception as e:
            self.handle_error(e, "Failed to adjust contrast")
    
    def adjust_sharpness(self, factor: float):
        """调整锐度"""
        if not self.current_image:
            return
        
        try:
            self.sharpness = max(0.1, min(3.0, factor))
            
            # 从原始图像开始处理
            image = self.original_image.copy() if self.original_image else self.current_image.copy()
            
            # 应用锐度调整
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(self.sharpness)
            
            # 应用其他调整
            if self.brightness != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(self.brightness)
            
            if self.contrast != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(self.contrast)
            
            self.current_image = image
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            # 发布处理事件
            self.publish(EventType.IMAGE_PROCESSED, {
                'operation': 'sharpness',
                'factor': self.sharpness
            })
            
        except Exception as e:
            self.handle_error(e, "Failed to adjust sharpness")
    
    def reset_adjustments(self):
        """重置所有调整"""
        if not self.original_image:
            return
        
        try:
            self.brightness = 1.0
            self.contrast = 1.0
            self.sharpness = 1.0
            
            self.current_image = self.original_image.copy()
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            # 发布处理事件
            self.publish(EventType.IMAGE_PROCESSED, {
                'operation': 'reset_adjustments'
            })
            
        except Exception as e:
            self.handle_error(e, "Failed to reset adjustments")
    
    def toggle_auto_enhance(self):
        """切换自动增强"""
        self.auto_enhance = not self.auto_enhance
        
        if self.auto_enhance and self.original_image:
            self._apply_auto_enhance()
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
        
        # 发布处理事件
        self.publish(EventType.IMAGE_PROCESSED, {
            'operation': 'toggle_auto_enhance',
            'enabled': self.auto_enhance
        })
    
    def apply_filter(self, filter_name: str):
        """应用滤镜"""
        if not self.current_image:
            return
        
        try:
            image = self.current_image.copy()
            
            if filter_name == 'blur':
                image = image.filter(ImageFilter.BLUR)
            elif filter_name == 'sharpen':
                image = image.filter(ImageFilter.SHARPEN)
            elif filter_name == 'edge_enhance':
                image = image.filter(ImageFilter.EDGE_ENHANCE)
            elif filter_name == 'emboss':
                image = image.filter(ImageFilter.EMBOSS)
            elif filter_name == 'smooth':
                image = image.filter(ImageFilter.SMOOTH)
            
            self.current_image = image
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            # 发布处理事件
            self.publish(EventType.IMAGE_PROCESSED, {
                'operation': 'apply_filter',
                'filter': filter_name
            })
            
        except Exception as e:
            self.handle_error(e, f"Failed to apply filter {filter_name}")
    
    def rotate_image(self, angle: float):
        """旋转图像"""
        if not self.current_image:
            return
        
        try:
            self.current_image = self.current_image.rotate(angle, expand=True)
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            # 发布处理事件
            self.publish(EventType.IMAGE_PROCESSED, {
                'operation': 'rotate',
                'angle': angle
            })
            
        except Exception as e:
            self.handle_error(e, f"Failed to rotate image by {angle} degrees")
    
    def flip_image(self, direction: str):
        """翻转图像"""
        if not self.current_image:
            return
        
        try:
            if direction == 'horizontal':
                self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
            elif direction == 'vertical':
                self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
            
            # 更新画布
            if self.image_canvas:
                self.image_canvas.current_image = self.current_image
                self.image_canvas._redraw_image()
            
            # 发布处理事件
            self.publish(EventType.IMAGE_PROCESSED, {
                'operation': 'flip',
                'direction': direction
            })
            
        except Exception as e:
            self.handle_error(e, f"Failed to flip image {direction}")
    
    def get_image_info(self) -> Optional[Dict[str, Any]]:
        """获取图像信息"""
        if not self.current_image:
            return None
        
        return {
            'path': self.image_path,
            'size': self.current_image.size,
            'mode': self.current_image.mode,
            'format': self.current_image.format,
            'brightness': self.brightness,
            'contrast': self.contrast,
            'sharpness': self.sharpness,
            'auto_enhance': self.auto_enhance
        }
    
    def get_current_image(self) -> Optional[Image.Image]:
        """获取当前图像"""
        return self.current_image
    
    def has_image(self) -> bool:
        """检查是否有图像"""
        return self.current_image is not None
    
    def save_processed_image(self, file_path: str):
        """保存处理后的图像"""
        if not self.current_image:
            return False
        
        try:
            # 确定格式
            if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                format_type = 'JPEG'
            elif file_path.lower().endswith('.png'):
                format_type = 'PNG'
            else:
                format_type = 'PNG'
            
            self.current_image.save(file_path, format=format_type)
            
            # 发布保存事件
            self.publish(EventType.FILE_SAVED, {
                'file_path': file_path,
                'file_type': 'processed_image'
            })
            
            return True
            
        except Exception as e:
            self.handle_error(e, f"Failed to save processed image to {file_path}")
            return False