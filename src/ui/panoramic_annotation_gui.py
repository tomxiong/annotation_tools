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
from models.enhanced_annotation import EnhancedPanoramicAnnotation, FeatureCombination
from models.enhanced_annotation import EnhancedPanoramicAnnotation
from ui.batch_import_dialog import show_batch_import_dialog


class PanoramicAnnotationGUI:
    """
    全景图像标注工具主界面
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("全景图像标注工具 - 微生物药敏检测")
        # 设置优化的窗口大小，调整为1600x900
        self.root.geometry("1600x900")   # 目标尺寸1600x900
        self.root.minsize(1400, 800)     # 保持最小尺寸
        
        # 服务和管理器
        self.image_service = PanoramicImageService()
        self.hole_manager = HoleManager()
        self.config_service = ConfigFileService()
        
        # 窗口尺寸跟踪
        self.window_resize_log = []
        self.initial_geometry = "1600x900"
        self.current_geometry = "1600x900"
        
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
        self.update_status("就绪 - 请选择全景图目录")
    
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
        
        # 全景图目录选择（必选）- 优化间距
        ttk.Label(toolbar, text="全景图:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.panoramic_dir_var = tk.StringVar()
        panoramic_dir_entry = ttk.Entry(toolbar, textvariable=self.panoramic_dir_var, width=45)
        panoramic_dir_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(toolbar, text="浏览", 
                  command=self.select_panoramic_directory).pack(side=tk.LEFT, padx=(0, 8))
        
        # 加载按钮
        ttk.Button(toolbar, text="加载数据", 
                  command=self.load_data).pack(side=tk.LEFT, padx=(0, 5))
        
        # 保存按钮
        ttk.Button(toolbar, text="保存标注", 
                  command=self.save_annotations).pack(side=tk.LEFT, padx=(0, 0))
        
        # 导出按钮
        ttk.Button(toolbar, text="导出训练数据", 
                  command=self.export_training_data).pack(side=tk.LEFT, padx=(0, 5))
        
        # 加载标注按钮
        ttk.Button(toolbar, text="加载标注", 
                  command=self.load_annotations).pack(side=tk.LEFT, padx=(0, 0))
        
        # 批量导入按钮
        ttk.Button(toolbar, text="批量导入", 
                  command=self.batch_import_annotations).pack(side=tk.LEFT)
    
    def create_panoramic_panel(self, parent):
        """创建全景图显示面板"""
        # 全景图面板 - 优化尺寸，减少固定高度
        panoramic_frame = ttk.LabelFrame(parent, text="全景图 (12×10孔位布局)")
        panoramic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        # 移除固定宽度限制，让面板自适应
        
        # 全景图显示区域 - 减少固定高度，让图像自适应
        self.panoramic_canvas = tk.Canvas(panoramic_frame, bg='white')
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
        # 标注操作面板宽度 - 优化为更紧凑的布局
        right_frame = ttk.Frame(parent, width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_frame.pack_propagate(False)  # 固定宽度
        
        # 批量操作 - 移到第一个位置
        self.create_batch_panel(right_frame)
        
        # 导航控制 - 移到切片前面，符合操作流程：导航→查看→标注
        self.create_navigation_panel(right_frame)
        
        # 切片显示区域 - 设置合理的显示尺寸
        slice_frame = ttk.LabelFrame(right_frame, text="当前切片")
        slice_frame.pack(fill=tk.X, padx=(0, 0), pady=(0, 5))
        
        # 设置优化的切片显示尺寸，适应新的窗口布局
        self.slice_canvas = tk.Canvas(slice_frame, bg='white', width=150, height=150)
        self.slice_canvas.pack(padx=5, pady=3)
        
        # 切片信息和标注预览合并区域 - 紧凑布局
        info_frame = ttk.Frame(slice_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 3))
        
        # 切片信息标签
        self.slice_info_label = ttk.Label(info_frame, text="未加载切片", 
                                         font=('TkDefaultFont', 8))
        self.slice_info_label.pack(fill=tk.X, pady=(0, 2))
        
        # 标注预览区域
        self.annotation_preview_label = ttk.Label(info_frame, text="标注状态: 未标注", 
                                                font=('TkDefaultFont', 8, 'bold'))
        self.annotation_preview_label.pack(fill=tk.X, pady=(0, 2))
        
        # 详细标注信息预览区域
        self.detailed_annotation_label = ttk.Label(info_frame, text="", 
                                                  font=('TkDefaultFont', 8))
        self.detailed_annotation_label.pack(fill=tk.X, pady=(0, 2))
        
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
        """创建简化的导航控制面板"""
        nav_frame = ttk.LabelFrame(parent, text="导航控制 (快捷键)")
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 第一行：全景图导航
        top_frame = ttk.Frame(nav_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # 全景图导航
        ttk.Label(top_frame, text="全景图:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(top_frame, text="◀", width=3,
                  command=self.go_prev_panoramic).pack(side=tk.LEFT, padx=1)
        
        self.panoramic_combobox = ttk.Combobox(top_frame, 
                                              textvariable=self.panoramic_id_var,
                                              width=12)
        self.panoramic_combobox.pack(side=tk.LEFT, padx=2)
        self.panoramic_combobox.bind('<<ComboboxSelected>>', self.on_panoramic_selected)
        
        ttk.Button(top_frame, text="▶", width=3,
                  command=self.go_next_panoramic).pack(side=tk.LEFT, padx=1)
        
        # 移除全景图快捷键提示
        
        # 第二行：孔位导航和序列导航
        bottom_frame = ttk.Frame(nav_frame)
        bottom_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # 孔位跳转（左侧）- 支持回车执行
        hole_frame = ttk.Frame(bottom_frame)
        hole_frame.pack(side=tk.LEFT)
        
        ttk.Label(hole_frame, text="跳转:").pack(side=tk.LEFT, padx=(0, 2))
        
        self.hole_number_var = tk.StringVar(value="1")
        hole_entry = ttk.Entry(hole_frame, textvariable=self.hole_number_var, width=4)
        hole_entry.pack(side=tk.LEFT, padx=1)
        hole_entry.bind('<Return>', self.go_to_hole)
        
        # 序列导航（右侧）
        seq_frame = ttk.Frame(bottom_frame)
        seq_frame.pack(side=tk.RIGHT)
        
        ttk.Button(seq_frame, text="◀◀", width=4,
                  command=self.go_first_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="◀", width=4,
                  command=self.go_prev_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="▶", width=4,
                  command=self.go_next_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="▶▶", width=4,
                  command=self.go_last_hole).pack(side=tk.LEFT, padx=1)
        
        # 移除序列导航快捷键提示
        
        # 进度信息（居中）
        self.progress_label = ttk.Label(bottom_frame, text="0/0")
        self.progress_label.pack(side=tk.LEFT, expand=True)
        
        # 画布点击提示
        click_label = ttk.Label(nav_frame, text="提示: 点击全景图跳转对应孔位", 
                               font=('TkDefaultFont', 8))
        click_label.pack(side=tk.BOTTOM, padx=5, pady=(0, 3))
    
    def create_annotation_panel(self, parent):
        """创建标注控制面板"""
        ann_frame = ttk.LabelFrame(parent, text="标注控制")
        ann_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        # 创建增强标注面板 - 减少边距，不扩展
        self.enhanced_annotation_frame = ttk.Frame(ann_frame)
        self.enhanced_annotation_frame.pack(fill=tk.X, padx=3, pady=(3, 3))
        
        # 初始化enhanced annotation panel
        self.enhanced_annotation_panel = EnhancedAnnotationPanel(
            self.enhanced_annotation_frame,
            on_annotation_change=self.on_enhanced_annotation_change
        )
        
        # 标注按钮 - 移到增强标注面板下方
        self.button_frame = ttk.Frame(ann_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=(3, 3))
        
        ttk.Button(self.button_frame, text="保存并下一个", 
                  command=self.save_current_annotation).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.button_frame, text="跳过", 
                  command=self.skip_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.button_frame, text="清除标注", 
                  command=self.clear_current_annotation).pack(side=tk.LEFT, padx=2)
    
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
        
        # 更新详细标注信息显示
        detailed_info = self.get_detailed_annotation_info()
        self.detailed_annotation_label.config(text=detailed_info)
        
        # 可以在这里添加实时预览或验证逻辑
        pass
    
    def get_detailed_annotation_info(self):
        """获取详细标注信息用于显示"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        if existing_ann:
            # 构建详细标注信息 - 按照新格式：细菌 | 阳性 | 聚集型 | 1.00 | 无干扰
            details = []
            
            # 微生物类型
            if hasattr(existing_ann, 'microbe_type') and existing_ann.microbe_type:
                microbe_text = "细菌" if existing_ann.microbe_type == "bacteria" else "真菌"
                details.append(microbe_text)
            
            # 生长级别
            if hasattr(existing_ann, 'growth_level') and existing_ann.growth_level:
                growth_map = {
                    'negative': '阴性',
                    'weak_growth': '弱生长',
                    'positive': '阳性'
                }
                growth_text = growth_map.get(existing_ann.growth_level, existing_ann.growth_level)
                details.append(growth_text)
            
            # 生长模式（如果是增强标注）
            if hasattr(existing_ann, 'growth_pattern') and existing_ann.growth_pattern:
                # 映射生长模式为中文显示
                pattern_map = {
                    'clean': '清亮',
                    'small_dots': '中心小点',
                    'light_gray': '浅灰色',
                    'irregular_areas': '不规则区域',
                    'clustered': '聚集型',
                    'scattered': '分散型',
                    'heavy_growth': '重度生长',
                    'focal': '聚焦性',
                    'diffuse': '弥漫性',
                    'default_positive': '阳性默认',
                    'default_weak_growth': '弱生长默认'
                }
                pattern_text = pattern_map.get(existing_ann.growth_pattern, existing_ann.growth_pattern)
                details.append(pattern_text)
            
            # 置信度
            if hasattr(existing_ann, 'confidence') and existing_ann.confidence:
                details.append(f"{existing_ann.confidence:.2f}")
            
            # 干扰因素
            if hasattr(existing_ann, 'interference_factors') and existing_ann.interference_factors:
                # 映射干扰因素为中文显示
                interference_map = {
                    'pores': '气孔',
                    'artifacts': '气孔重叠',
                    'noise': '气孔重叠',
                    'debris': '杂质',
                    'contamination': '污染'
                }
                if existing_ann.interference_factors:
                    interference_text = ", ".join([interference_map.get(f, f) for f in existing_ann.interference_factors])
                else:
                    interference_text = "无干扰"
                details.append(interference_text)
            else:
                details.append("无干扰")
            
            return " | ".join(details)
        else:
            # 如果没有标注，显示空字符串
            return ""
    
    def get_annotation_status_text(self):
        """获取标注状态文本，包含日期时间 - 优先使用JSON中的保存时间"""
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
                
                # 优先尝试从标注对象获取保存的时间戳
                saved_timestamp = None
                if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                    try:
                        import datetime
                        if isinstance(existing_ann.timestamp, str):
                            # 处理ISO格式时间戳
                            saved_timestamp = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                        else:
                            saved_timestamp = existing_ann.timestamp
                        
                        # 同步到内存缓存
                        self.last_annotation_time[annotation_key] = saved_timestamp
                        datetime_str = saved_timestamp.strftime("%m-%d %H:%M:%S")
                        return f"已标注 ({datetime_str})"
                    except Exception as e:
                        print(f"[ERROR] 解析保存的时间戳失败: {e}")
                
                # 如果标注对象中没有时间戳，尝试从内存缓存获取
                if annotation_key in self.last_annotation_time:
                    import datetime
                    datetime_str = self.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")
                    return f"已标注 ({datetime_str})"
                
                # 如果都没有时间戳，显示基本状态
                return "已标注"
            else:
                # 配置导入或其他类型 - 显示为配置状态
                return "配置"
        else:
            return "未标注"
    
    def create_batch_panel(self, parent):
        """创建统计面板"""
        # 统计信息 - 纯统计功能
        stats_frame = ttk.LabelFrame(parent, text="统计信息")
        stats_frame.pack(fill=tk.X, pady=(0, 2))
        
        self.stats_label = ttk.Label(stats_frame, text="统计: 未标注 0, 阴性 0, 弱生长 0, 阳性 0")
        self.stats_label.pack(padx=5, pady=3)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def setup_bindings(self):
        """设置键盘快捷键和窗口事件"""
        # 窗口尺寸变化事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 只在非输入控件获得焦点时响应快捷键
        # 方向导航快捷键
        self.root.bind('<Key-1>', self.on_key_1)
        self.root.bind('<Key-2>', self.on_key_2)
        self.root.bind('<Key-3>', self.on_key_3)
        self.root.bind('<Left>', self.on_key_left)
        self.root.bind('<Right>', self.on_key_right)
        self.root.bind('<Up>', self.on_key_up)
        self.root.bind('<Down>', self.on_key_down)
        
        # 序列导航快捷键（Home/End 对应 首个/最后）
        self.root.bind('<Home>', self.on_key_home)
        self.root.bind('<End>', self.on_key_end)
        
        # 全景图导航快捷键（PageUp/Down 对应 上一全景/下一全景）
        self.root.bind('<Prior>', self.on_key_page_up)  # PageUp
        self.root.bind('<Next>', self.on_key_page_down)  # PageDown
        
        # 窗口分析快捷键
        self.root.bind('<Control-l>', lambda e: self.analyze_window_resize_log())  # Ctrl+L 分析日志
        
        # 其他快捷键
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
    
    def on_key_home(self, event):
        """Home键事件处理 - 跳转到第一个孔位"""
        if not self.is_input_widget_focused():
            self.go_first_hole()
    
    def on_key_end(self, event):
        """End键事件处理 - 跳转到最后一个孔位"""
        if not self.is_input_widget_focused():
            self.go_last_hole()
    
    def on_key_page_up(self, event):
        """PageUp键事件处理 - 上一张全景图"""
        if not self.is_input_widget_focused():
            self.go_prev_panoramic()
    
    def on_key_page_down(self, event):
        """PageDown键事件处理 - 下一张全景图"""
        if not self.is_input_widget_focused():
            self.go_next_panoramic()
    
    def on_window_resize(self, event):
        """窗口尺寸变化事件处理"""
        if event.widget == self.root:  # 只处理主窗口的尺寸变化
            # 获取当前窗口尺寸
            geometry = self.root.geometry()
            self.current_geometry = geometry
            
            # 记录尺寸变化日志
            import time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                'timestamp': timestamp,
                'geometry': geometry,
                'width': event.width,
                'height': event.height,
                'event': 'resize'
            }
            self.window_resize_log.append(log_entry)
            
            # 打印日志
                        
            # 限制日志长度，避免内存占用过多
            if len(self.window_resize_log) > 100:
                self.window_resize_log = self.window_resize_log[-50:]
    
    def analyze_window_resize_log(self):
        """分析窗口尺寸变化日志，确定最佳窗口尺寸"""
        if not self.window_resize_log:
            print("[ANALYSIS] 没有窗口尺寸变化日志数据")
            return
        
        print("\n" + "="*60)
        print("[ANALYSIS] 窗口尺寸变化日志分析")
        print("="*60)
        
        # 分析不同事件类型的尺寸变化
        resize_events = [e for e in self.window_resize_log if e['event'] == 'resize']
        load_panoramic_events = [e for e in self.window_resize_log if e['event'] in ['load_panoramic_start', 'load_panoramic_complete']]
        load_annotation_events = [e for e in self.window_resize_log if e['event'] in ['load_annotations_start', 'load_annotations_complete']]
        
        print(f"\n1. 总体统计:")
        print(f"   - 总日志条目: {len(self.window_resize_log)}")
        print(f"   - 手动调整次数: {len(resize_events)}")
        print(f"   - 全景图加载事件: {len(load_panoramic_events)}")
        print(f"   - 标注加载事件: {len(load_annotation_events)}")
        
        # 分析手动调整的尺寸
        if resize_events:
            widths = [e['width'] for e in resize_events]
            heights = [e['height'] for e in resize_events]
            
            print(f"\n2. 手动调整尺寸分析:")
            print(f"   - 宽度范围: {min(widths)} - {max(widths)} px")
            print(f"   - 高度范围: {min(heights)} - {max(heights)} px")
            print(f"   - 平均宽度: {sum(widths)/len(widths):.0f} px")
            print(f"   - 平均高度: {sum(heights)/len(heights):.0f} px")
            
            # 找出最常用的尺寸
            from collections import Counter
            size_counts = Counter([f"{e['width']}x{e['height']}" for e in resize_events])
            most_common = size_counts.most_common(3)
            print(f"   - 最常用尺寸: {most_common[0][0]} (出现{most_common[0][1]}次)")
        
        # 分析加载前后的尺寸变化
        print(f"\n3. 加载事件分析:")
        
        # 全景图加载
        for i in range(0, len(load_panoramic_events), 2):
            if i+1 < len(load_panoramic_events):
                start = load_panoramic_events[i]
                complete = load_panoramic_events[i+1]
                if start['event'] == 'load_panoramic_start' and complete['event'] == 'load_panoramic_complete':
                    print(f"   - 全景图加载: {start['panoramic_id']}")
                    print(f"     加载前: {start['geometry']}")
                    print(f"     加载后: {complete['geometry']}")
        
        # 标注加载
        for i in range(0, len(load_annotation_events), 2):
            if i+1 < len(load_annotation_events):
                start = load_annotation_events[i]
                complete = load_annotation_events[i+1]
                if start['event'] == 'load_annotations_start' and complete['event'] == 'load_annotations_complete':
                    print(f"   - 标注加载: {complete.get('annotation_count', 'N/A')}个标注")
                    print(f"     加载前: {start['geometry']}")
                    print(f"     加载后: {complete['geometry']}")
        
        # 推荐最佳尺寸
        if resize_events:
            final_widths = [e['width'] for e in resize_events[-10:]]  # 最近10次调整
            final_heights = [e['height'] for e in resize_events[-10:]]
            recommended_width = int(sum(final_widths) / len(final_widths))
            recommended_height = int(sum(final_heights) / len(final_heights))
            
            print(f"\n4. 推荐尺寸:")
            print(f"   - 基于用户使用习惯推荐: {recommended_width}x{recommended_height}")
            print(f"   - 当前默认尺寸: {self.initial_geometry}")
            print(f"   - 当前实际尺寸: {self.current_geometry}")
        
        print("="*60 + "\n")
    
    def select_panoramic_directory(self):
        """选择全景图目录"""
        directory = filedialog.askdirectory(title="选择全景图目录")
        if directory:
            self.panoramic_dir_var.set(directory)
            self.panoramic_directory = directory
    
    def load_data(self):
        """加载数据 - 使用子目录结构"""
        if not self.panoramic_directory:
            messagebox.showerror("错误", "请先选择全景图目录")
            return
        
        try:
            # 使用子目录模式：直接使用全景目录下的子目录
            self.slice_files = self.image_service.get_slice_files_from_directory(
                self.panoramic_directory, self.panoramic_directory)
            structure_msg = '子目录模式'
            
            if not self.slice_files:
                messagebox.showwarning("警告", 
                    "未找到有效的切片文件。\n请检查：\n" +
                    "切片文件应在 <全景文件>/hole_<孔序号>.png 位置")
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
                
                # 获取画布尺寸用于缩放
                canvas_width = self.slice_canvas.winfo_width() or 200
                canvas_height = self.slice_canvas.winfo_height() or 200
                
                # 计算合适的缩放比例，充分利用可视区域
                img_width, img_height = enhanced_slice.size
                scale_factor = min((canvas_width - 20) / img_width, (canvas_height - 20) / img_height)
                scale_factor = min(scale_factor, 2.5)  # 最大放大2.5倍，避免过度模糊
                
                # 缩放图像以更好地利用空间
                if scale_factor > 1.0:  # 只有当需要放大时才缩放
                    new_width = int(img_width * scale_factor)
                    new_height = int(img_height * scale_factor)
                    enhanced_slice = enhanced_slice.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                self.slice_photo = ImageTk.PhotoImage(enhanced_slice)
                
                # 显示在画布上
                self.slice_canvas.delete("all")
                if canvas_width > 1 and canvas_height > 1:  # 确保画布已初始化
                    x = canvas_width // 2
                    y = canvas_height // 2
                    self.slice_canvas.create_image(x, y, image=self.slice_photo)
            
            # 加载对应的全景图
            self.load_panoramic_image()
            
            # 更新切片信息，包含标注状态
            self.update_slice_info_display()
            
            # 加载已有标注
            self.load_existing_annotation()
            
            # 重置修改标记
            self.current_annotation_modified = False
            
            # 尝试加载配置文件标注
            self.load_config_annotations()
            
            # 延迟强制刷新确保统计和状态完全同步
            self.root.after_idle(self._delayed_navigation_refresh)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载切片失败: {str(e)}")
    
    def _delayed_navigation_refresh(self):
        """延迟导航刷新，确保所有数据已正确加载"""
        try:
            print(f"[NAV] 延迟导航刷新 - 孔位{self.current_hole_number}")
            
            # 强制更新统计信息
            self.update_statistics()
            self.root.update_idletasks()
            
            # 强制更新状态显示
            self.update_slice_info_display()
            self.root.update_idletasks()
            
            # 再次验证更新结果，必要时重复更新
            self.root.after(100, self._verify_and_retry_sync)
            
            print("[NAV] 延迟导航刷新完成")
            
        except Exception as e:
            print(f"[ERROR] 延迟导航刷新失败: {e}")
    
    def _force_navigation_refresh(self):
        """导航后强制刷新，确保统计和状态更新"""
        try:
            print(f"[NAV] 强制导航刷新 - 孔位{self.current_hole_number}")
            
            # 立即更新统计和状态
            self.update_statistics()
            self.root.update_idletasks()
            
            self.update_slice_info_display()
            self.root.update_idletasks()
            
            # 强制刷新界面
            self.root.update()
            
            print("[NAV] 强制导航刷新完成")
            
        except Exception as e:
            print(f"[ERROR] 强制导航刷新失败: {e}")
    
    def _verify_and_retry_sync(self):
        """验证同步结果，必要时重试"""
        try:
            # Reduce verification logging frequency
                        
            # 再次更新统计和状态显示
            self.update_statistics()
            self.update_slice_info_display()
            self.root.update_idletasks()
            
            # Only log verification details when there are actual changes
            if hasattr(self, 'stats_label'):
                stats_text = self.stats_label.cget('text')
                if not hasattr(self, '_last_verified_stats') or self._last_verified_stats != stats_text:
                                        self._last_verified_stats = stats_text
            
            if hasattr(self, 'slice_info_label'):
                slice_text = self.slice_info_label.cget('text')
                if not hasattr(self, '_last_verified_info') or self._last_verified_info != slice_text:
                      # Truncate long text
                    self._last_verified_info = slice_text
                
            print("[VERIFY] 验证同步完成")
            
        except Exception as e:
            print(f"[ERROR] 验证同步失败: {e}")
    
    def load_panoramic_image(self):
        """加载全景图"""
        if not self.current_panoramic_id:
            return
        
        # 记录加载全景图前的窗口状态
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        current_geometry = self.root.geometry()
        print(f"[LOAD_PANORAMIC] {timestamp} - 开始加载全景图 {self.current_panoramic_id}, 当前窗口: {current_geometry}")
        
        # 记录到日志
        log_entry = {
            'timestamp': timestamp,
            'geometry': current_geometry,
            'event': 'load_panoramic_start',
            'panoramic_id': self.current_panoramic_id
        }
        self.window_resize_log.append(log_entry)
        
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
                
                # 使用实际画布尺寸，留少量边距 - 适应新的1240px宽度
                target_width = max(canvas_width - 40, 1220)  # 最小1220px宽度，适应右侧360px面板
                target_height = max(canvas_height - 40, 750)  # 最小750px高度
                
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
        
        # 记录加载全景图后的窗口状态
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        final_geometry = self.root.geometry()
        print(f"[LOAD_PANORAMIC] {timestamp} - 完成加载全景图 {self.current_panoramic_id}, 当前窗口: {final_geometry}")
        
        # 记录到日志
        log_entry = {
            'timestamp': timestamp,
            'geometry': final_geometry,
            'event': 'load_panoramic_complete',
            'panoramic_id': self.current_panoramic_id
        }
        self.window_resize_log.append(log_entry)
    
    def load_existing_annotation(self):
        """加载已有标注"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        print(f"[LOAD] 加载已有标注 - 孔位{self.current_hole_number}, 有标注: {existing_ann is not None}")
        
        if existing_ann:
            # 设置界面状态
            self.current_microbe_type.set(existing_ann.microbe_type)
            self.current_growth_level.set(existing_ann.growth_level)
            
            # 同步时间戳到内存（对所有手动标注处理，包括manual和enhanced_manual）
            if ((hasattr(existing_ann, 'annotation_source') and 
                 existing_ann.annotation_source in ['enhanced_manual', 'manual'])):
                import datetime
                annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                
                # 强制优先使用annotation对象中的timestamp
                if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                    try:
                        if isinstance(existing_ann.timestamp, str):
                            dt = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                        else:
                            dt = existing_ann.timestamp
                        self.last_annotation_time[annotation_key] = dt
                        print(f"[LOAD] 强制使用保存的时间戳: {annotation_key} -> {dt.strftime('%m-%d %H:%M:%S')}")
                    except Exception as e:
                        print(f"[ERROR] 时间戳解析失败: {e}")
                        # 解析失败时生成一个默认时间戳，但不使用可能错误的内存缓存
                        default_time = datetime.datetime.now()
                        self.last_annotation_time[annotation_key] = default_time
                        print(f"[LOAD] 生成新默认时间戳: {annotation_key} -> {default_time.strftime('%m-%d %H:%M:%S')}")
                else:
                    # 如果标注对象没有时间戳属性，生成一个默认时间戳
                    default_time = datetime.datetime.now()
                    self.last_annotation_time[annotation_key] = default_time
                    print(f"[LOAD] 标注对象无时间戳，生成默认时间戳: {annotation_key} -> {default_time.strftime('%m-%d %H:%M:%S')}")
                                
            # 同步到增强标注面板 - 改进逻辑以处理所有手动标注
            if self.enhanced_annotation_panel:
                if hasattr(existing_ann, 'enhanced_data'):
                    # Added: More detailed analysis of enhanced_data structure
                    if existing_ann.enhanced_data:
                        if isinstance(existing_ann.enhanced_data, dict):
                            if 'feature_combination' in existing_ann.enhanced_data:
                                fc_data = existing_ann.enhanced_data['feature_combination']
                            else:
                                print(f"[WARNING] enhanced_data不是字典类型: {type(existing_ann.enhanced_data)}")
                
                # 首先检查是否有增强标注数据
                # 改进逻辑：如果有enhanced_data，就认为是增强标注，不管annotation_source是什么
                if (hasattr(existing_ann, 'enhanced_data') and 
                    existing_ann.enhanced_data):
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
                            print(f"[LOAD] 已恢复增强标注数据 - 级别: {combination.growth_level}, 模式: {combination.growth_pattern}")
                        else:
                            print(f"[ERROR] 增强数据格式错误: {type(enhanced_data)}")
                            self.sync_basic_to_enhanced_annotation(existing_ann)
                    except Exception as e:
                        print(f"[ERROR] 增强标注数据恢复失败: {e}")
                        import traceback
                        traceback.print_exc()
                        # 如果增强数据解析失败，使用基础数据
                        self.sync_basic_to_enhanced_annotation(existing_ann)
                elif existing_ann.annotation_source in ['enhanced_manual', 'manual']:
                    # 手动标注但没有增强数据，使用基础数据同步到增强面板
                    print(f"[LOAD] 同步手动标注({existing_ann.annotation_source})到增强面板")
                    print(f"[FALLBACK] 由于JSON没有enhanced_data，使用基础数据同步 - 将使用区分性默认模式")
                    print(f"[FALLBACK] 原始数据: 生长级别={existing_ann.growth_level}, 源={existing_ann.annotation_source}")
                    self.sync_basic_to_enhanced_annotation(existing_ann)
                else:
                    # 配置导入标注：使用默认生长模式
                    print(f"[LOAD] 配置导入标注 - 使用默认生长模式")
                    if self.enhanced_annotation_panel:
                        # 使用配置的生长级别初始化面板，设置可区分的默认生长模式
                        self.enhanced_annotation_panel.initialize_with_defaults(
                            growth_level=existing_ann.growth_level,
                            microbe_type=existing_ann.microbe_type,
                            reset_interference=True  # 配置标注没有干扰因素，重置干扰因素
                        )
                        print(f"[LOAD] 配置导入标注 - 设置生长级别为默认模式: {existing_ann.growth_level}")
            
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
                        
            # 检查是否有用户之前选择的growth_pattern
            user_growth_pattern = getattr(annotation, 'growth_pattern', None)
                        
            # 检查是否有干扰因素
            has_interference_factors = bool(annotation.interference_factors)
                        
            if self.enhanced_annotation_panel:
                # 对于有干扰因素的标注，先初始化但不重置干扰因素
                if has_interference_factors:
                                        
                    if user_growth_pattern:
                        self.enhanced_annotation_panel.initialize_with_pattern(
                            growth_level=annotation.growth_level,
                            microbe_type=annotation.microbe_type,
                            growth_pattern=user_growth_pattern,
                            reset_interference=False
                        )
                    else:
                        self.enhanced_annotation_panel.initialize_with_defaults(
                            growth_level=annotation.growth_level,
                            microbe_type=annotation.microbe_type,
                            reset_interference=False
                        )
                else:
                    # 没有干扰因素的标注，正常初始化
                    if user_growth_pattern:
                                                self.enhanced_annotation_panel.initialize_with_pattern(
                            growth_level=annotation.growth_level,
                            microbe_type=annotation.microbe_type,
                            growth_pattern=user_growth_pattern
                        )
                    else:
                                                self.enhanced_annotation_panel.initialize_with_defaults(
                            growth_level=annotation.growth_level,
                            microbe_type=annotation.microbe_type
                        )
                
                # 处理干扰因素（如果有的话）
                if annotation.interference_factors:
                    from models.enhanced_annotation import InterferenceType
                    
                    # 干扰因素映射（现在直接使用中文值）
                    interference_map = {
                        '气孔': InterferenceType.PORES,
                        '气孔重叠': InterferenceType.ARTIFACTS,
                        '杂质': InterferenceType.DEBRIS,
                        '污染': InterferenceType.CONTAMINATION,
                        'pores': InterferenceType.PORES,           # 兼容英文
                        'artifacts': InterferenceType.ARTIFACTS,  # 兼容英文
                        'noise': InterferenceType.ARTIFACTS,     # 兼容英文
                        'debris': InterferenceType.DEBRIS,         # 兼容英文
                        'contamination': InterferenceType.CONTAMINATION,  # 兼容英文
                        'edge_blur': InterferenceType.PORES,      # 兼容旧的边缘模糊值
                        'scratches': InterferenceType.DEBRIS,     # 兼容英文
                        '污渍': InterferenceType.CONTAMINATION    # 污渍映射到污染
                    }
                    
                    for factor in annotation.interference_factors:
                        if factor in interference_map:
                            mapped_factor = interference_map[factor]
                            if mapped_factor in self.enhanced_annotation_panel.interference_vars:
                                self.enhanced_annotation_panel.interference_vars[mapped_factor].set(True)
                        else:
                            print(f"[WARNING] 未映射的干扰因素: {factor}")
                                            
                            
        except Exception as e:
            print(f"[ERROR] 同步基础标注到增强面板失败: {e}")
            import traceback
            traceback.print_exc()
    
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
                
                # 核心修复：配置文件导入后刷新当前孔位的界面显示
                self.load_existing_annotation()
            
        except Exception as e:
            print(f"加载配置文件标注失败: {e}")
    
    def get_next_hole_info(self):
        """获取下一个孔位的信息"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return None
        
        start_hole = self.hole_manager.start_hole_number
        current_index = self.current_slice_index
        
        # 查找下一个有效孔位
        for i in range(current_index + 1, len(self.slice_files)):
            hole_number = self.slice_files[i].get('hole_number', 1)
            if hole_number >= start_hole:
                return {
                    'index': i,
                    'hole_number': hole_number,
                    'panoramic_id': self.slice_files[i].get('panoramic_id'),
                    'file_info': self.slice_files[i]
                }
        
        return None
    
    def get_current_annotation_settings(self):
        """获取当前标注的设置"""
        if not hasattr(self, 'enhanced_annotation_panel') or not self.enhanced_annotation_panel:
            return None
        
        try:
            feature_combination = self.enhanced_annotation_panel.get_current_feature_combination()
            return {
                'growth_level': feature_combination.growth_level,
                'growth_pattern': feature_combination.growth_pattern,
                'interference_factors': feature_combination.interference_factors,
                'confidence': feature_combination.confidence,
                'microbe_type': self.current_microbe_type.get()
            }
        except Exception as e:
            print(f"[COPY] 获取当前标注设置失败: {e}")
            return None
    
    def apply_annotation_settings(self, settings):
        """应用标注设置到下一个孔位"""
        if not settings or not hasattr(self, 'enhanced_annotation_panel') or not self.enhanced_annotation_panel:
            return False
        
        try:
            print(f"[COPY] 应用设置到下一个孔位: 生长级别={settings['growth_level']}")
            
            # 设置微生物类型
            self.current_microbe_type.set(settings['microbe_type'])
            
            # 设置生长级别
            if hasattr(settings['growth_level'], 'value'):
                # 如果是枚举类型
                self.enhanced_annotation_panel.current_growth_level.set(settings['growth_level'].value)
            else:
                # 如果是字符串
                self.enhanced_annotation_panel.current_growth_level.set(settings['growth_level'])
            
            # 设置生长模式
            if settings['growth_pattern']:
                self.enhanced_annotation_panel.current_growth_pattern.set(settings['growth_pattern'])
            
            # 设置干扰因素
            print(f"[COPY] 准备设置干扰因素，当前有 {len(settings['interference_factors'])} 个因素")
            
            # 获取面板中的干扰因素映射
            panel_factors = self.enhanced_annotation_panel.interference_vars
            print(f"[COPY] 面板支持的干扰因素: {list(panel_factors.keys())}")
            
            # 先重置所有干扰因素
            for var in panel_factors.values():
                var.set(False)
            
            # 设置当前设置中的干扰因素
            interference_count = 0
            for factor in settings['interference_factors']:
                print(f"[COPY] 处理干扰因素: {factor} (类型: {type(factor)})")
                
                # 情况1: 直接匹配面板中的变量键
                if factor in panel_factors:
                    panel_factors[factor].set(True)
                    interference_count += 1
                    print(f"[COPY] ✓ 直接设置干扰因素: {factor}")
                
                # 情况2: 处理枚举类型的干扰因素
                elif hasattr(factor, 'value'):
                    factor_value = factor.value
                    print(f"[COPY] 枚举因素值: {factor_value}")
                    
                    # 在面板变量中查找匹配的值
                    for panel_key, panel_var in panel_factors.items():
                        panel_value = panel_key.value if hasattr(panel_key, 'value') else panel_key
                        if panel_value == factor_value:
                            panel_var.set(True)
                            interference_count += 1
                            print(f"[COPY] ✓ 通过枚举值设置干扰因素: {factor_value}")
                            break
                
                # 情况3: 处理字符串类型的干扰因素
                elif isinstance(factor, str):
                    # 在面板变量中查找匹配的值
                    for panel_key, panel_var in panel_factors.items():
                        panel_value = panel_key.value if hasattr(panel_key, 'value') else panel_key
                        if panel_value == factor:
                            panel_var.set(True)
                            interference_count += 1
                            print(f"[COPY] ✓ 通过字符串匹配设置干扰因素: {factor}")
                            break
                
                # 情况4: 处理类名字符串（如 'InterferenceType.PORES'）
                elif isinstance(factor, str) and '.' in factor:
                    factor_name = factor.split('.')[-1]
                    print(f"[COPY] 类名因素: {factor_name}")
                    
                    # 在面板变量中查找匹配的名称
                    for panel_key, panel_var in panel_factors.items():
                        panel_name = panel_key.__class__.__name__ + '.' + panel_key if hasattr(panel_key, '__class__') else str(panel_key)
                        if panel_name.endswith(factor_name):
                            panel_var.set(True)
                            interference_count += 1
                            print(f"[COPY] ✓ 通过类名匹配设置干扰因素: {factor_name}")
                            break
            
            print(f"[COPY] 总共设置了 {interference_count} 个干扰因素")
            
            # 设置置信度
            self.enhanced_annotation_panel.current_confidence.set(settings['confidence'])
            
            # 强制刷新界面
            self.enhanced_annotation_panel.update_pattern_options()
            self.root.update_idletasks()
            
            print(f"[COPY] 设置应用完成")
            return True
            
        except Exception as e:
            print(f"[COPY] 应用设置失败: {e}")
            return False
    
    def should_copy_settings(self, current_settings, next_hole_info):
        """判断是否应该复制设置"""
        if not current_settings or not next_hole_info:
            return False
        
        # 获取下一个孔位的现有标注（如果有）
        next_annotation = self.current_dataset.get_annotation_by_hole(
            next_hole_info['panoramic_id'], 
            next_hole_info['hole_number']
        )
        
        # 如果下一个孔位已有标注，检查是否为配置导入或非手动标注
        if next_annotation:
            annotation_source = getattr(next_annotation, 'annotation_source', 'unknown')
            print(f"[COPY] 下一个孔位已有标注，来源: {annotation_source}")
            
            # 如果是配置导入或非手动标注，检查生长级别是否相同
            if annotation_source in ['config_import', 'batch_import', 'auto_import'] or annotation_source == 'unknown':
                print(f"[COPY] 下一个孔位是{annotation_source}标注，检查生长级别")
                
                # 获取下一个孔位的生长级别
                next_growth_level = None
                if hasattr(next_annotation, 'growth_level'):
                    next_growth_level = next_annotation.growth_level
                    if hasattr(next_growth_level, 'value'):
                        next_growth_level = next_growth_level.value
                
                # 如果下一个孔位有配置的生长级别，检查是否与当前相同
                if next_growth_level and next_growth_level != current_settings['growth_level']:
                    print(f"[COPY] 生长级别不同：当前={current_settings['growth_level']}, 下一个={next_growth_level}，不复制设置")
                    return False
                elif next_growth_level:
                    print(f"[COPY] 生长级别相同：{next_growth_level}，允许复制设置")
                else:
                    print(f"[COPY] 下一个孔位无生长级别信息，允许复制设置")
            else:
                print(f"[COPY] 下一个孔位是手动标注，不复制设置")
                return False
        
        # 检查下一个孔位是否与当前孔位有相同的生长级别（基于配置）
        # 检查是否有配置文件为下一个孔位指定了生长级别
        config_growth_level = self.get_config_growth_level(next_hole_info['hole_number'])
        
        if config_growth_level:
            print(f"[COPY] 下一个孔位配置生长级别: {config_growth_level}")
            if config_growth_level != current_settings['growth_level']:
                print(f"[COPY] 配置生长级别不同：当前={current_settings['growth_level']}, 配置={config_growth_level}，不复制设置")
                return False
            else:
                print(f"[COPY] 配置生长级别相同：{config_growth_level}，允许复制设置")
        
        # 如果没有配置生长级别，使用位置接近性推断（相邻的孔位很可能有相似特性）
        current_row, current_col = self.hole_manager.number_to_position(self.current_hole_number)
        next_row, next_col = self.hole_manager.number_to_position(next_hole_info['hole_number'])
        
        # 计算距离
        row_distance = abs(current_row - next_row)
        col_distance = abs(current_col - next_col)
        
        # 如果是相邻的孔位（行距<=1，列距<=2），则认为可能有相似特性
        is_adjacent = (row_distance <= 1 and col_distance <= 2)
        
        print(f"[COPY] 当前孔位({self.current_hole_number})位置: ({current_row},{current_col})")
        print(f"[COPY] 下一个孔位({next_hole_info['hole_number']})位置: ({next_row},{next_col})")
        print(f"[COPY] 距离: 行{row_distance}, 列{col_distance}, 相邻={is_adjacent}")
        
        return is_adjacent
    
    def get_config_growth_level(self, hole_number):
        """获取配置文件中指定孔位的生长级别"""
        if not hasattr(self, 'config_data') or not self.config_data:
            return None
        
        # 查找配置文件中该孔位的生长级别设置
        for config_item in self.config_data:
            if config_item.get('hole_number') == hole_number:
                growth_level = config_item.get('growth_level')
                if growth_level:
                    print(f"[COPY] 孔位{hole_number}配置生长级别: {growth_level}")
                    return growth_level
        
        return None
    
    def save_current_annotation(self):
        """保存当前标注并跳转到下一个"""
        print(f"[SAVE] 用户点击保存并下一个 - 调用 save_current_annotation 方法")
        try:
            # 获取当前标注设置
            current_settings = self.get_current_annotation_settings()
            
            # 获取下一个孔位信息
            next_hole_info = self.get_next_hole_info()
            
            if self.save_current_annotation_internal():
                # 智能复制逻辑
                copy_applied = False
                if current_settings and next_hole_info:
                    if self.should_copy_settings(current_settings, next_hole_info):
                        print(f"[SAVE] 准备智能复制设置到下一个孔位")
                        
                        # 自动跳转到下一个
                        self.go_next_hole()
                        
                        # 延迟应用设置，确保界面加载完成
                        def apply_settings_delayed():
                            if self.apply_annotation_settings(current_settings):
                                self.update_status(f"已保存标注并智能复制设置到孔位{self.current_hole_number}")
                                copy_applied = True
                            else:
                                self.update_status(f"已保存标注，但设置复制失败")
                        
                        self.root.after(200, apply_settings_delayed)
                    else:
                        # 不复制设置，正常跳转
                        self.go_next_hole()
                        current_file = self.slice_files[self.current_slice_index - 1] if self.current_slice_index > 0 else self.slice_files[self.current_slice_index]
                        self.update_status(f"已保存标注: {current_file['filename']}")
                else:
                    # 无法获取设置或下一个孔位信息，正常跳转
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
                    # 导航后强制刷新统计和状态
                    self.root.after(10, self._force_navigation_refresh)
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
                # 导航后强制刷新统计和状态
                self.root.after(10, self._force_navigation_refresh)
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
        print(f"[SAVE] 进入 save_current_annotation_internal 方法")
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            print(f"[SAVE] 早期退出: 没有切片文件或索引超出范围")
            return
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            
            # 使用增强标注模式 - 唯一的标注方式
            print(f"[SAVE] 检查增强标注面板: hasattr={hasattr(self, 'enhanced_annotation_panel')}, not None={getattr(self, 'enhanced_annotation_panel', None) is not None}")
            if hasattr(self, 'enhanced_annotation_panel') and self.enhanced_annotation_panel:
                try:
                    feature_combination = self.enhanced_annotation_panel.get_current_feature_combination()
                    print(f"[SAVE] 准备保存增强标注: {feature_combination.growth_level} [{feature_combination.confidence:.2f}]")
                except Exception as e:
                    print(f"[ERROR] 获取特征组合失败: {e}")
                    raise
                
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
                print(f"[SAVE] 训练标签: {training_label}")
                
                # 创建兼容的PanoramicAnnotation对象用于显示
                annotation = PanoramicAnnotation.from_filename(
                    current_file['filename'],
                    label=training_label,
                    bbox=[0, 0, 70, 70],
                    confidence=feature_combination.confidence,
                    microbe_type=self.current_microbe_type.get(),
                    growth_level=feature_combination.growth_level.value if hasattr(feature_combination.growth_level, 'value') else feature_combination.growth_level,
                    interference_factors=[f.value if hasattr(f, 'value') else f for f in feature_combination.interference_factors],
                    annotation_source="enhanced_manual",
                    is_confirmed=True,
                    panoramic_id=current_file.get('panoramic_id')
                )
                
                # 存储增强标注数据
                try:
                    enhanced_data_dict = enhanced_annotation.to_dict()
                    print(f"[SAVE] enhanced_annotation.to_dict() 成功: {len(str(enhanced_data_dict))} 字符")
                    annotation.enhanced_data = enhanced_data_dict
                    print(f"[SAVE] enhanced_data 赋值成功")
                except Exception as e:
                    print(f"[ERROR] enhanced_data 赋值失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 继续执行，但不设置 enhanced_data
                
                # 设置对象的growth_pattern属性，确保状态正确恢复
                if hasattr(feature_combination, 'growth_pattern'):
                    growth_pattern_value = feature_combination.growth_pattern
                    if hasattr(growth_pattern_value, 'value'):
                        annotation.growth_pattern = growth_pattern_value.value
                    else:
                        annotation.growth_pattern = str(growth_pattern_value)
                    print(f"[SAVE] 设置growth_pattern: {annotation.growth_pattern}")
                
                print(f"[SAVE] 保存增强数据完成")
                
                # 验证enhanced_data是否正确设置
                if hasattr(annotation, 'enhanced_data') and annotation.enhanced_data:
                    print(f"[SAVE] ✓ enhanced_data设置成功")
                    if 'feature_combination' in annotation.enhanced_data:
                        fc_data = annotation.enhanced_data['feature_combination']
                    else:
                        print(f"[SAVE] ❌ enhanced_data设置失败或为空")
                    
            else:
                # 基础标注模式（向后兼容）
                print(f"[SAVE] 使用基础标注模式（无增强面板）")
                annotation = PanoramicAnnotation.from_filename(
                    current_file['filename'],
                    label=self.current_growth_level.get(),
                    bbox=[0, 0, 70, 70],
                    confidence=1.0,
                    microbe_type=self.current_microbe_type.get(),
                    growth_level=self.current_growth_level.get(),
                    interference_factors=[],
                    annotation_source="enhanced_manual",
                    is_confirmed=True,
                    panoramic_id=current_file.get('panoramic_id')
                )
            
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
            
            # 记录标泣时间
            import datetime
            current_time = datetime.datetime.now()
            annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
            self.last_annotation_time[annotation_key] = current_time
            print(f"[SAVE] 记录标注时间: {annotation_key} -> {current_time.strftime('%m-%d %H:%M:%S')}")
            
            # 更新显示
            self.load_panoramic_image()
            self.update_statistics()
            self.update_slice_info_display()
            self.root.update_idletasks()
            self.root.update()
            
            # 验证标注是否正确保存
            saved_ann = self.current_dataset.get_annotation_by_hole(self.current_panoramic_id, self.current_hole_number)
            if saved_ann:
                if hasattr(saved_ann, 'enhanced_data') and saved_ann.enhanced_data:
                    if 'feature_combination' in saved_ann.enhanced_data:
                        fc = saved_ann.enhanced_data['feature_combination']
                    else:
                        print(f"[SAVE] saved_ann缺少feature_combination")
                else:
                    print(f"[SAVE] saved_ann无enhanced_data")
            print("[SAVE] 保存后更新完成")
            
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
        # 传统导航模式：移动到上方相邻孔位
        nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
        if nav_info['can_go_up']:
            target_hole = nav_info['up_hole']
            self.navigate_to_hole(target_hole)
    
    def go_down(self):
        """向下导航"""
        # 传统导航模式：移动到下方相邻孔位
        nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
        if nav_info['can_go_down']:
            target_hole = nav_info['down_hole']
            self.navigate_to_hole(target_hole)
    
    def go_left(self):
        """向左导航"""
        # 传统导航模式：移动到左侧相邻孔位
        nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
        if nav_info['can_go_left']:
            target_hole = nav_info['left_hole']
            self.navigate_to_hole(target_hole)
    
    def go_right(self):
        """向右导航"""
        # 传统导航模式：移动到右侧相邻孔位
        nav_info = self.hole_manager.get_navigation_info(self.current_hole_number)
        if nav_info['can_go_right']:
            target_hole = nav_info['right_hole']
            self.navigate_to_hole(target_hole)
    
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
                # 导航后强制刷新统计和状态
                self.root.after(10, self._force_navigation_refresh)
                self.update_progress()
                return
    
    def switch_to_hole(self, hole_number: int):
        """切换到指定孔位（用于继续标注功能）"""
        if not hole_number:
            print(f"[SWITCH] 警告: 无效的孔位编号 {hole_number}")
            return
        
        print(f"[SWITCH] 切换到孔位 {hole_number}")
        
        # 更新当前孔位编号状态
        self.current_hole_number = hole_number
        
        # 使用现有的导航方法
        self.navigate_to_hole(hole_number)
        
        # 加载该孔位的标注数据
        self.load_existing_annotation()
        
        # 强制更新切片信息显示
        self.update_slice_info_display()
        
        # 确保状态栏更新
        self.update_status(f"已切换到孔位 {hole_number}")
        
        print(f"[SWITCH] 完成切换到孔位 {hole_number}")
    
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
    
    # 暂时移除批量标注功能
# def batch_annotate_row_negative(self):
#     """批量标注整行为阴性"""
#     if not self.current_panoramic_id:
#         return
#     
#     row, col = self.hole_manager.number_to_position(self.current_hole_number)
#     
#     # 获取同行的所有孔位
#     row_holes = []
#     for c in range(12):
#         hole_num = self.hole_manager.position_to_number(row, c)
#         row_holes.append(hole_num)
#     
#     # 批量标注
#     self.batch_annotate_holes(row_holes, 'negative')
#     
#     self.update_status(f"已批量标注第 {row + 1} 行为阴性")
# 
# def batch_annotate_col_negative(self):
#     """批量标注整列为阴性"""
#     if not self.current_panoramic_id:
#         return
#     
#     row, col = self.hole_manager.number_to_position(self.current_hole_number)
#     
#     # 获取同列的所有孔位
#     col_holes = []
#     for r in range(10):
#         hole_num = self.hole_manager.position_to_number(r, col)
#         col_holes.append(hole_num)
#     
#     # 批量标注
#     self.batch_annotate_holes(col_holes, 'negative')
#     
#     self.update_status(f"已批量标注第 {col + 1} 列为阴性")
    
    # 暂时移除批量标注功能
# def batch_annotate_holes(self, hole_numbers: List[int], growth_level: str):
#     """批量标注指定孔位"""
#     count = 0
#     for hole_number in hole_numbers:
#         # 查找对应的切片文件
#         for file_info in self.slice_files:
#             if (file_info['panoramic_id'] == self.current_panoramic_id and 
#                 file_info['hole_number'] == hole_number):
#                 
#                 # 创建标注 - 批量操作，已确认状态
#                 annotation = PanoramicAnnotation.from_filename(
#                     file_info['filename'],
#                     label=growth_level,
#                     bbox=[0, 0, 70, 70],
#                     confidence=1.0,
#                     microbe_type=self.current_microbe_type.get(),
#                     growth_level=growth_level,
#                     interference_factors=[],
#                     annotation_source="batch_operation",
#                     is_confirmed=True,
#                     panoramic_id=file_info.get('panoramic_id')
#                 )
#                 
#                 # 设置完整文件路径
#                 annotation.image_path = file_info['filepath']
#                 
#                 # 移除已有标注
#                 existing_ann = self.current_dataset.get_annotation_by_hole(
#                     self.current_panoramic_id, hole_number
#                 )
#                 if existing_ann:
#                     self.current_dataset.annotations.remove(existing_ann)
#                 
#                 # 添加新标注
#                 self.current_dataset.add_annotation(annotation)
#                 count += 1
#                 break
#     
#     # 更新显示
#     self.load_panoramic_image()
#     self.update_statistics()
#     
#     return count
    
    def update_slice_info_display(self):
        """更新切片信息显示，包括标注状态和时间戳"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            # 重置显示
            self.slice_info_label.config(text="未加载切片")
            self.annotation_preview_label.config(text="标注状态: 未标注")
            self.detailed_annotation_label.config(text="")
            return
            
        current_file = self.slice_files[self.current_slice_index]
        hole_label = self.hole_manager.get_hole_label(self.current_hole_number)
        annotation_status = self.get_annotation_status_text()
        
        # 更新切片信息标签 - 只显示文件和孔位信息
        self.slice_info_label.config(text=f"{current_file['filename']} - {hole_label}({self.current_hole_number})")
        
        # 更新标注预览标签
        self.annotation_preview_label.config(text=f"标注状态: {annotation_status}")
        
        # 更新详细标注信息
        detailed_info = self.get_detailed_annotation_info()
        self.detailed_annotation_label.config(text=detailed_info)
        
        # Only log significant info changes to reduce spam
        if not hasattr(self, '_last_info_display') or self._last_info_display != annotation_status:
            print(f"[INFO] 更新切片信息显示: {annotation_status}")
            self._last_info_display = annotation_status
        
        # 刷新显示
        self.root.update_idletasks()
    
    def get_annotation_status_text(self):
        """获取标注状态文本，包含日期时间 - 优先使用JSON中的保存时间"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        print(f"[STATUS] 检查标注状态 - 孔位{self.current_hole_number}, 有标注: {existing_ann is not None}")
        if existing_ann:
            source = getattr(existing_ann, 'annotation_source', 'unknown')
            has_enhanced_data = hasattr(existing_ann, 'enhanced_data') and existing_ann.enhanced_data
            # Only log details for first few or when there's an issue
            if not hasattr(self, '_status_logged_count'):
                self._status_logged_count = 0
            if self._status_logged_count < 3:  # Limit logging
                print(f"[STATUS] 标注详情 - 源: {source}, 级别: {existing_ann.growth_level}, 增强数据: {has_enhanced_data}")
                self._status_logged_count += 1
        
        if existing_ann:
            # Check if this is an enhanced annotation using multiple criteria
            source = getattr(existing_ann, 'annotation_source', 'unknown')
            has_enhanced_data = hasattr(existing_ann, 'enhanced_data') and existing_ann.enhanced_data
            
            # Enhanced if: enhanced_manual source OR any manual source (backward compatibility)
            has_enhanced = (
                source == 'enhanced_manual' or 
                source == 'manual'  # All manual annotations treated as enhanced
            )
            
            print(f"[STATUS] 标注源: {source}, 增强标注: {has_enhanced}, 时间戳: {getattr(existing_ann, 'timestamp', 'None')}")
            
            if has_enhanced:
                # 增强标注 - 显示已标注状态
                annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                
                # 优先尝试从标注对象获取保存的时间戳
                if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                    try:
                        import datetime
                        if isinstance(existing_ann.timestamp, str):
                            # 处理ISO格式时间戳
                            saved_timestamp = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                        else:
                            saved_timestamp = existing_ann.timestamp
                        
                        # 同步到内存缓存
                        self.last_annotation_time[annotation_key] = saved_timestamp
                        datetime_str = saved_timestamp.strftime("%m-%d %H:%M:%S")
                        status_text = f"状态: 已标注 ({datetime_str}) - {existing_ann.growth_level}"
                        print(f"[STATUS] 使用保存的时间戳: {datetime_str}")
                        return status_text
                    except Exception as e:
                        print(f"[ERROR] 解析保存的时间戳失败: {e}")
                
                # 如果标注对象中没有时间戳，尝试从内存缓存获取
                if annotation_key in self.last_annotation_time:
                    import datetime
                    datetime_str = self.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")
                    status_text = f"状态: 已标注 ({datetime_str}) - {existing_ann.growth_level}"
                    print(f"[STATUS] 使用内存缓存的时间戳: {datetime_str}")
                    return status_text
                
                # 如果都没有时间戳，显示基本状态
                status_text = f"状态: 已标注 - {existing_ann.growth_level}"
                print(f"[STATUS] 无时间戳信息，显示基本状态")
                return status_text
            else:
                # 配置导入或其他类型 - 显示为配置导入状态
                status_text = f"状态: 配置导入 - {existing_ann.growth_level}"
                return status_text
        else:
            status_text = "状态: 未标注"
            return status_text
    
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
        
        print(f"[STATS] 开始统计更新，总文件数: {stats['total']}")
        
        enhanced_count = 0
        config_count = 0
        
        for file_info in self.slice_files:
            panoramic_id = file_info.get('panoramic_id', '')
            hole_number = file_info.get('hole_number', 0)
            
            annotation = self.current_dataset.get_annotation_by_hole(panoramic_id, hole_number)
            if annotation:
                # Enhanced classification logic with improved backward compatibility
                source = getattr(annotation, 'annotation_source', 'unknown')
                has_enhanced_data = hasattr(annotation, 'enhanced_data') and annotation.enhanced_data
                
                # Classify as enhanced if:
                # 1. Source is enhanced_manual, OR
                # 2. Source is manual (for backward compatibility - treat all manual annotations as enhanced), OR
                # 3. Source is manual AND has enhanced_data
                is_enhanced = (
                    source == 'enhanced_manual' or 
                    source == 'manual' or  # All manual annotations treated as enhanced for backward compatibility
                    (source == 'manual' and has_enhanced_data)
                )
                
                if is_enhanced:
                    # Enhanced annotation counts toward statistics
                    stats['enhanced_annotated'] += 1
                    enhanced_count += 1
                    growth_level = annotation.growth_level
                    if growth_level in stats:
                        stats[growth_level] += 1
                        # Limit debug output to avoid spam
                        if enhanced_count <= 2:  # Only log first 2 enhanced annotations
                            print(f"[STATS] 统计增强标注 - 孔位{hole_number}, 级别: {growth_level}, 源: {source}")
                else:
                    # Config import or other types
                    stats['config_only'] += 1
                    config_count += 1
        
        stats['unannotated'] = stats['total'] - stats['enhanced_annotated']
        
        # Only log summary statistics to reduce console spam
        print(f"[STATS] 统计结果 - 增强标注: {enhanced_count}, 配置导入: {config_count}, 未标注: {stats['unannotated']}")
        if enhanced_count > 0 or config_count > 0:  # Only log details when there are annotations
            print(f"[STATS] 分类统计 - 阴性: {stats['negative']}, 弱生长: {stats['weak_growth']}, 阳性: {stats['positive']}")
        
        # 更新显示
        if stats['config_only'] > 0:
            stats_text = f"统计: 未标注 {stats['unannotated']}, 阴性 {stats['negative']}, 弱生长 {stats['weak_growth']}, 阳性 {stats['positive']} (配置: {stats['config_only']})"
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
        # 记录加载标注前的窗口状态
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        current_geometry = self.root.geometry()
        print(f"[LOAD_ANNOTATIONS] {timestamp} - 开始加载标注, 当前窗口: {current_geometry}")
        
        # 记录到日志
        log_entry = {
            'timestamp': timestamp,
            'geometry': current_geometry,
            'event': 'load_annotations_start'
        }
        self.window_resize_log.append(log_entry)
        
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
            
            # 获取最后标注的信息，用于自动切换
            latest_annotation = loaded_dataset.get_latest_annotation()
            auto_switch_info = ""
            
            if latest_annotation:
                # 记录自动切换信息
                auto_switch_info = f" - 自动切换到 {latest_annotation.panoramic_image_id}_{latest_annotation.hole_number}"
                print(f"[LOAD] 检测到最后标注: {latest_annotation.panoramic_image_id}_{latest_annotation.hole_number}")
                
                # 切换到对应的全景图
                if latest_annotation.panoramic_image_id in self.panoramic_ids:
                    print(f"[LOAD] 切换到全景图: {latest_annotation.panoramic_image_id}")
                    success = self.switch_to_panoramic(latest_annotation.panoramic_image_id)
                    
                    if success:
                        # 延迟切换到对应的孔位，确保全景图加载完成
                        self.root.after(100, lambda: self.switch_to_hole(latest_annotation.hole_number))
                    else:
                        auto_switch_info = f" - 切换全景图失败"
                else:
                    print(f"[LOAD] 警告: 全景图 {latest_annotation.panoramic_image_id} 不在可用列表中")
                    auto_switch_info = f" - 全景图 {latest_annotation.panoramic_image_id} 不可用"
            else:
                print(f"[LOAD] 没有找到标注信息，保持当前视图")
            
            # 更新显示
            self.load_panoramic_image()
            self.update_statistics()
            
            print(f"[LOAD] 标注加载完成{auto_switch_info}")
            
            # 重新加载当前切片的标注并完整刷新当前孔状态
            self.load_existing_annotation()
            
            # 强制刷新切片信息显示和增强标注面板
            self.update_slice_info_display()
            
            # 确保时间戳正确同步到内存 - 修复加载时时间戳显示问题
            self._force_timestamp_sync_after_load()
            
            # 延迟验证刷新 - 确保时间戳同步后再进行最终验证
            self.root.after(50, self._verify_timestamp_sync_after_load)
            
            # 确保增强标注面板状态同步 - 强制完整刷新
            if self.enhanced_annotation_panel:
                current_ann = self.current_dataset.get_annotation_by_hole(
                    self.current_panoramic_id, 
                    self.current_hole_number
                )
                if current_ann:
                    print(f"[LOAD] 加载标注后强制刷新增强面板 - 孔位{self.current_hole_number}")
                    print(f"[LOAD] 标注源: {getattr(current_ann, 'annotation_source', 'unknown')}")
                    
                    # 先重置面板再重新设置，确保完全刷新
                    self.enhanced_annotation_panel.reset_annotation()
                    self.root.update_idletasks()
                    
                    # 重新触发完整的标注加载流程
                    self.load_existing_annotation()
                    self.root.update_idletasks()
                    
                    # 最后一次强制UI刷新确保增强面板完全同步
                    self.root.update()
                    
                    print(f"[LOAD] 增强面板强制刷新完成 - 孔位{self.current_hole_number}")
                else:
                    print(f"[LOAD] 当前孔位{self.current_hole_number}无标注，重置增强面板")
                    self.enhanced_annotation_panel.reset_annotation()
            
            # 多重UI刷新确保状态完全更新
            self.root.update_idletasks()
            self.root.update()
            
            # 延迟验证刷新 - 确保所有异步更新完成
            self.root.after(100, self._verify_load_refresh)
            
            print(f"[LOAD] 加载标注完成，当前孔位状态已刷新")
            
            messagebox.showinfo("成功", f"已加载 {merge_count} 个标注进行review")
            self.update_status(f"已加载标注文件: {filename} ({merge_count} 个标注)")
            
            # 记录加载标注后的窗口状态
            import time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            final_geometry = self.root.geometry()
            print(f"[LOAD_ANNOTATIONS] {timestamp} - 完成加载标注, 当前窗口: {final_geometry}")
            
            # 记录到日志
            log_entry = {
                'timestamp': timestamp,
                'geometry': final_geometry,
                'event': 'load_annotations_complete',
                'annotation_count': merge_count
            }
            self.window_resize_log.append(log_entry)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载标注文件失败: {str(e)}")
    
    def _verify_timestamp_sync_after_load(self):
        """验证时间戳同步状态 - 确保加载后显示正确的时间戳"""
        try:
            print(f"[VERIFY_TIMESTAMP] 验证孔位{self.current_hole_number}的时间戳同步状态")
            
            # 获取当前孔位的标注
            current_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id, 
                self.current_hole_number
            )
            
            if current_ann:
                annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                
                # 检查内存中是否有时间戳
                has_memory_timestamp = annotation_key in self.last_annotation_time
                has_annotation_timestamp = hasattr(current_ann, 'timestamp') and current_ann.timestamp
                
                print(f"[VERIFY_TIMESTAMP] 内存中有时间戳: {has_memory_timestamp}")
                print(f"[VERIFY_TIMESTAMP] 标注对象有时间戳: {has_annotation_timestamp}")
                
                if has_memory_timestamp:
                    memory_time = self.last_annotation_time[annotation_key]
                    print(f"[VERIFY_TIMESTAMP] 内存时间戳: {memory_time.strftime('%m-%d %H:%M:%S')}")
                elif has_annotation_timestamp:
                    print(f"[VERIFY_TIMESTAMP] 标注对象时间戳: {current_ann.timestamp}")
                    # 如果内存中没有但标注对象有，再次强制同步
                    self._force_timestamp_sync_after_load()
                
                # 最终刷新显示
                self.update_slice_info_display()
                print(f"[VERIFY_TIMESTAMP] 验证完成，刷新显示")
            else:
                print(f"[VERIFY_TIMESTAMP] 孔位{self.current_hole_number}无标注")
                
        except Exception as e:
            print(f"[ERROR] 时间戳验证失败: {e}")
    
    def _force_timestamp_sync_after_load(self):
        """强制时间戳同步 - 修复加载标注后时间戳显示问题"""
        try:
            print(f"[FORCE_SYNC] 强制同步孔位{self.current_hole_number}的时间戳")
            
            # 获取当前孔位的标注
            current_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id, 
                self.current_hole_number
            )
            
            if current_ann and hasattr(current_ann, 'timestamp') and current_ann.timestamp:
                import datetime
                annotation_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                
                try:
                    # 解析时间戳
                    if isinstance(current_ann.timestamp, str):
                        dt = datetime.datetime.fromisoformat(current_ann.timestamp.replace('Z', '+00:00'))
                    else:
                        dt = current_ann.timestamp
                    
                    # 强制更新内存中的时间戳
                    self.last_annotation_time[annotation_key] = dt
                    print(f"[FORCE_SYNC] 成功同步时间戳: {annotation_key} -> {dt.strftime('%m-%d %H:%M:%S')}")
                    print(f"[FORCE_SYNC] 来源: JSON文件中的保存时间戳")
                    
                    # 再次刷新显示以确保时间戳正确显示
                    self.update_slice_info_display()
                    
                except Exception as e:
                    print(f"[FORCE_SYNC] 时间戳解析失败: {e}")
            else:
                print(f"[FORCE_SYNC] 孔位{self.current_hole_number}无有效时间戳")
                
        except Exception as e:
            print(f"[ERROR] 强制时间戳同步失败: {e}")
    
    def _verify_load_refresh(self):
        """验证加载后的刷新状态，确保当前孔位完全同步"""
        try:
            print(f"[VERIFY_LOAD] 验证孔位{self.current_hole_number}刷新状态")
            
            # 再次检查当前孔位的标注状态
            current_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id, 
                self.current_hole_number
            )
            
            if current_ann and self.enhanced_annotation_panel:
                print(f"[VERIFY_LOAD] 发现当前孔位有标注，验证增强面板同步状态")
                
                # 检查增强面板状态是否正确
                if hasattr(current_ann, 'enhanced_data') and current_ann.enhanced_data:
                    print(f"[VERIFY_LOAD] 验证增强数据同步状态")
                    # 确保增强数据已正确加载到面板
                    current_combination = self.enhanced_annotation_panel.get_current_feature_combination()
                    print(f"[VERIFY_LOAD] 当前面板状态: {current_combination.growth_level}_{current_combination.growth_pattern}")
                
                # 强制一次最终的状态更新
                self.update_slice_info_display()
                self.update_statistics()
                
                print(f"[VERIFY_LOAD] 孔位{self.current_hole_number}状态验证完成")
            else:
                print(f"[VERIFY_LOAD] 孔位{self.current_hole_number}无需验证或无增强面板")
                
        except Exception as e:
            print(f"[ERROR] 加载后验证失败: {e}")
    
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
                
                # 刷新当前孔状态（如果当前孔被更新）
                self.load_existing_annotation()
                self.update_slice_info_display()
                
                # 确保增强标注面板状态同步 - 强制完整刷新
                if self.enhanced_annotation_panel:
                    current_ann = self.current_dataset.get_annotation_by_hole(
                        self.current_panoramic_id, 
                        self.current_hole_number
                    )
                    if current_ann:
                        print(f"[BATCH_IMPORT] 批量导入后强制刷新增强面板 - 孔位{self.current_hole_number}")
                        
                        # 先重置面板再重新设置，确保完全刷新
                        self.enhanced_annotation_panel.reset_annotation()
                        self.root.update_idletasks()
                        
                        # 重新触发完整的标注加载流程
                        self.load_existing_annotation()
                        self.root.update_idletasks()
                        
                        print(f"[BATCH_IMPORT] 增强面板强制刷新完成 - 孔位{self.current_hole_number}")
                    else:
                        print(f"[BATCH_IMPORT] 当前孔位{self.current_hole_number}无标注，重置增强面板")
                        self.enhanced_annotation_panel.reset_annotation()
                
                # 强制UI刷新
                self.root.update_idletasks()
                self.root.update()
                
                # 延迟验证刷新
                self.root.after(100, self._verify_load_refresh)
                
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
    
    def switch_to_panoramic(self, panoramic_id):
        """自动切换到指定全景图（用于继续标注功能，不显示错误消息框）"""
        if panoramic_id not in self.panoramic_ids:
            print(f"[SWITCH] 警告: 全景图 {panoramic_id} 不在可用列表中")
            return False
        
        # 保存当前标注
        self.save_current_annotation_internal()
        
        # 查找目标全景图的第一个孔位
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
            
            print(f"[SWITCH] 已切换到全景图: {panoramic_id}")
            return True
        else:
            print(f"[SWITCH] 警告: 未找到全景图 {panoramic_id} 的切片文件")
            return False
    



def main():
    """主函数 - 启动全景标注工具"""
    print("启动全景标注工具...")
    
    try:
        # 创建主窗口和应用
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("GUI初始化成功")
        
        # 设置窗口图标（如果有的话）
        try:
            # root.iconbitmap('icon.ico')
            pass
        except:
            pass
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
