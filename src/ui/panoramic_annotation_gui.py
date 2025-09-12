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
from typing import Optional, Dict, List, Any, Callable
import json
from enum import Enum

# 日志导入
try:
    from src.utils.logger import (
        log_debug, log_info, log_warning, log_error,
        log_strategy, log_perf, log_nav, log_ann,
        log_debug_detail, log_ui_detail, log_timing,
        toggle_debug_logging, is_debug_logging_enabled
    )
except ImportError as e:
    # 日志模块导入失败，使用标准日志记录错误并退出
    import logging
    import sys
    
    logging.error(f"关键模块导入失败 - src.utils.logger: {e}")
    logging.error("请检查以下可能的问题:")
    logging.error("1. 文件 src/utils/logger.py 是否存在")
    logging.error("2. Python路径是否正确配置")
    logging.error("3. 相关依赖是否已安装")
    raise ImportError(f"无法导入必需的日志模块: {e}") from e

# 版本管理导入
try:
    from src.utils.version import get_version_display
except ImportError as e:
    # 注意：此时log_error可能还未定义，使用print作为临时方案
    print(f"警告: 版本模块导入失败 - src.utils.version: {e}")
    print("使用默认版本信息，请检查 src/utils/version.py 是否存在")
    
    def get_version_display():
        return "v1.0.0 (版本模块缺失)"

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
from src.ui.hole_manager import HoleManager
from src.ui.enhanced_annotation_panel import EnhancedAnnotationPanel
from src.services.panoramic_image_service import PanoramicImageService
from src.services.config_file_service import ConfigFileService
from src.models.panoramic_annotation import PanoramicAnnotation, PanoramicDataset
from src.models.enhanced_annotation import EnhancedPanoramicAnnotation, FeatureCombination


# 模型建议导入服务 - 尝试多个可能的路径
MODEL_SUGGESTION_SERVICE_AVAILABLE = False
ModelSuggestionImportService = None

# 尝试从不同路径导入模型建议服务
import_attempts = [
    ('src.services.model_suggestion_import_service', 'ModelSuggestionImportService'),
    ('services.model_suggestion_import_service', 'ModelSuggestionImportService'),
]

for module_path, class_name in import_attempts:
    try:
        module = __import__(module_path, fromlist=[class_name])
        ModelSuggestionImportService = getattr(module, class_name)
        MODEL_SUGGESTION_SERVICE_AVAILABLE = True
        print(f"信息: 成功从 {module_path} 导入模型建议服务")
        break
    except ImportError as e:
        # 使用print因为此时log函数可能还未定义
        print(f"调试: 尝试从 {module_path} 导入失败: {e}")
        continue

if not MODEL_SUGGESTION_SERVICE_AVAILABLE:
    print("警告: 模型建议服务不可用 - 模型建议功能将被禁用")
    print("警告: 缺失的服务: ModelSuggestionImportService")
    print("警告: 影响功能: 导入模型建议、模型视图模式")


# 视图模式枚举
class ViewMode(Enum):
    MANUAL = "人工"
    MODEL = "模型"


class ProgressDialog:
    """模态进度对话框"""

    def __init__(self, parent, title="正在加载", message="请稍候..."):
        self.parent = parent
        self.title = title
        self.message = message

        # 进度变量（必须在create_widgets之前初始化）
        self.progress_var = tk.DoubleVar()

        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)

        # 创建界面组件（在居中之前创建，以便获取准确尺寸）
        self.create_widgets()
        
        # 居中显示
        self.center_window()

        # 设置为模态窗口
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 强制显示并刷新
        self.dialog.update_idletasks()
        self.dialog.update()

    def center_window(self):
        """居中显示窗口 - 相对于父窗口居中"""
        # 先更新窗口以获取准确尺寸
        self.dialog.update_idletasks()
        self.parent.update_idletasks()  # 确保父窗口信息准确
        
        # 获取对话框窗口尺寸
        window_width = self.dialog.winfo_reqwidth()
        window_height = self.dialog.winfo_reqheight()
        
        # 如果窗口尺寸过小，使用默认值
        if window_width < 400:
            window_width = 400
        if window_height < 150:
            window_height = 150
        
        # 获取父窗口的位置和尺寸
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 计算相对于父窗口的居中位置
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        # 获取屏幕尺寸，确保窗口不会超出屏幕边界
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # 调整位置，确保完全在屏幕内
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        # 设置窗口位置和大小
        self.dialog.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 消息标签
        self.message_label = ttk.Label(main_frame, text=self.message, font=('TkDefaultFont', 10))
        self.message_label.pack(pady=(0, 15))

        # 进度条
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=300
        )
        self.progress_bar.pack(pady=(0, 10))

        # 进度文本
        self.progress_text_label = ttk.Label(main_frame, text="0%", font=('TkDefaultFont', 9))
        self.progress_text_label.pack()

    def update_progress(self, value, message=None):
        """更新进度"""
        self.progress_var.set(value)
        if message:
            self.message_label.config(text=message)
        self.progress_text_label.config(text=f"{int(value)}%")
        self.dialog.update_idletasks()
        self.dialog.update()  # 强制刷新界面

    def close(self):
        """关闭对话框"""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None


