"""
图像处理模块
负责图像加载、缩放、转换等图像处理相关的核心业务逻辑
"""

import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

# 日志导入
try:
    from src.utils.logger import log_debug, log_info, log_warning, log_error
except ImportError:
    def log_debug(msg, category=""): print(f"[DEBUG] {msg}")
    def log_info(msg, category=""): print(f"[INFO] {msg}")
    def log_warning(msg, category=""): print(f"[WARNING] {msg}")
    def log_error(msg, category=""): print(f"[ERROR] {msg}")

class ImageProcessor:
    """图像处理器 - 负责所有图像相关的处理操作"""
    
    def __init__(self, gui_instance):
        """
        初始化图像处理器
        
        Args:
            gui_instance: 主GUI实例，用于访问其他组件
        """
        self.gui = gui_instance
        
        # 图像缓存
        self._image_cache = {}
        self._cache_size_limit = 50  # 最大缓存50张图像
        
        # 支持的图像格式
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        
        log_debug("图像处理器初始化完成", "IMAGE_PROCESSOR")
    
    def load_slice_image(self, image_path: str) -> Optional[Image.Image]:
        """
        加载切片图像
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            PIL.Image对象，如果加载失败返回None
        """
        try:
            if not image_path or not os.path.exists(image_path):
                log_debug(f"切片图像文件不存在: {image_path}", "IMAGE_PROCESSOR")
                return None
            
            # 检查缓存
            cache_key = f"slice_{image_path}"
            if cache_key in self._image_cache:
                log_debug(f"从缓存加载切片图像: {image_path}", "IMAGE_PROCESSOR")
                return self._image_cache[cache_key]
            
            # 检查文件格式
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in self.supported_formats:
                log_warning(f"不支持的图像格式: {file_ext}", "IMAGE_PROCESSOR")
                return None
            
            # 加载图像
            image = Image.open(image_path)
            image = image.convert('RGB')  # 确保颜色模式一致
            
            # 添加到缓存
            self._add_to_cache(cache_key, image)
            
            log_debug(f"成功加载切片图像: {image_path} ({image.width}x{image.height})", "IMAGE_PROCESSOR")
            return image
            
        except Exception as e:
            log_error(f"加载切片图像失败 {image_path}: {str(e)}", "IMAGE_PROCESSOR")
            return None
    
    def load_panoramic_image(self, image_path: str) -> Optional[Image.Image]:
        """
        加载全景图像
        
        Args:
            image_path: 全景图像文件路径
            
        Returns:
            PIL.Image对象，如果加载失败返回None
        """
        try:
            if not image_path or not os.path.exists(image_path):
                log_debug(f"全景图像文件不存在: {image_path}", "IMAGE_PROCESSOR")
                return None
            
            # 检查缓存
            cache_key = f"panoramic_{image_path}"
            if cache_key in self._image_cache:
                log_debug(f"从缓存加载全景图像: {image_path}", "IMAGE_PROCESSOR")
                return self._image_cache[cache_key]
            
            # 检查文件格式
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in self.supported_formats:
                log_warning(f"不支持的图像格式: {file_ext}", "IMAGE_PROCESSOR")
                return None
            
            # 加载图像
            image = Image.open(image_path)
            image = image.convert('RGB')  # 确保颜色模式一致
            
            # 添加到缓存
            self._add_to_cache(cache_key, image)
            
            log_debug(f"成功加载全景图像: {image_path} ({image.width}x{image.height})", "IMAGE_PROCESSOR")
            return image
            
        except Exception as e:
            log_error(f"加载全景图像失败 {image_path}: {str(e)}", "IMAGE_PROCESSOR")
            return None
    
    def resize_image_for_display(self, image: Image.Image, target_width: int, target_height: int, fill_mode: str = 'fit') -> Image.Image:
        """
        调整图像尺寸以适应显示区域
        
        Args:
            image: 原始图像
            target_width: 目标宽度
            target_height: 目标高度
            fill_mode: 缩放模式 ('fit', 'fill', 'stretch')
            
        Returns:
            调整尺寸后的图像
        """
        try:
            if not image:
                raise ValueError("图像对象为空")
            
            original_width, original_height = image.size
            
            if fill_mode == 'fit':
                # 保持宽高比，完全显示图像
                ratio = min(target_width / original_width, target_height / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
            elif fill_mode == 'fill':
                # 保持宽高比，填满显示区域
                ratio = max(target_width / original_width, target_height / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
            elif fill_mode == 'stretch':
                # 拉伸到目标尺寸
                new_width = target_width
                new_height = target_height
                
            else:
                raise ValueError(f"不支持的缩放模式: {fill_mode}")
            
            # 执行缩放
            resized_image = image.resize((new_width, new_height), Image.LANCZOS)
            
            log_debug(f"图像缩放: {original_width}x{original_height} -> {new_width}x{new_height} (模式: {fill_mode})", "IMAGE_PROCESSOR")
            return resized_image
            
        except Exception as e:
            log_error(f"图像缩放失败: {str(e)}", "IMAGE_PROCESSOR")
            return image  # 返回原图像作为fallback
    
    def create_panoramic_overlay(self, panoramic_image: Image.Image, current_hole: int, annotated_holes: Dict[int, Dict[str, Any]]) -> Image.Image:
        """
        在全景图上创建标注覆盖层
        
        Args:
            panoramic_image: 原始全景图
            current_hole: 当前孔位编号
            annotated_holes: 已标注孔位信息 {hole_number: {'growth_level': str, 'annotation_source': str}}
            
        Returns:
            带覆盖层的全景图
        """
        try:
            if not panoramic_image:
                return panoramic_image
            
            # 创建图像副本
            overlay_image = panoramic_image.copy()
            draw = ImageDraw.Draw(overlay_image)
            
            # 定义颜色映射
            growth_colors = {
                'positive': (255, 0, 0, 128),     # 红色半透明
                'negative': (0, 255, 0, 128),     # 绿色半透明
                'weak_growth': (255, 165, 0, 128) # 橙色半透明
            }
            
            # 绘制已标注孔位的覆盖层
            if hasattr(self.gui, 'hole_manager') and annotated_holes:
                for hole_number, hole_info in annotated_holes.items():
                    try:
                        # 获取孔位坐标
                        hole_center = self.gui.hole_manager.get_hole_center_coordinates(hole_number)
                        x, y = hole_center
                        
                        # 获取颜色
                        growth_level = hole_info.get('growth_level', 'negative')
                        color = growth_colors.get(growth_level, (128, 128, 128, 128))
                        
                        # 绘制圆形覆盖
                        radius = 30
                        bbox = [x - radius, y - radius, x + radius, y + radius]
                        
                        # 创建透明覆盖层
                        overlay = Image.new('RGBA', panoramic_image.size, (0, 0, 0, 0))
                        overlay_draw = ImageDraw.Draw(overlay)
                        overlay_draw.ellipse(bbox, fill=color)
                        
                        # 合并覆盖层
                        overlay_image = Image.alpha_composite(
                            overlay_image.convert('RGBA'), 
                            overlay
                        ).convert('RGB')
                        
                    except Exception as e:
                        log_debug(f"绘制孔位{hole_number}覆盖层失败: {e}", "IMAGE_PROCESSOR")
                        continue
            
            log_debug(f"创建全景图覆盖层完成，覆盖{len(annotated_holes)}个孔位", "IMAGE_PROCESSOR")
            return overlay_image
            
        except Exception as e:
            log_error(f"创建全景图覆盖层失败: {str(e)}", "IMAGE_PROCESSOR")
            return panoramic_image
    
    def find_panoramic_image(self, filename: str, directory: str) -> Optional[str]:
        """
        查找全景图文件
        
        Args:
            filename: 文件名
            directory: 搜索目录
            
        Returns:
            文件完整路径，如果未找到返回None
        """
        try:
            if not directory or not os.path.exists(directory):
                return None
            
            # 直接路径查找
            direct_path = os.path.join(directory, filename)
            if os.path.exists(direct_path):
                return direct_path
            
            # 递归查找
            for root, dirs, files in os.walk(directory):
                if filename in files:
                    found_path = os.path.join(root, filename)
                    log_debug(f"找到全景图文件: {found_path}", "IMAGE_PROCESSOR")
                    return found_path
            
            log_debug(f"未找到全景图文件: {filename} (在目录 {directory})", "IMAGE_PROCESSOR")
            return None
            
        except Exception as e:
            log_error(f"查找全景图文件失败: {str(e)}", "IMAGE_PROCESSOR")
            return None
    
    def validate_image_file(self, file_path: str) -> bool:
        """
        验证图像文件是否有效
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            如果文件有效返回True，否则返回False
        """
        try:
            if not file_path or not os.path.exists(file_path):
                return False
            
            # 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                return False
            
            # 尝试打开图像
            with Image.open(file_path) as img:
                img.verify()  # 验证图像完整性
            
            return True
            
        except Exception as e:
            log_debug(f"图像文件验证失败 {file_path}: {str(e)}", "IMAGE_PROCESSOR")
            return False
    
    def get_image_info(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        获取图像信息
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            包含图像信息的字典，如果失败返回None
        """
        try:
            if not self.validate_image_file(image_path):
                return None
            
            with Image.open(image_path) as img:
                info = {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'file_size': os.path.getsize(image_path),
                    'file_path': image_path
                }
            
            return info
            
        except Exception as e:
            log_error(f"获取图像信息失败 {image_path}: {str(e)}", "IMAGE_PROCESSOR")
            return None
    
    def _add_to_cache(self, key: str, image: Image.Image):
        """
        添加图像到缓存
        
        Args:
            key: 缓存键
            image: 图像对象
        """
        try:
            # 如果缓存满了，删除最旧的图像
            if len(self._image_cache) >= self._cache_size_limit:
                oldest_key = next(iter(self._image_cache))
                del self._image_cache[oldest_key]
                log_debug(f"缓存已满，删除最旧图像: {oldest_key}", "IMAGE_PROCESSOR")
            
            # 添加新图像到缓存
            self._image_cache[key] = image.copy()
            log_debug(f"图像已添加到缓存: {key} (缓存大小: {len(self._image_cache)})", "IMAGE_PROCESSOR")
            
        except Exception as e:
            log_error(f"添加图像到缓存失败: {str(e)}", "IMAGE_PROCESSOR")
    
    def clear_cache(self):
        """清空图像缓存"""
        try:
            cache_size = len(self._image_cache)
            self._image_cache.clear()
            log_debug(f"图像缓存已清空，释放了{cache_size}张图像", "IMAGE_PROCESSOR")
            
        except Exception as e:
            log_error(f"清空图像缓存失败: {str(e)}", "IMAGE_PROCESSOR")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            缓存统计信息
        """
        return {
            'cache_size': len(self._image_cache),
            'cache_limit': self._cache_size_limit,
            'cached_images': list(self._image_cache.keys())
        }
