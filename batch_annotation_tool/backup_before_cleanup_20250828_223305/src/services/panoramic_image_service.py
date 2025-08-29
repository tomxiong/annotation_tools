"""
全景图像服务
处理全景图和切片图像的加载、显示、缩放等功能
"""

import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np

from ui.hole_manager import HoleManager


class PanoramicImageService:
    """
    全景图像服务类
    """
    
    def __init__(self):
        self.hole_manager = HoleManager()
        self.panoramic_images: Dict[str, Image.Image] = {}  # 缓存全景图
        self.slice_images: Dict[str, Image.Image] = {}      # 缓存切片图
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    
    def load_panoramic_image(self, image_path: str) -> Optional[Image.Image]:
        """
        加载全景图像
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"全景图文件不存在: {image_path}")
            
            if path.suffix.lower() not in self.supported_formats:
                raise ValueError(f"不支持的图像格式: {path.suffix}")
            
            # 加载图像
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 缓存图像
            panoramic_id = path.stem
            self.panoramic_images[panoramic_id] = image
            
            # 根据图像尺寸设置孔位布局
            self.hole_manager.set_layout_params(image.width, image.height)
            
            return image
            
        except Exception as e:
            messagebox.showerror("错误", f"加载全景图失败: {str(e)}")
            return None
    
    def load_slice_image(self, image_path: str) -> Optional[Image.Image]:
        """
        加载切片图像
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"切片图文件不存在: {image_path}")
            
            if path.suffix.lower() not in self.supported_formats:
                raise ValueError(f"不支持的图像格式: {path.suffix}")
            
            # 加载图像
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 缓存图像
            self.slice_images[path.name] = image
            
            return image
            
        except Exception as e:
            messagebox.showerror("错误", f"加载切片图失败: {str(e)}")
            return None
    
    def find_panoramic_image(self, slice_filename: str, panoramic_dir: str) -> Optional[str]:
        """
        根据切片文件名查找对应的全景图
        切片文件名格式: EB10000026_hole_108.png
        全景图文件名格式: EB10000026.bmp
        """
        try:
            # 解析切片文件名
            stem = Path(slice_filename).stem
            parts = stem.split('_')
            
            if len(parts) != 3 or parts[1] != 'hole':
                raise ValueError(f"切片文件名格式错误: {slice_filename}")
            
            panoramic_id = parts[0]
            
            # 在全景图目录中查找对应文件
            panoramic_path = Path(panoramic_dir)
            if not panoramic_path.exists():
                raise FileNotFoundError(f"全景图目录不存在: {panoramic_dir}")
            
            # 尝试不同的文件扩展名
            for ext in ['.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif']:
                panoramic_file = panoramic_path / f"{panoramic_id}{ext}"
                if panoramic_file.exists():
                    return str(panoramic_file)
            
            raise FileNotFoundError(f"未找到对应的全景图: {panoramic_id}")
            
        except Exception as e:
            print(f"查找全景图失败: {str(e)}")
            return None
    
    def create_panoramic_overlay(self, panoramic_image: Image.Image, 
                                current_hole: int, 
                                annotated_holes: Dict[int, str] = None) -> Image.Image:
        """
        在全景图上创建孔位覆盖层
        显示当前孔位和已标注孔位
        """
        # 创建副本
        overlay_image = panoramic_image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # 颜色定义
        colors = {
            'current': '#FF0000',      # 红色 - 当前孔位
            'negative': '#00FF00',     # 绿色 - 阴性
            'weak_growth': '#FFFF00',  # 黄色 - 弱生长
            'positive': '#FF8000',     # 橙色 - 阳性
            'unannotated': '#CCCCCC'   # 灰色 - 未标注
        }
        
        # 绘制所有孔位
        for hole_number in range(1, 121):
            x, y, width, height = self.hole_manager.get_hole_coordinates(hole_number)
            
            # 确定颜色
            if hole_number == current_hole:
                color = colors['current']
                outline_width = 3
            elif annotated_holes and hole_number in annotated_holes:
                growth_level = annotated_holes[hole_number]
                color = colors.get(growth_level, colors['unannotated'])
                outline_width = 2
            else:
                color = colors['unannotated']
                outline_width = 1
            
            # 绘制孔位边框
            draw.rectangle(
                [x, y, x + width, y + height],
                outline=color,
                width=outline_width
            )
            
            # 绘制孔位编号
            hole_label = self.hole_manager.get_hole_label(hole_number)
            text_x = x + width // 2
            text_y = y + height // 2
            
            # 获取文本尺寸
            bbox = draw.textbbox((0, 0), hole_label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 居中绘制文本
            draw.text(
                (text_x - text_width // 2, text_y - text_height // 2),
                hole_label,
                fill=color,
                font=font
            )
        
        return overlay_image
    
    def resize_image_for_display(self, image: Image.Image, max_width: int, max_height: int, 
                               fill_mode: str = 'fit') -> Image.Image:
        """
        调整图像尺寸以适应显示区域
        
        Args:
            image: 原始图像
            max_width: 最大宽度
            max_height: 最大高度  
            fill_mode: 填充模式
                - 'fit': 保持宽高比，完整显示图像（可能有黑边）
                - 'fill': 填满显示区域，可能裁剪图像
                - 'stretch': 拉伸填满，不保持宽高比
        """
        original_width, original_height = image.size
        
        if fill_mode == 'fit':
            # 保持宽高比，完整显示（默认模式）
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = min(width_ratio, height_ratio)
            
            # 如果图像已经足够小，不需要缩放
            if scale_ratio >= 1.0:
                return image
            
            # 计算新尺寸
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
        elif fill_mode == 'fill':
            # 填满显示区域，保持宽高比，可能裁剪
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = max(width_ratio, height_ratio)
            
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
            # 缩放图像
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 居中裁剪
            left = (new_width - max_width) // 2
            top = (new_height - max_height) // 2
            right = left + max_width
            bottom = top + max_height
            
            return resized.crop((left, top, right, bottom))
            
        elif fill_mode == 'stretch':
            # 拉伸填满，不保持宽高比
            new_width = max_width
            new_height = max_height
            
        else:
            raise ValueError(f"不支持的填充模式: {fill_mode}")
        
        # 使用高质量重采样
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def enhance_slice_image(self, image: Image.Image) -> Image.Image:
        """
        增强切片图像显示效果
        应用对比度增强和噪声抑制
        """
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 应用CLAHE（限制对比度自适应直方图均衡）
        if len(img_array.shape) == 3:
            # 彩色图像，转换为LAB色彩空间
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        else:
            # 灰度图像
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(img_array)
        
        # 轻微高斯滤波去噪
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0.5)
        
        return Image.fromarray(enhanced)
    
    def get_slice_files_from_directory(self, directory: str, panoramic_directory: str = None) -> List[Dict[str, Any]]:
        """
        从目录中获取所有切片文件信息
        支持两种目录结构：
        1. 独立路径：<全景文件>_hole_<孔序号>.png
        2. 子目录结构：<全景文件>\hole_<孔序号>.png
        """
        slice_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return slice_files
        
        # 检测目录结构类型
        structure_type = self._detect_directory_structure(directory_path, panoramic_directory)
        
        if structure_type == "independent":
            # 独立路径模式
            slice_files = self._get_slice_files_independent(directory_path)
        elif structure_type == "subdirectory":
            # 子目录模式
            slice_files = self._get_slice_files_subdirectory(directory_path, panoramic_directory)
        else:
            # 尝试两种模式
            slice_files = self._get_slice_files_independent(directory_path)
            if not slice_files and panoramic_directory:
                slice_files = self._get_slice_files_subdirectory(Path(panoramic_directory), panoramic_directory)
        
        # 按全景图ID和孔位编号排序
        slice_files.sort(key=lambda x: (x['panoramic_id'], x['hole_number']))
        
        return slice_files
    
    def _detect_directory_structure(self, slice_dir: Path, panoramic_dir: str = None) -> str:
        """
        检测目录结构类型
        返回: "independent", "subdirectory", "unknown"
        """
        # 检查独立路径模式
        independent_files = 0
        for file_path in slice_dir.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in self.supported_formats and
                self._is_slice_filename(file_path.name)):
                independent_files += 1
                if independent_files >= 3:  # 找到足够的文件确认模式
                    return "independent"
        
        # 检查子目录模式
        if panoramic_dir:
            panoramic_path = Path(panoramic_dir)
            if panoramic_path.exists():
                subdirectory_files = 0
                for subdir in panoramic_path.iterdir():
                    if subdir.is_dir():
                        for file_path in subdir.rglob('hole_*.png'):
                            if file_path.is_file():
                                subdirectory_files += 1
                                if subdirectory_files >= 3:
                                    return "subdirectory"
        
        return "unknown"
    
    def _get_slice_files_independent(self, directory_path: Path) -> List[Dict[str, Any]]:
        """
        获取独立路径模式的切片文件
        """
        slice_files = []
        
        # 遍历目录中的所有文件
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                filename = file_path.name
                
                # 检查是否是切片文件格式
                if self._is_slice_filename(filename):
                    try:
                        # 解析文件名信息
                        panoramic_id, hole_number = self._parse_slice_filename(filename)
                        
                        slice_info = {
                            'filename': filename,
                            'filepath': str(file_path),
                            'panoramic_id': panoramic_id,
                            'hole_number': hole_number,
                            'relative_path': str(file_path.relative_to(directory_path)),
                            'structure_type': 'independent'
                        }
                        slice_files.append(slice_info)
                        
                    except Exception as e:
                        print(f"解析切片文件名失败 {filename}: {e}")
        
        return slice_files
    
    def _get_slice_files_subdirectory(self, panoramic_path: Path, panoramic_directory: str) -> List[Dict[str, Any]]:
        """
        获取子目录模式的切片文件
        支持两种子目录结构：
        1. 传统子目录：切片文件在 <全景目录>/<全景ID>/hole_<孔序号>.png
        2. 全景文件名子目录：切片文件在 <全景目录>/<全景文件名>/hole_<孔序号>.png
        """
        slice_files = []
        
        # 遍历全景图目录中的子目录
        for subdir in panoramic_path.iterdir():
            if subdir.is_dir():
                panoramic_id = subdir.name
                
                # 在子目录中查找hole_*.png文件
                hole_files_found = False
                for file_path in subdir.rglob('hole_*.png'):
                    if file_path.is_file():
                        filename = file_path.name
                        hole_files_found = True
                        
                        # 解析孔位编号
                        try:
                            hole_number = self._parse_hole_number_from_filename(filename)
                            
                            slice_info = {
                                'filename': filename,
                                'filepath': str(file_path),
                                'panoramic_id': panoramic_id,
                                'hole_number': hole_number,
                                'relative_path': str(file_path.relative_to(panoramic_path)),
                                'structure_type': 'subdirectory'
                            }
                            slice_files.append(slice_info)
                            
                        except Exception as e:
                            print(f"解析子目录切片文件失败 {filename}: {e}")
                
                # 如果子目录中没有找到hole_*.png文件，尝试查找全景图文件
                if not hole_files_found:
                    # 尝试在全景目录中查找对应的全景图文件
                    panoramic_file = None
                    for ext in ['.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif']:
                        potential_file = panoramic_path / f"{panoramic_id}{ext}"
                        if potential_file.exists():
                            panoramic_file = potential_file
                            break
                    
                    # 如果找到全景图文件，则假设切片在全景文件名对应的子目录中
                    if panoramic_file:
                        # 检查是否存在以全景ID命名的子目录
                        panoramic_subdir = panoramic_path / panoramic_id
                        if panoramic_subdir.exists() and panoramic_subdir.is_dir():
                            for file_path in panoramic_subdir.rglob('hole_*.png'):
                                if file_path.is_file():
                                    filename = file_path.name
                                    
                                    # 解析孔位编号
                                    try:
                                        hole_number = self._parse_hole_number_from_filename(filename)
                                        
                                        slice_info = {
                                            'filename': filename,
                                            'filepath': str(file_path),
                                            'panoramic_id': panoramic_id,
                                            'hole_number': hole_number,
                                            'relative_path': str(file_path.relative_to(panoramic_path)),
                                            'structure_type': 'subdirectory'
                                        }
                                        slice_files.append(slice_info)
                                        
                                    except Exception as e:
                                        print(f"解析全景文件名子目录切片文件失败 {filename}: {e}")
        
        return slice_files
    
    def _parse_hole_number_from_filename(self, filename: str) -> int:
        """
        从hole_*.png格式的文件名中解析孔位编号
        """
        stem = Path(filename).stem
        if stem.startswith('hole_'):
            hole_str = stem[5:]  # 去掉'hole_'前缀
            if hole_str.isdigit():
                hole_number = int(hole_str)
                if 1 <= hole_number <= 120:
                    return hole_number
        
        raise ValueError(f"无效的孔位文件名格式: {filename}")
    
    def _is_slice_filename(self, filename: str) -> bool:
        """
        检查文件名是否符合切片文件格式
        格式: EB10000026_hole_108.png
        """
        stem = Path(filename).stem
        parts = stem.split('_')
        
        return (len(parts) == 3 and 
                parts[1] == 'hole' and 
                parts[2].isdigit() and 
                1 <= int(parts[2]) <= 120)
    
    def _parse_slice_filename(self, filename: str) -> Tuple[str, int]:
        """
        解析切片文件名
        返回 (panoramic_id, hole_number)
        """
        stem = Path(filename).stem
        parts = stem.split('_')
        
        if len(parts) != 3 or parts[1] != 'hole':
            raise ValueError(f"文件名格式错误: {filename}")
        
        panoramic_id = parts[0]
        hole_number = int(parts[2])
        
        if not (1 <= hole_number <= 120):
            raise ValueError(f"孔位编号超出范围: {hole_number}")
        
        return panoramic_id, hole_number
    
    def create_thumbnail_grid(self, slice_files: List[Dict[str, Any]], 
                             grid_size: Tuple[int, int] = (10, 12),
                             thumbnail_size: Tuple[int, int] = (50, 50)) -> Optional[Image.Image]:
        """
        创建切片图像的缩略图网格
        用于快速预览整个全景图的所有孔位
        """
        try:
            rows, cols = grid_size
            thumb_width, thumb_height = thumbnail_size
            
            # 创建网格图像
            grid_width = cols * thumb_width
            grid_height = rows * thumb_height
            grid_image = Image.new('RGB', (grid_width, grid_height), 'white')
            
            # 按孔位编号组织文件
            hole_files = {}
            for file_info in slice_files:
                hole_number = file_info['hole_number']
                hole_files[hole_number] = file_info
            
            # 填充网格
            for hole_number in range(1, 121):
                row, col = self.hole_manager.number_to_position(hole_number)
                
                # 计算在网格中的位置
                x = col * thumb_width
                y = row * thumb_height
                
                if hole_number in hole_files:
                    # 加载并缩放图像
                    file_path = hole_files[hole_number]['filepath']
                    try:
                        slice_img = Image.open(file_path)
                        slice_img = slice_img.resize(thumbnail_size, Image.Resampling.LANCZOS)
                        grid_image.paste(slice_img, (x, y))
                    except Exception as e:
                        print(f"加载缩略图失败 {file_path}: {e}")
                        # 创建占位符
                        placeholder = Image.new('RGB', thumbnail_size, 'lightgray')
                        grid_image.paste(placeholder, (x, y))
                else:
                    # 空孔位占位符
                    placeholder = Image.new('RGB', thumbnail_size, 'lightgray')
                    grid_image.paste(placeholder, (x, y))
            
            return grid_image
            
        except Exception as e:
            print(f"创建缩略图网格失败: {e}")
            return None
    
    def get_image_statistics(self, image: Image.Image) -> Dict[str, Any]:
        """
        获取图像统计信息
        """
        img_array = np.array(image)
        
        stats = {
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'format': getattr(image, 'format', 'Unknown'),
            'size_bytes': len(img_array.tobytes())
        }
        
        # 计算像素统计
        if len(img_array.shape) == 3:
            # 彩色图像
            stats['channels'] = img_array.shape[2]
            stats['mean_rgb'] = [float(np.mean(img_array[:, :, i])) for i in range(3)]
            stats['std_rgb'] = [float(np.std(img_array[:, :, i])) for i in range(3)]
        else:
            # 灰度图像
            stats['channels'] = 1
            stats['mean'] = float(np.mean(img_array))
            stats['std'] = float(np.std(img_array))
            stats['min'] = int(np.min(img_array))
            stats['max'] = int(np.max(img_array))
        
        return stats
    
    def clear_cache(self):
        """清理图像缓存"""
        self.panoramic_images.clear()
        self.slice_images.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            'panoramic_images_count': len(self.panoramic_images),
            'slice_images_count': len(self.slice_images),
            'panoramic_images': list(self.panoramic_images.keys()),
            'slice_images': list(self.slice_images.keys())
        }
