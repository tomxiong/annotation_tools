"""
图像处理功能Mixin
包含所有图像相关的方法
"""
import os
from PIL import Image, ImageTk
from tkinter import messagebox

class ImageMixin:
    """图像处理功能混入类"""
    
    def load_current_slice(self):
        """加载当前切片"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            image_path = current_file['path']
            
            # 更新当前全景图ID
            self.current_panoramic_id = current_file['panoramic_id']
            
            # 加载图像
            self.load_image(image_path)
            
            # 更新信息显示
            self.update_slice_info()
            
            # 加载对应的标注
            self.load_annotation_for_current_slice()
            
            # 更新全景图下拉列表
            if hasattr(self, 'panoramic_id_var'):
                self.panoramic_id_var.set(self.current_panoramic_id)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载切片失败: {e}")
    
    def load_image(self, image_path):
        """加载并显示图像"""
        try:
            if not os.path.exists(image_path):
                self.update_status(f"图像文件不存在: {image_path}")
                return
            
            # 加载图像
            image = Image.open(image_path)
            
            # 获取画布尺寸
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # 如果画布尺寸为1，说明还没有完全初始化，使用默认尺寸
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600
            
            # 计算缩放比例
            image_width, image_height = image.size
            scale_x = canvas_width / image_width
            scale_y = canvas_height / image_height
            self.scale_factor = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
            
            # 缩放图像
            new_width = int(image_width * self.scale_factor)
            new_height = int(image_height * self.scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter格式
            self.current_image = ImageTk.PhotoImage(image)
            
            # 清空画布并显示图像
            self.canvas.delete("all")
            
            # 计算居中位置
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            self.canvas.create_image(x, y, anchor="nw", image=self.current_image)
            
            # 保存图像位置和尺寸信息
            self.image_x = x
            self.image_y = y
            self.image_width = new_width
            self.image_height = new_height
            
            self.update_status(f"已加载图像: {os.path.basename(image_path)}")
            
        except Exception as e:
            self.update_status(f"加载图像失败: {e}")
            messagebox.showerror("错误", f"加载图像失败: {e}")
    
    def update_slice_info(self):
        """更新切片信息显示"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            
            # 更新信息标签
            info_text = (f"全景图: {current_file['panoramic_id']} | "
                        f"孔位: {current_file['hole_number']} | "
                        f"切片: {self.current_slice_index + 1}/{len(self.slice_files)}")
            
            self.info_label.config(text=info_text)
            
            # 更新孔位输入框
            if hasattr(self, 'hole_entry'):
                self.hole_entry.delete(0, 'end')
                self.hole_entry.insert(0, str(current_file['hole_number']))
            
        except Exception as e:
            print(f"更新切片信息失败: {e}")
    
    def zoom_in(self):
        """放大图像"""
        if hasattr(self, 'current_image') and self.current_image:
            # 这里可以实现图像放大功能
            self.update_status("放大功能待实现")
    
    def zoom_out(self):
        """缩小图像"""
        if hasattr(self, 'current_image') and self.current_image:
            # 这里可以实现图像缩小功能
            self.update_status("缩小功能待实现")
    
    def reset_zoom(self):
        """重置缩放"""
        if self.slice_files and self.current_slice_index < len(self.slice_files):
            current_file = self.slice_files[self.current_slice_index]
            self.load_image(current_file['path'])
    
    def fit_to_window(self):
        """适应窗口大小"""
        if self.slice_files and self.current_slice_index < len(self.slice_files):
            current_file = self.slice_files[self.current_slice_index]
            self.load_image(current_file['path'])
    
    def on_canvas_resize(self, event):
        """处理画布大小改变事件"""
        # 重新加载当前图像以适应新的画布尺寸
        if hasattr(self, 'slice_files') and self.slice_files and self.current_slice_index < len(self.slice_files):
            current_file = self.slice_files[self.current_slice_index]
            self.load_image(current_file['path'])
    
    def on_canvas_click(self, event):
        """处理画布点击事件"""
        # 这里可以实现图像点击功能，比如添加标记点
        if hasattr(self, 'image_x') and hasattr(self, 'image_y'):
            # 计算相对于图像的坐标
            rel_x = event.x - self.image_x
            rel_y = event.y - self.image_y
            
            # 检查点击是否在图像范围内
            if (0 <= rel_x <= self.image_width and 0 <= rel_y <= self.image_height):
                self.update_status(f"点击位置: ({rel_x}, {rel_y})")