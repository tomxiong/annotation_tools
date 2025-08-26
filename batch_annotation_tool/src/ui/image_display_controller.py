"""
图像显示控制模块
处理图像加载、显示和画布管理
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
from typing import Optional, Tuple
import os


class ImageDisplayController:
    """图像显示控制器"""
    
    def __init__(self, gui_instance):
        """初始化图像显示控制器"""
        self.gui = gui_instance
        self.panoramic_image: Optional[Image.Image] = None
        self.slice_image: Optional[Image.Image] = None
        self.panoramic_photo: Optional[ImageTk.PhotoImage] = None
        self.slice_photo: Optional[ImageTk.PhotoImage] = None
    
    def load_panoramic_image(self):
        """加载并显示全景图"""
        if not self.gui.current_panoramic_id:
            return
                
        try:
            # 查找全景图文件
            panoramic_file = None
            panoramic_filename = f"{self.gui.current_panoramic_id}.png"
            
            # 首先在全景图目录中查找
            if hasattr(self.gui, 'panoramic_directory') and self.gui.panoramic_directory:
                panoramic_file = os.path.join(self.gui.panoramic_directory, panoramic_filename)
                if os.path.exists(panoramic_file):
                    pass  # 找到了，继续
                else:
                    # 尝试其他常见格式
                    for ext in ['.jpg', '.jpeg', '.bmp', '.tiff', '.tif']:
                        alt_filename = f"{self.gui.current_panoramic_id}{ext}"
                        alt_path = os.path.join(self.gui.panoramic_directory, alt_filename)
                        if os.path.exists(alt_path):
                            panoramic_file = alt_path
                            break
            
            # 如果全景图目录中没找到，尝试从切片文件路径推断
            if not panoramic_file or not os.path.exists(panoramic_file):
                for file_info in self.gui.slice_files:
                    if file_info['panoramic_id'] == self.gui.current_panoramic_id:
                        # 尝试在切片文件的上级目录查找
                        panoramic_file = os.path.join(
                            os.path.dirname(file_info['filepath']), 
                            "..", 
                            panoramic_filename
                        )
                        panoramic_file = os.path.normpath(panoramic_file)
                        
                        if os.path.exists(panoramic_file):
                            break
                        
                        panoramic_file = None
            
            if not panoramic_file or not os.path.exists(panoramic_file):
                # 如果找不到全景图，显示占位符
                self.show_panoramic_placeholder()
                return
            
            # 加载全景图
            self.panoramic_image = Image.open(panoramic_file)
            
            # 在全景图上绘制孔位标记
            self.draw_hole_markers()
            
            # 显示全景图
            self.display_panoramic_image()
            
        except Exception as e:
            print(f"加载全景图失败: {e}")
            self.show_panoramic_placeholder()
    
    def draw_hole_markers(self):
        """在全景图上绘制孔位标记"""
        if not self.panoramic_image:
            return
        
        # 创建图像副本用于绘制
        img_with_markers = self.panoramic_image.copy()
        draw = ImageDraw.Draw(img_with_markers)
        
        # 绘制所有孔位的标记
        for hole_num in range(1, 121):  # 1-120个孔位
            row, col = self.gui.hole_manager.number_to_position(hole_num)
            
            # 计算孔位在图像中的位置
            x, y = self.gui.hole_manager.get_hole_center_coordinates(hole_num)
            
            # 获取该孔位的标注状态
            existing_ann = self.gui.current_dataset.get_annotation_by_hole(
                self.gui.current_panoramic_id, hole_num
            )
            
            # 根据标注状态选择颜色
            if existing_ann:
                if existing_ann.growth_level == 'positive':
                    color = 'red'
                elif existing_ann.growth_level == 'weak_growth':
                    color = 'orange'
                else:  # negative
                    color = 'green'
            else:
                color = 'gray'  # 未标注
            
            # 绘制孔位标记
            radius = 15
            if hole_num == self.gui.current_hole_number:
                # 当前孔位用更大的圆圈和不同颜色
                draw.ellipse([x-radius-3, y-radius-3, x+radius+3, y+radius+3], 
                           outline='blue', width=3)
            
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                       outline=color, width=2)
            
            # 绘制孔位编号
            draw.text((x-10, y-10), str(hole_num), fill='white')
        
        self.panoramic_image = img_with_markers
    
    def display_panoramic_image(self):
        """显示全景图到画布"""
        if not self.panoramic_image or not hasattr(self.gui, 'panoramic_canvas'):
            return
        
        try:
            # 获取画布尺寸
            canvas_width = self.gui.panoramic_canvas.winfo_width()
            canvas_height = self.gui.panoramic_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # 画布尺寸无效，稍后重试
                self.gui.root.after(100, self.display_panoramic_image)
                return
            
            # 计算缩放比例（保持宽高比）
            img_width, img_height = self.panoramic_image.size
            scale_w = (canvas_width - 20) / img_width
            scale_h = (canvas_height - 20) / img_height
            scale_factor = min(scale_w, scale_h)
            
            # 缩放图像
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)
            resized_image = self.panoramic_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage
            self.panoramic_photo = ImageTk.PhotoImage(resized_image)
            
            # 清除画布并显示图像
            self.gui.panoramic_canvas.delete("all")
            
            # 计算居中位置
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            self.gui.panoramic_canvas.create_image(x, y, anchor=tk.NW, image=self.panoramic_photo)
            
        except Exception as e:
            print(f"显示全景图失败: {e}")
    
    def show_panoramic_placeholder(self):
        """显示全景图占位符"""
        if not hasattr(self.gui, 'panoramic_canvas'):
            return
        
        self.gui.panoramic_canvas.delete("all")
        canvas_width = self.gui.panoramic_canvas.winfo_width()
        canvas_height = self.gui.panoramic_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            self.gui.panoramic_canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text="未找到全景图文件", fill="gray", font=("Arial", 16)
            )
    
    def load_slice_image(self):
        """加载并显示切片图像"""
        if (not self.gui.slice_files or 
            self.gui.current_slice_index >= len(self.gui.slice_files)):
            return
        
        try:
            current_file = self.gui.slice_files[self.gui.current_slice_index]
            image_path = current_file['filepath']
            
            if not os.path.exists(image_path):
                self.show_slice_placeholder(f"文件不存在: {image_path}")
                return
            
            # 加载切片图像
            self.slice_image = Image.open(image_path)
            
            # 显示切片图像
            self.display_slice_image()
            
        except Exception as e:
            print(f"加载切片图像失败: {e}")
            self.show_slice_placeholder(f"加载失败: {str(e)}")
    
    def display_slice_image(self):
        """显示切片图像到画布"""
        if not self.slice_image or not hasattr(self.gui, 'slice_canvas'):
            return
        
        try:
            # 获取画布尺寸
            canvas_width = self.gui.slice_canvas.winfo_width()
            canvas_height = self.gui.slice_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # 画布尺寸无效，稍后重试
                self.gui.root.after(100, self.display_slice_image)
                return
            
            # 计算缩放比例（保持宽高比）
            img_width, img_height = self.slice_image.size
            scale_w = (canvas_width - 20) / img_width
            scale_h = (canvas_height - 20) / img_height
            scale_factor = min(scale_w, scale_h)
            
            # 缩放图像
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)
            resized_image = self.slice_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage
            self.slice_photo = ImageTk.PhotoImage(resized_image)
            
            # 清除画布并显示图像
            self.gui.slice_canvas.delete("all")
            
            # 计算居中位置
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            self.gui.slice_canvas.create_image(x, y, anchor=tk.NW, image=self.slice_photo)
            
        except Exception as e:
            print(f"显示切片图像失败: {e}")
    
    def show_slice_placeholder(self, message: str = "未选择切片文件"):
        """显示切片图像占位符"""
        if not hasattr(self.gui, 'slice_canvas'):
            return
        
        self.gui.slice_canvas.delete("all")
        canvas_width = self.gui.slice_canvas.winfo_width()
        canvas_height = self.gui.slice_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            self.gui.slice_canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text=message, fill="gray", font=("Arial", 12)
            )
    
    def on_panoramic_click(self, event):
        """全景图点击事件处理 - 优化的孔位定位算法"""
        if not self.panoramic_image:
            return
        
        try:
            # 获取画布尺寸
            canvas_width = self.gui.panoramic_canvas.winfo_width()
            canvas_height = self.gui.panoramic_canvas.winfo_height()
            
            # 计算显示图像的实际尺寸（保持宽高比）
            original_width = self.panoramic_image.width
            original_height = self.panoramic_image.height
            
            # 计算缩放比例（保持宽高比，适应画布）
            scale_w = (canvas_width - 20) / original_width
            scale_h = (canvas_height - 20) / original_height
            scale_factor = min(scale_w, scale_h)
            
            # 计算显示尺寸
            display_width = int(original_width * scale_factor)
            display_height = int(original_height * scale_factor)
            
            # 计算图像在画布中的偏移（居中显示）
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2
            
            # 使用优化后的孔位查找方法
            hole_number = self.gui.hole_manager.find_hole_by_coordinates(
                event.x, event.y, scale_factor, offset_x, offset_y
            )
            
            if hole_number and hasattr(self.gui, 'navigation_controller'):
                self.gui.navigation_controller.navigate_to_hole(hole_number)
                self.gui.update_status(f"点击定位到孔位 {hole_number}")
            else:
                self.gui.update_status("点击位置未找到有效孔位")
                
        except Exception as e:
            print(f"孔位点击处理失败: {e}")
            self.gui.update_status("孔位定位失败")
    
    def refresh_display(self):
        """刷新显示"""
        self.load_panoramic_image()
        self.load_slice_image()
    
    def resize_canvas(self, event=None):
        """画布大小改变时的处理"""
        # 重新显示图像以适应新的画布尺寸
        if self.panoramic_image:
            self.display_panoramic_image()
        if self.slice_image:
            self.display_slice_image()