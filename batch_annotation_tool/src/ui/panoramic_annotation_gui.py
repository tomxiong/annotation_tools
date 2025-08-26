"""
全景图像标注工具主界面
基于Tkinter的图形用户界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkFont
from PIL import Image, ImageTk
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
import json

# 动态导入模块以避免相对导入问题
import sys
import os
from pathlib import Path

# 获取项目根目录
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent
project_root = src_dir.parent

# 添加src目录到Python路径
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 直接导入模块
from ui.hole_manager import HoleManager
from ui.hole_config_panel import HoleConfigPanel
from ui.enhanced_annotation_panel import EnhancedAnnotationPanel
from services.panoramic_image_service import PanoramicImageService
from services.config_file_service import ConfigFileService
from models.panoramic_annotation import PanoramicAnnotation, PanoramicDataset
from models.enhanced_annotation import EnhancedPanoramicAnnotation
from ui.batch_import_dialog import show_batch_import_dialog


class PanoramicAnnotationGUI:
    """
    全景图像标注工具主界面
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("全景图像标注工具 - 微生物药敏检测")
        self.root.geometry("2400x1300")
        
        # 服务和管理器
        self.image_service = PanoramicImageService()
        self.hole_manager = HoleManager()
        self.config_service = ConfigFileService()
        
        # 数据
        self.current_dataset = PanoramicDataset("新数据集", "全景图像标注数据集")
        self.slice_files: List[Dict[str, Any]] = []
        self.current_slice_index = 0
        self.current_panoramic_id = ""
        self.current_hole_number = 1
        
        # 自动保存控制
        self.auto_save_enabled = tk.BooleanVar(value=True)
        self.last_annotation_time = {}  # 记录每个孔位的最后标注时间
        self.current_annotation_modified = False  # 当前标注是否已修改
        
        # 目录路径
        self.slice_directory = ""
        self.panoramic_directory = ""
        
        # 图像显示
        self.panoramic_image: Optional[Image.Image] = None
        self.slice_image: Optional[Image.Image] = None
        self.panoramic_photo: Optional[ImageTk.PhotoImage] = None
        self.slice_photo: Optional[ImageTk.PhotoImage] = None
        
        # 标注状态
        # 标注状态
        self.current_microbe_type = tk.StringVar(value="bacteria")
        self.current_growth_level = tk.StringVar(value="negative")
        self.interference_factors = {
            'pores': tk.BooleanVar(),
            'artifacts': tk.BooleanVar(),
            'edge_blur': tk.BooleanVar()
        }
        
        # 全景图导航相关变量
        self.panoramic_ids = []  # 存储所有全景图ID
        self.panoramic_id_var = tk.StringVar()  # 当前选中的全景图ID
        
        # Enhanced annotation panel
        self.enhanced_annotation_panel = None
        
        # 创建界面
        self.create_widgets()
        self.setup_bindings()
        
        # 状态栏
        self.update_status("就绪 - 请选择切片目录和全景图目录")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 顶部工具栏
        self.create_toolbar(main_frame)
        
        # 中间内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 左侧全景图区域
        self.create_panoramic_panel(content_frame)
        
        # 中间分隔符
        separator = ttk.Separator(content_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 右侧切片和控制区域
        self.create_slice_panel(content_frame)
        
        # 孔位参数配置面板 - 已找到合适参数，暂时注释掉
        # 孔位参数配置面板 - 包含起始孔位设置
        # 孔位参数配置面板 - 隐藏，使用默认值
        # self.create_hole_config_panel(content_frame)
        
        # 底部状态栏
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # 全景图目录选择（必选）
        ttk.Label(toolbar, text="全景图目录:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.panoramic_dir_var = tk.StringVar()
        panoramic_dir_entry = ttk.Entry(toolbar, textvariable=self.panoramic_dir_var, width=50)
        panoramic_dir_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toolbar, text="浏览", 
                  command=self.select_panoramic_directory).pack(side=tk.LEFT, padx=(0, 10))
        
        # 切片目录选择（可选，用于独立路径模式）
        ttk.Label(toolbar, text="切片目录(可选):").pack(side=tk.LEFT, padx=(0, 5))
        
        self.slice_dir_var = tk.StringVar()
        slice_dir_entry = ttk.Entry(toolbar, textvariable=self.slice_dir_var, width=40)
        slice_dir_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toolbar, text="浏览", 
                  command=self.select_slice_directory).pack(side=tk.LEFT, padx=(0, 10))
        
        # 模式选项
        options_frame = ttk.Frame(toolbar)
        options_frame.pack(side=tk.LEFT, padx=(10, 10))
        
        # 子目录模式选项
        self.use_subdirectory_mode = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="子目录模式", 
                       variable=self.use_subdirectory_mode).pack(side=tk.LEFT, padx=(0, 5))
        
        # 居中导航选项
        self.use_centered_navigation = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="居中导航", 
                       variable=self.use_centered_navigation).pack(side=tk.LEFT, padx=(0, 5))
        
        # 加载按钮
        ttk.Button(toolbar, text="加载数据", 
                  command=self.load_data).pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存按钮
        ttk.Button(toolbar, text="保存标注", 
                  command=self.save_annotations).pack(side=tk.LEFT, padx=(0, 5))
        
        # 导出按钮
        ttk.Button(toolbar, text="导出训练数据", 
                  command=self.export_training_data).pack(side=tk.LEFT, padx=(0, 10))
        
        # 加载标注按钮
        ttk.Button(toolbar, text="加载标注", 
                  command=self.load_annotations).pack(side=tk.LEFT, padx=(0, 5))
        
        # 批量导入按钮
        ttk.Button(toolbar, text="批量导入", 
                  command=self.batch_import_annotations).pack(side=tk.LEFT)
    
    def create_panoramic_panel(self, parent):
        """创建全景图显示面板"""
        panoramic_frame = ttk.LabelFrame(parent, text="全景图 (12×10孔位布局)")
        panoramic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 全景图显示区域 - 调整尺寸以适应3088×2064比例
        # 全景图显示区域 - 增大尺寸适应2560×1440全屏操作
        self.panoramic_canvas = tk.Canvas(panoramic_frame, bg='white', width=1400, height=900)
        self.panoramic_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定鼠标点击事件
        self.panoramic_canvas.bind("<Button-1>", self.on_panoramic_click)
        
        # 全景图信息
        info_frame = ttk.Frame(panoramic_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.panoramic_info_label = ttk.Label(info_frame, text="未加载全景图")
        self.panoramic_info_label.pack(side=tk.LEFT)
    
    def create_slice_panel(self, parent):
        """创建切片显示和控制面板"""
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        # 批量操作 - 移到第一个位置
        self.create_batch_panel(right_frame)
        
        # 切片显示区域 - 缩小显示区域，按原始大小显示
        slice_frame = ttk.LabelFrame(right_frame, text="当前切片")
        slice_frame.pack(fill=tk.X, padx=(0, 0), pady=(0, 5))
        
        # 减小切片画布尺寸，使用原始大小显示
        self.slice_canvas = tk.Canvas(slice_frame, bg='white', width=200, height=200)
        self.slice_canvas.pack(padx=5, pady=5)
        
        # 切片信息
        slice_info_frame = ttk.Frame(slice_frame)
        slice_info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.slice_info_label = ttk.Label(slice_info_frame, text="未加载切片")
        self.slice_info_label.pack()
        
        # 导航控制
        self.create_navigation_panel(right_frame)
        
        # 标注控制 - 现在是最后一个区域，可以动态扩展
        self.create_annotation_panel(right_frame)
    
    def create_hole_config_panel(self, parent):
        """创建孔位配置面板"""
        # 创建孔位配置面板实例
        self.hole_config_panel = HoleConfigPanel(parent, self.apply_hole_config)
        
    def apply_hole_config(self, config: dict):
        """应用孔位配置"""
        try:
            # 更新HoleManager的参数
            self.hole_manager.update_positioning_params(
                first_hole_x=config['first_x'],
                first_hole_y=config['first_y'],
                horizontal_spacing=config['spacing_x'],
                vertical_spacing=config['spacing_y'],
                hole_diameter=config['hole_size'],
                start_hole=config.get('start_hole', 25)  # 默认从25号孔开始
            )
            
            # 更新PanoramicImageService中的hole_manager引用
            self.image_service.hole_manager = self.hole_manager
            
            # 重新加载全景图以显示新的孔位定位
            self.load_panoramic_image()
            
            start_hole = config.get('start_hole', 25)
            self.update_status(f"已应用孔位配置: 起始({config['first_x']},{config['first_y']}) 间距({config['spacing_x']},{config['spacing_y']}) 起始孔位({start_hole})")
            
        except Exception as e:
            messagebox.showerror("错误", f"应用孔位配置失败: {str(e)}")
    
    def create_navigation_panel(self, parent):
        """创建导航控制面板"""
        nav_frame = ttk.LabelFrame(parent, text="导航控制")
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 创建全景图导航部分
        panoramic_label = ttk.Label(nav_frame, text="全景图导航")
        panoramic_label.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        panoramic_frame = ttk.Frame(nav_frame)
        panoramic_frame.pack(pady=5, padx=5)
        
        # 上一个全景图按钮
        ttk.Button(panoramic_frame, text="◀ 上一全景", width=10,
                  command=self.go_prev_panoramic).pack(side=tk.LEFT, padx=2)
        
        # 全景图下拉列表
        # 全景图下拉列表
        self.panoramic_combobox = ttk.Combobox(panoramic_frame, 
                                              textvariable=self.panoramic_id_var,
                                              width=20)
        self.panoramic_combobox.pack(side=tk.LEFT, padx=5)
        self.panoramic_combobox.bind('<<ComboboxSelected>>', self.on_panoramic_selected)
        
        # 下一个全景图按钮
        ttk.Button(panoramic_frame, text="下一全景 ▶", width=10,
                  command=self.go_next_panoramic).pack(side=tk.LEFT, padx=2)
        
        # 添加分隔线
        separator1 = ttk.Separator(nav_frame, orient='horizontal')
        separator1.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建方向导航部分（基于孔位的二维布局）
        direction_label = ttk.Label(nav_frame, text="方向导航")
        direction_label.pack(anchor=tk.W, padx=5, pady=(0, 0))
        
        direction_frame = ttk.Frame(nav_frame)
        direction_frame.pack(pady=5, padx=5)
        
        # 上方向按钮
        ttk.Button(direction_frame, text="↑", width=4,
                  command=self.go_up).grid(row=0, column=1, padx=1, pady=1)
        
        # 左方向按钮、孔位输入框、右方向按钮
        ttk.Button(direction_frame, text="←", width=4,
                  command=self.go_left).grid(row=1, column=0, padx=1, pady=1)
        
        # 孔位输入框放在中间位置
        entry_frame = ttk.Frame(direction_frame)
        entry_frame.grid(row=1, column=1, padx=1, pady=1)
        
        self.hole_number_var = tk.StringVar(value="1")
        hole_entry = ttk.Entry(entry_frame, textvariable=self.hole_number_var, width=8)
        hole_entry.pack(padx=2, pady=2)
        hole_entry.bind('<Return>', self.go_to_hole)
        
        ttk.Button(direction_frame, text="→", width=4,
                  command=self.go_right).grid(row=1, column=2, padx=1, pady=1)
        
        # 下方向按钮
        ttk.Button(direction_frame, text="↓", width=4,
                  command=self.go_down).grid(row=2, column=1, padx=1, pady=1)
        
        # 添加分隔线
        separator2 = ttk.Separator(nav_frame, orient='horizontal')
        separator2.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建序列导航部分（基于切片文件列表的顺序）
        sequence_label = ttk.Label(nav_frame, text="序列导航")
        sequence_label.pack(anchor=tk.W, padx=5, pady=(0, 0))
        
        sequence_frame = ttk.Frame(nav_frame)
        sequence_frame.pack(pady=5, padx=5)
        
        # 序列导航按钮：首个、上一个、下一个、最后
        ttk.Button(sequence_frame, text="◀◀ 首个", width=8,
                  command=self.go_first_hole).pack(side=tk.LEFT, padx=2)
        ttk.Button(sequence_frame, text="◀ 上一个", width=8,
                  command=self.go_prev_hole).pack(side=tk.LEFT, padx=2)
        ttk.Button(sequence_frame, text="下一个 ▶", width=8,
                  command=self.go_next_hole).pack(side=tk.LEFT, padx=2)
        ttk.Button(sequence_frame, text="最后 ▶▶", width=8,
                  command=self.go_last_hole).pack(side=tk.LEFT, padx=2)
        
        # 进度信息
        self.progress_label = ttk.Label(nav_frame, text="0/0")
        self.progress_label.pack(pady=2)
    
    def create_annotation_panel(self, parent):
        """创建标注控制面板"""
        ann_frame = ttk.LabelFrame(parent, text="标注控制")
        ann_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        # 标注按钮 - 移动到增强标注面板之上
        self.button_frame = ttk.Frame(ann_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=(5, 5))
        
        ttk.Button(self.button_frame, text="保存并下一个", 
                  command=self.save_current_annotation).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="跳过", 
                  command=self.skip_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="清除标注", 
                  command=self.clear_current_annotation).pack(side=tk.LEFT, padx=5)
        
        # 创建增强标注面板 - 放在按钮下方
        self.enhanced_annotation_frame = ttk.Frame(ann_frame)
        self.enhanced_annotation_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 初始化enhanced annotation panel
        self.enhanced_annotation_panel = EnhancedAnnotationPanel(
            self.enhanced_annotation_frame,
            on_annotation_change=self.on_enhanced_annotation_change
        )
    
    def create_basic_annotation_controls(self, parent):
        """创建基础标注控件"""
        # 微生物类型
        microbe_frame = ttk.Frame(parent)
        microbe_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(microbe_frame, text="微生物类型:").pack(side=tk.LEFT)
        ttk.Radiobutton(microbe_frame, text="细菌", variable=self.current_microbe_type, 
                       value="bacteria").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(microbe_frame, text="真菌", variable=self.current_microbe_type, 
                       value="fungi").pack(side=tk.LEFT, padx=5)
        
        # 生长级别
        growth_frame = ttk.Frame(parent)
        growth_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(growth_frame, text="生长级别:").pack(anchor=tk.W)
        
        growth_buttons_frame = ttk.Frame(growth_frame)
        growth_buttons_frame.pack(fill=tk.X, pady=2)
        
        ttk.Radiobutton(growth_buttons_frame, text="阴性", variable=self.current_growth_level, 
                       value="negative", command=self.on_growth_level_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(growth_buttons_frame, text="弱生长", variable=self.current_growth_level, 
                       value="weak_growth", command=self.on_growth_level_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(growth_buttons_frame, text="阳性", variable=self.current_growth_level, 
                       value="positive", command=self.on_growth_level_change).pack(side=tk.LEFT, padx=5)
        
        # 干扰因素
        interference_frame = ttk.Frame(parent)
        interference_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(interference_frame, text="干扰因素:").pack(anchor=tk.W)
        
        factors_frame = ttk.Frame(interference_frame)
        factors_frame.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(factors_frame, text="气孔", 
                       variable=self.interference_factors['pores']).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(factors_frame, text="杂质", 
                       variable=self.interference_factors['artifacts']).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(factors_frame, text="边缘模糊", 
                       variable=self.interference_factors['edge_blur']).pack(side=tk.LEFT, padx=5)
    
    def toggle_annotation_mode(self):
        """切换标注模式"""
        # 清除当前显示的面板
        for widget in self.annotation_content_frame.winfo_children():
            widget.pack_forget()
        
        if self.use_enhanced_annotation.get():
            # 显示增强标注面板
            self.enhanced_annotation_frame.pack(fill=tk.BOTH, expand=True)
        else:
            # 显示基础标注面板
            self.basic_annotation_frame.pack(fill=tk.BOTH, expand=True)
    
    def on_enhanced_annotation_change(self, annotation_data=None):
        """增强标注变化回调"""
        # 标记当前标注已修改
        self.current_annotation_modified = True
        # 可以在这里添加实时预览或验证逻辑
        pass
    
    def get_annotation_status_text(self):
        """获取标注状态文本，包含日期时间 - 只有增强标注才算已标注"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        if existing_ann:
            # 检查是否为增强标注
            has_enhanced = (hasattr(existing_ann, 'enhanced_data') and 
                          existing_ann.enhanced_data and 
                          existing_ann.annotation_source == 'enhanced_manual')
            
            if has_enhanced:
                # 增强标注 - 显示已标注状态
                annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                if annotation_key in self.last_annotation_time:
                    import datetime
                    datetime_str = self.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")
                    return f"状态: 已标注 ({datetime_str}) - {existing_ann.growth_level}"
                else:
                    # 尝试从标注对象获取时间戳
                    if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                        import datetime
                        try:
                            if isinstance(existing_ann.timestamp, str):
                                dt = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                            else:
                                dt = existing_ann.timestamp
                            datetime_str = dt.strftime("%m-%d %H:%M:%S")
                            return f"状态: 已标注 ({datetime_str}) - {existing_ann.growth_level}"
                        except:
                            pass
                    return f"状态: 已标注 - {existing_ann.growth_level}"
            else:
                # 配置导入或其他类型 - 显示为配置导入状态
                return f"状态: 配置导入 - {existing_ann.growth_level}"
        else:
            return "状态: 未标注"
    
    def create_batch_panel(self, parent):
        """创建批量操作面板"""
        batch_frame = ttk.LabelFrame(parent, text="批量操作")
        batch_frame.pack(fill=tk.X, pady=(0, 0))
        
        # 统计信息
        stats_frame = ttk.Frame(batch_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.stats_label = ttk.Label(stats_frame, text="统计: 未标注 0, 阴性 0, 弱生长 0, 阳性 0")
        self.stats_label.pack()
        
        # 批量操作按钮
        batch_buttons_frame = ttk.Frame(batch_frame)
        batch_buttons_frame.pack(fill=tk.X, padx=5, pady=0)
        
        ttk.Button(batch_buttons_frame, text="标注整行为阴性", 
                  command=self.batch_annotate_row_negative).pack(side=tk.LEFT, padx=2)
        ttk.Button(batch_buttons_frame, text="标注整列为阴性", 
                  command=self.batch_annotate_col_negative).pack(side=tk.LEFT, padx=2)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def setup_bindings(self):
        """设置键盘快捷键"""
        # 只在非输入控件获得焦点时响应快捷键
        self.root.bind('<Key-1>', self.on_key_1)
        self.root.bind('<Key-2>', self.on_key_2)
        self.root.bind('<Key-3>', self.on_key_3)
        self.root.bind('<Left>', self.on_key_left)
        self.root.bind('<Right>', self.on_key_right)
        self.root.bind('<Up>', self.on_key_up)
        self.root.bind('<Down>', self.on_key_down)
        self.root.bind('<space>', self.on_key_space)
        self.root.bind('<Return>', self.on_key_return)
        
        # 设置焦点以接收键盘事件
        self.root.focus_set()
    
    def is_input_widget_focused(self):
        """检查当前焦点是否在输入控件上"""
        focused_widget = self.root.focus_get()
        if focused_widget is None:
            return False
        
        # 检查是否是Entry或Text控件
        widget_class = focused_widget.__class__.__name__
        return widget_class in ['Entry', 'Text', 'Spinbox']
    
    def on_key_1(self, event):
        """数字键1事件处理"""
        if not self.is_input_widget_focused():
            self.set_growth_level('negative')
    
    def on_key_2(self, event):
        """数字键2事件处理"""
        if not self.is_input_widget_focused():
            self.set_growth_level('weak_growth')
    
    def on_key_3(self, event):
        """数字键3事件处理"""
        if not self.is_input_widget_focused():
            self.set_growth_level('positive')
    
    def on_key_left(self, event):
        """左箭头键事件处理"""
        if not self.is_input_widget_focused():
            self.go_left()
    
    def on_key_right(self, event):
        """右箭头键事件处理"""
        if not self.is_input_widget_focused():
            self.go_right()
    
    def on_key_up(self, event):
        """上箭头键事件处理"""
        if not self.is_input_widget_focused():
            self.go_up()
    
    def on_key_down(self, event):
        """下箭头键事件处理"""
        if not self.is_input_widget_focused():
            self.go_down()
    
    def on_key_space(self, event):
        """空格键事件处理"""
        if not self.is_input_widget_focused():
            self.save_current_annotation()
    
    def on_key_return(self, event):
        """回车键事件处理"""
        if not self.is_input_widget_focused():
            self.go_next_hole()
    
    def select_slice_directory(self):
        """选择切片目录"""
        directory = filedialog.askdirectory(title="选择切片图像目录")
        if directory:
            self.slice_dir_var.set(directory)
            self.slice_directory = directory
    
    def select_panoramic_directory(self):
        """选择全景图目录"""
        directory = filedialog.askdirectory(title="选择全景图目录")
        if directory:
            self.panoramic_dir_var.set(directory)
            self.panoramic_directory = directory
    
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
            self.update_panoramic_list()
            
            # 重置状态
            # 重置状态
            self.current_dataset = PanoramicDataset("新数据集", 
                f"从 {self.panoramic_directory} 加载的数据集 ({structure_msg})")
            
            # 找到第一个有效孔位的索引（从起始孔位开始）
            self.current_slice_index = self.find_first_valid_slice_index()
            
            # 加载第一个有效切片
            self.load_current_slice()
            
            self.update_status(f"已加载 {len(self.slice_files)} 个切片文件 ({structure_msg})")
            self.update_progress()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
    
    def find_first_valid_slice_index(self) -> int:
        """找到第一个有效孔位的切片索引"""
        if not self.slice_files:
            return 0
        
        start_hole = self.hole_manager.start_hole_number
        
        # 查找第一个孔位号大于等于起始孔位的切片
        for i, slice_file in enumerate(self.slice_files):
            hole_number = slice_file.get('hole_number', 1)
            if hole_number >= start_hole:
                return i
        
        # 如果没找到有效孔位，返回0
        return 0
    
    def load_current_slice(self):
        """加载当前切片"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return
        
        current_file = self.slice_files[self.current_slice_index]
        
        try:
            # 更新当前信息
            # 更新当前信息
            self.current_panoramic_id = current_file['panoramic_id']
            self.current_hole_number = current_file['hole_number']
            self.hole_number_var.set(str(self.current_hole_number))
            
            # 更新全景图下拉列表选中项
            if self.current_panoramic_id and self.current_panoramic_id in self.panoramic_ids:
                self.panoramic_id_var.set(self.current_panoramic_id)
            
            # 加载切片图像
            self.slice_image = self.image_service.load_slice_image(current_file['filepath'])
            if self.slice_image:
                # 增强显示效果
                enhanced_slice = self.image_service.enhance_slice_image(self.slice_image)
                # 按原始大小显示，不进行放大
                self.slice_photo = ImageTk.PhotoImage(enhanced_slice)
                
                # 显示在画布上
                self.slice_canvas.delete("all")
                canvas_width = self.slice_canvas.winfo_width()
                canvas_height = self.slice_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:  # 确保画布已初始化
                    x = canvas_width // 2
                    y = canvas_height // 2
                    self.slice_canvas.create_image(x, y, image=self.slice_photo)
            
            # 加载对应的全景图
            self.load_panoramic_image()
            
            # 更新切片信息，包含标注状态
            hole_label = self.hole_manager.get_hole_label(self.current_hole_number)
            annotation_status = self.get_annotation_status_text()
            self.slice_info_label.config(text=f"文件: {current_file['filename']}\n孔位: {hole_label} ({self.current_hole_number})\n{annotation_status}")
            
            # 加载已有标注
            self.load_existing_annotation()
            
            # 重置修改标记
            self.current_annotation_modified = False
            
            # 尝试加载配置文件标注
            self.load_config_annotations()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载切片失败: {str(e)}")
    
    def load_panoramic_image(self):
        """加载全景图"""
        if not self.current_panoramic_id:
            return
        
        try:
            # 查找全景图文件
            panoramic_file = self.image_service.find_panoramic_image(
                f"{self.current_panoramic_id}_hole_1.png", 
                self.panoramic_directory
            )
            
            if not panoramic_file:
                self.panoramic_info_label.config(text=f"未找到全景图: {self.current_panoramic_id}")
                return
            
            # 加载全景图
            self.panoramic_image = self.image_service.load_panoramic_image(panoramic_file)
            if self.panoramic_image:
                # 获取已标注孔位信息
                annotated_holes = {}
                for ann in self.current_dataset.get_annotations_by_panoramic_id(self.current_panoramic_id):
                    annotated_holes[ann.hole_number] = ann.growth_level
                
                # 创建带标注覆盖的全景图
                overlay_image = self.image_service.create_panoramic_overlay(
                    self.panoramic_image, 
                    self.current_hole_number,
                    annotated_holes
                )
                
                # 调整尺寸适应显示 - 使用fill模式减少黑边，更好利用画布空间
                canvas_width = self.panoramic_canvas.winfo_width()
                canvas_height = self.panoramic_canvas.winfo_height()
                
                # 使用实际画布尺寸，留少量边距
                target_width = max(canvas_width - 40, 1300)  # 最小1300px宽度
                target_height = max(canvas_height - 40, 800)  # 最小800px高度
                
                display_panoramic = self.image_service.resize_image_for_display(
                    overlay_image, target_width, target_height, fill_mode='fit'
                )
                self.panoramic_photo = ImageTk.PhotoImage(display_panoramic)
                
                # 显示在画布上
                self.panoramic_canvas.delete("all")
                canvas_width = self.panoramic_canvas.winfo_width()
                canvas_height = self.panoramic_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    x = canvas_width // 2
                    y = canvas_height // 2
                    self.panoramic_canvas.create_image(x, y, image=self.panoramic_photo)
                
                # 更新全景图信息
                self.panoramic_info_label.config(text=f"全景图: {self.current_panoramic_id} ({self.panoramic_image.width}×{self.panoramic_image.height})")
            
        except Exception as e:
            print(f"加载全景图失败: {str(e)}")
            self.panoramic_info_label.config(text=f"加载全景图失败: {self.current_panoramic_id}")
    
    def load_existing_annotation(self):
        """加载已有标注"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        if existing_ann:
            # 设置界面状态
            self.current_microbe_type.set(existing_ann.microbe_type)
            self.current_growth_level.set(existing_ann.growth_level)
            
            # 同步到增强标注面板
            if self.enhanced_annotation_panel:
                # 检查是否有增强标注数据
                if (hasattr(existing_ann, 'enhanced_data') and 
                    existing_ann.enhanced_data and 
                    existing_ann.annotation_source == 'enhanced_manual'):
                    try:
                        from models.enhanced_annotation import FeatureCombination
                        enhanced_data = existing_ann.enhanced_data
                        
                        # 确保enhanced_data是字典格式
                        if isinstance(enhanced_data, dict):
                            # 检查是否包含feature_combination数据
                            if 'feature_combination' in enhanced_data:
                                combination_data = enhanced_data['feature_combination']
                            else:
                                combination_data = enhanced_data
                            
                            combination = FeatureCombination.from_dict(combination_data)
                            self.enhanced_annotation_panel.set_feature_combination(combination)
                            
                            # 同步时间戳到内存
                            if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                                import datetime
                                try:
                                    if isinstance(existing_ann.timestamp, str):
                                        dt = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                                    else:
                                        dt = existing_ann.timestamp
                                    annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                                    self.last_annotation_time[annotation_key] = dt
                                except Exception as e:
                                    print(f"时间戳解析失败: {e}")
                        else:
                            print(f"增强数据格式错误: {type(enhanced_data)}")
                            self.sync_basic_to_enhanced_annotation(existing_ann)
                    except Exception as e:
                        print(f"增强标注数据恢复失败: {e}")
                        # 如果增强数据解析失败，使用基础数据
                        self.sync_basic_to_enhanced_annotation(existing_ann)
                else:
                    # 配置导入或其他类型标注，使用基础数据同步到增强面板
                    self.sync_basic_to_enhanced_annotation(existing_ann)
            
            # 设置干扰因素（向后兼容）
            for factor in self.interference_factors:
                self.interference_factors[factor].set(factor in existing_ann.interference_factors)
        else:
            # 没有标注时，重置增强标注面板
            if self.enhanced_annotation_panel:
                self.enhanced_annotation_panel.reset_annotation()
    
    def sync_basic_to_enhanced_annotation(self, annotation):
        """将基础标注同步到增强标注面板"""
        try:
            from models.enhanced_annotation import FeatureCombination, GrowthLevel, GrowthPattern, InterferenceType
            
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
    
    def load_config_annotations(self):
        """加载配置文件中的标注数据"""
        if not self.current_panoramic_id or not self.panoramic_directory:
            return
        
        try:
            # 查找全景图文件
            panoramic_file = self.image_service.find_panoramic_image(
                f"{self.current_panoramic_id}_hole_1.png", 
                self.panoramic_directory
            )
            
            if not panoramic_file:
                return
            
            # 查找对应的配置文件
            config_file = self.config_service.find_config_file(panoramic_file)
            if not config_file:
                return
            
            # 解析配置文件
            config_annotations = self.config_service.parse_config_file(config_file)
            if not config_annotations:
                return
            
            # 导入标注数据
            imported_count = 0
            for hole_number, growth_level in config_annotations.items():
                # 检查是否已存在标注
                existing_ann = self.current_dataset.get_annotation_by_hole(
                    self.current_panoramic_id, hole_number
                )
                
                if not existing_ann:  # 只导入未标注的孔位
                    # 查找对应的切片文件
                    slice_filename = f"{self.current_panoramic_id}_hole_{hole_number}.png"
                    
                    # 创建标注对象 - 配置文件导入，未确认状态
                    annotation = PanoramicAnnotation.from_filename(
                        slice_filename,
                        label=growth_level,
                        bbox=[0, 0, 70, 70],
                        confidence=0.8,  # 配置文件导入的置信度
                        microbe_type=self.current_microbe_type.get(),
                        growth_level=growth_level,
                        interference_factors=[],
                        annotation_source="config_import",
                        is_confirmed=False,
                        panoramic_id=self.current_panoramic_id
                    )
                    
                    # 查找对应的切片文件完整路径
                    for file_info in self.slice_files:
                        if (file_info['panoramic_id'] == self.current_panoramic_id and 
                            file_info['hole_number'] == hole_number):
                            annotation.image_path = file_info['filepath']
                            break
                    
                    self.current_dataset.add_annotation(annotation)
                    imported_count += 1
            
            if imported_count > 0:
                self.update_status(f"从配置文件导入了 {imported_count} 个标注")
                self.update_statistics()
            
        except Exception as e:
            print(f"加载配置文件标注失败: {e}")
    
    def save_current_annotation(self):
        """保存当前标注并跳转到下一个"""
        try:
            if self.save_current_annotation_internal():
                # 自动跳转到下一个
                self.go_next_hole()
                
                current_file = self.slice_files[self.current_slice_index - 1] if self.current_slice_index > 0 else self.slice_files[self.current_slice_index]
                self.update_status(f"已保存标注: {current_file['filename']}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存标注失败: {str(e)}")
    
    def skip_current(self):
        """跳过当前切片"""
        self.go_next_hole()
        self.update_status("已跳过当前切片")
    
    def clear_current_annotation(self):
        """清除当前标注"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        if existing_ann:
            self.current_dataset.annotations.remove(existing_ann)
            self.load_panoramic_image()
            self.update_statistics()
            self.update_status("已清除当前标注")
        
        # 重置界面状态
        self.current_growth_level.set("negative")
        for var in self.interference_factors.values():
            var.set(False)
    
    def on_growth_level_change(self):
        """生长级别改变时的处理"""
        # 可以在这里添加自动保存逻辑或其他处理
        pass
    
    def set_growth_level(self, level: str):
        """设置生长级别（快捷键使用）"""
        self.current_growth_level.set(level)
        self.on_growth_level_change()
    
    # 导航方法
    def go_first_hole(self):
        """跳转到第一个全景图的第一个孔位"""
        if not self.slice_files:
            return
        
        # 找到第一个全景图的第一个孔位
        first_panoramic_id = None
        for i, file_info in enumerate(self.slice_files):
            if first_panoramic_id is None:
                first_panoramic_id = file_info['panoramic_id']
                self.current_slice_index = i
                break
            elif file_info['panoramic_id'] != first_panoramic_id:
                break
        
        self.load_current_slice()
        self.update_progress()
    
    def go_last_hole(self):
        """跳转到最后一个全景图的最后一个孔位"""
        if not self.slice_files:
            return
        
        # 找到最后一个全景图的最后一个孔位
        last_panoramic_id = None
        last_index = 0
        for i, file_info in enumerate(self.slice_files):
            if file_info['panoramic_id'] != last_panoramic_id:
                last_panoramic_id = file_info['panoramic_id']
                last_index = i
        
        # 找到该全景图的最后一个孔位
        for i in range(last_index, len(self.slice_files)):
            if self.slice_files[i]['panoramic_id'] == last_panoramic_id:
                self.current_slice_index = i
            else:
                break
        else:
            # 如果循环正常结束，说明到了文件列表末尾
            self.current_slice_index = len(self.slice_files) - 1
        
        self.load_current_slice()
        self.update_progress()
    
    def go_prev_hole(self):
        """上一个孔位"""
        # 自动保存当前标注
        self.auto_save_current_annotation()
        
        # 查找上一个有效孔位
        start_hole = self.hole_manager.start_hole_number
        current_index = self.current_slice_index
        
        for i in range(current_index - 1, -1, -1):
            if i < len(self.slice_files):
                hole_number = self.slice_files[i].get('hole_number', 1)
                if hole_number >= start_hole:
                    self.current_slice_index = i
                    self.load_current_slice()
                    self.update_progress()
                    return
        
        # 如果没找到有效的上一个孔位，保持当前位置
        self.update_status(f"已到达起始孔位({start_hole})，无法继续向前")
        
    def go_next_hole(self):
        """下一个孔位"""
        # 自动保存当前标注
        self.auto_save_current_annotation()
        
        # 查找下一个有效孔位
        start_hole = self.hole_manager.start_hole_number
        current_index = self.current_slice_index
        
        for i in range(current_index + 1, len(self.slice_files)):
            hole_number = self.slice_files[i].get('hole_number', 1)
            if hole_number >= start_hole:
                self.current_slice_index = i
                self.load_current_slice()
                self.update_progress()
                return
        
        # 如果没找到有效的下一个孔位，保持当前位置
        self.update_status("已到达最后一个有效孔位")
    
    def auto_save_current_annotation(self):
        """自动保存当前标注（如果已修改且启用自动保存）"""
        if self.auto_save_enabled.get() and self.current_annotation_modified:
            try:
                self.save_current_annotation_internal()
                self.update_status("自动保存完成")
            except Exception as e:
                print(f"自动保存失败: {e}")
    
    def save_current_annotation_internal(self):
        """内部保存方法，不自动跳转"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            
            # 使用增强标注模式 - 唯一的标注方式
            feature_combination = self.enhanced_annotation_panel.get_current_feature_combination()
            
            # 创建增强标注对象
            enhanced_annotation = EnhancedPanoramicAnnotation(
                image_path=current_file['filepath'],
                bbox=[0, 0, 70, 70],
                panoramic_image_id=current_file.get('panoramic_id'),
                hole_number=self.current_hole_number,
                microbe_type=self.current_microbe_type.get(),
                feature_combination=feature_combination,
                annotation_source="enhanced_manual",
                is_confirmed=True
            )
            
            # 转换为训练标签
            training_label = enhanced_annotation.get_training_label()
            
            # 创建兼容的PanoramicAnnotation对象用于显示
            annotation = PanoramicAnnotation.from_filename(
                current_file['filename'],
                label=training_label,
                bbox=[0, 0, 70, 70],
                confidence=feature_combination.confidence,  # 使用设置的置信度
                microbe_type=self.current_microbe_type.get(),
                growth_level=feature_combination.growth_level.value,
                interference_factors=[f.value for f in feature_combination.interference_factors],
                annotation_source="enhanced_manual",
                is_confirmed=True,
                panoramic_id=current_file.get('panoramic_id')
            )
            
            # 存储增强标注数据
            annotation.enhanced_data = enhanced_annotation.to_dict()
            
            # 添加时间戳
            import datetime
            annotation.timestamp = datetime.datetime.now().isoformat()
            
            # 更新image_path为完整路径
            annotation.image_path = current_file['filepath']
            
            # 移除已有标注（如果存在）
            existing_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id, 
                self.current_hole_number
            )
            if existing_ann:
                self.current_dataset.annotations.remove(existing_ann)
            
            # 添加新标注
            self.current_dataset.add_annotation(annotation)
            
            # 记录标注时间
            import datetime
            annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
            self.last_annotation_time[annotation_key] = datetime.datetime.now()
            
            # 更新显示
            self.load_panoramic_image()
            self.update_statistics()
            
            # 重置修改标记
            self.current_annotation_modified = False
            
            return True
            
        except Exception as e:
            raise Exception(f"保存标注失败: {str(e)}")
    
    def go_to_hole(self, event=None):
        """跳转到指定孔位"""
        try:
            hole_number = int(self.hole_number_var.get())
            
            # 查找对应的切片文件索引
            for i, file_info in enumerate(self.slice_files):
                if (file_info['panoramic_id'] == self.current_panoramic_id and 
                    file_info['hole_number'] == hole_number):
                    self.current_slice_index = i
                    self.load_current_slice()
                    self.update_progress()
                    return
            
            messagebox.showwarning("警告", f"未找到孔位 {hole_number} 的切片文件")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的孔位编号")
    
    def go_up(self):
        """向上导航"""
        if self.use_centered_navigation.get():
            # 居中导航模式：计算当前行上方的中间孔位
            self.navigate_to_middle('up')
        else:
            # 传统导航模式：移动到上方相邻孔位
            nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
            if nav_info['can_go_up']:
                target_hole = nav_info['up_hole']
                self.navigate_to_hole(target_hole)
    
    def go_down(self):
        """向下导航"""
        if self.use_centered_navigation.get():
            # 居中导航模式：计算当前行下方的中间孔位
            self.navigate_to_middle('down')
        else:
            # 传统导航模式：移动到下方相邻孔位
            nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
            if nav_info['can_go_down']:
                target_hole = nav_info['down_hole']
                self.navigate_to_hole(target_hole)
    
    def go_left(self):
        """向左导航"""
        if self.use_centered_navigation.get():
            # 居中导航模式：计算当前列左侧的中间孔位
            self.navigate_to_middle('left')
        else:
            # 传统导航模式：移动到左侧相邻孔位
            nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
            if nav_info['can_go_left']:
                target_hole = nav_info['left_hole']
                self.navigate_to_hole(target_hole)
    
    def go_right(self):
        """向右导航"""
        if self.use_centered_navigation.get():
            # 居中导航模式：计算当前列右侧的中间孔位
            self.navigate_to_middle('right')
        else:
            # 传统导航模式：移动到右侧相邻孔位
            nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
            if nav_info['can_go_right']:
                target_hole = nav_info['right_hole']
                self.navigate_to_hole(target_hole)
    
    def navigate_to_middle(self, direction: str):
        """导航到指定方向的中间位置"""
        middle_hole = self.get_middle_hole_in_direction(direction)
        if middle_hole:
            self.navigate_to_hole(middle_hole)
            self.update_status(f"已导航到{direction}方向的中间位置: 孔位 {middle_hole}")
        else:
            self.update_status(f"无法导航到{direction}方向的中间位置")
    
    def get_middle_hole_in_direction(self, direction: str) -> int:
        """计算指定方向上的中间孔位"""
        current_row, current_col = self.hole_manager.number_to_position(self.current_hole_number)
        
        if direction == 'up':
            if current_row <= 0:  # 已经在最上面一行
                return None
            target_row = current_row - 1
            target_col = 5  # 中间列（0-11中的第6列）
            return self.hole_manager.position_to_number(target_row, target_col)
            
        elif direction == 'down':
            if current_row >= 9:  # 已经在最下面一行
                return None
            target_row = current_row + 1
            target_col = 5  # 中间列（0-11中的第6列）
            return self.hole_manager.position_to_number(target_row, target_col)
            
        elif direction == 'left':
            if current_col <= 0:  # 已经在最左边一列
                return None
            target_row = 4  # 中间行（0-9中的第5行）
            target_col = current_col - 1
            return self.hole_manager.position_to_number(target_row, target_col)
            
        elif direction == 'right':
            if current_col >= 11:  # 已经在最右边一列
                return None
            target_row = 4  # 中间行（0-9中的第5行）
            target_col = current_col + 1
            return self.hole_manager.position_to_number(target_row, target_col)
            
        return None
    
    def navigate_to_hole(self, hole_number: int):
        """导航到指定孔位"""
        if not hole_number:
            return
            
        # 查找对应的切片文件索引
        for i, file_info in enumerate(self.slice_files):
            if (file_info['panoramic_id'] == self.current_panoramic_id and 
                file_info['hole_number'] == hole_number):
                self.current_slice_index = i
                self.load_current_slice()
                self.update_progress()
                return
        
        # 如果当前全景图没有该孔位，尝试查找其他全景图
        for i, file_info in enumerate(self.slice_files):
            if file_info['hole_number'] == hole_number:
                self.current_slice_index = i
                self.load_current_slice()
                self.update_progress()
                return
    
    def on_panoramic_click(self, event):
        """全景图点击事件处理 - 优化的孔位定位算法"""
        if not self.panoramic_image:
            return
        
        try:
            # 获取画布尺寸
            canvas_width = self.panoramic_canvas.winfo_width()
            canvas_height = self.panoramic_canvas.winfo_height()
            
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
            hole_number = self.hole_manager.find_hole_by_coordinates(
                event.x, event.y, scale_factor, offset_x, offset_y
            )
                        
            if hole_number:
                # 检查孔位是否可用于标注
                if self.hole_manager.is_hole_available_for_annotation(hole_number):
                    self.navigate_to_hole(hole_number)
                    self.update_status(f"点击定位到孔位 {hole_number}")
                else:
                    self.update_status(f"孔位 {hole_number} 在起始孔位({self.hole_manager.start_hole_number})之前，已忽略")
            else:
                self.update_status("点击位置未找到有效孔位")
                
        except Exception as e:
            print(f"孔位点击处理失败: {e}")
            self.update_status("孔位定位失败")
    
    def batch_annotate_row_negative(self):
        """批量标注整行为阴性"""
        if not self.current_panoramic_id:
            return
        
        row, col = self.hole_manager.number_to_position(self.current_hole_number)
        
        # 获取同行的所有孔位
        row_holes = []
        for c in range(12):
            hole_num = self.hole_manager.position_to_number(row, c)
            row_holes.append(hole_num)
        
        # 批量标注
        self.batch_annotate_holes(row_holes, 'negative')
        
        self.update_status(f"已批量标注第 {row + 1} 行为阴性")
    
    def batch_annotate_col_negative(self):
        """批量标注整列为阴性"""
        if not self.current_panoramic_id:
            return
        
        row, col = self.hole_manager.number_to_position(self.current_hole_number)
        
        # 获取同列的所有孔位
        col_holes = []
        for r in range(10):
            hole_num = self.hole_manager.position_to_number(r, col)
            col_holes.append(hole_num)
        
        # 批量标注
        self.batch_annotate_holes(col_holes, 'negative')
        
        self.update_status(f"已批量标注第 {col + 1} 列为阴性")
    
    def batch_annotate_holes(self, hole_numbers: List[int], growth_level: str):
        """批量标注指定孔位"""
        count = 0
        for hole_number in hole_numbers:
            # 查找对应的切片文件
            for file_info in self.slice_files:
                if (file_info['panoramic_id'] == self.current_panoramic_id and 
                    file_info['hole_number'] == hole_number):
                    
                    # 创建标注 - 批量操作，已确认状态
                    annotation = PanoramicAnnotation.from_filename(
                        file_info['filename'],
                        label=growth_level,
                        bbox=[0, 0, 70, 70],
                        confidence=1.0,
                        microbe_type=self.current_microbe_type.get(),
                        growth_level=growth_level,
                        interference_factors=[],
                        annotation_source="batch_operation",
                        is_confirmed=True,
                        panoramic_id=file_info.get('panoramic_id')
                    )
                    
                    # 设置完整文件路径
                    annotation.image_path = file_info['filepath']
                    
                    # 移除已有标注
                    existing_ann = self.current_dataset.get_annotation_by_hole(
                        self.current_panoramic_id, hole_number
                    )
                    if existing_ann:
                        self.current_dataset.annotations.remove(existing_ann)
                    
                    # 添加新标注
                    self.current_dataset.add_annotation(annotation)
                    count += 1
                    break
        
        # 更新显示
        self.load_panoramic_image()
        self.update_statistics()
        
        return count
    
    def update_progress(self):
        """更新进度显示"""
        if self.slice_files:
            current = self.current_slice_index + 1
            total = len(self.slice_files)
            self.progress_label.config(text=f"{current}/{total}")
        else:
            self.progress_label.config(text="0/0")
    
    def update_statistics(self):
        """更新统计信息 - 基于增强标注"""
        if not self.slice_files:
            self.stats_label.config(text="统计: 无数据")
            return
        
        # 统计各类别数量
        stats = {
            'negative': 0,
            'weak_growth': 0, 
            'positive': 0,
            'total': len(self.slice_files),
            'enhanced_annotated': 0,  # 增强标注数量
            'config_only': 0          # 仅有配置文件标注
        }
        
        for file_info in self.slice_files:
            panoramic_id = file_info.get('panoramic_id', '')
            hole_number = file_info.get('hole_number', 0)
            
            annotation = self.current_dataset.get_annotation_by_hole(panoramic_id, hole_number)
            if annotation:
                # 检查是否有增强标注数据
                has_enhanced = (hasattr(annotation, 'enhanced_data') and 
                              annotation.enhanced_data and 
                              annotation.annotation_source == 'enhanced_manual')
                
                if has_enhanced:
                    # 只有增强标注才算真正已标注
                    stats['enhanced_annotated'] += 1
                    growth_level = annotation.growth_level
                    if growth_level in stats:
                        stats[growth_level] += 1
                else:
                    # 仅有配置文件导入的标注，不算已标注
                    stats['config_only'] += 1
        
        stats['unannotated'] = stats['total'] - stats['enhanced_annotated']
        
        # 更新显示
        if stats['config_only'] > 0:
            stats_text = f"统计: 未标注 {stats['unannotated']}, 阴性 {stats['negative']}, 弱生长 {stats['weak_growth']}, 阳性 {stats['positive']} (配置导入: {stats['config_only']})"
        else:
            stats_text = f"统计: 未标注 {stats['unannotated']}, 阴性 {stats['negative']}, 弱生长 {stats['weak_growth']}, 阳性 {stats['positive']}"
        self.stats_label.config(text=stats_text)
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def save_annotations(self):
        """保存标注结果 - 只保存增强标注数据"""
        if not self.current_dataset.annotations:
            messagebox.showwarning("警告", "没有标注数据需要保存")
            return
        
        # 筛选出增强标注数据
        enhanced_annotations = []
        for annotation in self.current_dataset.annotations:
            # 只保存增强标注
            if (hasattr(annotation, 'enhanced_data') and 
                annotation.enhanced_data and 
                annotation.annotation_source == 'enhanced_manual'):
                enhanced_annotations.append(annotation)
        
        if not enhanced_annotations:
            messagebox.showwarning("警告", "没有增强标注数据需要保存\n请先进行增强标注操作")
            return
        
        # 选择保存文件
        filename = filedialog.asksaveasfilename(
            title="保存增强标注结果",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # 创建临时数据集，只包含增强标注
                temp_dataset = PanoramicDataset(
                    name=f"{self.current_dataset.name} - 增强标注",
                    description=f"增强标注数据 ({len(enhanced_annotations)} 个标注)"
                )
                temp_dataset.annotations = enhanced_annotations
                
                # 保存增强标注数据
                temp_dataset.save_to_json(filename)
                
                messagebox.showinfo("成功", 
                    f"增强标注结果已保存到: {filename}\n"
                    f"保存了 {len(enhanced_annotations)} 个增强标注")
                self.update_status(f"已保存 {len(enhanced_annotations)} 个增强标注: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def load_annotations(self):
        """加载标注结果进行review"""
        # 选择标注文件
        filename = filedialog.askopenfilename(
            title="选择标注文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # 加载标注数据
            loaded_dataset = PanoramicDataset.load_from_json(filename)
            
            # 合并到当前数据集
            merge_count = 0
            for annotation in loaded_dataset.annotations:
                # 检查是否已存在相同标注
                existing_ann = self.current_dataset.get_annotation_by_hole(
                    annotation.panoramic_image_id, 
                    annotation.hole_number
                )
                if existing_ann:
                    self.current_dataset.annotations.remove(existing_ann)
                
                # 添加加载的标注
                self.current_dataset.add_annotation(annotation)
                merge_count += 1
            
            # 更新显示
            self.load_panoramic_image()
            self.update_statistics()
            self.load_existing_annotation()  # 重新加载当前切片的标注
            
            messagebox.showinfo("成功", f"已加载 {merge_count} 个标注进行review")
            self.update_status(f"已加载标注文件: {filename} ({merge_count} 个标注)")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载标注文件失败: {str(e)}")
    
    def batch_import_annotations(self):
        """批量导入标注"""
        def import_callback(annotations):
            """导入回调函数"""
            try:
                imported_count = 0
                
                for ann_data in annotations:
                    # 创建PanoramicAnnotation对象
                    annotation = PanoramicAnnotation(
                        image_path=ann_data['slice_filename'],
                        label=ann_data['growth_level'],
                        bbox=ann_data['bbox'],
                        confidence=ann_data['confidence'],
                        panoramic_image_id=ann_data['panoramic_id'],
                        hole_number=ann_data['hole_number'],
                        hole_row=ann_data['hole_row'],
                        hole_col=ann_data['hole_col'],
                        microbe_type=ann_data['microbe_type'],
                        growth_level=ann_data['growth_level'],
                        interference_factors=[]
                    )
                    
                    # 检查是否已存在相同标注
                    existing_ann = self.current_dataset.get_annotation_by_hole(
                        ann_data['panoramic_id'], ann_data['hole_number']
                    )
                    if existing_ann:
                        self.current_dataset.annotations.remove(existing_ann)
                    
                    # 添加新标注
                    self.current_dataset.add_annotation(annotation)
                    imported_count += 1
                
                # 更新显示
                self.load_panoramic_image()
                self.update_statistics()
                self.update_status(f"成功导入 {imported_count} 个标注")
                
            except Exception as e:
                messagebox.showerror("错误", f"导入处理失败: {str(e)}")
        
        # 显示批量导入对话框
        show_batch_import_dialog(self.root, import_callback)
    
    def export_training_data(self):
        """导出训练数据"""
        if not self.current_dataset.annotations:
            messagebox.showwarning("警告", "没有标注数据需要导出")
            return
        
        # 选择导出目录
        output_dir = filedialog.askdirectory(title="选择导出目录")
        if not output_dir:
            return
        
        try:
            # 分别导出细菌和真菌数据
            bacteria_summary = self.current_dataset.export_for_training(output_dir, 'bacteria')
            fungi_summary = self.current_dataset.export_for_training(output_dir, 'fungi')
            
            # 显示导出摘要
            summary_text = f"导出完成!\n\n细菌数据: {bacteria_summary['total_exported']} 个样本\n"
            summary_text += f"真菌数据: {fungi_summary['total_exported']} 个样本\n\n"
            summary_text += f"导出目录: {output_dir}"
            
            messagebox.showinfo("导出完成", summary_text)
            messagebox.showinfo("导出完成", summary_text)
            self.update_status(f"已导出训练数据到: {output_dir}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    # ==================== 全景图导航方法 ====================
    
    def update_panoramic_list(self):
        """更新全景图列表"""
        try:
            # 从切片文件中提取唯一的全景图ID
            panoramic_ids = set()
            for slice_file in self.slice_files:
                panoramic_ids.add(slice_file['panoramic_id'])
            
            self.panoramic_ids = sorted(list(panoramic_ids))
            
            # 更新下拉列表
            if hasattr(self, 'panoramic_combobox'):
                self.panoramic_combobox['values'] = self.panoramic_ids
                
                # 设置当前选中项
                if self.current_panoramic_id in self.panoramic_ids:
                    self.panoramic_combobox.set(self.current_panoramic_id)
                elif self.panoramic_ids:
                    self.panoramic_combobox.set(self.panoramic_ids[0])
            
        except Exception as e:
            print(f"更新全景图列表失败: {e}")
    
    def on_panoramic_selected(self, event=None):
        """处理全景图选择事件"""
        selected_panoramic_id = self.panoramic_id_var.get()
        if selected_panoramic_id and selected_panoramic_id != self.current_panoramic_id:
            self.go_to_panoramic(selected_panoramic_id)
    
    def go_prev_panoramic(self):
        """导航到上一个全景图"""
        if not self.panoramic_ids:
            return
        
        # 保存当前标注
        self.save_current_annotation_internal()
        
        # 计算上一个全景图索引（循环）
        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)
        
        prev_index = (current_index - 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[prev_index]
        
        # 导航到目标全景图
        self.go_to_panoramic(target_panoramic_id)
    
    def go_next_panoramic(self):
        """导航到下一个全景图"""
        if not self.panoramic_ids:
            return
        
        # 保存当前标注
        self.save_current_annotation_internal()
        
        # 计算下一个全景图索引（循环）
        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)
        
        next_index = (current_index + 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[next_index]
        
        # 导航到目标全景图
        self.go_to_panoramic(target_panoramic_id)
    
    def go_to_panoramic(self, panoramic_id):
        """导航到指定全景图"""
        if panoramic_id not in self.panoramic_ids:
            messagebox.showerror("错误", f"全景图 {panoramic_id} 不存在")
            return
        
        # 保存当前标注
        self.save_current_annotation_internal()
        
        # 查找目标全景图的第一个孔位
        # 查找目标全景图的第一个有效孔位（从起始孔位开始）
        target_slice_index = None
        start_hole = self.hole_manager.start_hole_number
        
        for i, slice_file in enumerate(self.slice_files):
            if (slice_file['panoramic_id'] == panoramic_id and 
                slice_file.get('hole_number', 1) >= start_hole):
                target_slice_index = i
                break
        
        if target_slice_index is not None:
            # 更新当前索引和全景图ID
            self.current_slice_index = target_slice_index
            self.current_panoramic_id = panoramic_id
            
            # 更新下拉列表选中项
            if hasattr(self, 'panoramic_combobox'):
                self.panoramic_id_var.set(panoramic_id)
            
            # 加载新的切片
            self.load_current_slice()
            self.update_progress()
            self.update_statistics()
            
            self.update_status(f"已切换到全景图: {panoramic_id}")
        else:
            messagebox.showerror("错误", f"未找到全景图 {panoramic_id} 的切片文件")
    
    def save_current_annotation_internal(self):
        """内部保存方法，不自动跳转"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return False
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            
            # 使用增强标注模式
            if hasattr(self, 'enhanced_annotation_panel') and self.enhanced_annotation_panel:
                feature_combination = self.enhanced_annotation_panel.get_current_feature_combination()
                
                # 创建增强标注对象
                enhanced_annotation = EnhancedPanoramicAnnotation(
                    image_path=current_file['filepath'],
                    bbox=[0, 0, 70, 70],
                    panoramic_image_id=current_file.get('panoramic_id'),
                    hole_number=current_file.get('hole_number'),
                    hole_row=self.hole_manager.get_row_from_hole_number(current_file.get('hole_number', 1)),
                    hole_col=self.hole_manager.get_col_from_hole_number(current_file.get('hole_number', 1)),
                    feature_combination=feature_combination
                )
                
                # 移除现有标注
                existing_ann = self.current_dataset.get_annotation_by_hole(
                    current_file.get('panoramic_id'), 
                    current_file.get('hole_number')
                )
                if existing_ann:
                    self.current_dataset.annotations.remove(existing_ann)
                
                # 添加新标注
                self.current_dataset.add_annotation(enhanced_annotation)
                return True
            
        except Exception as e:
            print(f"保存标注失败: {e}")
            print(f"保存标注失败: {e}")
            return False


def main():
    """主函数 - 使用重构后的GUI"""
    print("启动重构后的全景标注工具...")
    
    try:
        # 导入重构后的GUI
        from panoramic_annotation_gui_refactored import PanoramicAnnotationGUI as RefactoredGUI
        
        root = tk.Tk()
        app = RefactoredGUI(root)
        
        print("重构版GUI初始化成功")
        
        # 设置窗口图标（如果有的话）
        try:
            # root.iconbitmap('icon.ico')
            pass
        except:
            pass
        
        # 启动主循环
        root.mainloop()
        
    except ImportError as e:
        print(f"无法导入重构版GUI，使用原始版本: {e}")
        # 回退到原始版本
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
