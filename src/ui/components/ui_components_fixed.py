"""
UI组件模块
负责创建和管理所有界面组件
从原panoramic_annotation_gui.py中拆分出来
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont


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
        
    def create_widgets(self):
        """创建界面组件"""
        try:
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

            # 底部状态栏
            self.create_status_bar(main_frame)
            
            self.gui.log_info("UI组件创建完成", "UI")
            
        except Exception as e:
            self.gui.log_error(f"UI组件创建失败: {e}", "UI")
            raise

    def create_toolbar(self, parent):
        """创建顶部工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))

        # 目录选择
        ttk.Label(toolbar_frame, text="全景图目录:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 创建一个变量来存储目录路径（如果不存在的话）
        if not hasattr(self.gui, 'panoramic_dir_var'):
            self.gui.panoramic_dir_var = tk.StringVar()
        
        dir_entry = ttk.Entry(toolbar_frame, textvariable=self.gui.panoramic_dir_var, width=50)
        dir_entry.pack(side=tk.LEFT, padx=(0, 5))

        # 浏览按钮
        browse_btn = ttk.Button(toolbar_frame, text="浏览...", 
                               command=self._on_browse_directory)
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 操作按钮
        load_btn = ttk.Button(toolbar_frame, text="加载数据", 
                             command=self._on_load_data)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))

        save_btn = ttk.Button(toolbar_frame, text="保存标注", 
                             command=self._on_save_annotations)
        save_btn.pack(side=tk.LEFT, padx=(0, 5))

    def create_panoramic_panel(self, parent):
        """创建全景图显示面板"""
        # 左侧全景图区域
        panoramic_frame = ttk.LabelFrame(parent, text="全景图像", padding=5)
        panoramic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 全景图显示区域
        panoramic_canvas = tk.Canvas(panoramic_frame, bg='white', width=800, height=600)
        panoramic_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 存储到GUI实例中供后续使用
        self.gui.panoramic_canvas = panoramic_canvas

    def create_slice_panel(self, parent):
        """创建切片显示和控制面板"""
        # 右侧区域
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        # 切片显示区域
        slice_frame = ttk.LabelFrame(right_frame, text="切片图像", padding=5)
        slice_frame.pack(fill=tk.BOTH, expand=True)

        # 切片显示画布
        slice_canvas = tk.Canvas(slice_frame, bg='white', width=400, height=400)
        slice_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 存储到GUI实例中
        self.gui.slice_canvas = slice_canvas

        # 控制面板
        self.create_controls_panel(right_frame)

    def create_controls_panel(self, parent):
        """创建控制面板"""
        controls_frame = ttk.LabelFrame(parent, text="控制面板", padding=5)
        controls_frame.pack(fill=tk.X, pady=(5, 0))

        # 微生物类型选择
        type_frame = ttk.Frame(controls_frame)
        type_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(type_frame, text="微生物类型:").pack(side=tk.LEFT)
        
        # 确保微生物类型变量存在
        if not hasattr(self.gui, 'current_microbe_type'):
            self.gui.current_microbe_type = tk.StringVar(value="bacteria")
            
        type_combo = ttk.Combobox(type_frame, textvariable=self.gui.current_microbe_type,
                                 values=["bacteria", "fungi"], state="readonly", width=15)
        type_combo.pack(side=tk.LEFT, padx=(5, 0))

        # 导航按钮
        nav_frame = ttk.Frame(controls_frame)
        nav_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(nav_frame, text="上一张", command=self._on_previous).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(nav_frame, text="下一张", command=self._on_next).pack(side=tk.LEFT)

        # 当前位置显示
        if not hasattr(self.gui, 'position_var'):
            self.gui.position_var = tk.StringVar(value="0 / 0")
            
        position_label = ttk.Label(nav_frame, textvariable=self.gui.position_var)
        position_label.pack(side=tk.RIGHT)

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        # 状态标签
        if not hasattr(self.gui, 'status_var'):
            self.gui.status_var = tk.StringVar(value="就绪")
            
        status_label = ttk.Label(status_frame, textvariable=self.gui.status_var, relief=tk.SUNKEN)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 版本信息
        try:
            version_text = "v1.2.0.0 (重构版)"
        except:
            version_text = "v1.2.0.0"
            
        version_label = ttk.Label(status_frame, text=version_text, relief=tk.SUNKEN)
        version_label.pack(side=tk.RIGHT, padx=(5, 0))

    # === 事件处理方法 (占位符) ===
    
    def _on_browse_directory(self):
        """浏览目录按钮事件"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.select_panoramic_directory()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

    def _on_load_data(self):
        """加载数据按钮事件"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.load_panoramic_data()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

    def _on_save_annotations(self):
        """保存标注按钮事件"""
        if hasattr(self.gui, 'data_operations'):
            self.gui.data_operations.save_annotations()
        else:
            self.gui.log_warning("数据操作模块未初始化", "UI")

    def _on_previous(self):
        """上一张按钮事件"""
        self.gui.log_info("上一张图像", "UI")
        # TODO: 实现导航逻辑

    def _on_next(self):
        """下一张按钮事件"""
        self.gui.log_info("下一张图像", "UI")
        # TODO: 实现导航逻辑
