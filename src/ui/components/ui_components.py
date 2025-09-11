"""
UI组件模块
负责创建和管理所有用户界面组件
从原panoramic_annotation_gui.py中拆分出来
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional, Dict, List, Any


class UIComponents:
    """UI组件管理类"""
    
    def __init__(self, parent_gui):
        """
        初始化UI组件管理器
        
        Args:
            parent_gui: 主GUI实例，用于访问必要的属性和方法
        """
        self.gui = parent_gui
        self.root = parent_gui.root
        
    # === UI创建方法 ===

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

        # 重新排列按钮顺序并调整间距
        ttk.Button(toolbar, text="浏览并加载",
                    command=self._on_select_directory).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="加载标注",
                    command=self._on_load_annotations).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="保存标注",
                    command=self._on_save_annotations).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="导入模型建议",
                    command=self.import_model_suggestions).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="导出训练数据",
                    command=self.export_training_data).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(toolbar, text="批量导入",
                    command=self.batch_import_annotations).pack(side=tk.LEFT, padx=(0, 10))

        # 调试日志开关
        ttk.Checkbutton(toolbar, text="调试日志",
                        variable=self.debug_logging_enabled,
                        command=self.toggle_debug_logging).pack(side=tk.LEFT, padx=(0, 5))

        # === 性能监控相关功能已隐藏，减少界面复杂度 ===
        # 如需启用，取消以下注释：
        # # 性能监控开关
        # ttk.Checkbutton(toolbar, text="性能监控",
        #                variable=self.performance_monitoring_enabled).pack(side=tk.LEFT, padx=(0, 5))

        # # 性能分析按钮
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


    def create_hole_config_panel(self, parent):
        """创建孔位配置面板"""
        # 创建孔位配置面板实例
        self.hole_config_panel = HoleConfigPanel(parent, self.apply_hole_config)

        # 绑定视图模式变更事件
        self.hole_config_panel.add_view_change_callback(self.on_view_mode_changed)


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

        # 批量导入按钮
        ttk.Button(button_frame, text="批量导入", 
                    command=self.batch_import_annotations).pack(side=tk.LEFT, padx=2)

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


    def create_stats_panel(self, parent):
        """创建统计面板"""
        # 统计信息 - 纯统计功能
        stats_frame = ttk.LabelFrame(parent, text="统计信息")
        stats_frame.pack(fill=tk.X, pady=(0, 2))

        self.stats_label = ttk.Label(stats_frame, text="统计: 未标注 0, 阴性 0, 弱生长 0, 阳性 0")
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

    # === 委托方法：将UI事件委托给相应的功能模块 ===
    
    def _on_select_directory(self):
        """委托给数据操作模块：选择目录"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.select_panoramic_directory()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

    def _on_load_annotations(self):
        """委托给数据操作模块：加载标注"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.load_annotations()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

    def _on_save_annotations(self):
        """委托给数据操作模块：保存标注"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.save_annotations()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

    def import_model_suggestions(self):
        """委托给数据操作模块：导入模型建议"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.import_model_suggestions()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

    def export_training_data(self):
        """委托给数据操作模块：导出训练数据"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.export_training_data()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

