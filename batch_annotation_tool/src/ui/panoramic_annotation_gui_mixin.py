"""
全景图标注GUI - Mixin重构版本
保持原有界面布局和功能不变，仅重构代码结构
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from PIL import Image, ImageTk

# 导入所有Mixin类
from .mixins.navigation_mixin import NavigationMixin
from .mixins.annotation_mixin import AnnotationMixin
from .mixins.image_mixin import ImageMixin
from .mixins.event_mixin import EventMixin
from .mixins.ui_mixin import UIMixin

# 导入其他必要的类
from .hole_manager import HoleManager
from .enhanced_annotation_panel import EnhancedAnnotationPanel

# 修复相对导入问题
try:
    from ..services.config_file_service import ConfigFileService
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from services.config_file_service import ConfigFileService


class PanoramicAnnotationGUI(NavigationMixin, AnnotationMixin, ImageMixin, EventMixin, UIMixin):
    """全景图标注GUI主类 - 使用Mixin重构"""
    
    def __init__(self, root):
        """初始化GUI"""
        self.root = root
        self.root.title("全景图标注工具")
        self.root.geometry("1400x900")
        
        # 初始化变量
        self.slice_files = []
        self.current_slice_index = 0
        self.current_panoramic_id = None
        self.panoramic_ids = []
        self.slice_directory = None
        self.current_image = None
        self.scale_factor = 1.0
        
        # 初始化服务
        self.config_service = ConfigFileService()
        self.hole_manager = HoleManager()
        
        # 初始化选项变量
        self.use_subdirectory_mode = tk.BooleanVar(value=True)
        self.use_centered_navigation = tk.BooleanVar(value=False)
        
        # 创建UI
        self.create_ui()
        
        # 设置事件绑定
        self.setup_event_bindings()
        
        # 加载窗口状态
        self.load_window_state()
    
    def create_ui(self):
        """创建用户界面"""
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建主要内容区域
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 左侧：图像显示区域
        self.create_image_area(content_frame)
        
        # 右侧：控制面板
        self.create_control_panel(content_frame)
        
        # 底部：状态栏
        self.create_status_bar()
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # 目录选择按钮
        ttk.Button(toolbar, text="选择目录", command=self.load_slice_directory).pack(side=tk.LEFT, padx=2)
        
        # 分隔符
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 导航按钮
        ttk.Button(toolbar, text="首个", command=self.go_first_hole).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="上一个", command=self.go_prev_hole).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="下一个", command=self.go_next_hole).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="末个", command=self.go_last_hole).pack(side=tk.LEFT, padx=2)
        
        # 分隔符
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 保存按钮
        ttk.Button(toolbar, text="保存标注", command=self.save_current_annotation).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空标注", command=self.clear_current_annotation).pack(side=tk.LEFT, padx=2)
        
        # 分隔符
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 选项复选框
        ttk.Checkbutton(toolbar, text="子目录模式", variable=self.use_subdirectory_mode).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(toolbar, text="居中导航", variable=self.use_centered_navigation).pack(side=tk.LEFT, padx=5)
    
    def create_image_area(self, parent):
        """创建图像显示区域"""
        # 左侧框架
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 信息标签
        self.info_label = ttk.Label(left_frame, text="请选择切片目录", font=("Arial", 10))
        self.info_label.pack(pady=5)
        
        # 图像画布
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定画布事件
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        # 右侧控制面板
        self.control_frame = ttk.Frame(parent, width=350)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.control_frame.pack_propagate(False)
        
        # 全景图导航面板
        self.create_panoramic_navigation_panel()
        
        # 切片导航面板
        self.create_navigation_panel()
        
        # 标注面板
        self.create_annotation_panel()
    
    def create_panoramic_navigation_panel(self):
        """创建全景图导航面板"""
        pano_frame = ttk.LabelFrame(self.control_frame, text="全景图导航", padding=5)
        pano_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 全景图导航按钮和下拉列表
        nav_frame = ttk.Frame(pano_frame)
        nav_frame.pack(fill=tk.X)
        
        # 上一个全景图按钮
        ttk.Button(nav_frame, text="◀", command=self.go_prev_panoramic, width=3).pack(side=tk.LEFT, padx=2)
        
        # 全景图下拉列表
        self.panoramic_id_var = tk.StringVar()
        self.panoramic_combobox = ttk.Combobox(nav_frame, textvariable=self.panoramic_id_var, 
                                             state="readonly", width=20)
        self.panoramic_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.panoramic_combobox.bind('<<ComboboxSelected>>', self.on_panoramic_selected)
        
        # 下一个全景图按钮
        ttk.Button(nav_frame, text="▶", command=self.go_next_panoramic, width=3).pack(side=tk.RIGHT, padx=2)
    
    def create_navigation_panel(self):
        """创建导航面板"""
        nav_frame = ttk.LabelFrame(self.control_frame, text="切片导航", padding=5)
        nav_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 3x3网格布局的方向按钮
        grid_frame = ttk.Frame(nav_frame)
        grid_frame.pack(pady=5)
        
        # 第一行：空 上 空
        ttk.Label(grid_frame, text="").grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(grid_frame, text="↑", command=self.go_up, width=3).grid(row=0, column=1, padx=2, pady=2)
        ttk.Label(grid_frame, text="").grid(row=0, column=2, padx=2, pady=2)
        
        # 第二行：左 孔位输入 右
        ttk.Button(grid_frame, text="←", command=self.go_left, width=3).grid(row=1, column=0, padx=2, pady=2)
        
        # 孔位输入框
        hole_frame = ttk.Frame(grid_frame)
        hole_frame.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(hole_frame, text="孔位:").pack(side=tk.TOP)
        self.hole_entry = ttk.Entry(hole_frame, width=6, justify=tk.CENTER)
        self.hole_entry.pack(side=tk.TOP)
        self.hole_entry.bind('<Return>', lambda e: self.go_to_hole(self.hole_entry.get()))
        
        ttk.Button(grid_frame, text="→", command=self.go_right, width=3).grid(row=1, column=2, padx=2, pady=2)
        
        # 第三行：空 下 空
        ttk.Label(grid_frame, text="").grid(row=2, column=0, padx=2, pady=2)
        ttk.Button(grid_frame, text="↓", command=self.go_down, width=3).grid(row=2, column=1, padx=2, pady=2)
        ttk.Label(grid_frame, text="").grid(row=2, column=2, padx=2, pady=2)
        
        # 序列导航按钮
        seq_frame = ttk.Frame(nav_frame)
        seq_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(seq_frame, text="上一个", command=self.go_prev_hole).pack(side=tk.LEFT, padx=2)
        ttk.Button(seq_frame, text="下一个", command=self.go_next_hole).pack(side=tk.RIGHT, padx=2)
    
    def create_annotation_panel(self):
        """创建标注面板"""
        # 标注面板
        annotation_frame = ttk.LabelFrame(self.control_frame, text="标注信息", padding=5)
        annotation_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        self.annotation_panel = EnhancedAnnotationPanel(
            annotation_frame, 
            on_annotation_change=self.on_annotation_change
        )
        # EnhancedAnnotationPanel不是Tkinter组件，不需要pack
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_event_bindings(self):
        """设置事件绑定"""
        # 设置键盘快捷键
        self.setup_keyboard_bindings()
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # 绑定窗口大小改变事件
        self.root.bind("<Configure>", self.on_window_resize)
    
    def load_slice_directory(self):
        """加载切片目录"""
        if self.use_subdirectory_mode.get():
            # 子目录模式：只选择全景目录
            directory = filedialog.askdirectory(title="选择全景图目录")
            if directory:
                self.slice_directory = directory
                self.scan_slice_files()
        else:
            # 普通模式：选择切片目录
            directory = filedialog.askdirectory(title="选择切片目录")
            if directory:
                self.slice_directory = directory
                self.scan_slice_files()
    
    def scan_slice_files(self):
        """扫描切片文件"""
        if not self.slice_directory:
            return
        
        self.slice_files = []
        
        try:
            if self.use_subdirectory_mode.get():
                # 子目录模式：扫描全景目录下的子目录
                for panoramic_name in os.listdir(self.slice_directory):
                    panoramic_path = os.path.join(self.slice_directory, panoramic_name)
                    if os.path.isdir(panoramic_path):
                        # 扫描该全景图的切片文件
                        self.scan_panoramic_slices(panoramic_path, panoramic_name)
            else:
                # 普通模式：直接扫描切片目录
                self.scan_panoramic_slices(self.slice_directory, "default")
            
            # 排序文件列表
            self.slice_files.sort(key=lambda x: (x['panoramic_id'], x['hole_number']))
            
            # 更新全景图列表
            self.update_panoramic_list()
            
            # 加载第一个切片
            if self.slice_files:
                self.current_slice_index = 0
                self.load_current_slice()
                self.update_status(f"已加载 {len(self.slice_files)} 个切片文件")
            else:
                self.update_status("未找到切片文件")
                
        except Exception as e:
            messagebox.showerror("错误", f"扫描切片文件失败: {e}")
    
    def scan_panoramic_slices(self, directory, panoramic_id):
        """扫描指定目录下的切片文件"""
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                # 从文件名提取孔位编号
                hole_number = self.extract_hole_number(filename)
                if hole_number:
                    file_path = os.path.join(directory, filename)
                    self.slice_files.append({
                        'path': file_path,
                        'filename': filename,
                        'panoramic_id': panoramic_id,
                        'hole_number': hole_number
                    })
    
    def extract_hole_number(self, filename):
        """从文件名提取孔位编号"""
        import re
        # 查找文件名中的数字
        numbers = re.findall(r'\d+', filename)
        for num_str in numbers:
            num = int(num_str)
            if 1 <= num <= 120:  # 假设孔位编号在1-120之间
                return num
        return None
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_bar.config(text=message)


def main():
    """主函数"""
    root = tk.Tk()
    app = PanoramicAnnotationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()