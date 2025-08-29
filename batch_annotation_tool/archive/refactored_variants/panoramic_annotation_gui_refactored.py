"""
重构后的全景图像标注工具主界面
使用模块化设计，提高代码可维护性
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
import datetime

# 动态导入模块以避免相对导入问题
import sys
from pathlib import Path

# 获取项目根目录
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent
project_root = src_dir.parent

# 添加src目录到Python路径
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 导入核心模块
from ui.hole_manager import HoleManager
from ui.enhanced_annotation_panel import EnhancedAnnotationPanel
from services.panoramic_image_service import PanoramicImageService
from services.config_file_service import ConfigFileService
from models.panoramic_annotation import PanoramicAnnotation, PanoramicDataset
from models.enhanced_annotation import EnhancedPanoramicAnnotation

# 导入重构后的模块
from ui.navigation_controller import NavigationController
from ui.annotation_manager import AnnotationManager
from ui.image_display_controller import ImageDisplayController
from ui.event_handlers import EventHandlers
from ui.ui_components import UIComponents


class PanoramicAnnotationGUI:
    """
    重构后的全景图像标注工具主界面
    使用模块化设计，各个功能模块独立管理
    """
    
    def __init__(self, root: tk.Tk):
        """初始化GUI"""
        self.root = root
        self.root.title("全景图像标注工具 - 微生物药敏检测 (重构版)")
        self.root.geometry("2400x1300")
        
        # 初始化核心服务
        self.image_service = PanoramicImageService()
        self.hole_manager = HoleManager()
        self.config_service = ConfigFileService()
        
        # 初始化数据
        self.current_dataset = PanoramicDataset("新数据集", "全景图像标注数据集")
        self.slice_files: List[Dict[str, Any]] = []
        self.current_slice_index = 0
        self.current_panoramic_id = ""
        self.current_hole_number = 1
        
        # 初始化状态变量
        self.auto_save_enabled = tk.BooleanVar(value=True)
        self.last_annotation_time = {}
        self.current_annotation_modified = False
        
        # 目录路径
        self.slice_directory = ""
        self.panoramic_directory = ""
        self.slice_dir_var = tk.StringVar()
        self.panoramic_dir_var = tk.StringVar()
        
        # 标注状态变量
        self.current_microbe_type = tk.StringVar(value="bacteria")
        self.current_growth_level = tk.StringVar(value="negative")
        self.interference_factors = {
            'pores': tk.BooleanVar(),
            'artifacts': tk.BooleanVar(),
            'edge_blur': tk.BooleanVar()
        }
        
        # 模式选项变量
        self.use_enhanced_mode = tk.BooleanVar(value=True)
        self.use_subdirectory_mode = tk.BooleanVar(value=True)
        self.use_centered_navigation = tk.BooleanVar(value=True)
        
        # 导航相关变量
        self.hole_number_var = tk.StringVar(value="1")
        self.panoramic_id_var = tk.StringVar()
        
        # 初始化功能模块
        self.navigation_controller = NavigationController(self)
        self.annotation_manager = AnnotationManager(self)
        self.image_display_controller = ImageDisplayController(self)
        self.event_handlers = EventHandlers(self)
        self.ui_components = UIComponents(self)
        
        # 增强标注面板
        self.enhanced_annotation_panel = None
        
        # 创建界面
        # 创建界面
        self.create_widgets()
        self.setup_bindings()
        
        # 初始化状态
        self.update_status("就绪 - 请选择全景图目录和切片目录")
    
    def create_widgets(self):
        """创建界面组件"""
        self.ui_components.create_main_layout()
        
        # 确保全景图显示组件存在
        if not hasattr(self, 'panoramic_canvas'):
            # 如果UI组件没有创建全景图canvas，手动创建
            self.create_panoramic_display()
        
        # 创建增强标注面板
        # 创建增强标注面板
        if hasattr(self, 'enhanced_annotation_frame'):
            self.enhanced_annotation_panel = EnhancedAnnotationPanel(
                self.enhanced_annotation_frame,
                on_annotation_change=self.event_handlers.on_enhanced_annotation_change
            )
    
    def create_panoramic_display(self):
        """创建全景图显示区域（如果不存在）"""
        if not hasattr(self, 'panoramic_canvas'):
            # 创建全景图显示框架
            panoramic_frame = ttk.LabelFrame(self.root, text="全景图 (12×10孔位布局)")
            panoramic_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 创建全景图canvas
            self.panoramic_canvas = tk.Canvas(panoramic_frame, bg='white', width=1400, height=900)
            self.panoramic_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 绑定点击事件
            self.panoramic_canvas.bind("<Button-1>", self.on_panoramic_click)
            
            # 全景图信息标签
            info_frame = ttk.Frame(panoramic_frame)
            info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            
            self.panoramic_info_label = ttk.Label(info_frame, text="未加载全景图")
            self.panoramic_info_label.pack(side=tk.LEFT)
    
    def on_panoramic_click(self, event):
        """处理全景图点击事件"""
        if hasattr(self.event_handlers, 'on_panoramic_click'):
            self.event_handlers.on_panoramic_click(event)
    
    def setup_bindings(self):
        """设置事件绑定"""
        self.event_handlers.setup_bindings()
        self.event_handlers.bind_canvas_events()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.event_handlers.on_window_closing)
    
    def load_data(self):
        """加载数据 - 支持两种目录结构"""
        if not self.panoramic_directory:
            messagebox.showerror("错误", "请先选择全景图目录")
            return
        
        try:
            # 根据模式选项决定如何加载数据
            if self.use_subdirectory_mode.get():
                # 子目录模式：忽略切片目录输入，直接使用全景目录下的子目录
                self.slice_files = self.image_service.get_slice_files_from_directory(
                    self.panoramic_directory, self.panoramic_directory)
                structure_msg = '子目录模式'
            else:
                # 独立路径模式：使用用户指定的切片目录
                if self.slice_directory:
                    self.slice_files = self.image_service.get_slice_files_from_directory(
                        self.slice_directory, self.panoramic_directory)
                    structure_msg = '独立路径模式'
                else:
                    # 尝试从全景图目录加载（兼容旧版本）
                    self.slice_files = self.image_service.get_slice_files_from_directory(
                        self.panoramic_directory, self.panoramic_directory)
                    structure_msg = '自动检测模式'
            
            if not self.slice_files:
                messagebox.showwarning("警告", 
                    "未找到有效的切片文件。\n请检查：\n" +
                    "1. 独立模式：切片文件名格式为 <全景文件>_hole_<孔序号>.png\n" +
                    "2. 子目录模式：切片文件在 <全景文件>/hole_<孔序号>.png")
                return
            
            # 更新全景图列表
            self.navigation_controller.update_panoramic_list()
            
            # 重置状态
            self.current_slice_index = 0
            self.load_current_slice()
            self.update_progress()
            self.update_statistics()
            
            self.update_status(f"成功加载 {len(self.slice_files)} 个切片文件 ({structure_msg})")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
    
    def load_current_slice(self):
        """加载当前切片"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            self.current_panoramic_id = current_file['panoramic_id']
            self.current_hole_number = current_file['hole_number']
            
            # 更新孔位输入框
            self.hole_number_var.set(str(self.current_hole_number))
            
            # 更新全景图下拉列表选中项
            if hasattr(self, 'panoramic_id_var'):
                self.panoramic_id_var.set(self.current_panoramic_id)
            
            # 加载图像
            self.image_display_controller.load_panoramic_image()
            self.image_display_controller.load_slice_image()
            
            # 加载现有标注
            self.load_existing_annotation()
            
            # 加载配置文件标注（如果存在）
            self.annotation_manager.load_config_annotations()
            
            # 更新状态显示
            self.update_annotation_status()
            
        except Exception as e:
            print(f"加载当前切片失败: {e}")
            self.update_status(f"加载切片失败: {str(e)}")
    
    def load_existing_annotation(self):
        """加载现有标注到界面"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        if existing_ann:
            # 更新基础标注界面
            self.current_growth_level.set(existing_ann.growth_level)
            self.current_microbe_type.set(existing_ann.microbe_type)
            
            # 更新增强标注面板
            if self.enhanced_annotation_panel and hasattr(existing_ann, 'enhanced_data'):
                try:
                    self.sync_basic_to_enhanced_annotation(existing_ann)
                except Exception as e:
                    print(f"同步标注到增强面板失败: {e}")
        else:
            # 重置界面状态
            self.current_growth_level.set("negative")
            if self.enhanced_annotation_panel:
                self.enhanced_annotation_panel.reset_to_default()
    
    def sync_basic_to_enhanced_annotation(self, annotation):
        """同步基础标注到增强标注面板"""
        if not self.enhanced_annotation_panel:
            return
        
        try:
            from models.enhanced_annotation import GrowthLevel, GrowthPattern, InterferenceType, FeatureCombination
            
            # 映射生长级别
            growth_level_map = {
                'negative': GrowthLevel.NEGATIVE,
                'weak_growth': GrowthLevel.WEAK_GROWTH,
                'positive': GrowthLevel.POSITIVE
            }
            
            growth_level = growth_level_map.get(annotation.growth_level, GrowthLevel.NEGATIVE)
            
            # 映射干扰因素
            interference_map = {
                'pores': InterferenceType.PORES,
                'artifacts': InterferenceType.ARTIFACTS,
                'edge_blur': InterferenceType.EDGE_BLUR,
                'contamination': InterferenceType.CONTAMINATION,
                'scratches': InterferenceType.SCRATCHES
            }
            
            interference_factors = set()
            for factor in annotation.interference_factors:
                if factor in interference_map:
                    interference_factors.add(interference_map[factor])
            
            # 根据干扰因素推断生长模式
            growth_pattern = None
            if not interference_factors:
                growth_pattern = GrowthPattern.CLEAN
            
            # 创建特征组合
            combination = FeatureCombination(
                growth_level=growth_level,
                growth_pattern=growth_pattern,
                interference_factors=interference_factors,
                confidence=getattr(annotation, 'confidence', 1.0)
            )
            
            # 设置到增强标注面板
            self.enhanced_annotation_panel.set_feature_combination(combination)
            
        except Exception as e:
            print(f"同步基础标注到增强面板失败: {e}")
    
    def update_progress(self):
        """更新进度显示"""
        if hasattr(self, 'progress_label'):
            total = len(self.slice_files)
            current = self.current_slice_index + 1
            self.progress_label.config(text=f"{current}/{total}")
    
    def update_statistics(self):
        """更新统计信息"""
        if not hasattr(self, 'stats_label'):
            return
        
        stats = {
            'negative': 0,
            'weak_growth': 0,
            'positive': 0,
            'total': 0
        }
        
        for annotation in self.current_dataset.annotations:
            if annotation.panoramic_id == self.current_panoramic_id:
                stats['total'] += 1
                if annotation.growth_level in stats:
                    stats[annotation.growth_level] += 1
        
        unannotated = 120 - stats['total']  # 假设每个全景图有120个孔位
        
        stats_text = f"统计: 未标注 {unannotated}, 阴性 {stats['negative']}, 弱生长 {stats['weak_growth']}, 阳性 {stats['positive']}"
        self.stats_label.config(text=stats_text)
    
    def update_annotation_status(self):
        """更新标注状态显示"""
        if hasattr(self, 'annotation_status_label'):
            status_text = self.annotation_manager.get_annotation_status_text()
            self.annotation_status_label.config(text=status_text)
    
    def update_status(self, message: str):
        """更新状态栏"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
    
    def save_dataset(self):
        """保存数据集"""
        if not self.current_dataset.annotations:
            messagebox.showwarning("警告", "没有标注数据可保存")
            return
        
        filename = filedialog.asksaveasfilename(
            title="保存数据集",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.current_dataset.save_to_file(filename)
                self.update_status(f"数据集已保存到: {filename}")
                messagebox.showinfo("成功", f"数据集已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存数据集失败: {str(e)}")
    
    def load_dataset(self):
        """加载数据集"""
        filename = filedialog.askopenfilename(
            title="加载数据集",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.current_dataset = PanoramicDataset.load_from_file(filename)
                self.update_statistics()
                self.update_annotation_status()
                self.image_display_controller.load_panoramic_image()  # 重新加载以显示标注
                self.update_status(f"数据集已加载: {filename}")
                messagebox.showinfo("成功", f"数据集已加载: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"加载数据集失败: {str(e)}")
    
    def export_annotations(self):
        """导出标注数据"""
        if not self.current_dataset.annotations:
            messagebox.showwarning("警告", "没有标注数据可导出")
            return
        
        filename = filedialog.asksaveasfilename(
            title="导出标注数据",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.csv'):
                    self.current_dataset.export_to_csv(filename)
                else:
                    self.current_dataset.export_to_json(filename)
                
                self.update_status(f"标注数据已导出到: {filename}")
                messagebox.showinfo("成功", f"标注数据已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出标注数据失败: {str(e)}")
    
    # ==================== 方法委托 ====================
    # 导航控制器方法委托
    def go_prev_panoramic(self):
        """导航到上一个全景图"""
        return self.navigation_controller.go_prev_panoramic()
    
    def go_next_panoramic(self):
        """导航到下一个全景图"""
        return self.navigation_controller.go_next_panoramic()
    
    def go_to_panoramic(self, panoramic_id):
        """导航到指定全景图"""
        return self.navigation_controller.go_to_panoramic(panoramic_id)
    
    def go_up(self):
        """向上导航"""
        return self.navigation_controller.go_up()
    
    def go_down(self):
        """向下导航"""
        return self.navigation_controller.go_down()
    
    def go_left(self):
        """向左导航"""
        return self.navigation_controller.go_left()
    
    def go_right(self):
        """向右导航"""
        return self.navigation_controller.go_right()
    
    def go_first_hole(self):
        """导航到首个孔位"""
        return self.navigation_controller.go_first_hole()
    
    def go_last_hole(self):
        """导航到最后孔位"""
        return self.navigation_controller.go_last_hole()
    
    def go_prev_hole(self):
        """导航到上一个孔位"""
        return self.navigation_controller.go_prev_hole()
    
    def go_next_hole(self):
        """导航到下一个孔位"""
        return self.navigation_controller.go_next_hole()
    
    def go_to_hole(self, hole_number=None):
        """导航到指定孔位"""
        return self.navigation_controller.go_to_hole(hole_number)
    
    # 标注管理器方法委托
    def save_current_annotation(self):
        """保存当前标注"""
        return self.annotation_manager.save_current_annotation()
    
    def clear_current_annotation(self):
        """清除当前标注"""
        return self.annotation_manager.clear_current_annotation()
    
    def annotate_row(self, growth_level):
        """标注整行"""
        return self.annotation_manager.annotate_row(growth_level)
    
    def annotate_column(self, growth_level):
        """标注整列"""
        return self.annotation_manager.annotate_column(growth_level)
    
    # 图像显示控制器方法委托
    def refresh_display(self):
        """刷新显示"""
        return self.image_display_controller.refresh_display()


def main():
    """主函数"""
    root = tk.Tk()
    app = PanoramicAnnotationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()