class PanoramicAnnotationGUI:
    """
    全景图像标注工具主界面
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        # 设置窗口标题（移除版本信息，保持简洁）
        self.root.title("全景图像标注工具")
        # 设置优化的窗口大小，调整为1600x900
        self.root.geometry("1600x900")   # 目标尺寸1600x900
        self.root.minsize(1400, 800)     # 保持最小尺寸
        
        # 记录服务可用性状态
        log_info(f"模型建议服务可用性: {MODEL_SUGGESTION_SERVICE_AVAILABLE}", "INIT")
        
        # 绑定日志方法到实例
        self.log_debug = log_debug
        self.log_info = log_info
        self.log_warning = log_warning
        self.log_error = log_error
        
        # 服务和管理器
        self.image_service = PanoramicImageService()
        self.hole_manager = HoleManager()
        self.config_service = ConfigFileService()
        
        # 模型建议服务 - 仅在可用时初始化
        if MODEL_SUGGESTION_SERVICE_AVAILABLE and ModelSuggestionImportService:
            try:
                self.model_suggestion_service = ModelSuggestionImportService()
                log_info("模型建议服务初始化成功", "INIT")
            except Exception as e:
                log_error(f"模型建议服务初始化失败: {e}", "INIT")
                self.model_suggestion_service = None
        else:
            self.model_suggestion_service = None
            log_warning("模型建议服务不可用，相关功能将被禁用", "INIT")
        
        # 模型建议相关属性
        self.current_suggestions_map = None
        self.model_suggestion_loaded = False
        
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
        
        # 起始点调整控制
        self.user_custom_start_coordinates = False  # 用户是否手动设置了起始坐标 (first_hole_x/y)

        # 操作状态控制 - 添加按钮状态管理
        self.is_saving = False  # 保存操作进行中标志
        self.save_button = None  # 保存按钮引用
        self.skip_button = None  # 跳过按钮引用
        self.clear_button = None  # 清除按钮引用

        # 高性能延迟配置 - 基于性能监控数据进一步优化（2025-09-12 22:00）
        # 性能分析显示延迟偏高，进一步优化延迟配置以提升响应速度
        self.delay_config = {
            'settings_apply': 10,       # 从30ms降至10ms，基于性能瓶颈分析结果
            'button_recovery': 50,      # 从150ms降至50ms，减少用户等待时间
            'quick_recovery': 30,       # 从100ms降至30ms，提升快速操作体验
            'ui_refresh': 20,           # 从50ms降至20ms，减少界面刷新延迟
            'verification': 50          # 从100ms降至50ms，加快验证速度
        }
        
        # 性能监控数据收集 - 详细分析复制设置性能
        self.performance_stats = {
            'settings_apply_times': [],     # 设置应用耗时记录
            'ui_load_times': [],           # UI加载耗时记录
            'button_response_times': [],   # 按钮响应时间记录
            
            # 详细的复制设置步骤计时
            'copy_settings_detailed': {
                'button_disable_times': [],     # 按钮禁用耗时
                'settings_collect_times': [],   # 设置收集耗时
                'navigation_times': [],         # 导航跳转耗时
                'ui_refresh_times': [],         # UI刷新耗时
                'settings_apply_times': [],     # 设置应用耗时
                'button_enable_times': [],      # 按钮启用耗时
                'total_copy_times': []          # 总耗时
            },
            
            # 按钮状态变化计时
            'button_state_changes': {
                'disable_start_times': [],      # 按钮开始禁用时间
                'disable_complete_times': [],   # 按钮禁用完成时间
                'enable_start_times': [],       # 按钮开始启用时间
                'enable_complete_times': []     # 按钮启用完成时间
            },
            
            'operation_counts': {          # 操作计数
                'save_and_next': 0,
                'skip': 0,
                'clear': 0,
                'settings_copy_success': 0,
                'settings_copy_fail': 0,
                'detailed_timing_collected': 0  # 详细计时收集次数
            }
        }
        
        # === 性能监控功能配置 ===
        # 性能数据收集开关 - 默认关闭
        # 如需重新启用性能监控功能：
        # 1. 将下行的 value=False 改为 value=True
        # 2. 取消注释工具栏中的性能监控相关按钮（搜索"性能监控相关功能已隐藏"）
        self.performance_monitoring_enabled = tk.BooleanVar(value=False)

        # 调试日志控制
        self.debug_logging_enabled = tk.BooleanVar(value=False)
        
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
        
        # 视图模式相关
        self.current_view_mode = ViewMode.MANUAL
        self.view_change_callbacks = []
        self.view_mode_var = tk.StringVar(value=ViewMode.MANUAL.value)
        
        # 全景图导航相关变量
        self.panoramic_ids = []  # 存储所有全景图ID
        self.panoramic_id_var = tk.StringVar()  # 当前选中的全景图ID
        
        # Enhanced annotation panel
        self.enhanced_annotation_panel = None
        
        # 创建界面
        self.create_widgets()
        self.setup_bindings()

        # 同步调试日志状态
        self.sync_debug_logging_state()

        # 状态栏
        self.update_status("就绪 - 请选择全景图目录")
    
    @staticmethod
    def determine_microbe_type_from_filename(panoramic_id: str) -> str:
        """根据全景图文件名前两位字符判断微生物类型
        
        Args:
            panoramic_id: 全景图ID，如 "FG10000026" 或 "EB10000026"
            
        Returns:
            str: "fungi" 如果前两位是FG，否则返回 "bacteria"
        """
        if panoramic_id and len(panoramic_id) >= 2:
            prefix = panoramic_id[:2].upper()
            if prefix == "FG":
                return "fungi"
        return "bacteria"
    
    def get_default_microbe_type(self, panoramic_id: str = None) -> str:
        """获取默认的微生物类型
        
        Args:
            panoramic_id: 全景图ID，如果提供则根据文件名判断，否则返回默认值
            
        Returns:
            str: 微生物类型，"bacteria" 或 "fungi"
        """
        if panoramic_id:
            return self.determine_microbe_type_from_filename(panoramic_id)
        return "bacteria"
    
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
        
        # 孔位参数配置面板已被移除（功能简化）
        
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

        # 重新排列按钮顺序并调整间距
        ttk.Button(toolbar, text="浏览并加载",
                  command=self.select_panoramic_directory).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="加载标注",
                  command=self.load_annotations).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="保存标注",
                  command=self.save_annotations).pack(side=tk.LEFT, padx=(0, 10))

        # 模型建议按钮 - 根据服务可用性设置状态
        self.model_suggestion_button = ttk.Button(toolbar, text="导入模型建议",
                  command=self.import_model_suggestions)
        self.model_suggestion_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 如果模型建议服务不可用，禁用按钮并添加提示
        if not MODEL_SUGGESTION_SERVICE_AVAILABLE:
            self.model_suggestion_button.configure(state='disabled')
            # 创建工具提示（简化版本）
            def show_unavailable_tooltip(event):
                messagebox.showwarning(
                    "功能不可用", 
                    "模型建议功能不可用\n\n原因：ModelSuggestionImportService 模块未找到"
                )
            self.model_suggestion_button.bind('<Double-Button-1>', show_unavailable_tooltip)

        # === 隐藏的调试和性能相关功能 ===
        # 以下按钮已隐藏，如需重新启用请取消注释：
        
        # ttk.Button(toolbar, text="起始点调整",
        #           command=self.show_start_position_dialog).pack(side=tk.LEFT, padx=(0, 10))

        # 调试日志开关 - 已隐藏，默认关闭
        # ttk.Checkbutton(toolbar, text="调试日志",
        #                variable=self.debug_logging_enabled,
        #                command=self.toggle_debug_logging).pack(side=tk.LEFT, padx=(0, 5))

        # === 性能监控相关功能已隐藏 ===
        # 性能监控开关
        # ttk.Checkbutton(toolbar, text="性能监控",
        #                variable=self.performance_monitoring_enabled).pack(side=tk.LEFT, padx=(0, 5))

        # 性能分析按钮
        # ttk.Button(toolbar, text="性能分析",
        #           command=self.show_performance_analysis).pack(side=tk.LEFT, padx=(0, 5))

        # # 延迟配置按钮
        # ttk.Button(toolbar, text="延迟配置",
        #           command=self.show_delay_config_dialog).pack(side=tk.LEFT, padx=(0, 5))
    
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

        # 统计 - 移到第一个位置
        self.create_stats_panel(right_frame)

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

        # 切片信息标签 - 添加debug日志跟踪字体大小
        slice_info_font = ('TkDefaultFont', 8)
        self.slice_info_label = ttk.Label(info_frame, text="未加载切片",
                                          font=slice_info_font)
        self.slice_info_label.pack(fill=tk.X, pady=(0, 2))
        log_ui_detail(f"创建切片信息标签 - 字体: {slice_info_font}, 位置: info_frame")

        # 标注预览区域 - 添加debug日志跟踪字体大小
        annotation_preview_font = ('TkDefaultFont', 8, 'bold')
        self.annotation_preview_label = ttk.Label(info_frame, text="标注状态: 未标注",
                                                font=annotation_preview_font)
        self.annotation_preview_label.pack(fill=tk.X, pady=(0, 2))
        log_ui_detail(f"创建标注预览标签 - 字体: {annotation_preview_font}, 位置: info_frame")

        # 详细标注信息预览区域 - 添加debug日志跟踪字体大小
        detailed_annotation_font = ('TkDefaultFont', 8)
        self.detailed_annotation_label = ttk.Label(info_frame, text="",
                                                  font=detailed_annotation_font)
        self.detailed_annotation_label.pack(fill=tk.X, pady=(0, 2))
        log_ui_detail(f"创建详细标注标签 - 字体: {detailed_annotation_font}, 位置: info_frame")

        # 标注控制 - 现在是最后一个区域，可以动态扩展
        self.create_annotation_panel(right_frame)
    
    # 孔位配置面板已移除（功能简化）
    
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
    
    def create_batch_panel(self, parent):
        """创建批量操作面板"""
        batch_frame = ttk.LabelFrame(parent, text="批量操作")
        batch_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 批量操作按钮
        button_frame = ttk.Frame(batch_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # 模型建议按钮
        ttk.Button(button_frame, text="模型建议", 
                  command=self.import_model_suggestions).pack(side=tk.LEFT, padx=2)
    
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
        
        # 注册增强标注面板的视图模式切换回调
        self.add_view_change_callback(self.enhanced_annotation_panel.on_view_mode_changed)
        
        # 标注按钮 - 移到增强标注面板下方
        self.button_frame = ttk.Frame(ann_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=(3, 3))
        
        # 保存按钮引用以便控制状态
        self.save_button = ttk.Button(self.button_frame, text="保存并下一个", 
                  command=self.save_current_annotation)
        self.save_button.pack(side=tk.LEFT, padx=2)
        
        self.skip_button = ttk.Button(self.button_frame, text="跳过", 
                  command=self.skip_current)
        self.skip_button.pack(side=tk.LEFT, padx=2)
        
        self.clear_button = ttk.Button(self.button_frame, text="清除标注", 
                  command=self.clear_current_annotation)
        self.clear_button.pack(side=tk.LEFT, padx=2)
    
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
        # 检查当前视图模式
        if hasattr(self, 'current_view_mode') and self.current_view_mode == ViewMode.MODEL:
            # 模型视图模式：显示模型预测结果，格式同人工视图，并在最后添加"预测"
            if hasattr(self, 'hole_manager') and self.hole_manager:
                suggestion = self.hole_manager.get_hole_suggestion(self.current_hole_number)
                if suggestion:
                    details = []

                    # 微生物类型
                    if hasattr(suggestion, 'microbe_type') and suggestion.microbe_type:
                        microbe_text = "细菌" if suggestion.microbe_type == "bacteria" else "真菌"
                        details.append(microbe_text)

                    # 生长级别
                    if hasattr(suggestion, 'growth_level') and suggestion.growth_level:
                        # 映射弱生长到阳性
                        mapped_level = self._map_growth_level_for_display(suggestion.growth_level)
                        growth_map = {
                            'negative': '阴性',
                            'positive': '阳性'
                        }
                        growth_text = growth_map.get(mapped_level, mapped_level)
                        details.append(growth_text)

                    # 生长模式
                    if hasattr(suggestion, 'growth_pattern') and suggestion.growth_pattern:
                        pattern_map = {
                            # 基础模式
                            'clean': '清亮',
                            'small_dots': '中心小点',
                            'light_gray': '浅灰色',
                            'irregular_areas': '不规则区域',
                            'clustered': '聚集型',
                            'scattered': '分散型',
                            'heavy_growth': '重度',
                            'focal': '聚焦性',
                            'diffuse': '弥散',
                            'default_positive': '阳性默认',
                            'default_weak_growth': '阳性默认',  # 弱生长默认映射为阳性默认
                            
                            # 新增的生长模式映射
                            'weak_scattered': '微弱分散',
                            'litter_center_dots': '弱中心点',
                            'strong_scattered': '强分散',
                            'center_dots': '强中心点',
                            'weak_scattered_pos': '弱分散',
                            'irregular': '不规则',
                            'filamentous_non_fused': '丝状非融合',
                            'filamentous_fused': '丝状融合'
                        }
                        if isinstance(suggestion.growth_pattern, list):
                            pattern_texts = [pattern_map.get(p, p) for p in suggestion.growth_pattern]
                            pattern_text = ", ".join(pattern_texts)
                        else:
                            pattern_text = pattern_map.get(suggestion.growth_pattern, suggestion.growth_pattern)
                        details.append(pattern_text)

                    # 置信度
                    if hasattr(suggestion, 'model_confidence') and suggestion.model_confidence is not None:
                        details.append(f"{suggestion.model_confidence:.2f}")

                    # 干扰因素 + 预测标识
                    if hasattr(suggestion, 'interference_factors') and suggestion.interference_factors:
                        interference_map = {
                            'pores': '气孔',
                            'artifacts': '气孔重叠',
                            'noise': '气孔重叠',
                            'debris': '杂质',
                            'contamination': '污染'
                        }
                        if isinstance(suggestion.interference_factors, list) and suggestion.interference_factors:
                            interference_text = ", ".join([interference_map.get(f, f) for f in suggestion.interference_factors])
                        else:
                            interference_text = "无干扰"
                        details.append(f"{interference_text} 预测")
                    else:
                        details.append("无干扰 预测")

                    return " | ".join(details)
                else:
                    return "当前切片无模型预测结果"
            else:
                return "模型数据未加载"


        else:
            # 人工视图模式：只显示人工标注结果，无则不显示
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
                    # 映射弱生长到阳性
                    mapped_level = self._map_growth_level_for_display(existing_ann.growth_level)
                    growth_map = {
                        'negative': '阴性',
                        'positive': '阳性'
                    }
                    growth_text = growth_map.get(mapped_level, mapped_level)
                    details.append(growth_text)

                # 生长模式（如果是增强标注）
                if hasattr(existing_ann, 'growth_pattern') and existing_ann.growth_pattern:
                    pattern_map = {
                        # 基础模式
                        'clean': '清亮',
                        'small_dots': '中心小点',
                        'light_gray': '浅灰色',
                        'irregular_areas': '不规则区域',
                        'clustered': '聚集型',
                        'scattered': '分散型',
                        'heavy_growth': '重度',
                        'focal': '聚焦性',
                        'diffuse': '弥散',
                        'default_positive': '阳性默认',
                        'default_weak_growth': '阳性默认',  # 弱生长默认映射为阳性默认
                        
                        # 新增的生长模式映射
                        'weak_scattered': '微弱分散',
                        'litter_center_dots': '弱中心点',
                        'strong_scattered': '强分散',
                        'center_dots': '强中心点',
                        'weak_scattered_pos': '弱分散',
                        'irregular': '不规则',
                        'filamentous_non_fused': '丝状非融合',
                        'filamentous_fused': '丝状融合'
                    }
                    pattern_text = pattern_map.get(existing_ann.growth_pattern, existing_ann.growth_pattern)
                    details.append(pattern_text)

                # 置信度
                if hasattr(existing_ann, 'confidence') and existing_ann.confidence:
                    details.append(f"{existing_ann.confidence:.2f}")

                # 干扰因素
                if hasattr(existing_ann, 'interference_factors') and existing_ann.interference_factors:
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
                # 人工视图无标注时，不显示任何结果
                return ""
    
    def get_annotation_status_text(self):
        """获取标注状态文本，包含日期时间 - 优先使用JSON中的保存时间"""
        # 检查当前视图模式
        if hasattr(self, 'current_view_mode') and self.current_view_mode == ViewMode.MODEL:
            # 模型视图模式：显示模型建议状态
            if hasattr(self, 'hole_manager') and self.hole_manager:
                if self.hole_manager.has_hole_suggestion(self.current_hole_number):
                    return "模型建议"
                else:
                    return "无模型建议"
            else:
                return "模型数据未加载"
        else:
            # 其他视图模式：显示已保存的标注状态
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
                            log_error(f"解析保存的时间戳失败: {e}", "TIMESTAMP")
                    
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
    
    def create_stats_panel(self, parent):
        """创建统计面板"""
        # 统计信息 - 纯统计功能
        stats_frame = ttk.LabelFrame(parent, text="统计信息")
        stats_frame.pack(fill=tk.X, pady=(0, 2))
        
        self.stats_label = ttk.Label(stats_frame, text="统计: 未标注 0, 阴性 0, 阳性 0")
        self.stats_label.pack(padx=5, pady=3)
        
        # 视图模式选择区域
        self.create_view_mode_panel(parent)
    
    def create_view_mode_panel(self, parent):
        """创建视图模式选择面板"""
        view_frame = ttk.LabelFrame(parent, text="视图模式")
        view_frame.pack(fill=tk.X, pady=(2, 2))

        # 视图模式单选按钮 - 只保留人工和模型
        mode_frame = ttk.Frame(view_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)

        self.manual_radio = ttk.Radiobutton(mode_frame, text="人工", variable=self.view_mode_var,
                                          value=ViewMode.MANUAL.value, command=self._on_view_mode_changed)
        self.manual_radio.pack(side=tk.LEFT, padx=5)

        self.model_radio = ttk.Radiobutton(mode_frame, text="模型", variable=self.view_mode_var,
                                          value=ViewMode.MODEL.value, command=self._on_view_mode_changed)
        self.model_radio.pack(side=tk.LEFT, padx=5)
        
        # 如果模型建议服务不可用，禁用模型视图模式
        if not MODEL_SUGGESTION_SERVICE_AVAILABLE:
            self.model_radio.configure(state='disabled')
            # 创建一个提示标签
            ttk.Label(mode_frame, text="(需要模型建议服务)", 
                     font=('TkDefaultFont', 8), foreground='gray').pack(side=tk.LEFT, padx=2)
    
    def _on_view_mode_changed(self):
        """视图模式变更事件处理"""
        try:
            # 获取当前选择的视图模式
            mode_value = self.view_mode_var.get()
            old_mode = self.current_view_mode
            
            # 如果尝试切换到模型视图但服务不可用，阻止切换
            if mode_value == ViewMode.MODEL.value and not MODEL_SUGGESTION_SERVICE_AVAILABLE:
                # 恢复到之前的模式
                self.view_mode_var.set(old_mode.value)
                messagebox.showwarning(
                    "模式不可用", 
                    "模型视图模式不可用\n\n原因：ModelSuggestionImportService 模块未找到\n\n"
                    "请检查系统配置或使用人工视图模式。"
                )
                return
            
            self.current_view_mode = ViewMode(mode_value)

            log_debug(f"[VIEW_MODE] 视图模式从 {old_mode.value} 切换到 {self.current_view_mode.value}")
            log_debug(f"[VIEW_MODE] 当前全景ID: {getattr(self, 'current_panoramic_id', 'None')}")
            log_debug(f"[VIEW_MODE] 当前孔号: {getattr(self, 'current_hole_number', 'None')}")

            # 检查hole_manager是否存在模型建议数据
            if hasattr(self, 'hole_manager') and self.hole_manager:
                # 获取建议摘要信息
                suggestions_summary = self.hole_manager.get_suggestions_summary()
                suggestions_count = suggestions_summary['total']
                log_debug(f"[VIEW_MODE] 模型建议数据总数: {suggestions_count}")

                # 检查当前切片是否有模型建议
                if hasattr(self, 'current_panoramic_id') and hasattr(self, 'current_hole_number'):
                    if self.current_panoramic_id and self.current_hole_number:
                        slice_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                        has_suggestion = self.hole_manager.has_hole_suggestion(self.current_hole_number)
                        log_debug(f"[VIEW_MODE] 当前切片键: {slice_key}, 是否有模型建议: {has_suggestion}")

                        if has_suggestion:
                            suggestion = self.hole_manager.get_hole_suggestion(self.current_hole_number)
                            if suggestion:
                                # 显示完整的模型建议信息
                                growth_pattern_str = ", ".join(suggestion.growth_pattern) if suggestion.growth_pattern else "无"
                                interference_factors_str = ", ".join(suggestion.interference_factors) if suggestion.interference_factors else "无"
                                log_debug(f"[VIEW_MODE] 模型建议详情: growth_level={suggestion.growth_level}, confidence={suggestion.model_confidence}, growth_pattern=[{growth_pattern_str}], interference_factors=[{interference_factors_str}]")
                            else:
                                log_debug(f"[VIEW_MODE] 获取模型建议详情失败")
                        else:
                            log_debug(f"[VIEW_MODE] 当前切片无模型建议数据")

            # 视图模式切换后，数据会通过load_current_slice重新加载，无需额外处理

            # 调用所有注册的回调函数
            callback_count = len(self.view_change_callbacks)
            log_debug(f"[VIEW_MODE] 注册的回调函数数量: {callback_count}")

            for i, callback in enumerate(self.view_change_callbacks):
                try:
                    log_debug(f"[VIEW_MODE] 执行回调函数 {i+1}/{callback_count}")
                    # 传递完整的参数：view_mode, hole_manager, slice_index
                    callback(self.current_view_mode, self.hole_manager, self.current_hole_number)
                    log_debug(f"[VIEW_MODE] 回调函数 {i+1} 执行成功")
                except Exception as e:
                    log_error(f"[VIEW_MODE] 回调函数 {i+1} 执行失败: {e}")

            # 更新状态显示
            mode_names = {
                ViewMode.MANUAL: "人工视图",
                ViewMode.MODEL: "模型视图"
            }
            mode_name = mode_names.get(self.current_view_mode, "未知视图")
            self.update_status(f"已切换到{mode_name}")

            # 重新加载当前切片以应用新的视图模式
            if hasattr(self, 'current_panoramic_id') and hasattr(self, 'current_hole_number'):
                if self.current_panoramic_id and self.current_hole_number:
                    log_debug(f"[VIEW_MODE] 开始重新加载切片")
                    self.load_current_slice()
                    log_debug(f"[VIEW_MODE] 切片重新加载完成")
                else:
                    log_debug(f"[VIEW_MODE] 当前无有效的全景ID或孔号，跳过切片重新加载")
            else:
                log_debug(f"[VIEW_MODE] 缺少current_panoramic_id或current_hole_number属性")

        except Exception as e:
            log_error(f"[VIEW_MODE] 视图模式变更失败: {e}")
            messagebox.showerror("错误", f"视图模式变更失败: {str(e)}")
    
    def add_view_change_callback(self, callback: Callable[[ViewMode], None]):
        """添加视图模式变更回调函数"""
        if callback not in self.view_change_callbacks:
            self.view_change_callbacks.append(callback)
    
    def remove_view_change_callback(self, callback: Callable[[ViewMode], None]):
        """移除视图模式变更回调函数"""
        if callback in self.view_change_callbacks:
            self.view_change_callbacks.remove(callback)
    
    def get_current_view_mode(self) -> ViewMode:
        """获取当前视图模式"""
        return self.current_view_mode
    
    def set_view_mode(self, mode: ViewMode):
        """设置视图模式"""
        try:
            self.view_mode_var.set(mode.value)
            self.current_view_mode = mode
            self._on_view_mode_changed()
        except Exception as e:
            log_error(f"设置视图模式失败: {e}", "VIEW_MODE")
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 主状态标签（左侧，可扩展）
        self.status_label = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 版本信息标签（右侧，固定宽度）
        version_display = get_version_display()
        self.version_label = ttk.Label(status_frame, text=f"版本: {version_display}", 
                                      relief=tk.SUNKEN, width=15)
        self.version_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def update_version_display(self):
        """更新版本信息显示"""
        try:
            version_display = get_version_display()
            if hasattr(self, 'version_label') and self.version_label:
                self.version_label.config(text=f"版本: {version_display}")
        except Exception as e:
            log_debug(f"更新版本显示时出错: {e}", "VERSION")
    
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
        
        # 版本信息快捷键
        self.root.bind('<F1>', lambda e: self.show_about_dialog())  # F1 显示操作指南
        
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
            self.set_growth_level('positive')  # 弱生长已移除，映射到阳性
    
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
            log_debug("没有窗口尺寸变化日志数据", "ANALYSIS")
            return
        
        log_debug("开始窗口尺寸变化日志分析", "ANALYSIS")

        # 分析不同事件类型的尺寸变化
        resize_events = [e for e in self.window_resize_log if e['event'] == 'resize']
        load_panoramic_events = [e for e in self.window_resize_log if e['event'] in ['load_panoramic_start', 'load_panoramic_complete']]
        load_annotation_events = [e for e in self.window_resize_log if e['event'] in ['load_annotations_start', 'load_annotations_complete']]

        log_debug(f"总体统计 - 总日志条目: {len(self.window_resize_log)}, 手动调整次数: {len(resize_events)}, 全景图加载事件: {len(load_panoramic_events)}, 标注加载事件: {len(load_annotation_events)}", "ANALYSIS")

        # 分析手动调整的尺寸
        if resize_events:
            widths = [e['width'] for e in resize_events]
            heights = [e['height'] for e in resize_events]

            log_debug(f"手动调整尺寸分析 - 宽度范围: {min(widths)} - {max(widths)} px, 高度范围: {min(heights)} - {max(heights)} px", "ANALYSIS")
            log_debug(f"平均尺寸 - 宽度: {sum(widths)/len(widths):.0f} px, 高度: {sum(heights)/len(heights):.0f} px", "ANALYSIS")

            # 找出最常用的尺寸
            from collections import Counter
            size_counts = Counter([f"{e['width']}x{e['height']}" for e in resize_events])
            most_common = size_counts.most_common(3)
            log_debug(f"最常用尺寸: {most_common[0][0]} (出现{most_common[0][1]}次)", "ANALYSIS")

        # 分析加载前后的尺寸变化
        log_debug("开始分析加载事件", "ANALYSIS")

        # 全景图加载
        for i in range(0, len(load_panoramic_events), 2):
            if i+1 < len(load_panoramic_events):
                start = load_panoramic_events[i]
                complete = load_panoramic_events[i+1]
                if start['event'] == 'load_panoramic_start' and complete['event'] == 'load_panoramic_complete':
                    log_debug(f"全景图加载: {start['panoramic_id']}", "ANALYSIS")
                    log_debug(f"加载前: {start['geometry']}", "ANALYSIS")
                    log_debug(f"加载后: {complete['geometry']}", "ANALYSIS")

        # 标注加载
        for i in range(0, len(load_annotation_events), 2):
            if i+1 < len(load_annotation_events):
                start = load_annotation_events[i]
                complete = load_annotation_events[i+1]
                if start['event'] == 'load_annotations_start' and complete['event'] == 'load_annotations_complete':
                    log_debug(f"标注加载: {complete.get('annotation_count', 'N/A')}个标注", "ANALYSIS")
                    log_debug(f"加载前: {start['geometry']}", "ANALYSIS")
                    log_debug(f"加载后: {complete['geometry']}", "ANALYSIS")

        # 推荐最佳尺寸
        if resize_events:
            final_widths = [e['width'] for e in resize_events[-10:]]  # 最近10次调整
            final_heights = [e['height'] for e in resize_events[-10:]]
            recommended_width = int(sum(final_widths) / len(final_widths))
            recommended_height = int(sum(final_heights) / len(final_heights))

            log_debug(f"推荐尺寸 - 基于用户使用习惯: {recommended_width}x{recommended_height}", "ANALYSIS")
            log_debug(f"当前尺寸 - 默认: {self.initial_geometry}, 实际: {self.current_geometry}", "ANALYSIS")

        log_debug("窗口尺寸变化日志分析完成", "ANALYSIS")
    
    def select_panoramic_directory(self):
        """选择全景图目录并自动加载数据"""
        directory = filedialog.askdirectory(title="选择全景图目录")
        if directory:
            self.panoramic_dir_var.set(directory)
            self.panoramic_directory = directory
            # 保留关键的用户提示信息
            log_info(f"已选择全景图目录: {directory}", "DIRECTORY")

            # 自动加载数据
            if not self.load_data():
                # 加载失败，重置目录选择
                self.panoramic_dir_var.set("")
                self.panoramic_directory = ""
                log_warning("目录加载失败，已重置选择", "DIRECTORY")
    
    def load_data(self):
        """加载数据 - 使用子目录结构"""
        if not self.panoramic_directory:
            messagebox.showerror("错误", "请先选择全景图目录")
            return False

        progress_dialog = None

        try:
            # 立即显示进度条以提供即时反馈
            log_debug("开始数据加载流程", "LOAD_DATA")
            progress_dialog = ProgressDialog(self.root, "正在加载全景图数据", "正在扫描目录...")
            progress_dialog.update_progress(0, "开始扫描文件...")
            log_debug("进度对话框已创建", "LOAD_DATA")
            
            # 预扫描：更精确的文件计数 - 只统计图像文件
            from pathlib import Path
            directory_path = Path(self.panoramic_directory)
            
            progress_dialog.update_progress(5, "正在统计图像文件...")
            
            # 只统计实际的图像文件
            image_extensions = {'.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif'}
            image_files = []
            subdirs = []
            
            progress_dialog.update_progress(10, "正在扫描主目录...")
            
            for item in directory_path.iterdir():
                if item.is_file() and item.suffix.lower() in image_extensions:
                    image_files.append(item)
                elif item.is_dir():
                    subdirs.append(item)
                    # 统计子目录中的图像文件
                    for sub_item in item.iterdir():
                        if sub_item.is_file() and sub_item.suffix.lower() in image_extensions:
                            image_files.append(sub_item)
            
            progress_dialog.update_progress(20, "文件统计完成...")
            
            total_files = len(image_files)
            log_debug(f"检测到 {total_files} 个图像文件", "LOAD_DATA")
            
            # 决定是否继续显示进度条
            show_progress = total_files > 5  # 进一步降低阈值到5个文件
            log_debug(f"继续显示进度条: {show_progress} (文件数: {total_files})", "LOAD_DATA")

            if not show_progress:
                # 如果文件不多，关闭进度条
                progress_dialog.close()
                progress_dialog = None
                log_debug("文件数量较少，关闭进度条", "LOAD_DATA")

            # 进度回调函数
            def progress_callback(current, total, message):
                if progress_dialog:
                    try:
                        # 计算百分比 (20-90%区间用于文件处理)
                        percentage = 20 + (current / max(total, 1)) * 70
                        progress_dialog.update_progress(percentage, message)
                        
                        # 强制刷新界面
                        self.root.update_idletasks()
                        
                        log_debug(f"进度更新: {current}/{total} ({percentage:.1f}%) - {message}", "PROGRESS")
                    except Exception as e:
                        log_error(f"进度更新失败: {e}", "PROGRESS")

            # 使用子目录模式：直接使用全景目录下的子目录
            log_debug("开始调用 get_slice_files_from_directory", "LOAD_DATA")
            
            # 确保进度回调被正确传递
            if progress_dialog:
                progress_callback(0, total_files, "开始处理切片文件...")
            
            self.slice_files = self.image_service.get_slice_files_from_directory(
                self.panoramic_directory, self.panoramic_directory, progress_callback)
            
            structure_msg = '子目录模式'

            if not self.slice_files:
                if progress_dialog:
                    progress_dialog.close()
                messagebox.showerror("错误",
                    "未找到有效的切片文件。\n请检查：\n" +
                    "1. 目录下是否存在全景图文件（.bmp, .png, .jpg等）\n" +
                    "2. 是否存在包含切片的子目录\n" +
                    "3. 切片文件应在 <全景文件>/hole_<孔序号>.png 位置")
                return False

            # 更新进度 - 数据加载完成
            if progress_dialog:
                progress_callback(total_files, total_files, "数据加载完成，正在初始化界面...")

            # 更新全景图列表
            self.update_panoramic_list()

            # 根据第一个全景图的类型设置起始孔位
            if self.slice_files and len(self.slice_files) > 0:
                first_panoramic_id = self.slice_files[0]['panoramic_id']
                if first_panoramic_id.upper().startswith('SE'):
                    # SE类型全景图：前4个孔位为空，从第5个孔开始
                    if hasattr(self, 'hole_manager') and self.hole_manager:
                        self.hole_manager.update_positioning_params(start_hole=5)
                        log_debug(f"初始全景图 {first_panoramic_id} 为SE类型，设置起始孔位为5", "LOAD_DATA")
                else:
                    # 普通全景图：从第1个孔开始
                    if hasattr(self, 'hole_manager') and self.hole_manager:
                        self.hole_manager.update_positioning_params(start_hole=1)
                        log_debug(f"初始全景图 {first_panoramic_id} 为普通类型，设置起始孔位为1", "LOAD_DATA")

            # 重置状态
            self.current_dataset = PanoramicDataset("新数据集",
                f"从 {self.panoramic_directory} 加载的数据集 ({structure_msg})")

            # 找到第一个有效孔位的索引（从起始孔位开始）
            self.current_slice_index = self.find_first_valid_slice_index()

            # 最后的界面初始化
            if progress_dialog:
                progress_dialog.update_progress(95, "正在加载切片...")

            # 加载第一个有效切片
            self.load_current_slice()

            # 自动切换视图模式
            self.auto_switch_view_mode()

            # 完成进度
            if progress_dialog:
                progress_dialog.update_progress(100, "加载完成")
                # 延迟关闭进度窗口，让用户看到完成状态
                self.root.after(500, lambda: progress_dialog.close() if progress_dialog else None)
                log_debug("进度条显示完成，延迟关闭", "LOAD_DATA")

            self.update_status(f"已加载 {len(self.slice_files)} 个切片文件 ({structure_msg})")
            self.update_progress()
            # 保留关键的用户提示信息
            log_info(f"数据加载完成: {len(self.slice_files)} 个切片", "LOAD_DATA")
            return True

        except Exception as e:
            # 确保进度窗口被关闭
            if progress_dialog:
                try:
                    progress_dialog.close()
                except:
                    pass
            log_error(f"数据加载失败: {str(e)}", "LOAD_DATA")
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
            return False
    
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
    
    def _load_annotations_optimized(self):
        """优化的标注加载：一次性设置所有属性，避免多次UI更新"""
        # 首先检查已有标注
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        log_debug(f"优化标注加载 - 孔位{self.current_hole_number}, 有已有标注: {existing_ann is not None}", "LOAD")
        
        if existing_ann:
            # 有已有标注，直接设置
            self._apply_existing_annotation(existing_ann)
            return
        
        # 没有已有标注，检查配置文件标注
        config_annotation = self._get_config_annotation(self.current_panoramic_id, self.current_hole_number)
        if config_annotation:
            # 有配置文件标注，设置并导入
            self._apply_config_annotation(config_annotation)
            return
        
        # 既没有已有标注也没有配置标注，只有在需要重置时才设置默认值
        # （在panoramic_changed且reset_to_defaults=True时已经设置过了）
        log_debug("无任何标注，保持当前设置或默认设置", "LOAD")

    def _apply_existing_annotation(self, existing_ann):
        """应用已有标注，一次性设置所有属性"""
        try:
            # 安全地获取属性，提供默认值（根据当前全景图判断微生物类型）
            default_microbe_type = self.get_default_microbe_type(getattr(self, 'current_panoramic_id', None))
            microbe_type = getattr(existing_ann, 'microbe_type', default_microbe_type)
            growth_level = getattr(existing_ann, 'growth_level', 'negative')
            
            log_debug(f"应用已有标注 - 类型:{microbe_type}, 等级:{growth_level}", "LOAD")
            
            # 设置界面状态
            self.current_microbe_type.set(microbe_type)
            self.current_growth_level.set(growth_level)
        except Exception as e:
            log_error(f"设置基本标注属性失败: {e}", "LOAD")
            # 使用默认值
            default_microbe_type = self.get_default_microbe_type(getattr(self, 'current_panoramic_id', None))
            self.current_microbe_type.set(default_microbe_type)
            self.current_growth_level.set('negative')
            return
        
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
                    log_debug(f"强制使用保存的时间戳: {annotation_key} -> {dt.strftime('%m-%d %H:%M:%S')}", "LOAD")
                except Exception as e:
                    log_error(f"时间戳解析失败: {e}", "TIMESTAMP")
                    # 解析失败时生成一个默认时间戳，但不使用可能错误的内存缓存
                    default_time = datetime.datetime.now()
                    self.last_annotation_time[annotation_key] = default_time
                    log_debug(f"生成新默认时间戳: {annotation_key} -> {default_time.strftime('%m-%d %H:%M:%S')}", "LOAD")
            else:
                # 如果标注对象没有时间戳属性，生成一个默认时间戳
                default_time = datetime.datetime.now()
                self.last_annotation_time[annotation_key] = default_time
                log_debug(f"标注对象无时间戳，生成默认时间戳: {annotation_key} -> {default_time.strftime('%m-%d %H:%M:%S')}", "LOAD")
                            
        # 同步到增强标注面板
        if self.enhanced_annotation_panel:
            if hasattr(existing_ann, 'enhanced_data') and existing_ann.enhanced_data:
                try:
                    from models.enhanced_annotation import FeatureCombination
                    enhanced_data = existing_ann.enhanced_data
                    
                    # 确保enhanced_data是字典格式
                    if isinstance(enhanced_data, dict):
                        # 检查是否包含feature_combination数据
                        if 'feature_combination' in enhanced_data:
                            combination_data = enhanced_data['feature_combination']
                            # 创建FeatureCombination对象并应用到面板
                            combination = FeatureCombination.from_dict(combination_data)
                            self.enhanced_annotation_panel.set_feature_combination(combination)
                            log_debug("成功加载增强标注数据到面板", "LOAD")
                        else:
                            log_warning("enhanced_data中缺少feature_combination字段", "LOAD")
                    else:
                        log_warning(f"enhanced_data不是字典类型: {type(enhanced_data)}", "LOAD")
                except Exception as e:
                    log_error(f"加载增强标注数据失败: {e}", "LOAD")
                    # 如果加载增强数据失败，至少确保基本标注数据可用
                    if self.enhanced_annotation_panel:
                        # 安全地获取属性
                        growth_level = getattr(existing_ann, 'growth_level', 'negative')
                        microbe_type = getattr(existing_ann, 'microbe_type', 'bacteria')
                        self.enhanced_annotation_panel.initialize_with_defaults(
                            growth_level=growth_level,
                            microbe_type=microbe_type,
                            reset_interference=False
                        )
            else:
                # 对于没有enhanced_data的标注（如配置文件导入的标注），使用基本数据初始化面板
                growth_level = getattr(existing_ann, 'growth_level', 'negative')
                microbe_type = getattr(existing_ann, 'microbe_type', 'bacteria')
                self.enhanced_annotation_panel.initialize_with_defaults(
                    growth_level=growth_level,
                    microbe_type=microbe_type,
                    reset_interference=False
                )
                log_debug(f"使用基本数据初始化增强面板: {microbe_type}, {growth_level}", "LOAD")
        
        # 设置干扰因素
        if hasattr(existing_ann, 'interference_factors') and existing_ann.interference_factors:
            try:
                if isinstance(existing_ann.interference_factors, list):
                    # 重置所有干扰因素
                    for factor in self.interference_factors:
                        self.interference_factors[factor].set(False)
                    # 设置已标注的干扰因素
                    for factor in existing_ann.interference_factors:
                        if factor in self.interference_factors:
                            self.interference_factors[factor].set(True)
                    log_debug(f"设置干扰因素: {existing_ann.interference_factors}", "LOAD")
            except Exception as e:
                log_error(f"设置干扰因素失败: {e}", "LOAD")
    
    def _get_config_annotation(self, panoramic_id: str, hole_number: int):
        """获取配置文件中的标注数据"""
        if not panoramic_id or not self.panoramic_directory:
            return None
        
        try:
            # 查找全景图文件 - 使用子目录模式
            panoramic_file = self.image_service.find_panoramic_image(
                f"{panoramic_id}/hole_1.png", 
                self.panoramic_directory
            )
            
            if not panoramic_file:
                return None
            
            # 查找对应的配置文件
            config_file = self.config_service.find_config_file(panoramic_file)
            if not config_file:
                return None
            
            # 解析配置文件
            config_annotations = self.config_service.parse_config_file(config_file)
            if not config_annotations or hole_number not in config_annotations:
                return None
            
            # 解析标注字符串
            annotation_str = config_annotations[hole_number]
            parsed_annotation = self._parse_annotation_string(annotation_str, panoramic_id)
            
            return {
                'annotation_str': annotation_str,
                'parsed': parsed_annotation,
                'slice_filename': f"hole_{hole_number}.png"  # 子目录模式
            }
        except Exception as e:
            log_debug(f"获取配置标注时出错: {e}", "LOAD")
            return None
    
    def _apply_config_annotation(self, config_annotation):
        """应用配置文件标注"""
        try:
            parsed = config_annotation['parsed']
            # 安全地获取属性，提供默认值（从解析结果中获取已确定的微生物类型）
            microbe_type = parsed.get('microbe_type', self.get_default_microbe_type(getattr(self, 'current_panoramic_id', None)))
            growth_level = parsed.get('growth_level', 'negative')
            
            log_debug(f"应用配置标注 - 类型:{microbe_type}, 等级:{growth_level}", "LOAD")
            
            # 设置界面状态
            self.current_microbe_type.set(microbe_type)
            self.current_growth_level.set(growth_level)
        except Exception as e:
            log_error(f"应用配置标注失败: {e}", "LOAD")
            # 使用默认值
            default_microbe_type = self.get_default_microbe_type(getattr(self, 'current_panoramic_id', None))
            self.current_microbe_type.set(default_microbe_type)
            self.current_growth_level.set('negative')
            return
        
        # 设置干扰因素
        if parsed.get('interference_factors'):
            # 重置所有干扰因素
            for factor in self.interference_factors:
                self.interference_factors[factor].set(False)
            # 设置解析出的干扰因素
            for factor in parsed['interference_factors']:
                if factor in self.interference_factors:
                    self.interference_factors[factor].set(True)
        
        # 导入到数据集（如果还未导入）
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, self.current_hole_number
        )
        
        if not existing_ann:
            # 创建标注对象 - 配置文件导入，未确认状态
            # 使用已导入的 PanoramicAnnotation 类
            default_microbe_type = self.get_default_microbe_type(getattr(self, 'current_panoramic_id', None))
            annotation = PanoramicAnnotation.from_filename(
                config_annotation['slice_filename'],
                label=parsed.get('label', ''),
                panoramic_id=self.current_panoramic_id,  # 子目录模式必需参数
                microbe_type=parsed.get('microbe_type', default_microbe_type),
                growth_level=parsed.get('growth_level', 'negative'),
                interference_factors=parsed.get('interference_factors', []),
                annotation_source='config',
                is_confirmed=False
            )
            
            # 添加到数据集
            self.current_dataset.add_annotation(annotation)
            log_debug(f"导入配置标注: {config_annotation['annotation_str']}", "LOAD")

    def _has_config_annotation(self, panoramic_id: str, hole_number: int) -> bool:
        """检查指定孔位是否有配置文件标注"""
        if not panoramic_id or not self.panoramic_directory:
            return False
        
        try:
            # 查找全景图文件 - 使用子目录模式
            panoramic_file = self.image_service.find_panoramic_image(
                f"{panoramic_id}/hole_1.png", 
                self.panoramic_directory
            )
            
            if not panoramic_file:
                return False
            
            # 查找对应的配置文件
            config_file = self.config_service.find_config_file(panoramic_file)
            if not config_file:
                return False
            
            # 解析配置文件
            config_annotations = self.config_service.parse_config_file(config_file)
            if not config_annotations:
                return False
            
            # 检查是否有该孔位的标注
            return hole_number in config_annotations
        except Exception as e:
            log_debug(f"检查配置标注时出错: {e}", "LOAD")
            return False

    def load_current_slice(self):
        """加载当前切片"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            self.log_debug("load_current_slice: 没有文件或索引超出范围")
            return
        
        current_file = self.slice_files[self.current_slice_index]
        self.log_debug(f"load_current_slice: 当前文件 {current_file.get('filepath', 'Unknown')}")
        
        try:
            # 检查全景图是否改变
            old_panoramic_id = getattr(self, 'current_panoramic_id', None)
            new_panoramic_id = current_file['panoramic_id']
            panoramic_changed = (not hasattr(self, 'current_panoramic_id') or 
                              self.current_panoramic_id != current_file['panoramic_id'])
            
            self.log_debug(f"load_current_slice: 旧全景图ID {old_panoramic_id}, 新全景图ID {new_panoramic_id}")
            self.log_debug(f"load_current_slice: 全景图是否改变 {panoramic_changed}")

            # 如果全景图改变，准备重置标注状态，但先检查是否有现有标注
            reset_to_defaults = False
            if panoramic_changed:
                # 检查当前孔位是否有已有标注或配置标注
                existing_ann = self.current_dataset.get_annotation_by_hole(
                    current_file['panoramic_id'], 
                    current_file['hole_number']
                )
                
                # 检查是否有配置文件标注
                has_config_annotation = self._has_config_annotation(
                    current_file['panoramic_id'], 
                    current_file['hole_number']
                )
                
                # 只有当没有任何标注时才重置为默认值
                if not existing_ann and not has_config_annotation:
                    reset_to_defaults = True
                    self.current_growth_level.set("negative")
                    # 根据全景图文件名设置默认微生物类型
                    default_microbe_type = self.get_default_microbe_type(new_panoramic_id)
                    self.current_microbe_type.set(default_microbe_type)
                    # 重置干扰因素
                    for factor in self.interference_factors:
                        self.interference_factors[factor].set(False)
                    # 重置增强标注面板
                    if self.enhanced_annotation_panel:
                        self.enhanced_annotation_panel.reset_annotation()
                    self.log_debug("全景图改变且无现有标注，重置为默认状态", "LOAD")
                else:
                    self.log_debug(f"全景图改变但有现有标注 (existing: {existing_ann is not None}, config: {has_config_annotation})，跳过默认重置", "LOAD")

            # 更新当前信息
            self.current_panoramic_id = current_file['panoramic_id']
            self.current_hole_number = current_file['hole_number']
            self.hole_number_var.set(str(self.current_hole_number))

            # 如果全景图改变，根据类型设置起始孔位
            if panoramic_changed:
                if self.current_panoramic_id.upper().startswith('SE'):
                    # SE类型全景图：前4个孔位为空，从第5个孔开始
                    if hasattr(self, 'hole_manager') and self.hole_manager:
                        self.hole_manager.update_positioning_params(start_hole=5)
                        self.log_debug(f"SE类型全景图，设置起始孔位为5", "LOAD")
                else:
                    # 普通全景图：恢复默认起始孔位
                    if hasattr(self, 'hole_manager') and self.hole_manager:
                        self.hole_manager.update_positioning_params(start_hole=1)
                        self.log_debug(f"普通类型全景图，设置起始孔位为1", "LOAD")

            # 更新hole_manager的panoramic_id，确保模型建议正确显示
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager._current_panoramic_id = self.current_panoramic_id

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
                    
                    # 添加标注状态指示
                    self.draw_slice_annotation_indicator(canvas_width, canvas_height)
            
            # 加载对应的全景图（强制每次都加载以确保刷新）
            self.log_debug(f"load_current_slice: 强制调用load_panoramic_image (panoramic_changed={panoramic_changed})")
            self.load_panoramic_image()
            self.log_debug("load_current_slice: load_panoramic_image调用完成")
            
            # 更新当前孔位指示框
            self.draw_current_hole_indicator()
            
            # 更新切片信息，包含标注状态
            self.update_slice_info_display()
            
            # 根据视图模式加载相应的标注数据 - 优化为一次性设置
            if hasattr(self, 'current_view_mode') and self.current_view_mode == ViewMode.MODEL:
                # 模型视图：不加载已有标注，显示模型预测结果
                log_debug("模型视图模式，显示模型预测结果", "LOAD")
                self._load_model_view_data()
            else:
                # 人工视图：优化标注加载逻辑，避免多次设置
                log_debug("人工视图模式，优化标注加载", "LOAD")
                self._load_annotations_optimized()

            # 重置修改标记
            self.current_annotation_modified = False

            # 延迟强制刷新确保统计和状态完全同步
            self.root.after_idle(self._delayed_navigation_refresh)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载切片失败: {str(e)}")
    
    def _delayed_navigation_refresh(self):
        """延迟导航刷新，确保所有数据已正确加载"""
        try:
            log_debug(f"延迟导航刷新 - 孔位{self.current_hole_number}", "NAV")
            
            # 强制更新统计信息
            self.update_statistics()
            self.root.update_idletasks()
            
            # 强制更新状态显示
            self.update_slice_info_display()
            self.root.update_idletasks()
            
            # 更新当前孔位的红色指示框（延迟执行确保画布已更新）
            self.root.after(50, self.draw_current_hole_indicator)
            
            # 再次验证更新结果，必要时重复更新
            self.root.after(100, self._verify_and_retry_sync)
            
            log_debug("延迟导航刷新完成", "NAV")
            
        except Exception as e:
            log_error(f"延迟导航刷新失败: {e}", "ERROR")
    
    def _force_navigation_refresh(self):
        """导航后强制刷新，确保统计和状态更新"""
        try:
            log_debug(f"强制导航刷新 - 孔位{self.current_hole_number}", "NAV")
            
            # 立即更新统计和状态
            self.update_statistics()
            self.root.update_idletasks()
            
            self.update_slice_info_display()
            self.root.update_idletasks()
            
            # 更新当前孔位的红色指示框（延迟执行确保画布已更新）
            self.root.after(50, self.draw_current_hole_indicator)
            
            # 强制刷新界面
            self.root.update()
            
            # 再次确保红色指示框正确显示
            self.root.after(100, self.draw_current_hole_indicator)
            
            log_debug("强制导航刷新完成", "NAV")
            
        except Exception as e:
            log_error(f"强制导航刷新失败: {e}", "ERROR")
    
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
                
            log_debug("验证同步完成", "VERIFY")
            
        except Exception as e:
            log_error(f"验证同步失败: {e}", "SYNC")
    
    def load_panoramic_image(self):
        """加载全景图"""
        if not self.current_panoramic_id:
            return
        
        # 检查画布是否准备就绪
        if not self._is_canvas_ready():
            # 初始化重试计数器
            if not hasattr(self, '_panoramic_load_retry_count'):
                self._panoramic_load_retry_count = 0
            
            # 限制重试次数
            if self._panoramic_load_retry_count < 5:
                self._panoramic_load_retry_count += 1
                log_debug(f"画布未准备就绪，延迟重试 ({self._panoramic_load_retry_count}/5)", "LOAD_PANORAMIC")
                self.root.after(100, self.load_panoramic_image)
                return
            else:
                log_debug("画布重试次数已达上限，使用默认尺寸", "LOAD_PANORAMIC")
        
        # 重置重试计数器
        self._reset_panoramic_load_retry()
        
        # 记录加载全景图前的窗口状态
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        current_geometry = self.root.geometry()
        
        # 避免重复记录同一个全景图的加载日志
        current_time = time.time()
        should_log = True
        if hasattr(self, '_last_panoramic_load_time'):
            if (self._last_panoramic_load_id == self.current_panoramic_id and 
                current_time - self._last_panoramic_load_time < 1.0):
                # 1秒内重复加载同一个全景图，跳过日志记录
                should_log = False
        
        if should_log:
            log_debug(f"{timestamp} - 开始加载全景图 {self.current_panoramic_id}, 当前窗口: {current_geometry}", "LOAD_PANORAMIC")
        
        # 更新最后加载时间和ID
        self._last_panoramic_load_time = current_time
        self._last_panoramic_load_id = self.current_panoramic_id
        
        # 记录到日志
        log_entry = {
            'timestamp': timestamp,
            'geometry': current_geometry,
            'event': 'load_panoramic_start',
            'panoramic_id': self.current_panoramic_id
        }
        self.window_resize_log.append(log_entry)
        
        try:
            # 查找全景图文件 - 使用子目录模式
            panoramic_file = self.image_service.find_panoramic_image(
                f"{self.current_panoramic_id}/hole_1.png", 
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
                
                # 记录画布尺寸用于调试
                log_debug(f"画布尺寸: {canvas_width}x{canvas_height}", "LOAD_PANORAMIC")
                
                # 使用实际画布尺寸，留少量边距 - 适应新的1240px宽度
                # 如果画布尺寸无效，使用默认尺寸
                if canvas_width <= 1 or canvas_height <= 1:
                    log_debug(f"画布尺寸无效，使用默认尺寸", "LOAD_PANORAMIC")
                    canvas_width, canvas_height = 1220, 750
                
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
            
        except FileNotFoundError as e:
            log_debug(f"全景图文件未找到: {str(e)}", "LOAD_PANORAMIC")
            self.panoramic_info_label.config(text=f"文件未找到: {self.current_panoramic_id}")
        except PermissionError as e:
            log_debug(f"全景图文件权限错误: {str(e)}", "LOAD_PANORAMIC")
            self.panoramic_info_label.config(text=f"文件权限错误: {self.current_panoramic_id}")
        except Exception as e:
            log_error(f"加载全景图失败: {str(e)}", "LOAD_PANORAMIC")
            self.panoramic_info_label.config(text=f"加载全景图失败: {self.current_panoramic_id}")
        
        # 记录加载全景图后的窗口状态
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        final_geometry = self.root.geometry()
        
        # 只有在开始记录了日志时才记录完成日志
        if should_log:
            log_debug(f"{timestamp} - 完成加载全景图 {self.current_panoramic_id}, 当前窗口: {final_geometry}", "LOAD_PANORAMIC")
        
        # 记录到日志
        log_entry = {
            'timestamp': timestamp,
            'geometry': final_geometry,
            'event': 'load_panoramic_complete',
            'panoramic_id': self.current_panoramic_id
        }
        self.window_resize_log.append(log_entry)
        
        # 绘制当前孔位的红色指示框
        self.draw_current_hole_indicator()
        
        # 清除配置数据缓存，强制重新加载新全景图的配置
        if hasattr(self, '_config_data_cache'):
            self._config_data_cache.clear()
    
    def _is_canvas_ready(self):
        """检查画布是否准备就绪"""
        try:
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
    
    def _parse_annotation_string(self, annotation_str: str, panoramic_id: str = None) -> dict:
        """
        解析标注字符串，支持复杂格式和中文干扰因素
        
        Args:
            annotation_str: 标注字符串，如 "positive", "positive_with_artifacts", "positive_with_气孔重叠"
            panoramic_id: 全景图ID，用于确定默认微生物类型
            
        Returns:
            dict: 包含解析结果的字典 {'label': str, 'growth_level': str, 'microbe_type': str, 'interference_factors': list}
        """
        try:
            # 根据全景图ID确定默认微生物类型
            default_microbe_type = self.get_default_microbe_type(panoramic_id)
            
            # 默认值
            result = {
                'label': annotation_str,
                'growth_level': 'negative',
                'microbe_type': default_microbe_type,
                'interference_factors': []
            }
            
            if not annotation_str:
                return result
            
            # 检查是否为复杂标注格式
            if '_with_' in annotation_str:
                parts = annotation_str.split('_with_', 1)
                growth_level = parts[0]
                factors_str = parts[1]
                
                # 解析干扰因素
                interference_factors = []
                if factors_str:
                    # 支持用下划线分隔的多个干扰因素
                    factors = factors_str.split('_')
                    
                    # 中文到英文的映射
                    interference_mapping = {
                        '气孔': 'pores',
                        '气孔重叠': 'artifacts',
                        '伪影': 'artifacts',
                        '杂质': 'debris',
                        '污染': 'contamination',
                        '污渍': 'contamination',
                        # 英文别名兼容
                        'pores': 'pores',
                        'debris': 'debris',
                        'contamination': 'contamination',
                        'artifacts': 'artifacts',
                        'noise': 'artifacts',
                        'edge_blur': 'pores',
                        'scratches': 'debris'
                    }
                    
                    for factor in factors:
                        # 映射到标准英文值
                        mapped_factor = interference_mapping.get(factor, factor)
                        interference_factors.append(mapped_factor)
                
                result.update({
                    'label': annotation_str,
                    'growth_level': growth_level,
                    'microbe_type': default_microbe_type,
                    'interference_factors': interference_factors
                })
            else:
                # 简单标注格式
                result.update({
                    'label': annotation_str,
                    'growth_level': annotation_str,
                    'microbe_type': default_microbe_type,
                    'interference_factors': []
                })
            
            return result
            
        except Exception as e:
            log_error(f"解析标注字符串失败: {annotation_str}, 错误: {e}", "ANNOTATION")
            return {
                'label': annotation_str,
                'growth_level': 'negative',
                'microbe_type': self.get_default_microbe_type(panoramic_id),
                'interference_factors': []
            }
    
    def draw_slice_annotation_indicator(self, canvas_width, canvas_height):
        """在切片预览画布上绘制标注状态指示器"""
        if not hasattr(self, 'current_panoramic_id') or not hasattr(self, 'current_hole_number'):
            return
            
        try:
            # 检查当前孔位是否已人工标注
            is_manual_confirmed = False
            manual_annotation = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id, self.current_hole_number
            )
            if manual_annotation and hasattr(manual_annotation, 'annotation_source'):
                is_manual_confirmed = manual_annotation.annotation_source in ['enhanced_manual', 'manual']
            
            # 如果已标注，在右上角绘制亮黄色标记
            if is_manual_confirmed:
                # 计算标记位置和尺寸
                indicator_size = 20  # 标记尺寸
                margin = 5  # 距离边缘的间距
                
                # 右上角位置
                x = canvas_width - margin - indicator_size // 2
                y = margin + indicator_size // 2
                
                # 绘制圆形标记
                self.slice_canvas.create_oval(
                    x - indicator_size // 2, y - indicator_size // 2,
                    x + indicator_size // 2, y + indicator_size // 2,
                    fill='#FFFF00',  # 亮黄色
                    outline='black',  # 黑色边框
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

    def draw_current_hole_indicator(self):
        """更新当前孔位的外框颜色状态"""
        log_debug(f"draw_current_hole_indicator 调用 - panoramic_image: {self.panoramic_image is not None}, current_hole_number: {getattr(self, 'current_hole_number', 'N/A')}", "DISPLAY")
        
        if not self.panoramic_image or not hasattr(self, 'current_hole_number'):
            log_debug("draw_current_hole_indicator 早期退出: 缺少panoramic_image或current_hole_number", "DISPLAY")
            return
            
        # 直接调用绘制所有配置框的方法，会自动高亮当前孔位
        self.draw_all_config_hole_boxes()
    
    def draw_all_config_hole_boxes(self):
        """在全景图上绘制所有孔位的配置状态框，当前孔位用特殊样式高亮，并显示人工确认状态"""
        if not self.panoramic_image or not hasattr(self, 'current_panoramic_id'):
            return

        try:
            # 获取画布尺寸
            canvas_width = self.panoramic_canvas.winfo_width()
            canvas_height = self.panoramic_canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                return

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

            # 删除之前的所有配置框（包括可能的遗留标签）
            self.panoramic_canvas.delete("config_hole_boxes")
            self.panoramic_canvas.delete("config_hole_boxes_current")
            self.panoramic_canvas.delete("current_hole_indicator")  # 清理可能的遗留标签
            self.panoramic_canvas.delete("manual_annotation_markers")  # 清理人工标注标记

            # 获取当前全景图的所有配置数据
            config_data = self.get_current_panoramic_config()
            if not config_data:
                log_debug("没有配置数据可绘制", "DISPLAY")
                return

            # 定义新的颜色方案 - 更符合逻辑的医学检测颜色
            color_map = {
                'positive': '#CC0000',        # 阳性：深红色（危险/需关注）
                'negative': '#00AA00',        # 阴性：深绿色（安全/正常）
                'uncertain': '#9932CC',       # 不确定：深紫色（需进一步确认）
                'default': '#708090'          # 默认：石板灰（未分类/中性）
            }

            # 当前孔位的特殊高亮颜色（更亮的版本）
            current_color_map = {
                'positive': '#FF0000',        # 阳性当前：亮红色
                'negative': '#00FF00',        # 阴性当前：亮绿色
                'uncertain': '#DA70D6',       # 不确定当前：亮紫色
                'default': '#C0C0C0'          # 默认当前：银色
            }

            # 人工确认状态的视觉标记颜色 - 使用亮黄色
            manual_confirm_color = '#FFFF00'      # 亮黄色 - 醒目但不过于刺眼

            # 绘制每个有配置的孔位
            drawn_count = 0
            manual_confirmed_count = 0

            for hole_number, growth_level in config_data.items():
                try:
                    # 获取孔位中心坐标
                    hole_center = self.hole_manager.get_hole_center_coordinates(hole_number)

                    # 计算孔位在画布上的坐标
                    hole_x = offset_x + int(hole_center[0] * scale_factor)
                    hole_y = offset_y + int(hole_center[1] * scale_factor)

                    # 计算框的大小（使用原始的90像素外框设计）
                    box_size = max(20, int(90 * scale_factor))

                    # 判断是否为当前孔位
                    is_current = (hole_number == self.current_hole_number)

                    # 检查是否已人工确认（有增强手动标注）
                    is_manual_confirmed = False
                    manual_annotation = self.current_dataset.get_annotation_by_hole(
                        self.current_panoramic_id, hole_number
                    )
                    if manual_annotation and hasattr(manual_annotation, 'annotation_source'):
                        is_manual_confirmed = manual_annotation.annotation_source in ['enhanced_manual', 'manual']

                    # 如果已人工确认，显示人工标注的颜色而非配置文件的颜色
                    if is_manual_confirmed:
                        # 使用人工标注的生长级别，而不是配置文件的
                        display_growth_level = manual_annotation.growth_level
                        log_debug(f"孔位{hole_number}使用人工标注颜色: {display_growth_level}", "DISPLAY")
                    else:
                        # 使用配置文件的生长级别
                        display_growth_level = growth_level

                    # 选择颜色和线宽
                    if is_current:
                        color = current_color_map.get(display_growth_level, current_color_map['default'])
                        width = 3  # 当前孔位用较粗的线框
                        tags = "config_hole_boxes_current"
                    else:
                        color = color_map.get(display_growth_level, color_map['default'])
                        width = 1  # 其他孔位用普通线宽
                        tags = "config_hole_boxes"

                    # 绘制配置状态框
                    self.panoramic_canvas.create_rectangle(
                        hole_x - box_size//2, hole_y - box_size//2,
                        hole_x + box_size//2, hole_y + box_size//2,
                        outline=color, width=width, tags=tags
                    )

                    # 如果已人工确认，绘制醒目的亮黄色三角标记
                    if is_manual_confirmed:
                        # 计算更大的三角形标记 - 增大尺寸提高可见性
                        triangle_size = max(12, int(25 * scale_factor))  # 保持较大尺寸
                        
                        # 右上角三角形标记点
                        triangle_points = [
                            hole_x + box_size//2, hole_y - box_size//2,  # 右上角顶点
                            hole_x + box_size//2 - triangle_size, hole_y - box_size//2,  # 左上点
                            hole_x + box_size//2, hole_y - box_size//2 + triangle_size   # 右下点
                        ]

                        # 绘制简洁的亮黄色人工确认标记
                        self.panoramic_canvas.create_polygon(
                            triangle_points,
                            fill=manual_confirm_color,
                            outline='black',  # 黑色边框增强对比
                            width=1,
                            tags="manual_annotation_markers"
                        )

                        manual_confirmed_count += 1

                    drawn_count += 1

                    if is_current:
                        log_debug(f"当前孔位{hole_number}高亮显示: {growth_level}, 颜色{color}, 线宽{width}", "DISPLAY")

                except Exception as e:
                    log_debug(f"绘制孔位{hole_number}配置框失败: {e}", "DISPLAY")
                    continue

            log_debug(f"绘制了 {drawn_count} 个配置孔位框，其中 {manual_confirmed_count} 个已人工确认，当前孔位: {self.current_hole_number}", "DISPLAY")

            # 确保当前孔位框在最顶层
            self.panoramic_canvas.tag_raise("config_hole_boxes_current")
            # 人工确认标记也放在较高层级
            self.panoramic_canvas.tag_raise("manual_annotation_markers")

        except Exception as e:
            log_debug(f"绘制所有配置孔位框失败: {e}", "DISPLAY")
    
    def get_current_panoramic_config(self):
        """获取当前全景图的配置数据"""
        if not hasattr(self, 'current_panoramic_id') or not self.current_panoramic_id:
            return {}
        
        # 检查缓存中是否有配置数据
        cache_key = f"{self.current_panoramic_id}_config_data"
        if hasattr(self, '_config_data_cache') and cache_key in self._config_data_cache:
            return self._config_data_cache[cache_key]
        
        try:
            # 查找配置文件 - 使用子目录模式
            panoramic_filename = f"{self.current_panoramic_id}/hole_1.png"
            panoramic_file = self.image_service.find_panoramic_image(
                panoramic_filename, 
                getattr(self, 'panoramic_directory', '')
            )
            
            if not panoramic_file:
                return {}
            
            # 解析配置文件
            config_file = self.config_service.find_config_file(panoramic_file)
            if not config_file:
                return {}
            
            config_annotations = self.config_service.parse_config_file(config_file)
            if not config_annotations:
                return {}
            
            # 缓存配置数据
            if not hasattr(self, '_config_data_cache'):
                self._config_data_cache = {}
            self._config_data_cache[cache_key] = config_annotations
            
            return config_annotations
            
        except Exception as e:
            log_debug(f"获取当前全景图配置失败: {e}", "CONFIG")
            return {}
    
    def load_existing_annotation(self):
        """加载已有标注（保留兼容性）"""
        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id, 
            self.current_hole_number
        )
        
        log_debug(f"加载已有标注 - 孔位{self.current_hole_number}, 有标注: {existing_ann is not None}", "LOAD")
        
        if existing_ann:
            self._apply_existing_annotation(existing_ann)

    def load_config_annotations(self):
        """加载配置文件中的标注数据"""
        if not self.current_panoramic_id or not self.panoramic_directory:
            return
        
        # 检查是否已经加载过这个全景图的配置文件
        config_cache_key = f"{self.current_panoramic_id}_config"
        if hasattr(self, '_config_cache') and config_cache_key in self._config_cache:
            return  # 已经加载过，避免重复解析
        
        try:
            # 查找全景图文件 - 使用子目录模式
            panoramic_file = self.image_service.find_panoramic_image(
                f"{self.current_panoramic_id}/hole_1.png", 
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
            for hole_number, annotation_str in config_annotations.items():
                # 检查是否已存在标注
                existing_ann = self.current_dataset.get_annotation_by_hole(
                    self.current_panoramic_id, hole_number
                )
                
                if not existing_ann:  # 只导入未标注的孔位
                    # 解析标注字符串，支持复杂格式
                    parsed_annotation = self._parse_annotation_string(annotation_str, self.current_panoramic_id)
                    
                    # 查找对应的切片文件 - 使用子目录模式
                    slice_filename = f"hole_{hole_number}.png"
                    
                    # 创建标注对象 - 配置文件导入，未确认状态
                    # 使用已导入的 PanoramicAnnotation 类
                    default_microbe_type = self.get_default_microbe_type(self.current_panoramic_id)
                    annotation = PanoramicAnnotation.from_filename(
                        slice_filename,
                        panoramic_id=self.current_panoramic_id,  # 子目录模式需要提供panoramic_id
                        label=parsed_annotation.get('label', ''),
                        microbe_type=parsed_annotation.get('microbe_type', default_microbe_type),
                        growth_level=parsed_annotation.get('growth_level', 'negative'),
                        interference_factors=parsed_annotation.get('interference_factors', []),
                        annotation_source='config',
                        is_confirmed=False
                    )
                    
                    # 添加到数据集
                    self.current_dataset.add_annotation(annotation)
                    imported_count += 1
                    
                    log_debug(f"导入配置标注: 孔位{hole_number} - {annotation_str}", "CONFIG")
            
            if imported_count > 0:
                log_info(f"从配置文件导入了 {imported_count} 个标注", "CONFIG")
                self.update_statistics()
                
                # 核心修复：配置文件导入后刷新当前孔位的界面显示
                self.load_existing_annotation()
            
            # 标记已加载此配置文件
            if not hasattr(self, '_config_cache'):
                self._config_cache = set()
            self._config_cache.add(config_cache_key)
            
        except Exception as e:
            log_error(f"加载配置文件标注失败: {e}", "CONFIG")
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
                    # 安全地获取属性
                    growth_level = getattr(annotation, 'growth_level', 'negative')
                    default_microbe_type = self.get_default_microbe_type(getattr(self, 'current_panoramic_id', None))
                    microbe_type = getattr(annotation, 'microbe_type', default_microbe_type)
                                        
                    if user_growth_pattern:
                        self.enhanced_annotation_panel.initialize_with_pattern(
                            growth_level=growth_level,
                            microbe_type=microbe_type,
                            growth_pattern=user_growth_pattern,
                            reset_interference=False
                        )
                    else:
                        self.enhanced_annotation_panel.initialize_with_defaults(
                            growth_level=growth_level,
                            microbe_type=microbe_type,
                            reset_interference=False
                        )
                else:
                    # 没有干扰因素的标注，正常初始化
                    # 安全地获取属性
                    growth_level = getattr(annotation, 'growth_level', 'negative')
                    default_microbe_type = self.get_default_microbe_type(getattr(self, 'current_panoramic_id', None))
                    microbe_type = getattr(annotation, 'microbe_type', default_microbe_type)
                    
                    if user_growth_pattern:
                                                self.enhanced_annotation_panel.initialize_with_pattern(
                            growth_level=growth_level,
                            microbe_type=microbe_type,
                            growth_pattern=user_growth_pattern
                        )
                    else:
                                                self.enhanced_annotation_panel.initialize_with_defaults(
                            growth_level=growth_level,
                            microbe_type=microbe_type
                        )
                
                # 处理干扰因素（如果有的话）
                if annotation.interference_factors:
                    from models.enhanced_annotation import InterferenceType
                    
                    # 干扰因素映射（现在使用标准英文值）
                    interference_map = {
                        # 标准英文值
                        'pores': InterferenceType.PORES,
                        'artifacts': InterferenceType.ARTIFACTS,
                        'debris': InterferenceType.DEBRIS,
                        'contamination': InterferenceType.CONTAMINATION,
                        # 中文兼容
                        '气孔': InterferenceType.PORES,
                        '气孔重叠': InterferenceType.ARTIFACTS,
                        '伪影': InterferenceType.ARTIFACTS,
                        '杂质': InterferenceType.DEBRIS,
                        '污染': InterferenceType.CONTAMINATION,
                        '污渍': InterferenceType.CONTAMINATION,
                        # 英文别名兼容
                        'noise': InterferenceType.ARTIFACTS,     # 噪声 -> 伪影
                        'edge_blur': InterferenceType.PORES,      # 兼容旧的边缘模糊值
                        'scratches': InterferenceType.DEBRIS      # 划痕 -> 杂质
                    }
                    
                    for factor in annotation.interference_factors:
                        if factor in interference_map:
                            mapped_factor = interference_map[factor]
                            if mapped_factor in self.enhanced_annotation_panel.interference_vars:
                                self.enhanced_annotation_panel.interference_vars[mapped_factor].set(True)
                        else:
                            log_warning(f"未映射的干扰因素: {factor}")
                                            
                            
        except Exception as e:
            log_error(f"同步基础标注到增强面板失败: {e}")
            import traceback
            traceback.print_exc()

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
            log_debug(f"获取当前标注设置失败: {e}", "COPY")
            return None
    
    def apply_annotation_settings(self, settings):
        """应用标注设置到下一个孔位 - 性能优化版本"""
        if not settings or not hasattr(self, 'enhanced_annotation_panel') or not self.enhanced_annotation_panel:
            return False
        
        try:
            log_debug(f"应用设置到下一个孔位: 生长级别={settings['growth_level']}", "COPY")
            
            # 批量设置，减少UI刷新次数
            
            # 1. 设置微生物类型
            self.current_microbe_type.set(settings['microbe_type'])
            
            # 2. 设置生长级别
            growth_level_value = settings['growth_level']
            if hasattr(growth_level_value, 'value'):
                growth_level_value = growth_level_value.value
            self.enhanced_annotation_panel.current_growth_level.set(growth_level_value)
            
            # 3. 设置生长模式
            if settings['growth_pattern']:
                self.enhanced_annotation_panel.current_growth_pattern.set(settings['growth_pattern'])
            
            # 4. 优化的干扰因素处理
            if settings['interference_factors']:
                self._apply_interference_factors_optimized(settings['interference_factors'])
            else:
                # 如果没有干扰因素，快速重置
                panel_factors = self.enhanced_annotation_panel.interference_vars
                for var in panel_factors.values():
                    var.set(False)
            
            # 5. 设置置信度
            self.enhanced_annotation_panel.current_confidence.set(settings['confidence'])
            
            # 6. 统一刷新界面（只调用一次）
            self.enhanced_annotation_panel.update_pattern_options()
            self.root.update_idletasks()
            
            log_debug(f"设置应用完成", "COPY")
            return True
            
        except Exception as e:
            log_error(f"应用设置失败: {e}", "COPY")
            return False

    def _apply_interference_factors_optimized(self, interference_factors):
        """优化的干扰因素应用方法"""
        try:
            panel_factors = self.enhanced_annotation_panel.interference_vars
            
            # 先重置所有干扰因素
            for var in panel_factors.values():
                var.set(False)
            
            # 创建快速查找映射，避免重复循环
            panel_mapping = {}
            for panel_key, panel_var in panel_factors.items():
                # 直接键匹配
                panel_mapping[panel_key] = panel_var
                
                # 值匹配
                panel_value = panel_key.value if hasattr(panel_key, 'value') else str(panel_key)
                panel_mapping[panel_value] = panel_var
                
                # 字符串表示匹配
                panel_mapping[str(panel_key)] = panel_var
            
            # 快速设置干扰因素
            applied_count = 0
            for factor in interference_factors:
                factor_applied = False
                
                # 1. 直接匹配
                if factor in panel_mapping:
                    panel_mapping[factor].set(True)
                    factor_applied = True
                
                # 2. 值匹配
                elif hasattr(factor, 'value') and factor.value in panel_mapping:
                    panel_mapping[factor.value].set(True)
                    factor_applied = True
                
                # 3. 字符串匹配
                elif str(factor) in panel_mapping:
                    panel_mapping[str(factor)].set(True)
                    factor_applied = True
                
                # 4. 类名匹配（最后尝试，避免复杂操作）
                elif isinstance(factor, str) and '.' in factor:
                    factor_name = factor.split('.')[-1]
                    for key, var in panel_mapping.items():
                        if str(key).endswith(factor_name):
                            var.set(True)
                            factor_applied = True
                            break
                
                if factor_applied:
                    applied_count += 1
                else:
                    log_debug(f"未能匹配干扰因素: {factor}", "COPY")
            
            if applied_count > 0:
                log_debug(f"成功应用 {applied_count}/{len(interference_factors)} 个干扰因素", "COPY")
            
        except Exception as e:
            log_error(f"应用干扰因素失败: {e}", "COPY")
    
    def apply_annotation_settings_sync(self, settings):
        """同步应用标注设置，优化性能减少UI刷新次数"""
        if not settings or not hasattr(self, 'enhanced_annotation_panel') or not self.enhanced_annotation_panel:
            return False
        
        try:
            log_debug(f"开始优化同步应用设置: 生长级别={settings['growth_level']}", "APPLY_SYNC")
            
            # 批量设置所有参数，减少中间刷新
            # 1. 设置微生物类型
            self.current_microbe_type.set(settings['microbe_type'])
            
            # 2. 设置生长级别
            growth_level_value = settings['growth_level']
            if hasattr(growth_level_value, 'value'):
                growth_level_value = growth_level_value.value
            self.enhanced_annotation_panel.current_growth_level.set(growth_level_value)
            
            # 3. 更新生长模式选项（必须在设置生长级别后）
            self.enhanced_annotation_panel.update_pattern_options()
            
            # 4. 批量设置干扰因素（优化性能）
            if settings['interference_factors']:
                self._apply_interference_factors_optimized_fast(settings['interference_factors'])
            else:
                # 快速重置干扰因素
                panel_factors = self.enhanced_annotation_panel.interference_vars
                for var in panel_factors.values():
                    var.set(False)
            
            # 5. 设置生长模式（放在干扰因素之后）
            if settings['growth_pattern']:
                self.enhanced_annotation_panel.current_growth_pattern.set(settings['growth_pattern'])
            
            # 6. 设置置信度
            self.enhanced_annotation_panel.current_confidence.set(settings['confidence'])
            
            # 7. 单次同步UI更新 - 最小化刷新操作
            self.root.update_idletasks()  # 使用轻量级刷新而非完整update()
            
            log_debug(f"优化同步设置应用完成", "APPLY_SYNC")
            return True
            
        except Exception as e:
            log_error(f"同步应用设置失败: {e}", "APPLY_SYNC")
            return False

    def _apply_interference_factors_optimized_fast(self, interference_factors):
        """快速优化的干扰因素应用方法，减少查找和匹配开销"""
        try:
            panel_factors = self.enhanced_annotation_panel.interference_vars
            
            # 先重置所有干扰因素（批量操作）
            for var in panel_factors.values():
                var.set(False)
            
            # 使用预构建的快速映射减少查找时间
            if not hasattr(self, '_interference_factor_mapping'):
                self._build_interference_factor_mapping()
            
            # 快速设置干扰因素
            applied_count = 0
            for factor in interference_factors:
                # 使用预构建映射快速查找
                panel_var = self._interference_factor_mapping.get(factor)
                if panel_var:
                    panel_var.set(True)
                    applied_count += 1
                else:
                    # 如果直接映射失败，尝试值匹配
                    factor_value = factor.value if hasattr(factor, 'value') else str(factor)
                    panel_var = self._interference_factor_mapping.get(factor_value)
                    if panel_var:
                        panel_var.set(True)
                        applied_count += 1
            
            log_debug(f"快速应用了 {applied_count}/{len(interference_factors)} 个干扰因素", "APPLY_SYNC")
            
        except Exception as e:
            log_error(f"快速应用干扰因素失败: {e}", "APPLY_SYNC")
    
    def _build_interference_factor_mapping(self):
        """构建干扰因素的快速映射表，减少运行时查找开销"""
        try:
            self._interference_factor_mapping = {}
            panel_factors = self.enhanced_annotation_panel.interference_vars
            
            for panel_key, panel_var in panel_factors.items():
                # 直接键映射
                self._interference_factor_mapping[panel_key] = panel_var
                
                # 值映射
                panel_value = panel_key.value if hasattr(panel_key, 'value') else str(panel_key)
                self._interference_factor_mapping[panel_value] = panel_var
                
                # 字符串表示映射
                self._interference_factor_mapping[str(panel_key)] = panel_var
            
            log_debug(f"构建干扰因素映射表，包含{len(self._interference_factor_mapping)}个条目", "APPLY_SYNC")
            
        except Exception as e:
            log_error(f"构建干扰因素映射失败: {e}", "APPLY_SYNC")

    def _apply_single_interference_factor(self, factor, panel_factors):
        """应用单个干扰因素"""
        try:
            # 情况1: 直接匹配
            if factor in panel_factors:
                panel_factors[factor].set(True)
                log_debug(f"✓ 直接设置干扰因素: {factor}", "APPLY_INTERFERENCE")
                return True
            
            # 情况2: 枚举匹配
            elif hasattr(factor, 'value'):
                factor_value = factor.value
                for panel_key, panel_var in panel_factors.items():
                    panel_value = panel_key.value if hasattr(panel_key, 'value') else panel_key
                    if panel_value == factor_value:
                        panel_var.set(True)
                        log_debug(f"✓ 通过枚举值设置干扰因素: {factor_value}", "APPLY_INTERFERENCE")
                        return True
            
            # 情况3: 字符串匹配
            elif isinstance(factor, str):
                for panel_key, panel_var in panel_factors.items():
                    panel_value = panel_key.value if hasattr(panel_key, 'value') else panel_key
                    if panel_value == factor:
                        panel_var.set(True)
                        log_debug(f"✓ 通过字符串匹配设置干扰因素: {factor}", "APPLY_INTERFERENCE")
                        return True
            
            log_warning(f"未能匹配干扰因素: {factor}", "APPLY_INTERFERENCE")
            return False
            
        except Exception as e:
            log_error(f"应用干扰因素失败: {factor}, 错误: {e}", "APPLY_INTERFERENCE")
            return False
    
    def _record_performance_data(self, operation_type, duration_ms, success=True):
        """记录性能数据 - 不自动调整，仅收集分析用"""
        if not self.performance_monitoring_enabled.get():
            return
            
        try:
            # 记录操作时长
            if operation_type == 'settings_apply':
                self.performance_stats['settings_apply_times'].append(duration_ms)
                # 保持最近100次记录
                if len(self.performance_stats['settings_apply_times']) > 100:
                    self.performance_stats['settings_apply_times'] = self.performance_stats['settings_apply_times'][-100:]
                    
                # 记录成功/失败计数
                if success:
                    self.performance_stats['operation_counts']['settings_copy_success'] += 1
                else:
                    self.performance_stats['operation_counts']['settings_copy_fail'] += 1
                    
            elif operation_type == 'ui_load':
                self.performance_stats['ui_load_times'].append(duration_ms)
                if len(self.performance_stats['ui_load_times']) > 100:
                    self.performance_stats['ui_load_times'] = self.performance_stats['ui_load_times'][-100:]
                    
            elif operation_type == 'button_response':
                self.performance_stats['button_response_times'].append(duration_ms)
                if len(self.performance_stats['button_response_times']) > 100:
                    self.performance_stats['button_response_times'] = self.performance_stats['button_response_times'][-100:]
            
            # 记录操作计数
            if operation_type in ['save_and_next', 'skip', 'clear']:
                self.performance_stats['operation_counts'][operation_type] += 1
                
            log_debug(f"性能数据记录: {operation_type} = {duration_ms:.1f}ms, 成功: {success}", "PERFORMANCE")
            
        except Exception as e:
            log_error(f"记录性能数据失败: {e}", "PERFORMANCE")

    def _record_detailed_copy_timing(self, step_name, duration_ms):
        """记录详细的复制设置步骤计时"""
        if not self.performance_monitoring_enabled.get():
            return
            
        try:
            detailed_stats = self.performance_stats['copy_settings_detailed']
            
            if step_name in detailed_stats:
                detailed_stats[step_name].append(duration_ms)
                # 保持最近50次记录
                if len(detailed_stats[step_name]) > 50:
                    detailed_stats[step_name] = detailed_stats[step_name][-50:]
                    
                log_debug(f"详细计时记录: {step_name} = {duration_ms:.1f}ms", "DETAILED_TIMING")
            else:
                log_warning(f"未知的详细计时步骤: {step_name}", "DETAILED_TIMING")
                
        except Exception as e:
            log_error(f"记录详细计时失败: {e}", "DETAILED_TIMING")

    def _record_button_state_timing(self, event_type, timestamp_ms):
        """记录按钮状态变化时间点"""
        if not self.performance_monitoring_enabled.get():
            return
            
        try:
            state_stats = self.performance_stats['button_state_changes']
            
            if event_type in state_stats:
                state_stats[event_type].append(timestamp_ms)
                # 保持最近50次记录
                if len(state_stats[event_type]) > 50:
                    state_stats[event_type] = state_stats[event_type][-50:]
                    
                log_debug(f"按钮状态计时: {event_type} = {timestamp_ms:.1f}ms", "BUTTON_TIMING")
            else:
                log_warning(f"未知的按钮状态事件: {event_type}", "BUTTON_TIMING")
                
        except Exception as e:
            log_error(f"记录按钮状态计时失败: {e}", "BUTTON_TIMING")

    def _get_performance_summary(self):
        """获取性能数据摘要 - 包含详细计时分析"""
        try:
            summary = {
                'delay_config': self.delay_config.copy(),
                'stats': {},
                'detailed_stats': {},  # 新增详细统计
                'button_timing_stats': {},  # 新增按钮时序统计
                'recommendations': []
            }
            
            # 分析设置应用性能
            if self.performance_stats['settings_apply_times']:
                times = self.performance_stats['settings_apply_times']
                summary['stats']['settings_apply'] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times),
                    'min_ms': min(times),
                    'max_ms': max(times),
                    'p95_ms': sorted(times)[int(len(times) * 0.95)] if len(times) >= 20 else max(times)
                }
                
                # 分析并给出建议 - 改进的智能建议算法
                avg_time = summary['stats']['settings_apply']['avg_ms']
                p95_time = summary['stats']['settings_apply']['p95_ms']
                current_delay = self.delay_config['settings_apply']
                
                # 智能延迟建议算法
                if p95_time < current_delay * 0.2:
                    # 如果95%的操作都比当前延迟快5倍以上，大幅减少延迟
                    recommended_delay = max(20, int(p95_time * 3))  # 最小20ms，3倍安全边距
                    summary['recommendations'].append({
                        'type': 'settings_apply_delay',
                        'current': current_delay,
                        'recommended': recommended_delay,
                        'reason': f'95%操作耗时({p95_time:.1f}ms)明显小于当前延迟({current_delay}ms)，可以大幅减少延迟提高响应速度'
                    })
                elif p95_time < current_delay * 0.5:
                    # 如果95%的操作都比当前延迟快2倍以上，适度减少延迟
                    recommended_delay = max(30, int(p95_time * 2))  # 最小30ms，2倍安全边距
                    summary['recommendations'].append({
                        'type': 'settings_apply_delay',
                        'current': current_delay,
                        'recommended': recommended_delay,
                        'reason': f'95%操作耗时({p95_time:.1f}ms)小于当前延迟({current_delay}ms)，可以减少延迟提高响应速度'
                    })
                elif avg_time > current_delay * 0.8:
                    # 如果平均时间接近当前延迟，建议增加延迟
                    recommended_delay = min(800, int(avg_time * 1.1))  # 更保守的建议，最大800ms
                    summary['recommendations'].append({
                        'type': 'settings_apply_delay',
                        'current': current_delay,
                        'recommended': recommended_delay,
                        'reason': f'平均操作耗时({avg_time:.1f}ms)接近当前延迟({current_delay}ms)，建议增加延迟避免设置应用不完整'
                    })
                
                # 性能优化成功的正面反馈
                if avg_time < 10 and current_delay > avg_time * 10:
                    summary['recommendations'].append({
                        'type': 'optimization_success',
                        'target': 'settings_apply_performance',
                        'current_time': avg_time,
                        'improvement': f'设置应用性能优异({avg_time:.1f}ms)，相比之前的性能问题已完全解决',
                        'reason': f'算法优化效果显著，设置应用耗时从数百毫秒降至{avg_time:.1f}ms，建议适当降低延迟提升响应速度'
                    })
                
                # 新增：设置应用性能过慢的优化建议
                if avg_time > 400:  # 如果设置应用超过400ms
                    summary['recommendations'].append({
                        'type': 'performance_optimization',
                        'target': 'settings_apply',
                        'current_time': avg_time,
                        'reason': f'设置应用耗时({avg_time:.1f}ms)过长，建议：1)减少UI刷新频率 2)优化干扰因素匹配算法 3)使用预构建映射表'
                    })
                
                # 新增：总操作时间过长的警告
                if 'total_copy_times' in summary.get('detailed_stats', {}):
                    total_avg = summary['detailed_stats']['total_copy_times']['avg_ms']
                    if total_avg > 2000:  # 总时间超过2秒
                        summary['recommendations'].append({
                            'type': 'user_experience_warning',
                            'target': 'total_operation_time',
                            'current_time': total_avg,
                            'reason': f'完整操作耗时({total_avg:.1f}ms)过长，影响用户体验，建议分析各步骤进行针对性优化'
                        })
            
            # === 新增：分析详细的复制设置步骤计时 ===
            detailed_copy_stats = self.performance_stats['copy_settings_detailed']
            for step_name, times in detailed_copy_stats.items():
                if times:
                    summary['detailed_stats'][step_name] = {
                        'count': len(times),
                        'avg_ms': sum(times) / len(times),
                        'min_ms': min(times),
                        'max_ms': max(times),
                        'p95_ms': sorted(times)[int(len(times) * 0.95)] if len(times) >= 10 else max(times),
                        'last_10_avg': sum(times[-10:]) / len(times[-10:]) if len(times) >= 10 else sum(times) / len(times)
                    }
            
            # === 新增：分析按钮状态变化时序 ===
            button_timing = self.performance_stats['button_state_changes']
            
            # 计算按钮禁用/启用的时间间隔
            disable_starts = button_timing.get('disable_start_times', [])
            disable_completes = button_timing.get('disable_complete_times', [])
            enable_starts = button_timing.get('enable_start_times', [])
            enable_completes = button_timing.get('enable_complete_times', [])
            
            # 按钮禁用耗时
            if len(disable_starts) == len(disable_completes):
                disable_durations = [complete - start for start, complete in zip(disable_starts, disable_completes)]
                if disable_durations:
                    summary['button_timing_stats']['disable_duration'] = {
                        'count': len(disable_durations),
                        'avg_ms': sum(disable_durations) / len(disable_durations),
                        'max_ms': max(disable_durations)
                    }
            
            # 按钮启用耗时
            if len(enable_starts) == len(enable_completes):
                enable_durations = [complete - start for start, complete in zip(enable_starts, enable_completes)]
                if enable_durations:
                    summary['button_timing_stats']['enable_duration'] = {
                        'count': len(enable_durations),
                        'avg_ms': sum(enable_durations) / len(enable_durations),
                        'max_ms': max(enable_durations)
                    }
            
            # 完整的按钮状态周期时间（从禁用开始到启用完成）
            if len(disable_starts) > 0 and len(enable_completes) > 0:
                min_pairs = min(len(disable_starts), len(enable_completes))
                if min_pairs > 0:
                    button_cycles = [enable_completes[i] - disable_starts[i] for i in range(min_pairs)]
                    summary['button_timing_stats']['full_cycle_duration'] = {
                        'count': len(button_cycles),
                        'avg_ms': sum(button_cycles) / len(button_cycles),
                        'max_ms': max(button_cycles),
                        'min_ms': min(button_cycles)
                    }
            
            # === 性能瓶颈分析 ===
            if 'total_copy_times' in summary['detailed_stats']:
                total_stats = summary['detailed_stats']['total_copy_times']
                
                # 找出最耗时的步骤
                step_times = {}
                for step_name, stats in summary['detailed_stats'].items():
                    if step_name != 'total_copy_times':
                        step_times[step_name] = stats['avg_ms']
                
                if step_times:
                    slowest_step = max(step_times, key=step_times.get)
                    slowest_time = step_times[slowest_step]
                    
                    if slowest_time > total_stats['avg_ms'] * 0.3:  # 如果某步骤占总时间30%以上
                        summary['recommendations'].append({
                            'type': 'performance_bottleneck',
                            'bottleneck_step': slowest_step,
                            'bottleneck_time': slowest_time,
                            'total_time': total_stats['avg_ms'],
                            'percentage': (slowest_time / total_stats['avg_ms']) * 100,
                            'reason': f'"{slowest_step}" 步骤耗时占总时间的 {(slowest_time / total_stats["avg_ms"]) * 100:.1f}%，是主要性能瓶颈'
                        })
            
            # 分析UI加载性能
            if self.performance_stats['ui_load_times']:
                times = self.performance_stats['ui_load_times']
                summary['stats']['ui_load'] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times),
                    'min_ms': min(times),
                    'max_ms': max(times),
                    'p95_ms': sorted(times)[int(len(times) * 0.95)] if len(times) >= 20 else max(times)
                }
            
            # 操作统计
            summary['stats']['operations'] = self.performance_stats['operation_counts'].copy()
            
            # 成功率分析
            total_copy_attempts = (self.performance_stats['operation_counts']['settings_copy_success'] + 
                                 self.performance_stats['operation_counts']['settings_copy_fail'])
            if total_copy_attempts > 0:
                success_rate = self.performance_stats['operation_counts']['settings_copy_success'] / total_copy_attempts
                summary['stats']['settings_copy_success_rate'] = success_rate
                
                if success_rate < 0.9:  # 成功率低于90%
                    summary['recommendations'].append({
                        'type': 'settings_copy_reliability',
                        'current_success_rate': success_rate,
                        'recommended_action': '增加按钮恢复延迟',
                        'reason': f'设置复制成功率({success_rate:.1%})较低，建议增加延迟时间确保操作完整性'
                    })
            
            return summary
            
        except Exception as e:
            log_error(f"生成性能摘要失败: {e}", "PERFORMANCE")
            return {'error': str(e)}

    def show_performance_analysis(self):
        """显示性能分析结果"""
        try:
            summary = self._get_performance_summary()
            
            if 'error' in summary:
                messagebox.showerror("错误", f"性能分析失败: {summary['error']}")
                return
            
            # 创建性能分析窗口
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title("性能分析报告")
            analysis_window.geometry("800x600")
            analysis_window.transient(self.root)
            analysis_window.grab_set()
            
            # 创建滚动文本框
            text_frame = ttk.Frame(analysis_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 生成报告内容
            report = self._generate_performance_report(summary)
            text_widget.insert(tk.END, report)
            text_widget.config(state=tk.DISABLED)
            
            # 按钮框
            button_frame = ttk.Frame(analysis_window)
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            ttk.Button(button_frame, text="导出报告", 
                      command=lambda: self._export_performance_report(summary)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="清除数据", 
                      command=self._clear_performance_data).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", 
                      command=analysis_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示性能分析失败: {str(e)}")

    def _generate_performance_report(self, summary):
        """生成性能报告文本 - 包含详细计时分析"""
        import time
        
        report = []
        report.append("=" * 80)
        report.append("全景图像标注工具 - 详细性能分析报告")
        report.append("=" * 80)
        report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 当前配置
        report.append("当前延迟配置:")
        for key, value in summary['delay_config'].items():
            report.append(f"  {key}: {value}ms")
        report.append("")
        
        # 基础性能统计
        if 'settings_apply' in summary['stats']:
            stats = summary['stats']['settings_apply']
            report.append("设置应用性能统计:")
            report.append(f"  操作次数: {stats['count']}")
            report.append(f"  平均耗时: {stats['avg_ms']:.1f}ms")
            report.append(f"  最小耗时: {stats['min_ms']:.1f}ms")
            report.append(f"  最大耗时: {stats['max_ms']:.1f}ms")
            report.append(f"  95%耗时: {stats['p95_ms']:.1f}ms")
            report.append("")
        
        # === 新增：详细步骤计时分析 ===
        if 'detailed_stats' in summary and summary['detailed_stats']:
            report.append("详细步骤计时分析:")
            report.append("-" * 60)
            
            step_order = [
                'button_disable_times', 'settings_collect_times', 'navigation_times',
                'ui_refresh_times', 'settings_apply_times', 'button_enable_times', 'total_copy_times'
            ]
            
            step_names = {
                'button_disable_times': '1. 按钮禁用',
                'settings_collect_times': '2. 设置收集',  
                'navigation_times': '3. 导航跳转',
                'ui_refresh_times': '4. UI刷新准备',
                'settings_apply_times': '5. 设置应用',
                'button_enable_times': '6. 按钮启用',
                'total_copy_times': '总计复制时间'
            }
            
            for step in step_order:
                if step in summary['detailed_stats']:
                    stats = summary['detailed_stats'][step]
                    step_name = step_names.get(step, step)
                    report.append(f"  {step_name}:")
                    report.append(f"    执行次数: {stats['count']}")
                    report.append(f"    平均耗时: {stats['avg_ms']:.1f}ms")
                    report.append(f"    最小耗时: {stats['min_ms']:.1f}ms")
                    report.append(f"    最大耗时: {stats['max_ms']:.1f}ms")
                    if 'last_10_avg' in stats:
                        report.append(f"    最近10次平均: {stats['last_10_avg']:.1f}ms")
                    report.append("")
            
            # 计算步骤占比
            if 'total_copy_times' in summary['detailed_stats']:
                total_avg = summary['detailed_stats']['total_copy_times']['avg_ms']
                report.append("步骤耗时占比分析:")
                for step in step_order[:-1]:  # 排除total_copy_times
                    if step in summary['detailed_stats']:
                        step_avg = summary['detailed_stats'][step]['avg_ms']
                        percentage = (step_avg / total_avg) * 100
                        step_name = step_names.get(step, step)
                        report.append(f"  {step_name}: {percentage:.1f}%")
                report.append("")
        
        # === 新增：按钮状态变化时序分析 ===
        if 'button_timing_stats' in summary and summary['button_timing_stats']:
            report.append("按钮状态变化时序分析:")
            report.append("-" * 60)
            
            if 'disable_duration' in summary['button_timing_stats']:
                stats = summary['button_timing_stats']['disable_duration']
                report.append(f"  按钮禁用耗时:")
                report.append(f"    执行次数: {stats['count']}")
                report.append(f"    平均耗时: {stats['avg_ms']:.1f}ms")
                report.append(f"    最大耗时: {stats['max_ms']:.1f}ms")
                report.append("")
            
            if 'enable_duration' in summary['button_timing_stats']:
                stats = summary['button_timing_stats']['enable_duration']
                report.append(f"  按钮启用耗时:")
                report.append(f"    执行次数: {stats['count']}")
                report.append(f"    平均耗时: {stats['avg_ms']:.1f}ms") 
                report.append(f"    最大耗时: {stats['max_ms']:.1f}ms")
                report.append("")
            
            if 'full_cycle_duration' in summary['button_timing_stats']:
                stats = summary['button_timing_stats']['full_cycle_duration']
                report.append(f"  完整按钮状态周期(禁用→启用):")
                report.append(f"    执行次数: {stats['count']}")
                report.append(f"    平均耗时: {stats['avg_ms']:.1f}ms")
                report.append(f"    最小耗时: {stats['min_ms']:.1f}ms")
                report.append(f"    最大耗时: {stats['max_ms']:.1f}ms")
                report.append("")
        
        # UI加载性能统计
        if 'ui_load' in summary['stats']:
            stats = summary['stats']['ui_load']
            report.append("UI加载性能统计:")
            report.append(f"  加载次数: {stats['count']}")
            report.append(f"  平均耗时: {stats['avg_ms']:.1f}ms")
            report.append(f"  最小耗时: {stats['min_ms']:.1f}ms")
            report.append(f"  最大耗时: {stats['max_ms']:.1f}ms")
            report.append(f"  95%耗时: {stats['p95_ms']:.1f}ms")
            report.append("")
        
        # 操作统计
        if 'operations' in summary['stats']:
            ops = summary['stats']['operations']
            report.append("操作统计:")
            report.append(f"  保存并下一个: {ops['save_and_next']} 次")
            report.append(f"  跳过操作: {ops['skip']} 次")
            report.append(f"  清除操作: {ops['clear']} 次")
            report.append(f"  设置复制成功: {ops['settings_copy_success']} 次")
            report.append(f"  设置复制失败: {ops['settings_copy_fail']} 次")
            if 'detailed_timing_collected' in ops:
                report.append(f"  详细计时收集: {ops['detailed_timing_collected']} 次")
            
            if 'settings_copy_success_rate' in summary['stats']:
                rate = summary['stats']['settings_copy_success_rate']
                report.append(f"  设置复制成功率: {rate:.1%}")
            report.append("")
        
        # 优化建议
        if summary['recommendations']:
            report.append("优化建议:")
            report.append("-" * 40)
            for i, rec in enumerate(summary['recommendations'], 1):
                report.append(f"{i}. {rec['type'].replace('_', ' ').title()}:")
                if 'current' in rec and 'recommended' in rec:
                    report.append(f"   当前值: {rec['current']}ms")
                    report.append(f"   建议值: {rec['recommended']}ms")
                elif 'bottleneck_step' in rec:
                    report.append(f"   瓶颈步骤: {rec['bottleneck_step']}")
                    report.append(f"   瓶颈耗时: {rec['bottleneck_time']:.1f}ms")
                    report.append(f"   占比: {rec['percentage']:.1f}%")
                report.append(f"   原因: {rec['reason']}")
                report.append("")
        else:
            report.append("优化建议: 当前配置表现良好，无需调整")
            report.append("")
        
        report.append("=" * 80)
        report.append("说明:")
        report.append("1. 此报告基于实际使用数据生成，包含详细的步骤计时分析")
        report.append("2. 建议值仅供参考，请根据实际体验调整")
        report.append("3. 可在调试面板中手动调整延迟参数")
        report.append("4. 详细计时数据有助于识别性能瓶颈和优化方向")
        report.append("=" * 80)
        
        return "\n".join(report)

    def _export_performance_report(self, summary):
        """导出性能报告"""
        try:
            filename = filedialog.asksaveasfilename(
                title="导出性能报告",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filename:
                if filename.endswith('.json'):
                    import json
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(summary, f, indent=2, ensure_ascii=False)
                else:
                    report_text = self._generate_performance_report(summary)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report_text)
                
                messagebox.showinfo("成功", f"性能报告已导出: {filename}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出性能报告失败: {str(e)}")

    def _clear_performance_data(self):
        """清除性能数据"""
        if messagebox.askyesno("确认", "确定要清除所有性能数据吗？"):
            # 重置为初始状态，包含详细计时结构
            self.performance_stats = {
                'settings_apply_times': [],
                'ui_load_times': [],
                'button_response_times': [],
                
                # 详细的复制设置步骤计时
                'copy_settings_detailed': {
                    'button_disable_times': [],
                    'settings_collect_times': [],
                    'navigation_times': [],
                    'ui_refresh_times': [],
                    'settings_apply_times': [],
                    'button_enable_times': [],
                    'total_copy_times': []
                },
                
                # 按钮状态变化计时
                'button_state_changes': {
                    'disable_start_times': [],
                    'disable_complete_times': [],
                    'enable_start_times': [],
                    'enable_complete_times': []
                },
                
                'operation_counts': {
                    'save_and_next': 0,
                    'skip': 0, 
                    'clear': 0,
                    'settings_copy_success': 0,
                    'settings_copy_fail': 0,
                    'detailed_timing_collected': 0
                }
            }
            messagebox.showinfo("完成", "性能数据已清除")

    def show_delay_config_dialog(self):
        """显示延迟配置对话框"""
        try:
            # 创建配置窗口
            config_window = tk.Toplevel(self.root)
            config_window.title("延迟配置 - 标准参数调整")
            config_window.geometry("500x400")
            config_window.transient(self.root)
            config_window.grab_set()
            
            # 主框架
            main_frame = ttk.Frame(config_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 说明标签
            explanation = ttk.Label(main_frame, text="调整延迟参数来优化操作响应速度\n建议先运行性能分析获得优化建议", 
                                   font=('TkDefaultFont', 9))
            explanation.pack(pady=(0, 10))
            
            # 配置框架
            config_frame = ttk.LabelFrame(main_frame, text="延迟参数配置 (毫秒)")
            config_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 创建配置变量
            self.temp_delay_config = {}
            
            # 设置应用延迟
            settings_frame = ttk.Frame(config_frame)
            settings_frame.pack(fill=tk.X, padx=5, pady=3)
            ttk.Label(settings_frame, text="设置应用延迟:", width=15).pack(side=tk.LEFT)
            self.temp_delay_config['settings_apply'] = tk.IntVar(value=self.delay_config['settings_apply'])
            settings_spin = ttk.Spinbox(settings_frame, from_=50, to=500, width=8,
                                       textvariable=self.temp_delay_config['settings_apply'])
            settings_spin.pack(side=tk.LEFT, padx=5)
            ttk.Label(settings_frame, text="(50-500ms, 当前安全值: 250ms)", 
                     font=('TkDefaultFont', 8), foreground='gray').pack(side=tk.LEFT, padx=5)
            
            # 按钮恢复延迟
            recovery_frame = ttk.Frame(config_frame)
            recovery_frame.pack(fill=tk.X, padx=5, pady=3)
            ttk.Label(recovery_frame, text="按钮恢复延迟:", width=15).pack(side=tk.LEFT)
            self.temp_delay_config['button_recovery'] = tk.IntVar(value=self.delay_config['button_recovery'])
            recovery_spin = ttk.Spinbox(recovery_frame, from_=200, to=800, width=8,
                                       textvariable=self.temp_delay_config['button_recovery'])
            recovery_spin.pack(side=tk.LEFT, padx=5)
            ttk.Label(recovery_frame, text="(200-800ms, 当前标准值: 300ms)", 
                     font=('TkDefaultFont', 8), foreground='gray').pack(side=tk.LEFT, padx=5)
            
            # 快速恢复延迟
            quick_frame = ttk.Frame(config_frame)
            quick_frame.pack(fill=tk.X, padx=5, pady=3)
            ttk.Label(quick_frame, text="快速恢复延迟:", width=15).pack(side=tk.LEFT)
            self.temp_delay_config['quick_recovery'] = tk.IntVar(value=self.delay_config['quick_recovery'])
            quick_spin = ttk.Spinbox(quick_frame, from_=100, to=400, width=8,
                                    textvariable=self.temp_delay_config['quick_recovery'])
            quick_spin.pack(side=tk.LEFT, padx=5)
            ttk.Label(quick_frame, text="(100-400ms, 当前标准值: 200ms)", 
                     font=('TkDefaultFont', 8), foreground='gray').pack(side=tk.LEFT, padx=5)
            
            # 预设配置
            preset_frame = ttk.LabelFrame(main_frame, text="预设配置")
            preset_frame.pack(fill=tk.X, pady=(0, 10))
            
            preset_buttons_frame = ttk.Frame(preset_frame)
            preset_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
            
            def apply_high_performance():
                # 基于代码优化后的实际性能数据（设置应用最大耗时5.7ms）
                self.temp_delay_config['settings_apply'].set(50)
                self.temp_delay_config['button_recovery'].set(150)
                self.temp_delay_config['quick_recovery'].set(100)
            
            def apply_standard_performance():
                # 保守配置，适合普通使用场景
                self.temp_delay_config['settings_apply'].set(150)
                self.temp_delay_config['button_recovery'].set(250)
                self.temp_delay_config['quick_recovery'].set(150)
            
            def apply_safe_performance():
                # 高安全性配置，适合不稳定环境
                self.temp_delay_config['settings_apply'].set(300)
                self.temp_delay_config['button_recovery'].set(400)
                self.temp_delay_config['quick_recovery'].set(250)
            
            ttk.Button(preset_buttons_frame, text="高性能", 
                      command=apply_high_performance).pack(side=tk.LEFT, padx=5)
            ttk.Button(preset_buttons_frame, text="标准", 
                      command=apply_standard_performance).pack(side=tk.LEFT, padx=5)
            ttk.Button(preset_buttons_frame, text="安全", 
                      command=apply_safe_performance).pack(side=tk.LEFT, padx=5)
            
            # 说明文本
            help_text = """
配置说明:
• 设置应用延迟: 控制"保存并下一个"时设置复制的等待时间
• 按钮恢复延迟: 控制操作完成后按钮重新可点击的时间
• 快速恢复延迟: 控制跳过、清除等快速操作的按钮恢复时间

预设配置 (基于最新性能分析调整):
• 高性能: 100/250/150ms - 适合稳定环境
• 标准: 250/300/200ms - 安全可靠配置 (推荐)
• 安全: 300/400/250ms - 最大兼容性配置

注意: 最新测试显示95%设置应用耗时达228ms，建议使用标准或安全配置
            """
            
            help_label = tk.Text(main_frame, height=10, width=60, wrap=tk.WORD,
                                font=('TkDefaultFont', 8))
            help_label.pack(fill=tk.BOTH, expand=True)
            help_label.insert(tk.END, help_text.strip())
            help_label.config(state=tk.DISABLED)
            
            # 按钮框
            button_frame = ttk.Frame(config_window)
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            def apply_config():
                # 应用新配置
                self.delay_config['settings_apply'] = self.temp_delay_config['settings_apply'].get()
                self.delay_config['button_recovery'] = self.temp_delay_config['button_recovery'].get() 
                self.delay_config['quick_recovery'] = self.temp_delay_config['quick_recovery'].get()
                
                log_info(f"延迟配置已更新: 设置应用={self.delay_config['settings_apply']}ms, "
                        f"按钮恢复={self.delay_config['button_recovery']}ms, "
                        f"快速恢复={self.delay_config['quick_recovery']}ms", "CONFIG")
                
                messagebox.showinfo("完成", "延迟配置已更新")
                config_window.destroy()
            
            def reset_config():
                # 重置为标准配置
                apply_standard_performance()
                
            ttk.Button(button_frame, text="应用", command=apply_config).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="重置为标准", command=reset_config).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=config_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示延迟配置对话框失败: {str(e)}")
    
    def show_start_position_dialog(self):
        """显示起始点位置调整对话框"""
        try:
            # 检查是否已加载全景图
            if not hasattr(self, 'hole_manager') or not self.hole_manager:
                messagebox.showwarning("提示", "请先加载全景图数据")
                return
            
            # 创建调整窗口
            position_window = tk.Toplevel(self.root)
            position_window.title("起始点位置调整")
            position_window.geometry("350x250")
            position_window.transient(self.root)
            position_window.grab_set()
            
            # 窗口居中显示
            position_window.update_idletasks()
            width = position_window.winfo_width()
            height = position_window.winfo_height()
            x = (position_window.winfo_screenwidth() // 2) - (width // 2)
            y = (position_window.winfo_screenheight() // 2) - (height // 2)
            position_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # 主框架
            main_frame = ttk.Frame(position_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 当前值显示
            current_frame = ttk.LabelFrame(main_frame, text="当前起始位置", padding=10)
            current_frame.pack(fill=tk.X, pady=(0, 15))
            
            current_x = getattr(self.hole_manager, 'first_hole_x', 0)
            current_y = getattr(self.hole_manager, 'first_hole_y', 0)
            
            current_display = ttk.Frame(current_frame)
            current_display.pack(fill=tk.X)
            ttk.Label(current_display, text=f"X: {current_x}").pack(side=tk.LEFT)
            ttk.Label(current_display, text=f"Y: {current_y}").pack(side=tk.LEFT, padx=(20, 0))
            
            # 调整框架
            adjust_frame = ttk.LabelFrame(main_frame, text="新的起始位置", padding=10)
            adjust_frame.pack(fill=tk.X, pady=(0, 15))
            
            # X和Y坐标输入在一行
            coord_frame = ttk.Frame(adjust_frame)
            coord_frame.pack(fill=tk.X)
            
            ttk.Label(coord_frame, text="X坐标:").pack(side=tk.LEFT)
            x_var = tk.StringVar(value=str(current_x))
            x_entry = ttk.Entry(coord_frame, textvariable=x_var, width=8)
            x_entry.pack(side=tk.LEFT, padx=(5, 15))
            
            ttk.Label(coord_frame, text="Y坐标:").pack(side=tk.LEFT)
            y_var = tk.StringVar(value=str(current_y))
            y_entry = ttk.Entry(coord_frame, textvariable=y_var, width=8)
            y_entry.pack(side=tk.LEFT, padx=(5, 0))
            
            # 按钮框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(15, 0))
            
            def apply_position():
                try:
                    # 获取新的坐标值
                    new_x = int(x_var.get())
                    new_y = int(y_var.get())
                    
                    # 更新hole_manager的起始位置
                    self.hole_manager.update_positioning_params(
                        first_hole_x=new_x,
                        first_hole_y=new_y
                    )
                    
                    # 标记用户已手动设置起始坐标
                    self.user_custom_start_coordinates = True
                    
                    log_info(f"起始坐标已更新: X={new_x}, Y={new_y} (用户自定义)", "POSITION")
                    
                    # 如果当前有显示的切片，刷新显示
                    if hasattr(self, 'current_hole_info') and self.current_hole_info:
                        self.load_current_slice()
                    
                    messagebox.showinfo("完成", f"起始点位置已更新为: X={new_x}, Y={new_y}")
                    position_window.destroy()
                    
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字坐标")
                except Exception as e:
                    messagebox.showerror("错误", f"更新起始点位置失败: {str(e)}")
            
            def reset_position():
                # 重置为默认值或当前值
                x_var.set(str(current_x))
                y_var.set(str(current_y))
            
            ttk.Button(button_frame, text="应用", command=apply_position).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="重置", command=reset_position).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=position_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示起始点调整对话框失败: {str(e)}")

    def should_copy_settings(self, current_settings, next_hole_info):
        """
        判断是否应该复制设置
        条件1: 下一个切片未标注过
        条件2: 当前切片的生长级别与下一个切片的CFG配置生长级别一致
        """
        if not current_settings or not next_hole_info:
            return False

        # 只有人工视图才允许复制设置
        if self.current_view_mode != ViewMode.MANUAL:
            log_debug(f"当前视图模式为{self.current_view_mode.value}，不复制设置", "COPY")
            return False

        # 条件1: 检查下一个切片是否已经标注过
        next_hole_number = next_hole_info['hole_number']
        next_panoramic_id = next_hole_info.get('panoramic_id')
        
        if self.is_hole_annotated(next_hole_number, next_panoramic_id):
            log_debug(f"下一个孔位{next_hole_number}已标注过，不复制设置以避免覆盖", "COPY")
            return False

        # 条件2: 检查生长级别是否一致
        config_growth_level = self.get_config_growth_level(next_hole_number)
        if not config_growth_level:
            log_debug(f"下一个孔位{next_hole_number}无CFG配置，不复制设置", "COPY")
            return False

        # 规范化当前生长级别（处理枚举和字符串）
        current_growth_level = current_settings['growth_level']
        if hasattr(current_growth_level, 'value'):
            current_growth_level = current_growth_level.value

        if config_growth_level != current_growth_level:
            log_debug(f"生长级别不同：当前={current_growth_level}, CFG={config_growth_level}，不复制设置", "COPY")
            return False

        log_debug(f"满足复制条件: 孔位{next_hole_number}未标注且生长级别相同({config_growth_level})，允许复制设置", "COPY")
        return True

    def is_hole_annotated(self, hole_number, panoramic_id=None):
        """检查指定孔位是否已经标注过"""
        try:
            # 使用当前全景图ID（如果未提供）
            if not panoramic_id:
                panoramic_id = self.current_panoramic_id
            
            if not panoramic_id:
                return False

            # 检查数据集中是否存在该孔位的标注
            if hasattr(self, 'dataset') and self.dataset:
                for annotation in self.dataset.annotations:
                    if (annotation.panoramic_id == panoramic_id and 
                        annotation.hole_number == hole_number):
                        # 检查是否有实际的标注内容（不是默认值）
                        has_annotation = (
                            getattr(annotation, 'microbe_type', None) or 
                            getattr(annotation, 'growth_level', None) or 
                            getattr(annotation, 'growth_pattern', None) or 
                            getattr(annotation, 'interference_factors', None) or
                            getattr(annotation, 'confidence', 0) > 0
                        )
                        if has_annotation:
                            log_debug(f"孔位{hole_number}已有标注: {annotation.growth_level}", "COPY")
                            return True

            # 检查增强标注
            if hasattr(self, 'enhanced_annotations') and self.enhanced_annotations:
                annotation_key = f"{panoramic_id}_{hole_number}"
                if annotation_key in self.enhanced_annotations:
                    enhanced_annotation = self.enhanced_annotations[annotation_key]
                    # 检查是否有实际的增强标注内容
                    has_enhanced_annotation = (
                        enhanced_annotation.growth_level or 
                        enhanced_annotation.growth_pattern or 
                        enhanced_annotation.interference_factors or
                        enhanced_annotation.confidence > 0
                    )
                    if has_enhanced_annotation:
                        log_debug(f"孔位{hole_number}已有增强标注", "COPY")
                        return True

            log_debug(f"孔位{hole_number}未标注过", "COPY")
            return False

        except Exception as e:
            log_error(f"检查孔位{hole_number}标注状态失败: {e}", "COPY")
            return True  # 安全起见，如果检查失败则认为已标注，避免覆盖
    
    def _disable_annotation_controls(self):
        """禁用标注相关控件"""
        if self.save_button:
            self.save_button.config(state='disabled', text="保存中...")
        if self.skip_button:
            self.skip_button.config(state='disabled')
        if self.clear_button:
            self.clear_button.config(state='disabled')
        
        # 也可以禁用导航按钮，避免用户在保存过程中切换
        try:
            # 查找导航按钮并禁用（如果存在）
            navigation_buttons = []
            # 在导航面板中查找按钮
            for widget in self.root.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'winfo_children'):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Button):
                                    button_text = grandchild.cget('text')
                                    if button_text in ['◀', '▶', '◀◀', '▶▶']:
                                        navigation_buttons.append(grandchild)
            
            for btn in navigation_buttons:
                btn.config(state='disabled')
                
        except Exception as e:
            log_debug(f"禁用导航按钮时出错: {e}", "BUTTON_STATE")

    def _enable_annotation_controls(self):
        """恢复标注相关控件"""
        self.is_saving = False
        if self.save_button:
            self.save_button.config(state='normal', text="保存并下一个")
        if self.skip_button:
            self.skip_button.config(state='normal')
        if self.clear_button:
            self.clear_button.config(state='normal')
        
        # 恢复导航按钮
        try:
            navigation_buttons = []
            # 在导航面板中查找按钮
            for widget in self.root.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'winfo_children'):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Button):
                                    button_text = grandchild.cget('text')
                                    if button_text in ['◀', '▶', '◀◀', '▶▶']:
                                        navigation_buttons.append(grandchild)
            
            for btn in navigation_buttons:
                btn.config(state='normal')
                
        except Exception as e:
            log_debug(f"恢复导航按钮时出错: {e}", "BUTTON_STATE")
    
    def save_current_annotation(self):
        """保存当前标注并跳转到下一个 - 智能设置继承策略"""
        # 防重复点击保护
        if self.is_saving:
            log_debug("保存操作正在进行中，忽略重复点击", "SAVE")
            return
        
        # 智能设置继承开始执行
        
        # 记录操作开始时间 (用于性能监控)
        import time
        operation_start_time = time.time()
        
        # === 步骤1: 禁用按钮和控件 ===
        button_disable_start = time.time()
        self._record_button_state_timing('disable_start_times', button_disable_start * 1000)
        
        # 设置保存状态
        self.is_saving = True
        self._disable_annotation_controls()
        
        button_disable_time = (time.time() - button_disable_start) * 1000
        self._record_detailed_copy_timing('button_disable_times', button_disable_time)
        self._record_button_state_timing('disable_complete_times', time.time() * 1000)
        
        # 记录操作计数
        self._record_performance_data('save_and_next', 0)
        
        try:
            log_debug(f"用户点击保存并下一个 - 开始智能设置继承", "SAVE")
            
            # === 步骤2: 收集当前设置信息 ===
            settings_collect_start = time.time()
            
            # 记录当前视图模式
            original_view_mode = self.current_view_mode
            log_debug(f"保存前视图模式: {original_view_mode.value}", "SAVE")

            # 获取当前标注设置（作为下一个孔位的潜在设置）
            current_settings = self.get_current_annotation_settings()
            
            # 获取下一个孔位信息
            next_hole_info = self.get_next_hole_info()
            
            settings_collect_time = (time.time() - settings_collect_start) * 1000
            self._record_detailed_copy_timing('settings_collect_times', settings_collect_time)
            log_timing(f"设置收集完成，耗时: {settings_collect_time:.1f}ms")

            internal_result = self.save_current_annotation_internal("manual")
            
            if internal_result:
                # === 步骤3: 导航跳转 ===
                navigation_start = time.time()
                self.go_next_hole()
                navigation_time = (time.time() - navigation_start) * 1000
                self._record_detailed_copy_timing('navigation_times', navigation_time)
                self._record_performance_data('ui_load', navigation_time)
                log_timing(f"导航跳转完成，耗时: {navigation_time:.1f}ms")

                # === 步骤4: 智能设置继承策略 ===
                if current_settings and next_hole_info:
                    def apply_smart_settings():
                        # === 步骤4.1: UI刷新准备 ===
                        ui_refresh_start = time.time()
                        self.root.update_idletasks()
                        ui_refresh_time = (time.time() - ui_refresh_start) * 1000
                        self._record_detailed_copy_timing('ui_refresh_times', ui_refresh_time)
                        
                        # === 步骤4.2: 智能设置应用 ===
                        settings_apply_start = time.time()
                        
                        success, strategy = self._apply_smart_inheritance_strategy(
                            current_settings, next_hole_info, original_view_mode
                        )
                        
                        settings_apply_time = (time.time() - settings_apply_start) * 1000
                        self._record_detailed_copy_timing('settings_apply_times', settings_apply_time)
                        self._record_performance_data('settings_apply', settings_apply_time, success=success)
                        
                        # === 步骤4.3: 启用按钮 ===
                        button_enable_start = time.time()
                        self._record_button_state_timing('enable_start_times', button_enable_start * 1000)
                        self._enable_annotation_controls()
                        button_enable_time = (time.time() - button_enable_start) * 1000
                        self._record_detailed_copy_timing('button_enable_times', button_enable_time)
                        self._record_button_state_timing('enable_complete_times', time.time() * 1000)
                        
                        # === 记录总时间 ===
                        total_copy_time = (time.time() - operation_start_time) * 1000
                        self._record_detailed_copy_timing('total_copy_times', total_copy_time)
                        self.performance_stats['operation_counts']['detailed_timing_collected'] += 1
                        
                        # 根据策略显示状态消息
                        strategy_messages = {
                            "keep_current": f"保持当前设置到孔位{self.current_hole_number}",
                            "apply_existing": f"应用已有标注到孔位{self.current_hole_number}",
                            "apply_cfg": f"应用CFG配置到孔位{self.current_hole_number}",
                            "apply_model": f"应用模型预测到孔位{self.current_hole_number}",
                            "reset_default": f"重置为默认设置到孔位{self.current_hole_number}"
                        }
                        
                        status_msg = f"已保存标注并{strategy_messages.get(strategy, '更新设置')}"
                        if original_view_mode != ViewMode.MANUAL:
                            status_msg += f" (保持{original_view_mode.value}视图)"
                        self.update_status(status_msg)

                    # 使用优化的延迟时间和智能调度策略
                    delay_time = self.delay_config['settings_apply']
                    log_debug(f"使用延迟时间: {delay_time}ms", "PERFORMANCE")
                    
                    # 智能调度策略：当延迟很短时直接调用，避免GUI事件队列阻塞
                    if delay_time <= 10:
                        apply_smart_settings()
                    else:
                        self.root.after(delay_time, apply_smart_settings)
                else:
                    # 无设置信息，直接启用控件
                    self._enable_annotation_controls()
                    current_file = self.slice_files[self.current_slice_index - 1] if self.current_slice_index > 0 else self.slice_files[self.current_slice_index]
                    self.update_status(f"已保存标注: {current_file['filename']}")

                # 确保视图模式保持不变
                if self.current_view_mode != original_view_mode:
                    log_debug(f"恢复视图模式从 {self.current_view_mode.value} 到 {original_view_mode.value}", "SAVE")
                    self.set_view_mode(original_view_mode)

        except Exception as e:
            import traceback
            error_msg = f"保存标注失败: {str(e)}"
            # 记录详细错误信息到日志
            log_error(f"{error_msg}\n{traceback.format_exc()}")
            # 同时显示简化的用户友好错误消息
            messagebox.showerror("错误", error_msg)
            self._enable_annotation_controls()  # 确保在错误时恢复按钮状态
        finally:
            # 记录总操作时间（非复制设置的情况）
            if not hasattr(self, '_detailed_timing_recorded'):
                total_operation_time = (time.time() - operation_start_time) * 1000
                self._record_performance_data('button_response', total_operation_time)
            
            # 无论成功失败，都要恢复按钮状态
            # 使用标准配置的恢复延迟时间
            recovery_delay = self.delay_config['button_recovery']
            log_debug(f"使用标准配置按钮恢复延迟: {recovery_delay}ms", "PERFORMANCE")
            self.root.after(recovery_delay, self._enable_annotation_controls)
    
    def _apply_smart_inheritance_strategy(self, current_settings, next_hole_info, view_mode):
        """智能设置继承策略 - 根据不同情况和视图模式选择最优策略
        
        策略优先级：
        0. 模型视图：优先使用模型预测（如果可用）
        1. 用户手动标注：保持不变（最高优先级）
        2. CFG配置：根据生长级别匹配情况决定复制设置还是应用CFG
        3. 无配置：复制当前设置（手动视图）或重置为默认（其他情况）
        """
        try:
            next_hole_number = next_hole_info['hole_number']
            next_panoramic_id = next_hole_info.get('panoramic_id')
            
            log_debug(f"开始智能设置继承 - 目标孔位{next_hole_number}，视图模式: {view_mode.value}", "SMART_INHERIT")
            
            # 策略0: 模型视图优先处理 - 优先显示模型预测
            if view_mode == ViewMode.MODEL:
                if hasattr(self, 'hole_manager') and self.hole_manager:
                    if self.hole_manager.has_hole_suggestion(next_hole_number):
                        self._load_model_view_data()
                        return True, "apply_model"
            
            # 策略1: 用户手动标注保护（仅人工视图）
            
            # 只在人工视图下保护手动标注
            if view_mode == ViewMode.MANUAL:
                existing_annotation = self.current_dataset.get_annotation_by_hole(
                    next_panoramic_id or self.current_panoramic_id, 
                    next_hole_number
                )
                
                # 检查是否为用户手动标注（只对用户手动标注保持不变）
                if existing_annotation and hasattr(existing_annotation, 'annotation_source'):
                    is_manual_annotation = existing_annotation.annotation_source in ['enhanced_manual', 'manual']
                    
                    if is_manual_annotation:
                        self._apply_existing_annotation(existing_annotation)
                        return True, "apply_existing"
            
            # 策略2: 检查是否有CFG配置
            config_growth_level = self.get_config_growth_level(next_hole_number)
            current_growth_level = current_settings['growth_level']
            if hasattr(current_growth_level, 'value'):
                current_growth_level = current_growth_level.value
            
            log_debug(f"智能设置继承 - 孔位{next_hole_number}: CFG生长级别='{config_growth_level}', 当前生长级别='{current_growth_level}'", "SMART_INHERIT")
            
            if config_growth_level:
                # 有CFG配置，比较生长级别
                if config_growth_level == current_growth_level:
                    # 生长级别匹配，复制当前设置
                    if self.apply_annotation_settings_sync(current_settings):
                        return True, "keep_current"
                    else:
                        log_debug_detail(f"复制当前设置失败，降级到CFG配置")
                        self._apply_cfg_based_settings(next_hole_number, config_growth_level)
                        return True, "apply_cfg"
                else:
                    # 生长级别不匹配，直接应用CFG配置
                    log_debug_detail(f"应用CFG配置到孔位{next_hole_number}")
                    self._apply_cfg_based_settings(next_hole_number, config_growth_level)
                    return True, "apply_cfg"
            else:
                # 策略3: 无CFG配置，这是大部分连续孔位的情况，复制当前设置
                if self.apply_annotation_settings_sync(current_settings):
                    log_debug_detail(f"策略3: 成功复制当前设置")
                    return True, "keep_current"
                else:
                    log_debug(f"复制当前设置失败，重置为默认设置", "SMART_INHERIT")
                    # 复制失败，重置为默认设置
                    self._apply_default_settings(next_hole_number)
                    return True, "reset_default"
                
        except Exception as e:
            log_error(f"智能设置继承失败: {e}", "SMART_INHERIT")
            return False, "error"

    def _apply_cfg_based_settings(self, hole_number, cfg_growth_level):
        """根据CFG配置应用设置"""
        try:
            log_debug(f"应用CFG设置 - 孔位{hole_number}, 生长级别{cfg_growth_level}", "CFG_APPLY")
            
            # 根据全景图文件名设置默认微生物类型
            default_microbe_type = self.get_default_microbe_type(self.current_panoramic_id)
            
            # 设置基本属性
            self.current_microbe_type.set(default_microbe_type)
            
            # 应用到增强标注面板
            if self.enhanced_annotation_panel:
                # 设置生长级别
                self.enhanced_annotation_panel.current_growth_level.set(cfg_growth_level)
                
                # 更新生长模式选项
                self.enhanced_annotation_panel.update_pattern_options()
                
                # 重置干扰因素
                panel_factors = self.enhanced_annotation_panel.interference_vars
                for var in panel_factors.values():
                    var.set(False)
                
                # 获取可用的生长模式选项（直接从面板逻辑复制）
                microbe_type = default_microbe_type
                pattern_options = {
                    "negative": ["clean"],
                    "weak_growth": ["default_weak_growth", "small_dots", "light_gray", "irregular_areas"],
                    "positive": (["default_positive", "clustered", "scattered", "heavy_growth"] if microbe_type == "bacteria"
                                else ["default_positive", "focal", "diffuse", "heavy_growth"])
                }
                
                available_patterns = pattern_options.get(cfg_growth_level, [])
                if available_patterns:
                    # 设置为第一个可用的模式
                    self.enhanced_annotation_panel.current_growth_pattern.set(available_patterns[0])
                else:
                    # 如果没有可用模式，清空设置
                    self.enhanced_annotation_panel.current_growth_pattern.set("")
                
                # 设置默认置信度
                self.enhanced_annotation_panel.current_confidence.set(1.0)
                
                # 轻量级UI刷新
                self.root.update_idletasks()
                
                log_debug(f"CFG设置应用完成: {default_microbe_type}, {cfg_growth_level}", "CFG_APPLY")
            
        except Exception as e:
            log_error(f"应用CFG设置失败: {e}", "CFG_APPLY")

    def _apply_default_settings(self, hole_number):
        """应用默认设置"""
        try:
            log_debug(f"应用默认设置 - 孔位{hole_number}", "DEFAULT_APPLY")
            
            # 根据全景图文件名设置默认微生物类型
            default_microbe_type = self.get_default_microbe_type(self.current_panoramic_id)
            
            # 设置基本属性
            self.current_microbe_type.set(default_microbe_type)
            
            # 应用到增强标注面板
            if self.enhanced_annotation_panel:
                # 重置为阴性
                self.enhanced_annotation_panel.current_growth_level.set('negative')
                
                # 更新生长模式选项
                self.enhanced_annotation_panel.update_pattern_options()
                
                # 重置干扰因素
                panel_factors = self.enhanced_annotation_panel.interference_vars
                for var in panel_factors.values():
                    var.set(False)
                
                # 设置阴性默认模式
                # 对于阴性，默认使用 "clean" 模式
                self.enhanced_annotation_panel.current_growth_pattern.set("clean")
                
                # 设置默认置信度
                self.enhanced_annotation_panel.current_confidence.set(1.0)
                
                # 轻量级UI刷新
                self.root.update_idletasks()
                
                log_debug(f"默认设置应用完成: {default_microbe_type}, negative", "DEFAULT_APPLY")
            
        except Exception as e:
            log_error(f"应用默认设置失败: {e}", "DEFAULT_APPLY")

    def get_config_growth_level(self, hole_number):
        """获取指定孔位的CFG配置生长级别"""
        try:
            if not hasattr(self, 'current_panoramic_id') or not self.current_panoramic_id:
                log_debug(f"get_config_growth_level: 没有current_panoramic_id", "CFG")
                return None
            
            # 获取当前全景图的配置数据
            config_data = self.get_current_panoramic_config()
            log_debug(f"get_config_growth_level: 孔位{hole_number}, 配置数据数量={len(config_data) if config_data else 0}", "CFG")
            
            if not config_data or hole_number not in config_data:
                log_debug(f"get_config_growth_level: 孔位{hole_number}没有CFG配置", "CFG")
                return None
            
            # 解析标注字符串获取生长级别
            annotation_str = config_data[hole_number]
            log_debug(f"get_config_growth_level: 孔位{hole_number}原始CFG字符串='{annotation_str}'", "CFG")
            
            parsed_annotation = self._parse_annotation_string(annotation_str, self.current_panoramic_id)
            growth_level = parsed_annotation.get('growth_level', None)
            
            log_debug(f"get_config_growth_level: 孔位{hole_number}解析后生长级别='{growth_level}'", "CFG")
            return growth_level
            
        except Exception as e:
            log_error(f"获取CFG生长级别失败: {e}", "CFG")
            return None

    def get_cfg_display_text(self):
        """获取CFG配置的显示文本，用于切片信息展示
        
        Returns:
            str: CFG配置的显示文本，格式为"细菌|阳性"或"真菌|阴性"，如无配置则返回空字符串
        """
        try:
            if not hasattr(self, 'current_panoramic_id') or not self.current_panoramic_id:
                return ""
            
            if not hasattr(self, 'current_hole_number') or not self.current_hole_number:
                return ""
            
            # 获取当前全景图的配置数据
            config_data = self.get_current_panoramic_config()
            if not config_data or self.current_hole_number not in config_data:
                return ""
            
            # 解析标注字符串获取详细信息
            annotation_str = config_data[self.current_hole_number]
            parsed_annotation = self._parse_annotation_string(annotation_str, self.current_panoramic_id)
            
            # 获取微生物类型和生长级别
            microbe_type = parsed_annotation.get('microbe_type', 'bacteria')
            growth_level = parsed_annotation.get('growth_level', 'negative')
            
            # 转换为中文显示
            microbe_text = "细菌" if microbe_type == "bacteria" else "真菌"
            if growth_level == "positive":
                level_text = "阳性"
            elif growth_level == "negative":
                level_text = "阴性"
            else:
                level_text = growth_level  # 其他情况直接显示原值
            
            return f"{microbe_text}|{level_text}"
            
        except Exception as e:
            log_debug(f"获取CFG显示文本失败: {e}", "CFG")
            return ""
    
    def skip_current(self):
        """跳过当前切片 - 带性能监控"""
        if self.is_saving:
            log_debug("保存操作正在进行中，忽略跳过操作", "SKIP")
            return
        
        # 记录操作开始时间
        import time
        operation_start_time = time.time()
        
        self.is_saving = True
        self._disable_annotation_controls()
        
        # 记录操作计数
        self._record_performance_data('skip', 0)
        
        try:
            ui_load_start = time.time()
            self.go_next_hole()
            ui_load_time = (time.time() - ui_load_start) * 1000
            self._record_performance_data('ui_load', ui_load_time)
            
            self.update_status("已跳过当前切片")
        finally:
            # 记录总操作时间
            total_operation_time = (time.time() - operation_start_time) * 1000
            self._record_performance_data('button_response', total_operation_time)
            
            # 使用标准配置的快速恢复延迟
            recovery_delay = self.delay_config['quick_recovery']
            self.root.after(recovery_delay, self._enable_annotation_controls)
    
    def clear_current_annotation(self):
        """清除当前标注 - 带性能监控"""
        if self.is_saving:
            log_debug("保存操作正在进行中，忽略清除操作", "CLEAR")
            return
        
        # 记录操作开始时间
        import time
        operation_start_time = time.time()
        
        self.is_saving = True
        self._disable_annotation_controls()
        
        # 记录操作计数
        self._record_performance_data('clear', 0)
        
        try:
            existing_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id, 
                self.current_hole_number
            )
            if existing_ann:
                self.current_dataset.annotations.remove(existing_ann)
                self.update_statistics()
                self.update_status("已清除当前标注")
                
                # 更新切片预览区域的标注指示器
                canvas_width = self.slice_canvas.winfo_width() or 150
                canvas_height = self.slice_canvas.winfo_height() or 150
                self.draw_slice_annotation_indicator(canvas_width, canvas_height)
            
            # 重置界面状态
            self.current_growth_level.set("negative")
            for var in self.interference_factors.values():
                var.set(False)
                
            # 重置增强标注面板
            if self.enhanced_annotation_panel:
                self.enhanced_annotation_panel.reset_annotation()
                
        finally:
            # 记录总操作时间
            total_operation_time = (time.time() - operation_start_time) * 1000
            self._record_performance_data('button_response', total_operation_time)
            
            # 使用标准配置的快速恢复延迟
            recovery_delay = self.delay_config['quick_recovery']
            self.root.after(recovery_delay, self._enable_annotation_controls)
    
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
                self.save_current_annotation_internal("auto")
                self.update_status("自动保存完成")
            except Exception as e:
                log_error(f"自动保存失败: {e}", "AUTO_SAVE")
    
    def save_current_annotation_internal(self, save_type="manual"):
        """内部保存方法，不自动跳转
        save_type: "manual" (用户手动保存), "auto" (自动保存), "navigation" (导航时保存)
        """
        log_debug(f"进入 save_current_annotation_internal 方法，类型: {save_type}", "SAVE")
        
        # 检查基本条件
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            log_debug(f"早期退出: 没有切片文件或索引超出范围", "SAVE")
            return False  # 明确返回False而不是None

        # 记录保存前的状态用于对比
        pre_save_state = self._capture_annotation_state()

        try:
            current_file = self.slice_files[self.current_slice_index]
            
            # 使用增强标注模式 - 唯一的标注方式
            log_debug(f"检查增强标注面板: hasattr={hasattr(self, 'enhanced_annotation_panel')}, not None={getattr(self, 'enhanced_annotation_panel', None) is not None}", "SAVE")
            if hasattr(self, 'enhanced_annotation_panel') and self.enhanced_annotation_panel:
                try:
                    feature_combination = self.enhanced_annotation_panel.get_current_feature_combination()
                    log_debug(f"准备保存增强标注: {feature_combination.growth_level} [{feature_combination.confidence:.2f}]", "SAVE")
                except Exception as e:
                    log_error(f"获取特征组合失败: {e}")
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
                log_debug(f"训练标签: {training_label}", "SAVE")
                
                # 创建兼容的PanoramicAnnotation对象用于显示
                # 人工标注时置信度默认为1.0
                annotation = PanoramicAnnotation.from_filename(
                    current_file['filename'],
                    label=training_label,
                    bbox=[0, 0, 70, 70],
                    confidence=1.0,  # 人工标注置信度默认为1.0
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
                    log_debug(f"enhanced_annotation.to_dict() 成功: {len(str(enhanced_data_dict))} 字符", "SAVE")
                    annotation.enhanced_data = enhanced_data_dict
                    log_debug(f"enhanced_data 赋值成功", "SAVE")
                except Exception as e:
                    log_error(f"enhanced_data 赋值失败: {e}")
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
                    log_debug(f"设置growth_pattern: {annotation.growth_pattern}", "SAVE")
                
                log_debug(f"保存增强数据完成", "SAVE")
                
                # 验证enhanced_data是否正确设置
                if hasattr(annotation, 'enhanced_data') and annotation.enhanced_data:
                    log_debug(f"✓ enhanced_data设置成功", "SAVE")
                    if 'feature_combination' in annotation.enhanced_data:
                        fc_data = annotation.enhanced_data['feature_combination']
                    else:
                        log_debug(f"❌ enhanced_data设置失败或为空", "SAVE")
                    
            else:
                # 基础标注模式（向后兼容）
                log_debug(f"使用基础标注模式（无增强面板）", "SAVE")
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
            log_debug(f"记录标注时间: {annotation_key} -> {current_time.strftime('%m-%d %H:%M:%S')}", "SAVE")
            
            # 更新显示（不重新加载全景图，因为图像没有改变）
            self.update_statistics()
            self.update_slice_info_display()
            
            # 更新切片预览区域的标注指示器
            canvas_width = self.slice_canvas.winfo_width() or 150
            canvas_height = self.slice_canvas.winfo_height() or 150
            self.draw_slice_annotation_indicator(canvas_width, canvas_height)
            
            self.root.update_idletasks()
            self.root.update()
            
            # 验证标注是否正确保存
            saved_ann = self.current_dataset.get_annotation_by_hole(self.current_panoramic_id, self.current_hole_number)
            if saved_ann:
                if hasattr(saved_ann, 'enhanced_data') and saved_ann.enhanced_data:
                    if 'feature_combination' in saved_ann.enhanced_data:
                        fc = saved_ann.enhanced_data['feature_combination']
                    else:
                        log_debug(f"saved_ann缺少feature_combination", "SAVE")
                else:
                    log_debug(f"saved_ann无enhanced_data", "SAVE")
            log_debug("保存后更新完成", "SAVE")

            # 记录保存后的状态并生成详细日志
            post_save_state = self._capture_annotation_state()
            if pre_save_state and post_save_state:
                self._log_annotation_change(pre_save_state, post_save_state, save_type)

            # 重置修改标记
            self.current_annotation_modified = False

            # 记录标注保存的关键操作信息（仅手动保存显示INFO级别）
            if save_type == "manual":
                try:
                    # 获取详细的标注信息
                    feature_combination = self.enhanced_annotation_panel.get_current_feature_combination()

                    # 构建详细信息字符串
                    details_parts = []

                    # 生长级别
                    if hasattr(feature_combination, 'growth_level') and feature_combination.growth_level:
                        details_parts.append(feature_combination.growth_level)

                    # 生长模式
                    if hasattr(feature_combination, 'growth_pattern') and feature_combination.growth_pattern:
                        details_parts.append(f"生长模式: {feature_combination.growth_pattern}")

                    # 干扰因素
                    if hasattr(feature_combination, 'interference_factors') and feature_combination.interference_factors:
                        interference_names = []
                        for factor in feature_combination.interference_factors:
                            if hasattr(factor, 'value'):
                                interference_names.append(factor.value)
                            else:
                                interference_names.append(str(factor))
                        if interference_names:
                            details_parts.append(f"干扰因素: {', '.join(sorted(interference_names))}")

                    # 置信度
                    if hasattr(feature_combination, 'confidence'):
                        details_parts.append(f"置信度: {feature_combination.confidence:.2f}")

                    # 组合详细信息
                    detail_str = " - " + "，".join(details_parts) if details_parts else ""

                    # 保留关键的用户提示信息（改为DEBUG级别，避免控制台输出过多）
                    log_debug(f"保存标注: {self.current_panoramic_id}_孔位{self.current_hole_number}{detail_str}", "SAVE")

                except Exception as e:
                    # 如果获取详细信息失败，记录错误并使用简化版本
                    log_warning(f"获取标注详细信息失败: {e}，使用简化日志格式", "SAVE")
                    log_info(f"保存标注: {self.current_panoramic_id}_孔位{self.current_hole_number}", "SAVE")
            else:
                # 自动保存和导航保存使用DEBUG级别
                log_debug(f"自动保存标注: {self.current_panoramic_id}_孔位{self.current_hole_number}，类型: {save_type}", "SAVE")

            return True
            
        except Exception as e:
            import traceback
            error_msg = f"保存标注失败: {str(e)}"
            # 记录详细错误信息到日志
            log_error(f"{error_msg}\n{traceback.format_exc()}")
            # 重新抛出异常，让上层处理
            raise Exception(error_msg)
    
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
            log_debug(f"无效的孔位编号 {hole_number}", "SWITCH")
            return
        
        # 保留关键的用户提示信息
        log_info(f"切换到孔位 {hole_number}", "SWITCH")
        
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
        
        log_debug(f"完成切换到孔位 {hole_number}", "SWITCH")
    
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
            log_error(f"孔位点击处理失败: {e}", "PANORAMIC_CLICK")
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

        # 获取CFG配置信息用于显示
        cfg_info_text = self.get_cfg_display_text()

        # 更新切片信息标签 - 显示文件、孔位信息和CFG配置
        if cfg_info_text:
            slice_info_text = f"{current_file['filename']} - {hole_label}({self.current_hole_number}) | {cfg_info_text}"
        else:
            slice_info_text = f"{current_file['filename']} - {hole_label}({self.current_hole_number})"
        self.slice_info_label.config(text=slice_info_text)

        # 更新标注预览标签
        annotation_preview_text = f"标注状态: {annotation_status}"
        self.annotation_preview_label.config(text=annotation_preview_text)

        # 更新详细标注信息
        detailed_info = self.get_detailed_annotation_info()
        self.detailed_annotation_label.config(text=detailed_info)

        # 添加debug日志跟踪字体大小和定位信息
        log_debug(f"更新切片信息显示 - 切片标签: '{slice_info_text}' (字体: TkDefaultFont 8)", "UI_UPDATE")
        log_debug(f"更新标注预览显示 - 预览标签: '{annotation_preview_text}' (字体: TkDefaultFont 8 bold)", "UI_UPDATE")
        log_debug(f"更新详细标注显示 - 详细标签: '{detailed_info}' (字体: TkDefaultFont 8)", "UI_UPDATE")

        # Only log significant info changes to reduce spam
        if not hasattr(self, '_last_info_display') or self._last_info_display != annotation_status:
            log_debug(f"更新切片信息显示: {annotation_status}", "INFO")
            self._last_info_display = annotation_status

        # 刷新显示
        self.root.update_idletasks()
    
    def update_progress(self):
        """更新进度显示"""
        if self.slice_files:
            current = self.current_slice_index + 1
            total = len(self.slice_files)
            self.progress_label.config(text=f"{current}/{total}")
        else:
            self.progress_label.config(text="0/0")
    
    def _map_growth_level_for_display(self, growth_level):
        """映射生长级别以用于显示 - 将弱生长映射为阳性"""
        if growth_level == 'weak_growth':
            return 'positive'
        return growth_level
    
    def update_statistics(self):
        """更新统计信息 - 基于增强标注"""
        if not self.slice_files:
            self.stats_label.config(text="统计: 无数据")
            return

        # 统计各类别数量 - 只统计有效孔位(25-120)
        stats = {
            'negative': 0,
            'positive': 0,  # 弱生长已映射到阳性，不再单独统计
            'total': 0,  # 将在循环中计算有效孔位总数
            'enhanced_annotated': 0,  # 增强标注数量
            'config_only': 0          # 仅有配置文件标注
        }
        
        log_debug(f"开始统计更新，总文件数: {stats['total']}", "STATS")
        
        enhanced_count = 0
        config_count = 0
        
        for file_info in self.slice_files:
            panoramic_id = file_info.get('panoramic_id', '')
            hole_number = file_info.get('hole_number', 0)

            # 只统计有效孔位(25-120)
            if 25 <= hole_number <= 120:
                stats['total'] += 1

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
                        # 映射弱生长到阳性
                        mapped_level = self._map_growth_level_for_display(growth_level)
                        if mapped_level in stats:
                            stats[mapped_level] += 1
                            # Limit debug output to avoid spam
                            if enhanced_count <= 2:  # Only log first 2 enhanced annotations
                                log_debug(f"统计增强标注 - 孔位{hole_number}, 级别: {growth_level} -> {mapped_level}, 源: {source}", "STATS")
                    else:
                        # Config import or other types
                        stats['config_only'] += 1
                        config_count += 1
        
        stats['unannotated'] = stats['total'] - stats['enhanced_annotated']
        
        # Only log summary statistics to reduce console spam
        log_debug(f"统计结果 - 增强标注: {enhanced_count}, 配置导入: {config_count}, 未标注: {stats['unannotated']}", "STATS")
        if enhanced_count > 0 or config_count > 0:  # Only log details when there are annotations
            log_debug(f"分类统计 - 阴性: {stats['negative']}, 阳性: {stats['positive']} (弱生长已映射到阳性)", "STATS")
        
        # 更新显示
        if stats['config_only'] > 0:
            stats_text = f"统计: 未标注 {stats['unannotated']}, 阴性 {stats['negative']}, 阳性 {stats['positive']} (配置: {stats['config_only']})"
        else:
            stats_text = f"统计: 未标注 {stats['unannotated']}, 阴性 {stats['negative']}, 阳性 {stats['positive']}"
        self.stats_label.config(text=stats_text)
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def toggle_debug_logging(self):
        """切换调试日志开关"""
        try:
            # 切换调试日志状态
            toggle_debug_logging()

            # 更新复选框状态以反映实际状态
            current_state = is_debug_logging_enabled()
            self.debug_logging_enabled.set(current_state)

            # 更新状态栏显示
            status_text = "调试日志已开启" if current_state else "调试日志已关闭"
            self.update_status(status_text)

            # 记录操作日志
            log_info(f"调试日志开关已切换: {'开启' if current_state else '关闭'}", "DEBUG_TOGGLE")

        except Exception as e:
            log_error(f"切换调试日志失败: {str(e)}", "DEBUG_TOGGLE")
            self.update_status(f"切换调试日志失败: {str(e)}")

    def sync_debug_logging_state(self):
        """同步调试日志状态到UI"""
        try:
            # 获取当前调试日志状态
            current_state = is_debug_logging_enabled()

            # 同步到复选框
            self.debug_logging_enabled.set(current_state)

            # 记录同步状态
            log_debug(f"调试日志状态已同步: {'开启' if current_state else '关闭'}", "DEBUG_SYNC")

        except Exception as e:
            log_error(f"同步调试日志状态失败: {str(e)}", "DEBUG_SYNC")
    
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

        # 计算标注统计信息 - 使用界面上的统计数据
        # 获取当前界面统计信息
        current_stats_text = self.stats_label.cget('text')
        unannotated_count = 0
        annotated_holes = len(enhanced_annotations)

        # 从界面统计文本中解析未标注数量
        try:
            if "未标注" in current_stats_text:
                # 解析统计文本，如 "统计: 未标注 10, 阴性 5, 弱生长 3, 阳性 2"
                parts = current_stats_text.replace("统计: ", "").split(", ")
                for part in parts:
                    if part.startswith("未标注"):
                        unannotated_count = int(part.split()[1])
                        break
        except (ValueError, IndexError) as e:
            log_warning(f"解析界面统计数据失败: {e}, 使用默认计算", "SAVE")
            # 回退到原计算方法
            total_valid_holes = 0
            panoramic_ids = set()
            for annotation in enhanced_annotations:
                panoramic_ids.add(annotation.panoramic_image_id)

            for panoramic_id in panoramic_ids:
                valid_holes_for_panoramic = 96  # 120 - 25 + 1 = 96
                total_valid_holes += valid_holes_for_panoramic

        # 使用界面统计数据计算总有效孔位数
        total_valid_holes = annotated_holes + unannotated_count

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

                # 记录文件保存的关键操作 - 保留关键用户提示
                log_info(f"标注文件保存成功: {filename}，共 {len(enhanced_annotations)} 个标注", "SAVE")

                # 显示保存成功消息，包含标注统计信息
                success_message = (f"增强标注结果已保存到: {filename}\n"
                                  f"保存了 {len(enhanced_annotations)} 个增强标注\n\n"
                                  f"标注统计:\n"
                                  f"- 需要标注的孔位总数: {total_valid_holes}\n"
                                  f"- 已标注的孔位数: {annotated_holes}")

                messagebox.showinfo("成功", success_message)
                self.update_status(f"已保存 {len(enhanced_annotations)} 个增强标注: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def load_annotations(self):
        """加载标注结果进行review"""
        # 记录加载标注文件的关键操作 - 保留关键用户提示
        log_info("开始加载标注文件...", "LOAD_ANNOTATIONS")
        
        # 记录加载标注前的窗口状态
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        current_geometry = self.root.geometry()
        log_debug(f"{timestamp} - 开始加载标注, 当前窗口: {current_geometry}", "LOAD_ANNOTATIONS")
        
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
                log_debug(f"检测到最后标注: {latest_annotation.panoramic_image_id}_{latest_annotation.hole_number}", "LOAD")
                
                # 切换到对应的全景图
                if latest_annotation.panoramic_image_id in self.panoramic_ids:
                    log_debug(f"切换到全景图: {latest_annotation.panoramic_image_id}", "LOAD")
                    success = self.switch_to_panoramic(latest_annotation.panoramic_image_id)
                    
                    if success:
                        # 延迟切换到对应的孔位，确保全景图加载完成
                        self.root.after(100, lambda: self.switch_to_hole(latest_annotation.hole_number))
                    else:
                        auto_switch_info = f" - 切换全景图失败"
                else:
                    log_debug(f"警告: 全景图 {latest_annotation.panoramic_image_id} 不在可用列表中", "LOAD")
                    auto_switch_info = f" - 全景图 {latest_annotation.panoramic_image_id} 不可用"
            else:
                log_debug(f"没有找到标注信息，保持当前视图", "LOAD")
            
            # 更新显示
            self.load_panoramic_image()
            self.update_statistics()
            
            log_debug(f"标注加载完成{auto_switch_info}", "LOAD")
            
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
                    log_debug(f"加载标注后强制刷新增强面板 - 孔位{self.current_hole_number}", "LOAD")
                    log_debug(f"标注源: {getattr(current_ann, 'annotation_source', 'unknown')}", "LOAD")
                    
                    # 先重置面板再重新设置，确保完全刷新
                    self.enhanced_annotation_panel.reset_annotation()
                    self.root.update_idletasks()
                    
                    # 重新触发完整的标注加载流程
                    self.load_existing_annotation()
                    self.root.update_idletasks()
                    
                    # 最后一次强制UI刷新确保增强面板完全同步
                    self.root.update()
                    
                    log_debug(f"增强面板强制刷新完成 - 孔位{self.current_hole_number}", "LOAD")
                else:
                    log_debug(f"当前孔位{self.current_hole_number}无标注，重置增强面板", "LOAD")
                    self.enhanced_annotation_panel.reset_annotation()
            
            # 多重UI刷新确保状态完全更新
            self.root.update_idletasks()
            self.root.update()
            
            # 延迟验证刷新 - 确保所有异步更新完成
            self.root.after(100, self._verify_load_refresh)
            
            log_debug(f"加载标注完成，当前孔位状态已刷新", "LOAD")
            
            messagebox.showinfo("成功", f"已加载 {merge_count} 个标注进行review")
            self.update_status(f"已加载标注文件: {filename} ({merge_count} 个标注)")
            
            # 记录标注加载完成的关键操作 - 保留关键用户提示
            log_info(f"标注文件加载完成: {filename}，共 {merge_count} 个标注", "LOAD_ANNOTATIONS")
            
            # 记录加载标注后的窗口状态
            import time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            final_geometry = self.root.geometry()
            log_debug(f"{timestamp} - 完成加载标注, 当前窗口: {final_geometry}", "LOAD_ANNOTATIONS")
            
            # 记录到日志
            log_entry = {
                'timestamp': timestamp,
                'geometry': final_geometry,
                'event': 'load_annotations_complete',
                'annotation_count': merge_count
            }
            self.window_resize_log.append(log_entry)
            
        except Exception as e:
            import traceback
            error_msg = f"加载标注文件失败: {str(e)}"
            # 记录详细错误信息到日志
            log_error(f"{error_msg}\n{traceback.format_exc()}")
            # 同时显示简化的用户友好错误消息
            messagebox.showerror("错误", error_msg)
    
    def _verify_timestamp_sync_after_load(self):
        """验证时间戳同步状态 - 确保加载后显示正确的时间戳"""
        try:
            log_debug(f"验证孔位{self.current_hole_number}的时间戳同步状态", "VERIFY_TIMESTAMP")
            
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
                
                log_debug(f"内存中有时间戳: {has_memory_timestamp}", "VERIFY_TIMESTAMP")
                log_debug(f"标注对象有时间戳: {has_annotation_timestamp}", "VERIFY_TIMESTAMP")
                
                if has_memory_timestamp:
                    memory_time = self.last_annotation_time[annotation_key]
                    log_debug(f"内存时间戳: {memory_time.strftime('%m-%d %H:%M:%S')}", "VERIFY_TIMESTAMP")
                elif has_annotation_timestamp:
                    log_debug(f"标注对象时间戳: {current_ann.timestamp}", "VERIFY_TIMESTAMP")
                    # 如果内存中没有但标注对象有，再次强制同步
                    self._force_timestamp_sync_after_load()
                
                # 最终刷新显示
                self.update_slice_info_display()
                log_debug(f"验证完成，刷新显示", "VERIFY_TIMESTAMP")
            else:
                log_debug(f"孔位{self.current_hole_number}无标注", "VERIFY_TIMESTAMP")
                
        except Exception as e:
            log_error(f"时间戳验证失败: {e}", "TIMESTAMP")
    
    def _force_timestamp_sync_after_load(self):
        """强制时间戳同步 - 修复加载标注后时间戳显示问题"""
        try:
            log_debug(f"强制同步孔位{self.current_hole_number}的时间戳", "FORCE_SYNC")
            
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
                    log_debug(f"成功同步时间戳: {annotation_key} -> {dt.strftime('%m-%d %H:%M:%S')}", "FORCE_SYNC")
                    log_debug(f"来源: JSON文件中的保存时间戳", "FORCE_SYNC")
                    
                    # 再次刷新显示以确保时间戳正确显示
                    self.update_slice_info_display()
                    
                except Exception as e:
                    log_debug(f"时间戳解析失败: {e}", "FORCE_SYNC")
            else:
                log_debug(f"孔位{self.current_hole_number}无有效时间戳", "FORCE_SYNC")
                
        except Exception as e:
            log_error(f"强制时间戳同步失败: {e}", "TIMESTAMP")
    
    def _verify_load_refresh(self):
        """验证加载后的刷新状态，确保当前孔位完全同步"""
        try:
            log_debug(f"验证孔位{self.current_hole_number}刷新状态", "VERIFY_LOAD")

            # 再次检查当前孔位的标注状态
            current_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id,
                self.current_hole_number
            )

            if current_ann and self.enhanced_annotation_panel:
                log_debug(f"发现当前孔位有标注，验证增强面板同步状态", "VERIFY_LOAD")

                # 检查增强面板状态是否正确
                if hasattr(current_ann, 'enhanced_data') and current_ann.enhanced_data:
                    log_debug(f"验证增强数据同步状态", "VERIFY_LOAD")
                    # 确保增强数据已正确加载到面板
                    current_combination = self.enhanced_annotation_panel.get_current_feature_combination()
                    log_debug(f"当前面板状态: {current_combination.growth_level}_{current_combination.growth_pattern}", "VERIFY_LOAD")

                # 强制一次最终的状态更新
                self.update_slice_info_display()
                self.update_statistics()

                log_debug(f"孔位{self.current_hole_number}状态验证完成", "VERIFY_LOAD")
            else:
                log_debug(f"孔位{self.current_hole_number}无需验证或无增强面板", "VERIFY_LOAD")

        except Exception as e:
            log_error(f"加载后验证失败: {e}")

    def _capture_annotation_state(self):
        """捕获当前标注状态，用于保存前后的对比"""
        try:
            state = {
                'panoramic_id': self.current_panoramic_id,
                'hole_number': self.current_hole_number,
                'timestamp': None,
                'existing_annotation': None,
                'cfg_config': None,
                'model_suggestion': None,
                'current_panel_state': None
            }

            # 获取现有标注
            existing_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id,
                self.current_hole_number
            )
            if existing_ann:
                state['existing_annotation'] = {
                    'growth_level': getattr(existing_ann, 'growth_level', 'negative'),
                    'microbe_type': getattr(existing_ann, 'microbe_type', 'bacteria'),
                    'interference_factors': getattr(existing_ann, 'interference_factors', []),
                    'annotation_source': getattr(existing_ann, 'annotation_source', 'unknown'),
                    'timestamp': getattr(existing_ann, 'timestamp', None),
                    'has_enhanced_data': hasattr(existing_ann, 'enhanced_data') and bool(existing_ann.enhanced_data)
                }
                if hasattr(existing_ann, 'enhanced_data') and existing_ann.enhanced_data:
                    state['existing_annotation']['enhanced_data'] = existing_ann.enhanced_data

            # 获取CFG配置
            config_data = self.get_current_panoramic_config()
            if config_data and self.current_hole_number in config_data:
                state['cfg_config'] = config_data[self.current_hole_number]

            # 获取模型建议
            if hasattr(self, 'hole_manager') and self.hole_manager:
                suggestion = self.hole_manager.get_hole_suggestion(self.current_hole_number)
                if suggestion:
                    state['model_suggestion'] = {
                        'growth_level': getattr(suggestion, 'growth_level', None),
                        'microbe_type': getattr(suggestion, 'microbe_type', None),
                        'growth_pattern': getattr(suggestion, 'growth_pattern', None),
                        'interference_factors': getattr(suggestion, 'interference_factors', None),
                        'model_confidence': getattr(suggestion, 'model_confidence', None)
                    }

            # 获取当前面板状态
            if self.enhanced_annotation_panel:
                try:
                    current_combination = self.enhanced_annotation_panel.get_current_feature_combination()
                    state['current_panel_state'] = {
                        'growth_level': current_combination.growth_level,
                        'growth_pattern': current_combination.growth_pattern,
                        'interference_factors': current_combination.interference_factors,
                        'confidence': current_combination.confidence,
                        'microbe_type': self.current_microbe_type.get()
                    }
                except Exception as e:
                    log_debug(f"获取面板状态失败: {e}", "STATE_CAPTURE")

            return state

        except Exception as e:
            log_error(f"捕获标注状态失败: {e}", "STATE_CAPTURE")
            return None

    def _log_annotation_change(self, pre_state, post_state, save_type="manual"):
        """记录标注变更的详细日志"""
        try:
            import datetime
            import os

            # 创建标注日志目录
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            annotation_log_file = log_dir / "annotation_changes.log"

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(annotation_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"标注变更记录 - {timestamp}\n")
                f.write(f"保存类型: {save_type}\n")
                f.write(f"全景图ID: {pre_state['panoramic_id']}\n")
                f.write(f"孔位编号: {pre_state['hole_number']}\n")
                f.write(f"{'='*80}\n")

                # CFG配置信息
                f.write(f"\nCFG配置:\n")
                if pre_state.get('cfg_config'):
                    f.write(f"  生长级别: {pre_state['cfg_config']}\n")
                else:
                    f.write(f"  无CFG配置\n")

                # 模型预测信息
                f.write(f"\n模型预测:\n")
                if pre_state.get('model_suggestion'):
                    ms = pre_state['model_suggestion']
                    f.write(f"  生长级别: {ms.get('growth_level', 'N/A')}\n")
                    f.write(f"  微生物类型: {ms.get('microbe_type', 'N/A')}\n")
                    f.write(f"  生长模式: {ms.get('growth_pattern', 'N/A')}\n")
                    f.write(f"  干扰因素: {ms.get('interference_factors', 'N/A')}\n")
                    f.write(f"  置信度: {ms.get('model_confidence', 'N/A')}\n")
                else:
                    f.write(f"  无模型预测\n")

                # 保存前状态
                f.write(f"\n保存前状态:\n")
                if pre_state.get('existing_annotation'):
                    ann = pre_state['existing_annotation']
                    f.write(f"  生长级别: {ann.get('growth_level', 'N/A')}\n")
                    f.write(f"  微生物类型: {ann.get('microbe_type', 'N/A')}\n")
                    f.write(f"  干扰因素: {ann.get('interference_factors', 'N/A')}\n")
                    f.write(f"  标注来源: {ann.get('annotation_source', 'N/A')}\n")
                    f.write(f"  时间戳: {ann.get('timestamp', 'N/A')}\n")
                    f.write(f"  增强数据: {'是' if ann.get('has_enhanced_data') else '否'}\n")
                else:
                    f.write(f"  无现有标注\n")

                # 当前面板状态（用户输入）
                f.write(f"\n用户输入状态:\n")
                if pre_state.get('current_panel_state'):
                    ps = pre_state['current_panel_state']
                    f.write(f"  生长级别: {ps.get('growth_level', 'N/A')}\n")
                    f.write(f"  生长模式: {ps.get('growth_pattern', 'N/A')}\n")
                    f.write(f"  干扰因素: {ps.get('interference_factors', 'N/A')}\n")
                    f.write(f"  置信度: {ps.get('confidence', 'N/A')}\n")
                    f.write(f"  微生物类型: {ps.get('microbe_type', 'N/A')}\n")
                else:
                    f.write(f"  无面板状态\n")

                # 保存后状态
                f.write(f"\n保存后状态:\n")
                if post_state.get('existing_annotation'):
                    ann = post_state['existing_annotation']
                    f.write(f"  生长级别: {ann.get('growth_level', 'N/A')}\n")
                    f.write(f"  微生物类型: {ann.get('microbe_type', 'N/A')}\n")
                    f.write(f"  干扰因素: {ann.get('interference_factors', 'N/A')}\n")
                    f.write(f"  标注来源: {ann.get('annotation_source', 'N/A')}\n")
                    f.write(f"  时间戳: {ann.get('timestamp', 'N/A')}\n")
                    f.write(f"  增强数据: {'是' if ann.get('has_enhanced_data') else '否'}\n")
                else:
                    f.write(f"  无保存后标注\n")

                # 变更分析
                f.write(f"\n变更分析:\n")
                changes = []

                # 检查是否有变更
                pre_ann = pre_state.get('existing_annotation')
                post_ann = post_state.get('existing_annotation')

                if not pre_ann and post_ann:
                    changes.append("新增标注")
                elif pre_ann and not post_ann:
                    changes.append("删除标注")
                elif pre_ann and post_ann:
                    # 比较各个字段
                    if pre_ann.get('growth_level') != post_ann.get('growth_level'):
                        changes.append(f"生长级别: {pre_ann.get('growth_level')} -> {post_ann.get('growth_level')}")
                    if pre_ann.get('microbe_type') != post_ann.get('microbe_type'):
                        changes.append(f"微生物类型: {pre_ann.get('microbe_type')} -> {post_ann.get('microbe_type')}")
                    if pre_ann.get('interference_factors') != post_ann.get('interference_factors'):
                        changes.append(f"干扰因素: {pre_ann.get('interference_factors')} -> {post_ann.get('interference_factors')}")

                if changes:
                    for change in changes:
                        f.write(f"  - {change}\n")
                else:
                    f.write(f"  无变更\n")

                f.write(f"{'='*80}\n")

        except Exception as e:
            log_error(f"记录标注变更日志失败: {e}", "ANNOTATION_LOG")
    

    
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
            log_error(f"更新全景图列表失败: {e}", "PANORAMIC_LIST")
    
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
        self.save_current_annotation_internal("navigation")
        
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
        self.save_current_annotation_internal("navigation")
        
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
        self.save_current_annotation_internal("navigation")

        # 根据全景图类型设置起始孔位（SE类型从5号孔开始，普通类型从默认值开始）
        if panoramic_id.upper().startswith('SE'):
            # SE类型全景图：前4个孔位为空，从第5个孔开始
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager.update_positioning_params(start_hole=5)
                log_debug(f"SE类型全景图，设置起始孔位为5", "NAVIGATION")
        else:
            # 普通全景图：恢复默认起始孔位
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager.update_positioning_params(start_hole=1)
                log_debug(f"普通类型全景图，设置起始孔位为1", "NAVIGATION")

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

            # 更新hole_manager的panoramic_id，确保模型建议正确显示
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager._current_panoramic_id = panoramic_id

            # 更新下拉列表选中项
            if hasattr(self, 'panoramic_combobox'):
                self.panoramic_id_var.set(panoramic_id)

            # 加载新的切片
            self.load_current_slice()
            self.update_progress()
            self.update_statistics()

            self.update_status(f"已切换到全景图: {panoramic_id}，起始孔位: {start_hole}")
        else:
            messagebox.showerror("错误", f"未找到全景图 {panoramic_id} 的切片文件")
    
    def switch_to_panoramic(self, panoramic_id):
        """自动切换到指定全景图（用于继续标注功能，不显示错误消息框）"""
        if panoramic_id not in self.panoramic_ids:
            log_debug(f"全景图 {panoramic_id} 不在可用列表中", "SWITCH")
            return False

        # 保存当前标注
        self.save_current_annotation_internal("navigation")

        # 根据全景图类型设置起始孔位（SE类型从5号孔开始，普通类型从默认值开始）
        if panoramic_id.upper().startswith('SE'):
            # SE类型全景图：前4个孔位为空，从第5个孔开始
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager.update_positioning_params(start_hole=5)
                log_debug(f"SE类型全景图，设置起始孔位为5", "SWITCH")
        else:
            # 普通全景图：恢复默认起始孔位
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager.update_positioning_params(start_hole=1)
                log_debug(f"普通类型全景图，设置起始孔位为1", "SWITCH")

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

            # 更新hole_manager的panoramic_id，确保模型建议正确显示
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager._current_panoramic_id = panoramic_id

            # 更新下拉列表选中项
            if hasattr(self, 'panoramic_combobox'):
                self.panoramic_id_var.set(panoramic_id)

            # 加载新的切片
            self.load_current_slice()
            self.update_progress()
            self.update_statistics()

            # 保留关键的用户提示信息
            log_info(f"已切换到全景图: {panoramic_id}，起始孔位: {start_hole}", "SWITCH")
            return True
        else:
            log_debug(f"未找到全景图 {panoramic_id} 的切片文件", "SWITCH")
            return False
    
    def import_model_suggestions(self):
        """导入模型预测结果文件"""
        # 检查模型建议服务是否可用
        if not self.model_suggestion_service:
            messagebox.showerror(
                "功能不可用", 
                "模型建议服务不可用。\n\n可能的原因：\n"
                "1. 模块 ModelSuggestionImportService 未实现\n"
                "2. 相关依赖未安装\n"
                "3. 文件路径配置错误\n\n"
                "请检查系统配置或联系开发人员。"
            )
            return
        
        try:
            file_path = filedialog.askopenfilename(
                title="选择模型预测结果文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )

            if not file_path:
                return

            # 使用模型建议服务加载文件
            try:
                suggestions_map, warnings = self.model_suggestion_service.load_from_json(file_path)
            except Exception as e:
                log_error(f"模型建议服务调用失败: {e}", "MODEL_SUGGESTION")
                messagebox.showerror("服务错误", f"模型建议服务调用失败：\n{str(e)}")
                return

            if suggestions_map:
                self.current_suggestions_map = suggestions_map
                self.model_suggestion_loaded = True

                # 设置到hole_manager
                self.hole_manager.set_suggestions_map(suggestions_map, self.current_panoramic_id)

                # 更新当前显示
                self.update_hole_suggestion_display()

                # 计算有建议的孔位数量
                suggestion_count = 0
                for hole_num in range(1, 121):
                    if suggestions_map.get_suggestion(self.current_panoramic_id, hole_num):
                        suggestion_count += 1

                # 构建成功消息，包含警告信息（如果有的话）
                success_message = f"已成功导入模型建议，共 {suggestion_count} 条记录"
                if warnings:
                    warning_msg = "\n".join(warnings)
                    success_message += f"\n\n警告信息：\n{warning_msg}"

                messagebox.showinfo("成功", success_message)
                # 保留关键的用户提示信息
                log_info(f"导入模型建议成功: {file_path}", "MODEL_SUGGESTION")
            else:
                messagebox.showerror("错误", "导入模型建议失败，请检查文件格式")

        except Exception as e:
            messagebox.showerror("错误", f"导入模型建议时发生错误: {str(e)}")
            log_error(f"导入模型建议失败: {str(e)}", "MODEL_SUGGESTION")
    
    def on_view_mode_changed(self, view_mode):
        """处理视图模式变更事件"""
        try:
            # 保留关键的用户提示信息
            log_info(f"视图模式切换到: {view_mode}", "VIEW_MODE")
            
            # 更新建议显示
            self.update_hole_suggestion_display()
            
        except Exception as e:
            log_error(f"处理视图模式变更失败: {str(e)}", "VIEW_MODE")
    
    def _load_model_view_data(self):
        """加载模型视图数据 - 显示模型预测结果（符合文档v2.1策略）"""
        try:
            # 策略：模型视图下优先显示模型预测，无模型预测时降级到CFG或默认
            if not hasattr(self, 'hole_manager') or not self.hole_manager:
                log_debug("hole_manager不存在，降级到CFG/默认设置", "MODEL_VIEW")
                self._load_fallback_data_for_model_view()
                return

            suggestion = self.hole_manager.get_hole_suggestion(self.current_hole_number)
            if suggestion:
                log_debug(f"模型视图显示预测结果: 生长级别={suggestion.growth_level}", "MODEL_VIEW")

                # 应用预测结果到增强标注面板
                if self.enhanced_annotation_panel:
                    try:
                        # 设置微生物类型
                        if hasattr(suggestion, 'microbe_type') and suggestion.microbe_type:
                            self.current_microbe_type.set(suggestion.microbe_type)

                        # 设置生长级别
                        if hasattr(suggestion, 'growth_level') and suggestion.growth_level:
                            self.enhanced_annotation_panel.current_growth_level.set(suggestion.growth_level)

                        # 设置生长模式
                        if hasattr(suggestion, 'growth_pattern') and suggestion.growth_pattern:
                            if isinstance(suggestion.growth_pattern, list):
                                pattern = suggestion.growth_pattern[0] if suggestion.growth_pattern else None
                            else:
                                pattern = suggestion.growth_pattern

                            if pattern:
                                self.enhanced_annotation_panel.current_growth_pattern.set(pattern)

                        # 设置干扰因素
                        panel_factors = self.enhanced_annotation_panel.interference_vars

                        # 先重置所有干扰因素
                        for var in panel_factors.values():
                            var.set(False)

                        # 设置预测的干扰因素
                        if hasattr(suggestion, 'interference_factors') and suggestion.interference_factors:
                            for factor in suggestion.interference_factors:
                                factor_set = False

                                # 直接匹配枚举对象
                                if factor in panel_factors:
                                    panel_factors[factor].set(True)
                                    factor_set = True

                                # 通过枚举值匹配
                                elif hasattr(factor, 'value'):
                                    factor_value = factor.value
                                    for panel_key, panel_var in panel_factors.items():
                                        if hasattr(panel_key, 'value') and panel_key.value == factor_value:
                                            panel_var.set(True)
                                            factor_set = True
                                            break

                                # 通过字符串匹配
                                elif isinstance(factor, str):
                                    string_mapping = {
                                        'pores': 'PORES',
                                        'artifacts': 'ARTIFACTS',
                                        'debris': 'DEBRIS',
                                        'contamination': 'CONTAMINATION',
                                        '气孔': 'PORES',
                                        '气孔重叠': 'ARTIFACTS',
                                        '杂质': 'DEBRIS',
                                        '污染': 'CONTAMINATION'
                                    }
                                    if factor in string_mapping:
                                        enum_name = string_mapping[factor]
                                        for panel_key, panel_var in panel_factors.items():
                                            if hasattr(panel_key, 'name') and panel_key.name == enum_name:
                                                panel_var.set(True)
                                                factor_set = True
                                                break

                        # 设置置信度
                        if hasattr(suggestion, 'model_confidence') and suggestion.model_confidence is not None:
                            self.enhanced_annotation_panel.current_confidence.set(suggestion.model_confidence)

                        # 刷新界面
                        self.enhanced_annotation_panel.update_pattern_options()
                        self.root.update_idletasks()

                        log_debug(f"模型视图数据加载完成: {suggestion.growth_level}", "MODEL_VIEW")

                    except Exception as e:
                        log_error(f"模型视图数据加载失败: {e}", "MODEL_VIEW")
            else:
                # 无模型预测，按照文档策略降级到CFG配置或默认设置
                log_debug(f"当前孔位{self.current_hole_number}无模型预测结果，降级处理", "MODEL_VIEW")
                self._load_fallback_data_for_model_view()

        except Exception as e:
            log_error(f"加载模型视图数据失败: {e}", "MODEL_VIEW")

    def _load_fallback_data_for_model_view(self):
        """模型视图下的降级数据加载：CFG配置 > 默认设置"""
        try:
            # 检查CFG配置
            config_annotation = self._get_config_annotation(self.current_panoramic_id, self.current_hole_number)
            if config_annotation:
                log_debug(f"模型视图降级：应用CFG配置", "MODEL_VIEW")
                self._apply_config_annotation(config_annotation)
                return
            
            # 无CFG配置，应用默认设置
            log_debug(f"模型视图降级：应用默认设置", "MODEL_VIEW")
            default_microbe_type = self.get_default_microbe_type(self.current_panoramic_id)
            self.current_microbe_type.set(default_microbe_type)
            
            if self.enhanced_annotation_panel:
                # 重置为默认的阴性状态
                self.enhanced_annotation_panel.current_growth_level.set('negative')
                self.enhanced_annotation_panel.current_growth_pattern.set('clean')
                self.enhanced_annotation_panel.current_confidence.set(1.0)
                
                # 重置干扰因素
                for var in self.enhanced_annotation_panel.interference_vars.values():
                    var.set(False)
                
                # 刷新界面
                self.enhanced_annotation_panel.update_pattern_options()
                self.root.update_idletasks()
                
        except Exception as e:
            log_error(f"模型视图降级数据加载失败: {e}", "MODEL_VIEW")


    def update_hole_suggestion_display(self):
        """更新孔位建议显示"""
        try:
            if not self.model_suggestion_loaded or not self.current_suggestions_map:
                return

            # 获取当前孔位信息
            current_slice = self.slice_files[self.current_slice_index]
            panoramic_id = current_slice['panoramic_id']
            hole_number = current_slice.get('hole_number', 1)

            # 获取当前孔位的建议
            suggestion = self.hole_manager.get_hole_suggestion(hole_number)

            # hole_config_panel已移除（功能简化）

        except Exception as e:
            log_error(f"更新孔位建议显示失败: {str(e)}", "MODEL_SUGGESTION")

    def auto_switch_view_mode(self):
        """自动切换视图模式"""
        try:
            log_debug("开始自动切换视图模式", "AUTO_VIEW")

            # 检查是否有人工标注数据
            has_manual_annotations = False
            for annotation in self.current_dataset.annotations:
                if hasattr(annotation, 'annotation_source'):
                    if annotation.annotation_source in ['enhanced_manual', 'manual']:
                        has_manual_annotations = True
                        break

            if has_manual_annotations:
                log_debug("检测到人工标注数据，切换到人工视图", "AUTO_VIEW")
                self.set_view_mode(ViewMode.MANUAL)
                return

            # 检查是否有模型建议数据（仅在服务可用时）
            if (MODEL_SUGGESTION_SERVICE_AVAILABLE and 
                hasattr(self, 'model_suggestion_loaded') and self.model_suggestion_loaded):
                log_debug("检测到模型建议数据且服务可用，切换到模型视图", "AUTO_VIEW")
                self.set_view_mode(ViewMode.MODEL)
                return

            # 默认保持人工视图
            log_debug("无特殊数据，保持人工视图", "AUTO_VIEW")
            self.set_view_mode(ViewMode.MANUAL)

        except Exception as e:
            log_error(f"自动切换视图模式失败: {str(e)}", "AUTO_VIEW")

    def show_about_dialog(self):
        """显示操作指南对话框"""
        try:            
            # 创建关于对话框窗口
            about_window = tk.Toplevel(self.root)
            about_window.title("操作指南")
            about_window.geometry("800x750")  # 增加尺寸以容纳更新日志
            about_window.resizable(True, True)
            about_window.transient(self.root)
            about_window.grab_set()
            
            # 创建滚动框架
            canvas = tk.Canvas(about_window)
            scrollbar = tk.Scrollbar(about_window, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # 标题
            title_label = tk.Label(scrollable_frame, 
                                  text="全景图像标注工具 - 操作指南", 
                                  font=("Arial", 14, "bold"),
                                  fg="#2E86AB")
            title_label.pack(pady=(10, 20))
            
            # 版本信息（简化显示）
            version_info = get_version_display()
            version_label = tk.Label(scrollable_frame,
                                    text=f"版本: {version_info}",
                                    font=("Arial", 10),
                                    fg="#666666")
            version_label.pack(pady=(0, 15))
            
            # 操作指南内容
            guide_text = """【基本操作流程】

1. 浏览并加载图像
   • 点击"浏览"按钮选择全景图像文件
   • 支持BMP格式的全景图像
   • 选择后自动加载并显示在预览区域

2. 加载标注配置
   • 点击"加载标注"按钮选择对应的配置文件(.cfg)
   • 配置文件包含标注的坐标和类型信息
   • 加载后标注会显示在图像上

3. 导入模型建议
   • 使用"导入模型建议"功能加载AI模型的标注建议
   • 可以基于模型建议进行人工确认和调整
   • 提高标注效率和准确性

4. 标注操作
   • 在图像上拖拽创建标注框
   • 右键点击标注框可删除或修改类型
   • 支持多种微生物类型的标注

5. 保存并下一个
   • 点击"保存并下一个"保存当前标注
   • 自动复制上一个同生长级别的标注设置
   • 提高批量标注的连续性

【标注颜色标准】

• 红色框: 目标微生物（主要标注对象）
• 绿色框: 参考微生物
• 蓝色框: 疑似目标
• 黄色框: 其他类型
• 橙色框: 需要确认的标注

【显示方法】

• 缩放: 使用鼠标滚轮或缩放按钮
• 平移: 按住鼠标左键拖拽图像
• 全景浏览: 点击导航窗口快速定位

【已标注显示】

• 已完成标注的图像会在文件列表中标记
• 绿色表示已完成，红色表示有错误
• 点击可重新打开进行修改

【统计功能】

• 实时显示当前图像的标注数量
• 按类型统计标注分布
• 提供整体进度统计

【开始孔位】

• 设置批量标注的起始位置
• 支持从指定孔位开始标注
• 便于大批量数据的分段处理

【快捷键】

• F1: 显示此帮助信息
• Ctrl+S: 快速保存
• Ctrl+N: 下一个图像
• Delete: 删除选中的标注框
• 方向键: 孔位导航
• 1/2/3: 设置生长级别
• 空格: 保存并下一个

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【生长级别与模式详解】

▶ 阴性模式（药物敏感，生长抑制）
• 清亮: 完全抑制，无可见生长
• 微弱分散: 极少量散在生长点，生长明显受抑制
• 弱中心点: 仅在中心区域有少量微弱生长点

▶ 阳性模式（药物耐药，生长明显）
• 聚焦性: 集中密集生长，形成聚焦病灶
• 强分散: 广泛分散的密集生长点
• 重度: 大面积密集生长，生长旺盛
• 强中心点: 中心区域密集生长点，生长活跃
• 弱分散: 分散但可见的生长点，数量相对较少
• 不规则: 不规则形状的生长区域

▶ 真菌专用模式
• 弥散: 真菌呈弥散性生长（阳性）
• 丝状非融合: 菌丝分离，生长受限（阴性）
• 丝状融合: 菌丝融合，生长旺盛（阳性）

【关键模式对比分析】

★ 强中心点 vs 弱中心点的判别要点：
• 阳性+强中心点: 中心区域生长密集，颜色深，数量多，边界清晰
• 阴性+弱中心点: 中心区域生长稀疏，颜色浅，数量少，生长受抑制

★ 弱分散 vs 微弱分散的判别要点：
• 阳性+弱分散: 分散生长但仍可见明显的菌落点，显示一定的生长能力
• 阴性+微弱分散: 极少量散在点，生长明显受到药物抑制

【弱生长的医学意义】

传统的"弱生长"概念实际上代表了阳性与阴性之间的临界状态，但在临床判断中：

✓ 倾向阳性的弱生长表现：
• 虽然生长量少，但菌落形态相对完整
• 分散分布但生长点清晰可辨
• 表明微生物具有一定的药物耐受性
• 临床判断为耐药，归类为"阳性"

✓ 倾向阴性的弱生长表现：
• 生长点极其微弱，几乎不可见
• 生长受到明显抑制，形态不完整
• 表明药物对微生物有明显抑制作用
• 临床判断为敏感，归类为"阴性"

这种精确的二分法有助于：
• 明确临床用药决策
• 避免模糊判断造成的治疗延误
• 提高药敏检测的临床指导价值

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【版本更新日志】

▶ v1.2.0.0 (2025年9月11日)
• 💊 医学标准升级：修正真菌生长模式分类
  - 丝状融合：改为阳性（菌丝融合表示生长旺盛，耐药）
  - 丝状非融合：改为阴性（菌丝分离表示生长受限，敏感）
  - 优化阴性/阳性二分法，确保临床指导价值

• 🧬 CFG配置信息显示：在切片信息中增加微生物类型和生长级别显示
  - 自动识别文件名前缀判断微生物类型（FG=真菌，其他=细菌）
  - 实时显示配置文件中的生长级别信息
  - 提升标注信息的完整性和可追溯性

• 🖥️ 界面布局优化：解决生长模式选择按钮宽度显示问题
  - 改用响应式网格布局，确保所有模式按钮完整显示
  - 优化真菌模式切换时的界面刷新机制
  - 提高用户操作体验

• 📖 操作指南完善：新增详细生长模式分类说明
  - 补充真菌专用模式的医学解释
  - 增加关键模式对比分析
  - 详细说明弱生长的临床判断标准

• 🧹 代码优化：清理调试脚本，更新映射关系
  - 生成模型训练用的分类映射文档
  - 建立完整的医学标准验证机制
  - 为后续AI模型训练提供准确分类指导

▶ v1.1.0.0 (之前版本)
• 基础标注功能
• 全景图像显示
• 孔位导航
• 模型建议导入"""
            
            # 创建文本框显示指南内容
            text_widget = tk.Text(scrollable_frame, 
                                 wrap=tk.WORD, 
                                 width=75, 
                                 height=30,
                                 font=("Arial", 10),
                                 bg="#f8f9fa",
                                 relief=tk.FLAT,
                                 padx=15,
                                 pady=10)
            text_widget.insert(tk.END, guide_text)
            text_widget.config(state=tk.DISABLED)  # 只读
            text_widget.pack(padx=20, pady=10)
            
            # 关闭按钮
            close_button = tk.Button(scrollable_frame, 
                                   text="关闭", 
                                   command=about_window.destroy,
                                   bg="#2E86AB",
                                   fg="white",
                                   font=("Arial", 10, "bold"),
                                   padx=20,
                                   pady=5)
            close_button.pack(pady=20)
            
            # 配置滚动
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # 绑定鼠标滚轮事件
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            about_window.bind("<MouseWheel>", _on_mousewheel)
            
            # 居中显示窗口 - 相对于父窗口居中
            about_window.update_idletasks()
            self.root.update_idletasks()  # 确保父窗口信息准确
            
            # 获取窗口尺寸
            window_width = about_window.winfo_width()
            window_height = about_window.winfo_height()
            
            # 获取父窗口的位置和尺寸
            parent_x = self.root.winfo_x()
            parent_y = self.root.winfo_y()
            parent_width = self.root.winfo_width()
            parent_height = self.root.winfo_height()
            
            # 计算相对于父窗口的居中位置
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2
            
            # 获取屏幕尺寸，确保窗口不会超出屏幕边界
            screen_width = about_window.winfo_screenwidth()
            screen_height = about_window.winfo_screenheight()
            
            # 调整位置，确保完全在屏幕内
            x = max(0, min(x, screen_width - window_width))
            y = max(0, min(y, screen_height - window_height))
            
            about_window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            log_error(f"显示操作指南对话框时出错: {e}")
            # 显示简化的版本信息
            simple_text = f"""全景图像标注工具
版本: {get_version_display()}

操作指南功能暂时不可用，请查看相关文档。"""
            messagebox.showinfo("操作指南", simple_text)


def main():
    """主函数 - 启动全景标注工具"""
    try:
        # 创建主窗口和应用
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)

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


# === 开发者快速启用性能监控的方法 ===
# 如需临时启用性能监控功能，可在Python控制台中执行：
# 
# gui = app  # 假设gui实例变量名为app
# gui.performance_monitoring_enabled.set(True)  # 启用性能监控
# gui.show_performance_analysis()  # 显示性能分析
# gui.show_delay_config_dialog()  # 显示延迟配置
# 
# 如需永久启用，请按照文件中"性能监控功能配置"部分的说明操作


if __name__ == '__main__':
    main()
