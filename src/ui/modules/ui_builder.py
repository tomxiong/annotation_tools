"""
UI组件创建、布局管理、样式设置模块
负责所有用户界面组件的创建和布局管理
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont
from typing import Dict, Any, Optional


class UIBuilder:
    """UI构建器 - 负责界面组件创建和布局管理"""
    
    def __init__(self, parent_gui):
        """
        初始化UI构建器
        
        Args:
            parent_gui: 主GUI实例
        """
        self.gui = parent_gui
        self.root = parent_gui.root
        self.components = {}
        
    def create_main_layout(self):
        """创建主布局结构"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建顶部工具栏
        self.create_toolbar()
        
        # 创建主内容区域（水平布局：左侧全景图 + 分隔符 + 右侧切片控制）
        self.create_content_area()
        
        # 创建底部状态栏
        self.create_status_bar()
        
        return self.main_frame
    
    def create_toolbar(self):
        """创建工具栏"""
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 全景图目录选择
        ttk.Label(self.toolbar_frame, text="全景图:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.panoramic_dir_var = tk.StringVar()
        panoramic_dir_entry = ttk.Entry(self.toolbar_frame, textvariable=self.panoramic_dir_var, width=45)
        panoramic_dir_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 功能按钮
        ttk.Button(self.toolbar_frame, text="浏览并加载",
                  command=self.gui.open_directory).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(self.toolbar_frame, text="加载标注",
                  command=self.gui.load_annotations).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(self.toolbar_frame, text="保存标注", 
                  command=self.gui.save_current_annotation).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(self.toolbar_frame, text="导入模型建议",
                  command=self.gui.import_model_suggestions).pack(side=tk.LEFT, padx=(0, 10))
        
        # 调试日志开关
        self.debug_logging_enabled = tk.BooleanVar()
        ttk.Checkbutton(self.toolbar_frame, text="调试日志",
                       variable=self.debug_logging_enabled,
                       command=self.gui.toggle_debug_logging).pack(side=tk.LEFT, padx=(0, 5))
        
    def create_content_area(self):
        """创建主内容区域"""
        # 中间内容区域
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 左侧全景图区域
        self.create_panoramic_panel()
        
        # 中间分隔符
        separator = ttk.Separator(self.content_frame, orient='vertical')
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 右侧切片和控制区域
        self.create_slice_panel()
        
    def create_panoramic_panel(self):
        """创建全景图显示面板"""
        # 全景图面板
        self.panoramic_frame = ttk.LabelFrame(self.content_frame, text="全景图 (12×10孔位布局)")
        self.panoramic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 全景图显示区域
        self.panoramic_canvas = tk.Canvas(self.panoramic_frame, bg='white')
        self.panoramic_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 全景图信息
        info_frame = ttk.Frame(self.panoramic_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.panoramic_info_label = ttk.Label(info_frame, text="未加载全景图")
        self.panoramic_info_label.pack(side=tk.LEFT)
        
    def create_slice_panel(self):
        """创建切片显示和控制面板"""
        # 右侧标注操作面板
        self.right_frame = ttk.Frame(self.content_frame, width=360)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.right_frame.pack_propagate(False)  # 固定宽度
        
        # 统计面板
        self.create_stats_panel()
        
        # 导航控制面板
        self.create_navigation_panel()
        
        # 切片显示区域
        self.create_slice_display()
        
        # 标注控制面板
        self.create_annotation_panel()
        
    def create_stats_panel(self):
        """创建统计面板"""
        stats_frame = ttk.LabelFrame(self.right_frame, text="统计信息")
        stats_frame.pack(fill=tk.X, pady=(0, 2))
        
        # 总体统计 - 匹配原始格式
        self.stats_label = ttk.Label(stats_frame, text="统计: 未标注 0, 阴性 0, 弱生长 0, 阳性 0")
        self.stats_label.pack(padx=5, pady=3)
        
        # 视图模式选择区域
        self.create_view_mode_panel()
    
    def create_view_mode_panel(self):
        """创建视图模式选择面板"""
        view_frame = ttk.LabelFrame(self.right_frame, text="视图模式")
        view_frame.pack(fill=tk.X, pady=(2, 2))

        # 视图模式单选按钮 - 只保留人工和模型
        mode_frame = ttk.Frame(view_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)

        self.view_mode_var = tk.StringVar(value="manual")
        self.manual_radio = ttk.Radiobutton(mode_frame, text="人工", variable=self.view_mode_var,
                                          value="manual", command=self.gui.on_view_mode_changed)
        self.manual_radio.pack(side=tk.LEFT, padx=5)

        self.model_radio = ttk.Radiobutton(mode_frame, text="模型", variable=self.view_mode_var,
                                          value="model", command=self.gui.on_view_mode_changed)
        self.model_radio.pack(side=tk.LEFT, padx=5)
        
    def create_navigation_panel(self):
        """创建导航控制面板"""
        nav_frame = ttk.LabelFrame(self.right_frame, text="导航控制 (快捷键)")
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 第一行：全景图导航
        top_frame = ttk.Frame(nav_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=3)
        
        ttk.Label(top_frame, text="全景图:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(top_frame, text="◀", width=3,
                  command=self.gui.go_prev_panoramic).pack(side=tk.LEFT, padx=1)
        
        self.panoramic_id_var = tk.StringVar()
        self.panoramic_combo = ttk.Combobox(top_frame, 
                                          textvariable=self.panoramic_id_var,
                                          width=12, state="readonly")
        self.panoramic_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(top_frame, text="▶", width=3,
                  command=self.gui.go_next_panoramic).pack(side=tk.LEFT, padx=1)
        
        # 第二行：孔位导航
        bottom_frame = ttk.Frame(nav_frame)
        bottom_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # 孔位跳转（左侧）
        hole_frame = ttk.Frame(bottom_frame)
        hole_frame.pack(side=tk.LEFT)
        
        ttk.Label(hole_frame, text="跳转:").pack(side=tk.LEFT, padx=(0, 2))
        
        self.hole_number_var = tk.StringVar(value="1")
        hole_entry = ttk.Entry(hole_frame, textvariable=self.hole_number_var, width=4)
        hole_entry.pack(side=tk.LEFT, padx=1)
        
        # 序列导航（右侧）
        seq_frame = ttk.Frame(bottom_frame)
        seq_frame.pack(side=tk.RIGHT)
        
        ttk.Button(seq_frame, text="◀◀", width=4,
                  command=self.gui.go_first_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="◀", width=4,
                  command=self.gui.go_prev_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="▶", width=4,
                  command=self.gui.go_next_hole).pack(side=tk.LEFT, padx=1)
        ttk.Button(seq_frame, text="▶▶", width=4,
                  command=self.gui.go_last_hole).pack(side=tk.LEFT, padx=1)
        
        # 进度信息（居中）
        self.progress_label = ttk.Label(bottom_frame, text="0/0")
        self.progress_label.pack(side=tk.LEFT, expand=True)
        
        # 提示信息
        click_label = ttk.Label(nav_frame, text="提示: 点击全景图跳转对应孔位", 
                               font=('TkDefaultFont', 8))
        click_label.pack(side=tk.BOTTOM, padx=5, pady=(0, 3))
        
    def create_slice_display(self):
        """创建切片显示区域"""
        # 切片显示框架
        slice_frame = ttk.LabelFrame(self.right_frame, text="当前切片")
        slice_frame.pack(fill=tk.X, padx=(0, 0), pady=(0, 5))
        
        # 切片画布
        self.slice_canvas = tk.Canvas(slice_frame, bg='white', width=150, height=150)
        self.slice_canvas.pack(padx=5, pady=3)
        
        # 切片信息区域
        info_frame = ttk.Frame(slice_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 3))
        
        # 切片信息标签
        slice_info_font = ('TkDefaultFont', 8)
        self.slice_info_label = ttk.Label(info_frame, text="未加载切片", font=slice_info_font)
        self.slice_info_label.pack(fill=tk.X, pady=(0, 2))
        
        # 标注预览区域
        annotation_preview_font = ('TkDefaultFont', 8, 'bold')
        self.annotation_preview_label = ttk.Label(info_frame, text="标注状态: 未标注",
                                                font=annotation_preview_font)
        self.annotation_preview_label.pack(fill=tk.X, pady=(0, 2))
        
        # 详细标注信息预览区域
        detailed_annotation_font = ('TkDefaultFont', 8)
        self.detailed_annotation_label = ttk.Label(info_frame, text="",
                                                  font=detailed_annotation_font)
        self.detailed_annotation_label.pack(fill=tk.X, pady=(0, 2))
        
    def create_annotation_panel(self):
        """创建标注控制面板"""
        ann_frame = ttk.LabelFrame(self.right_frame, text="标注控制")
        ann_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        # 创建增强标注面板
        try:
            from src.ui.enhanced_annotation_panel import EnhancedAnnotationPanel
            
            # 创建增强标注面板 - 减少边距，不扩展
            self.enhanced_annotation_frame = ttk.Frame(ann_frame)
            self.enhanced_annotation_frame.pack(fill=tk.X, padx=3, pady=(3, 3))
            
            # 初始化enhanced annotation panel
            self.enhanced_annotation_panel = EnhancedAnnotationPanel(
                self.enhanced_annotation_frame,
                on_annotation_change=self.gui.on_enhanced_annotation_change
            )
        except ImportError:
            # 如果增强标注面板不可用，使用基础标注面板
            self.create_basic_annotation_controls(ann_frame)
        
        # 标注按钮 - 移到增强标注面板下方
        self.button_frame = ttk.Frame(ann_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=(3, 3))
        
        # 保存按钮引用以便控制状态
        self.save_button = ttk.Button(self.button_frame, text="保存并下一个", 
                  command=self.gui.save_current_annotation)
        self.save_button.pack(side=tk.LEFT, padx=2)
        
        self.skip_button = ttk.Button(self.button_frame, text="跳过", 
                  command=self.gui.skip_current)
        self.skip_button.pack(side=tk.LEFT, padx=2)
        
        self.clear_button = ttk.Button(self.button_frame, text="清除标注", 
                  command=self.gui.clear_current_annotation)
        self.clear_button.pack(side=tk.LEFT, padx=2)
    
    def create_basic_annotation_controls(self, parent):
        """创建基础标注控件（后备方案）"""
        # 微生物类型
        microbe_frame = ttk.Frame(parent)
        microbe_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(microbe_frame, text="微生物类型:").pack(side=tk.LEFT)
        
        self.microbe_type_var = tk.StringVar(value="bacteria")
        ttk.Radiobutton(microbe_frame, text="细菌", variable=self.microbe_type_var, 
                       value="bacteria").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(microbe_frame, text="真菌", variable=self.microbe_type_var, 
                       value="fungi").pack(side=tk.LEFT, padx=5)
        
        # 生长级别
        growth_frame = ttk.Frame(parent)
        growth_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(growth_frame, text="生长级别:").pack(anchor=tk.W)
        
        growth_buttons_frame = ttk.Frame(growth_frame)
        growth_buttons_frame.pack(fill=tk.X, pady=2)
        
        self.growth_level_var = tk.StringVar(value="negative")
        ttk.Radiobutton(growth_buttons_frame, text="阴性", variable=self.growth_level_var, 
                       value="negative").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(growth_buttons_frame, text="弱生长", variable=self.growth_level_var, 
                       value="weak_growth").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(growth_buttons_frame, text="阳性", variable=self.growth_level_var, 
                       value="positive").pack(side=tk.LEFT, padx=5)
        
        # 干扰因素
        interference_frame = ttk.Frame(parent)
        interference_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(interference_frame, text="干扰因素:").pack(anchor=tk.W)
        
        factors_frame = ttk.Frame(interference_frame)
        factors_frame.pack(fill=tk.X, pady=2)
        
        # 干扰因素复选框
        self.interference_factors = {
            'pores': tk.BooleanVar(),
            'artifacts': tk.BooleanVar(), 
            'edge_blur': tk.BooleanVar()
        }
        
        ttk.Checkbutton(factors_frame, text="气孔", 
                       variable=self.interference_factors['pores']).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(factors_frame, text="杂质", 
                       variable=self.interference_factors['artifacts']).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(factors_frame, text="边缘模糊", 
                       variable=self.interference_factors['edge_blur']).pack(side=tk.LEFT, padx=5)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X)
        
        # 状态标签
        self.status_label = ttk.Label(
            self.status_frame,
            text="准备就绪",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 版本信息
        try:
            from src.utils.version import get_version_display
            version_text = get_version_display()
        except ImportError:
            version_text = "v1.0.0"
            
        self.version_label = ttk.Label(
            self.status_frame,
            text=version_text,
            relief=tk.SUNKEN
        )
        self.version_label.pack(side=tk.RIGHT)
        
    def update_status(self, message: str):
        """更新状态栏消息"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
            
    def update_info_display(self, panoramic_id: str, hole_number: int, status: str):
        """更新信息显示"""
        info_text = f"全景ID: {panoramic_id} | 孔位: {hole_number} | 状态: {status}"
        if hasattr(self, 'info_label'):
            self.info_label.config(text=info_text)
            
    def update_stats_display(self, annotated: int, total: int):
        """更新统计显示"""
        progress = int((annotated / total * 100)) if total > 0 else 0
        stats_text = f"已标注: {annotated} | 总数: {total} | 进度: {progress}%"
        if hasattr(self, 'stats_label'):
            self.stats_label.config(text=stats_text)
            
    def get_component(self, name: str):
        """获取UI组件"""
        return self.components.get(name)
        
    def set_component_state(self, component_name: str, state: str):
        """设置组件状态"""
        component = self.get_component(component_name)
        if component and hasattr(component, 'config'):
            component.config(state=state)
