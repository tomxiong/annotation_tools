"""
全景图像标注工具主界面 - 重构版本
基于原panoramic_annotation_gui.py创建，用于逐步分解重构
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
        log_debug_detail, log_ui_detail, log_timing
    )
except ImportError:
    # 如果日志模块不可用，使用文件日志作为后备
    import logging
    import os
    from pathlib import Path

# 版本管理导入
try:
    from src.utils.version import get_version_display
except ImportError:
    def get_version_display():
        return "v1.2.0.0"

    # 配置日志系统
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "annotation_tools.log"

    logging.basicConfig(
        filename=str(log_file),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器 - 完全禁用控制台输出，将所有日志重定向到文件
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.CRITICAL + 1)  # 设置为高于CRITICAL的级别，禁用所有控制台输出
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)

    # 获取根日志器并添加控制台处理器（但不输出任何内容）
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)

    def log_debug(msg, category=""):
        logging.debug(f"[{category}] {msg}" if category else msg)
    def log_info(msg, category=""):
        logging.info(f"[{category}] {msg}" if category else msg)
    def log_warning(msg, category=""):
        logging.warning(f"[{category}] {msg}" if category else msg)
    def log_error(msg, category=""):
        logging.error(f"[{category}] {msg}" if category else msg)

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
from src.ui.hole_config_panel import HoleConfigPanel
from src.ui.enhanced_annotation_panel import EnhancedAnnotationPanel
from src.services.panoramic_image_service import PanoramicImageService
from src.services.config_file_service import ConfigFileService
from src.models.panoramic_annotation import PanoramicAnnotation, PanoramicDataset
from src.models.enhanced_annotation import EnhancedPanoramicAnnotation, FeatureCombination
from src.models.enhanced_annotation import EnhancedPanoramicAnnotation
from src.ui.batch_import_dialog import show_batch_import_dialog

# 模型建议导入服务
try:
    from services.model_suggestion_import_service import ModelSuggestionImportService
except ImportError:
    # 如果模块不可用，使用占位符
    class ModelSuggestionImportService:
        def __init__(self):
            pass
        def load_from_json(self, path):
            return {}
        def merge_into_session(self, session, suggestions_map):
            pass


# 视图模式枚举
class ViewMode(Enum):
    MANUAL = "人工"
    MODEL = "模型"


# 此文件将被逐步拆分为以下模块：
# 1. ui_components.py - UI组件创建和布局
# 2. event_handlers.py - 事件处理逻辑
# 3. data_operations.py - 数据加载、保存、导入导出
# 4. slice_manager.py - 切片显示和导航管理
# 5. annotation_manager.py - 标注相关操作管理
# 6. dialog_managers.py - 对话框管理

# 为了便于逐步拆分，我们将在每次拆分时明确标记被拆分的内容
# 当前状态：完整副本，准备开始拆分

# UI组件模块导入
from .components.ui_components import UIComponents
from .components.event_handlers import EventHandlers
from .components.data_operations import DataOperations


class AnnotationToolsGUI:
    """
    全景图像标注工具主界面 - 重构版本
    此类将逐步分解为多个功能模块
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        # 设置窗口标题，标明这是重构版本
        self.root.title("全景图像标注工具 - 重构版 v1.2.0.0")
        # 设置优化的窗口大小，调整为1600x900
        self.root.geometry("1600x900")
        self.root.minsize(1400, 800)
        
        log_info("开始初始化AnnotationToolsGUI", "INIT")
        
        # 初始化所有属性和组件
        self._init_attributes()
        self._init_services()
        self._init_data_structures()
        self._init_performance_monitoring()
        
        # 创建界面（第一个要拆分的模块）
        self.create_widgets()
        self.setup_bindings()

        # 同步调试日志状态
        self.sync_debug_logging_state()

        # 状态栏
        self.update_status("就绪 - 请选择全景图目录 (重构版)")
        
        log_info("AnnotationToolsGUI初始化完成", "INIT")
    
    def _init_attributes(self):
        """初始化基本属性"""
        # 绑定日志方法到实例
        self.log_debug = log_debug
        self.log_info = log_info
        self.log_warning = log_warning
        self.log_error = log_error
        
        # 窗口尺寸跟踪
        self.window_resize_log = []
        self.initial_geometry = "1600x900"
        self.current_geometry = "1600x900"
        
        # 自动保存控制
        self.auto_save_enabled = tk.BooleanVar(value=True)
        self.last_annotation_time = {}
        self.current_annotation_modified = False

        # 操作状态控制
        self.is_saving = False
        self.save_button = None
        self.skip_button = None
        self.clear_button = None

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
        self.panoramic_ids = []
        self.panoramic_id_var = tk.StringVar()
        
        # Enhanced annotation panel
        self.enhanced_annotation_panel = None
        
        # 事件处理器（第二步拆分添加）
        self.event_handlers = None
        
        # 数据操作器（第三步拆分添加）
        self.data_operations = None
    
    def _init_services(self):
        """初始化服务和管理器"""
        self.image_service = PanoramicImageService()
        self.hole_manager = HoleManager()
        self.config_service = ConfigFileService()
        self.model_suggestion_service = ModelSuggestionImportService()
        
        # 模型建议相关属性
        self.current_suggestions_map = None
        self.model_suggestion_loaded = False
    
    def _init_data_structures(self):
        """初始化数据结构"""
        self.current_dataset = PanoramicDataset("新数据集", "全景图像标注数据集")
        self.slice_files: List[Dict[str, Any]] = []
        self.current_slice_index = 0
        self.current_panoramic_id = ""
        self.current_hole_number = 1
    
    def _init_performance_monitoring(self):
        """初始化性能监控"""
        # 高性能延迟配置
        self.delay_config = {
            'settings_apply': 30,
            'button_recovery': 150,
            'quick_recovery': 100,
            'ui_refresh': 50,
            'verification': 100
        }
        
        # 性能监控数据收集
        self.performance_stats = {
            'settings_apply_times': [],
            'ui_load_times': [],
            'button_response_times': [],
            'copy_settings_detailed': {
                'button_disable_times': [],
                'settings_collect_times': [],
                'navigation_times': [],
                'ui_refresh_times': [],
                'settings_apply_times': [],
                'button_enable_times': [],
                'total_copy_times': []
            },
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
        
        # 性能监控功能配置
        self.performance_monitoring_enabled = tk.BooleanVar(value=False)
    
    # === 占位方法 - 这些方法将在后续步骤中从原文件复制过来 ===
    
    def create_widgets(self):
        """创建界面组件 - 使用UI组件模块"""
        log_info("开始创建界面组件（使用UI组件模块）", "UI")
        
        # 初始化UI组件管理器
        self.ui_components = UIComponents(self)
        
        # 初始化数据操作管理器
        self.data_operations = DataOperations(self)
        
        # 调用UI组件创建方法
        try:
            self.ui_components.create_widgets()
            log_info("UI组件创建完成", "UI")
        except Exception as e:
            log_error(f"UI组件创建失败: {e}", "UI")
            # 回退到临时界面
            self._create_temporary_ui()
    
    def _create_temporary_ui(self):
        """创建临时界面用于测试"""
        log_info("开始创建界面组件", "UI")
        
        # 临时创建一个简单的界面来验证框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部标签
        title_label = ttk.Label(main_frame, 
                               text="全景图像标注工具 - 重构版本", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, 
                                     text="框架初始化完成，准备拆分UI模块",
                                     foreground="green")
        self.status_label.pack(pady=10)
        
        # 测试按钮
        test_button = ttk.Button(main_frame, 
                                text="测试框架", 
                                command=self.test_framework)
        test_button.pack(pady=10)
        
        log_info("临时界面创建完成", "UI")
    
    def setup_bindings(self):
        """设置事件绑定 - 使用事件处理模块"""
        log_info("开始设置事件绑定（使用事件处理模块）", "EVENT")
        
        # 初始化事件处理器
        if not self.event_handlers:
            self.event_handlers = EventHandlers(self)
        
        # 调用事件绑定方法
        try:
            self.event_handlers.setup_bindings()
            log_info("事件绑定设置完成", "EVENT")
        except Exception as e:
            log_error(f"事件绑定设置失败: {e}", "EVENT")
    
    def sync_debug_logging_state(self):
        """同步调试日志状态 - 待实现"""
        log_info("同步调试日志状态", "LOG")
        pass
    
    def update_status(self, message: str):
        """更新状态栏"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
        log_info(f"状态更新: {message}", "STATUS")
    
    def test_framework(self):
        """测试框架功能"""
        messagebox.showinfo("测试", "AnnotationToolsGUI框架运行正常！\n准备开始模块拆分。")
        log_info("框架测试通过", "TEST")
    
    # === 微生物类型判断方法（已实现） ===
    @staticmethod
    def determine_microbe_type_from_filename(panoramic_id: str) -> str:
        """根据全景图文件名前两位字符判断微生物类型"""
        if panoramic_id and len(panoramic_id) >= 2:
            prefix = panoramic_id[:2].upper()
            if prefix == "FG":
                return "fungi"
        return "bacteria"
    
    def get_default_microbe_type(self, panoramic_id: str = None) -> str:
        """获取默认的微生物类型"""
        if panoramic_id:
            return self.determine_microbe_type_from_filename(panoramic_id)
        return "bacteria"


def create_main_app():
    """创建主应用程序"""
    root = tk.Tk()
    app = AnnotationToolsGUI(root)
    return root, app


if __name__ == "__main__":
    log_info("启动全景标注工具GUI - 重构版", "MAIN")
    
    try:
        root, app = create_main_app()
        
        # 启动主循环
        log_info("开始GUI主循环", "MAIN")
        root.mainloop()
        
    except Exception as e:
        log_error(f"应用程序启动失败: {e}", "MAIN")
        if 'root' in locals():
            try:
                root.destroy()
            except:
                pass
        raise
