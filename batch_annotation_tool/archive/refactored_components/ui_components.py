"""
UI组件工厂模块
创建和管理界面组件
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional


class UIComponents:
    """UI组件工厂"""
    
    def __init__(self, gui_instance):
        """初始化UI组件工厂"""
        self.gui = gui_instance
    
    def create_main_layout(self):
        """创建主界面布局"""
        # 主框架
        main_frame = ttk.Frame(self.gui.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建工具栏
        self.create_toolbar(main_frame)
        
        # 创建主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 左侧面板（控制面板）
        left_panel = ttk.Frame(content_frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # 右侧面板（图像显示）
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建左侧控制面板
        self.create_control_panels(left_panel)
        
        # 创建右侧图像显示区域
        self.create_image_display_area(right_panel)
        
        # 创建状态栏
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 文件操作按钮
        file_frame = ttk.LabelFrame(toolbar_frame, text="文件操作")
        file_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(file_frame, text="选择全景图目录", 
                  command=self.select_panoramic_directory).pack(side=tk.LEFT, padx=2, pady=2)
        # 注释掉切片目录选择按钮，因为现在自动使用全景文件名对应的文件夹
        # ttk.Button(file_frame, text="选择切片目录", 
        #           command=self.select_slice_directory).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(file_frame, text="加载数据", 
                  command=self.gui.load_data).pack(side=tk.LEFT, padx=2, pady=2)
        
        # 数据操作按钮
        data_frame = ttk.LabelFrame(toolbar_frame, text="数据操作")
        data_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(data_frame, text="保存数据集", 
                  command=self.gui.save_dataset).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(data_frame, text="加载数据集", 
                  command=self.gui.load_dataset).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(data_frame, text="导出标注", 
                  command=self.gui.export_annotations).pack(side=tk.LEFT, padx=2, pady=2)
        
        # 模式选项
        options_frame = ttk.LabelFrame(toolbar_frame, text="模式选项")
        options_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        # 子目录模式
        self.gui.use_subdirectory_mode = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="子目录模式", 
                       variable=self.gui.use_subdirectory_mode,
                       command=self.gui.event_handlers.on_subdirectory_mode_toggle if hasattr(self.gui, 'event_handlers') else None).pack(side=tk.LEFT, padx=2)
        
        # 居中导航
        self.gui.use_centered_navigation = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="居中导航", 
                       variable=self.gui.use_centered_navigation,
                       command=self.gui.event_handlers.on_centered_navigation_toggle if hasattr(self.gui, 'event_handlers') else None).pack(side=tk.LEFT, padx=2)
        
        # 自动保存
        ttk.Checkbutton(options_frame, text="自动保存", 
                       variable=self.gui.auto_save_enabled,
                       command=self.gui.event_handlers.on_auto_save_toggle if hasattr(self.gui, 'event_handlers') else None).pack(side=tk.LEFT, padx=2)
    
    def create_control_panels(self, parent):
        """创建左侧控制面板"""
        # 导航控制面板
        self.create_navigation_panel(parent)
        
        # 标注控制面板
        self.create_annotation_panel(parent)
        
        # 批量操作面板
        self.create_batch_panel(parent)
    
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
                  command=self.gui.navigation_controller.go_prev_panoramic if hasattr(self.gui, 'navigation_controller') else None).pack(side=tk.LEFT, padx=2)
        
        # 全景图下拉列表
        self.gui.panoramic_id_var = tk.StringVar()
        self.gui.panoramic_combobox = ttk.Combobox(panoramic_frame, 
                                                  textvariable=self.gui.panoramic_id_var,
                                                  width=20)
        self.gui.panoramic_combobox.pack(side=tk.LEFT, padx=5)
        self.gui.panoramic_combobox.bind('<<ComboboxSelected>>', 
                                        self.gui.navigation_controller.on_panoramic_selected if hasattr(self.gui, 'navigation_controller') else None)
        
        # 下一个全景图按钮
        ttk.Button(panoramic_frame, text="下一全景 ▶", width=10,
                  command=self.gui.navigation_controller.go_next_panoramic if hasattr(self.gui, 'navigation_controller') else None).pack(side=tk.LEFT, padx=2)
        
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
                  command=self.gui.navigation_controller.go_up if hasattr(self.gui, 'navigation_controller') else None).grid(row=0, column=1, padx=1, pady=1)
        
        # 左方向按钮、孔位输入框、右方向按钮
        ttk.Button(direction_frame, text="←", width=4,
                  command=self.gui.navigation_controller.go_left if hasattr(self.gui, 'navigation_controller') else None).grid(row=1, column=0, padx=1, pady=1)
        
        # 孔位输入框放在中间位置
        entry_frame = ttk.Frame(direction_frame)
        entry_frame.grid(row=1, column=1, padx=1, pady=1)
        
        self.gui.hole_number_var = tk.StringVar(value="1")
        hole_entry = ttk.Entry(entry_frame, textvariable=self.gui.hole_number_var, width=8)
        hole_entry.pack(padx=2, pady=2)
        hole_entry.bind('<Return>', self.gui.navigation_controller.go_to_hole if hasattr(self.gui, 'navigation_controller') else None)
        
        ttk.Button(direction_frame, text="→", width=4,
                  command=self.gui.navigation_controller.go_right if hasattr(self.gui, 'navigation_controller') else None).grid(row=1, column=2, padx=1, pady=1)
        
        # 下方向按钮
        ttk.Button(direction_frame, text="↓", width=4,
                  command=self.gui.navigation_controller.go_down if hasattr(self.gui, 'navigation_controller') else None).grid(row=2, column=1, padx=1, pady=1)
        
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
                  command=self.gui.navigation_controller.go_first_hole if hasattr(self.gui, 'navigation_controller') else None).pack(side=tk.LEFT, padx=2)
        ttk.Button(sequence_frame, text="◀ 上一个", width=8,
                  command=self.gui.navigation_controller.go_prev_hole if hasattr(self.gui, 'navigation_controller') else None).pack(side=tk.LEFT, padx=2)
        ttk.Button(sequence_frame, text="下一个 ▶", width=8,
                  command=self.gui.navigation_controller.go_next_hole if hasattr(self.gui, 'navigation_controller') else None).pack(side=tk.LEFT, padx=2)
        ttk.Button(sequence_frame, text="最后 ▶▶", width=8,
                  command=self.gui.navigation_controller.go_last_hole if hasattr(self.gui, 'navigation_controller') else None).pack(side=tk.LEFT, padx=2)
        
        # 进度信息
        self.gui.progress_label = ttk.Label(nav_frame, text="0/0")
        self.gui.progress_label.pack(pady=2)
    
    def create_annotation_panel(self, parent):
        """创建标注控制面板"""
        annotation_frame = ttk.LabelFrame(parent, text="标注控制")
        annotation_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 微生物类型选择
        type_frame = ttk.Frame(annotation_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(type_frame, text="微生物类型:").pack(side=tk.LEFT)
        type_combo = ttk.Combobox(type_frame, textvariable=self.gui.current_microbe_type,
                                 values=["bacteria", "fungi"], width=15)
        type_combo.pack(side=tk.LEFT, padx=(5, 0))
        type_combo.bind('<<ComboboxSelected>>', 
                       self.gui.event_handlers.on_microbe_type_change if hasattr(self.gui, 'event_handlers') else None)
        
        # 生长级别选择
        growth_frame = ttk.Frame(annotation_frame)
        growth_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(growth_frame, text="生长级别:").pack(anchor=tk.W)
        
        growth_buttons_frame = ttk.Frame(growth_frame)
        growth_buttons_frame.pack(fill=tk.X, pady=2)
        
        ttk.Radiobutton(growth_buttons_frame, text="阴性 (1)", 
                       variable=self.gui.current_growth_level, value="negative",
                       command=self.gui.event_handlers.on_growth_level_change if hasattr(self.gui, 'event_handlers') else None).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(growth_buttons_frame, text="弱生长 (2)", 
                       variable=self.gui.current_growth_level, value="weak_growth",
                       command=self.gui.event_handlers.on_growth_level_change if hasattr(self.gui, 'event_handlers') else None).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(growth_buttons_frame, text="阳性 (3)", 
                       variable=self.gui.current_growth_level, value="positive",
                       command=self.gui.event_handlers.on_growth_level_change if hasattr(self.gui, 'event_handlers') else None).pack(side=tk.LEFT, padx=2)
        
        # 操作按钮
        action_frame = ttk.Frame(annotation_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(action_frame, text="保存标注 (空格)", 
                  command=self.gui.annotation_manager.save_current_annotation if hasattr(self.gui, 'annotation_manager') else None).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="跳过 (ESC)", 
                  command=self.gui.annotation_manager.skip_current if hasattr(self.gui, 'annotation_manager') else None).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="清除 (Del)", 
                  command=self.gui.annotation_manager.clear_current_annotation if hasattr(self.gui, 'annotation_manager') else None).pack(side=tk.LEFT, padx=2)
        
        # 增强标注面板容器
        self.gui.enhanced_annotation_frame = ttk.Frame(annotation_frame)
        self.gui.enhanced_annotation_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 基础标注面板容器（向后兼容）
        self.gui.basic_annotation_frame = ttk.Frame(annotation_frame)
        
        # 状态显示
        self.gui.annotation_status_label = ttk.Label(annotation_frame, text="状态: 未标注")
        self.gui.annotation_status_label.pack(pady=2)
    
    def create_batch_panel(self, parent):
        """创建批量操作面板"""
        batch_frame = ttk.LabelFrame(parent, text="批量操作")
        batch_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 统计信息
        stats_frame = ttk.Frame(batch_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.gui.stats_label = ttk.Label(stats_frame, text="统计: 未标注 0, 阴性 0, 弱生长 0, 阳性 0")
        self.gui.stats_label.pack()
        
        # 批量操作按钮
        batch_buttons_frame = ttk.Frame(batch_frame)
        batch_buttons_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(batch_buttons_frame, text="标注整行为阴性", 
                  command=self.gui.annotation_manager.batch_annotate_row_negative if hasattr(self.gui, 'annotation_manager') else None).pack(side=tk.LEFT, padx=2)
        ttk.Button(batch_buttons_frame, text="标注整列为阴性", 
                  command=self.gui.annotation_manager.batch_annotate_col_negative if hasattr(self.gui, 'annotation_manager') else None).pack(side=tk.LEFT, padx=2)
    
    def create_image_display_area(self, parent):
        """创建图像显示区域"""
        # 创建分割面板
        paned_window = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 全景图显示区域
        panoramic_frame = ttk.LabelFrame(paned_window, text="全景图")
        paned_window.add(panoramic_frame, weight=2)
        
        self.gui.panoramic_canvas = tk.Canvas(panoramic_frame, bg='white')
        self.gui.panoramic_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 切片图显示区域
        slice_frame = ttk.LabelFrame(paned_window, text="当前切片")
        paned_window.add(slice_frame, weight=1)
        
        self.gui.slice_canvas = tk.Canvas(slice_frame, bg='white')
        self.gui.slice_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.gui.status_label = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN)
        self.gui.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def select_slice_directory(self):
        """选择切片目录"""
        directory = filedialog.askdirectory(title="选择切片图像目录")
        if directory:
            self.gui.slice_dir_var.set(directory)
            self.gui.slice_directory = directory
    
    def select_panoramic_directory(self):
        """选择全景图目录"""
        directory = filedialog.askdirectory(title="选择全景图目录")
        if directory:
            self.gui.panoramic_dir_var.set(directory)
            self.gui.panoramic_directory = directory
            
            # 功能1：自动设置切片目录为全景文件名对应的文件夹
            # 这里暂时设置为全景目录，具体逻辑在加载数据时处理
            if hasattr(self.gui, 'slice_dir_var'):
                self.gui.slice_dir_var.set(directory)
            self.gui.slice_directory = directory
            
            # 启用子目录模式和居中导航
            if hasattr(self.gui, 'use_subdirectory_mode'):
                self.gui.use_subdirectory_mode.set(True)
            if hasattr(self.gui, 'use_centered_navigation'):
                self.gui.use_centered_navigation.set(True)
