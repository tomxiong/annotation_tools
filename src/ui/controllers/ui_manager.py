"""
UI管理器模块

负责UI组件的创建、布局和管理
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, TYPE_CHECKING
import logging
from src.ui.components.navigation_panel import NavigationPanel
from src.ui.components.annotation_panel import AnnotationPanel
from src.ui.components.image_canvas import ImageCanvas
from src.ui.enhanced_annotation_panel import EnhancedAnnotationPanel

if TYPE_CHECKING:
    from .main_controller import MainController

logger = logging.getLogger(__name__)


class UIManager:
    """UI管理器 - 负责UI组件的创建和管理"""

    def __init__(self, controller: 'MainController'):
        self.controller = controller
        self.root: Optional[tk.Tk] = None

        # UI组件引用
        self.main_frame: Optional[ttk.Frame] = None
        self.toolbar: Optional[ttk.Frame] = None
        self.panoramic_canvas: Optional[tk.Canvas] = None
        self.slice_canvas: Optional[tk.Canvas] = None
        self.stats_label: Optional[ttk.Label] = None
        self.status_label: Optional[ttk.Label] = None
        self.panoramic_info_label: Optional[ttk.Label] = None
        self.slice_info_label: Optional[ttk.Label] = None
        self.annotation_preview_label: Optional[ttk.Label] = None
        self.detailed_annotation_label: Optional[ttk.Label] = None
        self.progress_label: Optional[ttk.Label] = None
        self.panoramic_combobox: Optional[ttk.Combobox] = None

    def initialize(self, root: tk.Tk):
        """初始化UI管理器"""
        self.root = root
        self._create_main_layout()
        logger.info("UIManager initialized")

    def _create_main_layout(self):
        """创建主布局"""
        if not self.root:
            return

        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建工具栏
        self._create_toolbar()

        # 创建内容区域
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # 创建全景图显示区域
        self._create_panoramic_panel(content_frame)

        # 创建分隔符
        separator = ttk.Separator(content_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 创建右侧控制面板
        self._create_control_panel(content_frame)

        # 创建状态栏
        self._create_status_bar()

    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, pady=(0, 5))

        # 全景图目录选择
        ttk.Label(self.toolbar, text="全景图:").pack(side=tk.LEFT, padx=(0, 5))

        self.controller.panoramic_dir_var = tk.StringVar()
        panoramic_dir_entry = ttk.Entry(self.toolbar, textvariable=self.controller.panoramic_dir_var, width=45)
        panoramic_dir_entry.pack(side=tk.LEFT, padx=(0, 5))

        # 操作按钮
        ttk.Button(self.toolbar, text="浏览并加载",
                  command=self.controller._select_panoramic_directory).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(self.toolbar, text="加载标注",
                  command=self.controller._load_annotations).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(self.toolbar, text="保存标注",
                  command=self.controller._save_annotations).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(self.toolbar, text="导入模型建议",
                  command=self.controller._import_model_suggestions).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(self.toolbar, text="导出训练数据",
                  command=self.controller._export_training_data).pack(side=tk.LEFT, padx=(0, 10))

    def _create_panoramic_panel(self, parent):
        """创建全景图显示面板"""
        panoramic_frame = ttk.LabelFrame(parent, text="全景图 (12×10孔位布局)")
        panoramic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 全景图显示区域
        self.panoramic_canvas = tk.Canvas(panoramic_frame, bg='white')
        self.panoramic_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 绑定鼠标点击事件
        self.panoramic_canvas.bind("<Button-1>", self.controller._on_panoramic_click)

        # 全景图信息
        info_frame = ttk.Frame(panoramic_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.panoramic_info_label = ttk.Label(info_frame, text="未加载全景图")
        self.panoramic_info_label.pack(side=tk.LEFT)

    def _create_control_panel(self, parent):
        """创建右侧控制面板"""
        right_frame = ttk.Frame(parent, width=360)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_frame.pack_propagate(False)

        # 创建统计面板
        self._create_stats_panel(right_frame)

        # 创建导航面板
        self._create_navigation_panel(right_frame)

        # 创建切片显示区域
        self._create_slice_panel(right_frame)

        # 创建标注控制面板
        self._create_annotation_panel(right_frame)

    def _create_stats_panel(self, parent):
        """创建统计面板"""
        stats_frame = ttk.LabelFrame(parent, text="统计信息")
        stats_frame.pack(fill=tk.X, pady=(0, 2))

        self.stats_label = ttk.Label(stats_frame, text="统计: 未标注 0, 阴性 0, 弱生长 0, 阳性 0")
        self.stats_label.pack(padx=5, pady=3)

        # 视图模式选择区域
        self._create_view_mode_panel(parent)

    def _create_view_mode_panel(self, parent):
        """创建视图模式选择面板"""
        view_frame = ttk.LabelFrame(parent, text="视图模式")
        view_frame.pack(fill=tk.X, pady=(2, 2))

        # 视图模式单选按钮
        mode_frame = ttk.Frame(view_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)

        self.controller.view_mode_var = tk.StringVar(value="manual")

        self.controller.manual_radio = ttk.Radiobutton(mode_frame, text="人工",
                                          variable=self.controller.view_mode_var,
                                          value="manual", command=self.controller._on_view_mode_changed)
        self.controller.manual_radio.pack(side=tk.LEFT, padx=5)

        self.controller.model_radio = ttk.Radiobutton(mode_frame, text="模型",
                                         variable=self.controller.view_mode_var,
                                         value="model", command=self.controller._on_view_mode_changed)
        self.controller.model_radio.pack(side=tk.LEFT, padx=5)

    def _create_navigation_panel(self, parent):
        """创建导航面板"""
        nav_frame = ttk.LabelFrame(parent, text="导航控制 (快捷键)")
        nav_frame.pack(fill=tk.X, pady=(0, 5))

        # 第一行：全景图导航
        top_frame = ttk.Frame(nav_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(top_frame, text="全景图:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(top_frame, text="◀", width=3,
                  command=self.controller._go_prev_panoramic).pack(side=tk.LEFT, padx=1)

        self.panoramic_combobox = ttk.Combobox(top_frame, width=12)
        self.panoramic_combobox.pack(side=tk.LEFT, padx=2)
        self.panoramic_combobox.bind('<<ComboboxSelected>>', self.controller._on_panoramic_selected)

        ttk.Button(top_frame, text="▶", width=3,
                  command=self.controller._go_next_panoramic).pack(side=tk.LEFT, padx=1)

        # 第二行：孔位导航
        bottom_frame = ttk.Frame(nav_frame)
        bottom_frame.pack(fill=tk.X, padx=5, pady=3)

        # 孔位跳转
        hole_frame = ttk.Frame(bottom_frame)
        hole_frame.pack(side=tk.LEFT)

        ttk.Label(hole_frame, text="跳转:").pack(side=tk.LEFT, padx=(0, 2))

        self.controller.hole_number_var = tk.StringVar(value="1")
        hole_entry = ttk.Entry(hole_frame, textvariable=self.controller.hole_number_var, width=4)
        hole_entry.pack(side=tk.LEFT, padx=1)
        hole_entry.bind('<Return>', self.controller._go_to_hole)

        # 序列导航
        seq_frame = ttk.Frame(bottom_frame)
        seq_frame.pack(side=tk.RIGHT)

        ttk.Button(seq_frame, text="◀◀", width=4,
                  command=self.controller._go_first_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="◀", width=4,
                  command=self.controller._go_prev_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="▶", width=4,
                  command=self.controller._go_next_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="▶▶", width=4,
                  command=self.controller._go_last_hole).pack(side=tk.LEFT, padx=1)

        # 进度信息
        self.progress_label = ttk.Label(bottom_frame, text="0/0")
        self.progress_label.pack(side=tk.LEFT, expand=True)

        # 画布点击提示
        click_label = ttk.Label(nav_frame, text="提示: 点击全景图跳转对应孔位",
                               font=('TkDefaultFont', 8))
        click_label.pack(side=tk.BOTTOM, padx=5, pady=(0, 3))

    def _create_slice_panel(self, parent):
        """创建切片显示面板"""
        slice_frame = ttk.LabelFrame(parent, text="当前切片")
        slice_frame.pack(fill=tk.X, padx=(0, 0), pady=(0, 5))

        # 切片显示区域
        self.slice_canvas = tk.Canvas(slice_frame, bg='white', width=150, height=150)
        self.slice_canvas.pack(padx=5, pady=3)

        # 创建图像画布 - 移到切片面板中
        self.controller.image_canvas = ImageCanvas(slice_frame, self.controller)
        self.controller.image_canvas.get_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 3))

        # 切片信息区域
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

    def _create_annotation_panel(self, parent):
        """创建标注控制面板"""
        ann_frame = ttk.LabelFrame(parent, text="标注控制")
        ann_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

        # 创建导航面板
        self.controller.navigation_panel = NavigationPanel(ann_frame, self.controller)
        self.controller.navigation_panel.get_widget().pack(fill=tk.BOTH, expand=True, padx=3, pady=(3, 3))

        # 创建标注面板
        self.controller.annotation_panel = AnnotationPanel(ann_frame, self.controller)
        self.controller.annotation_panel.get_widget().pack(fill=tk.BOTH, expand=True, padx=3, pady=(3, 3))

        # 创建图像画布
        self.controller.image_canvas = ImageCanvas(ann_frame, self.controller)
        self.controller.image_canvas.get_widget().pack(fill=tk.BOTH, expand=True, padx=3, pady=(3, 3))

        # 创建增强标注面板 - 减少边距，不扩展
        self.controller.enhanced_annotation_frame = ttk.Frame(ann_frame)
        self.controller.enhanced_annotation_frame.pack(fill=tk.X, padx=3, pady=(3, 3))

        # 初始化enhanced annotation panel
        self.controller.annotation_panel = EnhancedAnnotationPanel(
            self.controller.enhanced_annotation_frame,
            on_annotation_change=self.controller._on_enhanced_annotation_change
        )

        # 标注按钮 - 移到增强标注面板下方
        self.controller.button_frame = ttk.Frame(ann_frame)
        self.controller.button_frame.pack(fill=tk.X, padx=5, pady=(3, 3))

        ttk.Button(self.controller.button_frame, text="保存并下一个",
                  command=self.controller._save_current_annotation).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.controller.button_frame, text="跳过",
                  command=self.controller._skip_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.controller.button_frame, text="清除标注",
                  command=self.controller._clear_current_annotation).pack(side=tk.LEFT, padx=2)

    def _create_status_bar(self):
        """创建状态栏"""
        if not self.main_frame:
            return

        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.status_label = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def update_status(self, message: str):
        """更新状态栏"""
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.config(text=message)
            if self.root:
                self.root.update_idletasks()

    def update_statistics(self, stats_text: str):
        """更新统计信息"""
        if self.stats_label:
            self.stats_label.config(text=stats_text)

    def update_progress(self, progress_text: str):
        """更新进度信息"""
        if self.progress_label:
            self.progress_label.config(text=progress_text)

    def update_panoramic_info(self, info_text: str):
        """更新全景图信息"""
        if self.panoramic_info_label:
            self.panoramic_info_label.config(text=info_text)

    def update_slice_info(self, info_text: str):
        """更新切片信息"""
        if self.slice_info_label:
            self.slice_info_label.config(text=info_text)

    def update_annotation_preview(self, preview_text: str):
        """更新标注预览"""
        if self.annotation_preview_label:
            self.annotation_preview_label.config(text=preview_text)

    def update_detailed_annotation(self, detail_text: str):
        """更新详细标注信息"""
        if self.detailed_annotation_label:
            self.detailed_annotation_label.config(text=detail_text)

    def get_panoramic_canvas(self):
        """获取全景图画布"""
        return self.panoramic_canvas

    def get_slice_canvas(self):
        """获取切片画布"""
        return self.slice_canvas

    def get_panoramic_combobox(self):
        """获取全景图下拉列表"""
        return self.panoramic_combobox