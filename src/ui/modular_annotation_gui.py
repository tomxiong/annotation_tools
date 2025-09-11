"""
全景图像标注工具主界面 - 模块化重构版本
按照正确的模块化设计重新组织
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any
import sys
import os
from pathlib import Path

# 添加src路径到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

# 导入模块
from src.ui.modules import (
    UIBuilder, EventDispatcher, DataManager, 
    SliceController, AnnotationAssistant, DialogFactory,
    AnnotationProcessor, ViewManager, ImageProcessor,
    NavigationController, StateManager
)

# 导入HoleManager
from src.ui.hole_manager import HoleManager

# 日志导入
try:
    from src.utils.logger import (
        enable_debug_logging,
        log_debug as _log_debug, 
        log_info as _log_info, 
        log_warning as _log_warning, 
        log_error as _log_error
    )
    # 启用详细调试日志
    enable_debug_logging(verbose=True)
    
    # 创建具体的日志函数
    def log_debug(msg, tag="DEBUG"): _log_debug(msg, tag)
    def log_info(msg, tag="INFO"): _log_info(msg, tag)
    def log_warning(msg, tag="WARNING"): _log_warning(msg, tag)
    def log_error(msg, tag="ERROR"): _log_error(msg, tag)
    def log_strategy(msg): log_info(msg, "STRATEGY")
    def log_perf(msg): log_info(msg, "PERF")
    def log_nav(msg): log_info(msg, "NAV")
    def log_ann(msg): log_info(msg, "ANN")
    def log_debug_detail(msg): log_debug(msg, "DETAIL")
    def log_ui_detail(msg): log_debug(msg, "UI")
    def log_timing(msg): log_debug(msg, "TIMING")
    
    print("日志系统初始化成功")
    
except ImportError as e:
    print(f"日志导入失败: {e}")
    # 日志后备方案
    import logging
    logging.basicConfig(level=logging.DEBUG, 
                       format='%(asctime)s [%(levelname)s] %(message)s')
    
    def log_debug(msg, tag="DEBUG"): logging.debug(f"[{tag}] {msg}")
    def log_info(msg, tag="INFO"): logging.info(f"[{tag}] {msg}")
    def log_warning(msg, tag="WARNING"): logging.warning(f"[{tag}] {msg}")
    def log_error(msg, tag="ERROR"): logging.error(f"[{tag}] {msg}")
    def log_strategy(msg): log_info(msg, "STRATEGY")
    def log_perf(msg): log_info(msg, "PERF")
    def log_nav(msg): log_info(msg, "NAV")
    def log_ann(msg): log_info(msg, "ANN")
    def log_debug_detail(msg): log_debug(msg, "DETAIL")
    def log_ui_detail(msg): log_debug(msg, "UI")
    def log_timing(msg): log_debug(msg, "TIMING")


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


class ModularAnnotationGUI:
    """模块化的全景图像标注工具主界面"""
    
    def __init__(self):
        """初始化主界面"""
        self.root = None
        self.is_initialized = False
        
        # 模块实例
        self.ui_builder = None
        self.event_dispatcher = None
        self.data_manager = None
        self.slice_controller = None
        self.annotation_assistant = None
        self.dialog_factory = None
        self.annotation_processor = None
        self.view_manager = None
        self.image_processor = None
        self.navigation_controller = None
        self.state_manager = None
        self.hole_manager = None
        
    def initialize(self):
        """初始化应用程序"""
        try:
            log_info("开始初始化模块化GUI应用程序", "INIT")
            
            # 创建主窗口
            self._create_main_window()
            
            # 初始化模块
            self._initialize_modules()
            
            # 设置模块间连接
            self._setup_module_connections()
            
            # 创建UI
            self._create_ui()
            
            # 设置事件绑定
            self._setup_events()
            
            self.is_initialized = True
            log_info("模块化GUI应用程序初始化完成", "INIT")
            
        except Exception as e:
            log_error(f"初始化失败: {e}", "INIT")
            raise
            
    def _create_main_window(self):
        """创建主窗口"""
        self.root = tk.Tk()
        self.root.title("全景图像标注工具 - 模块化版本")
        self.root.geometry("1600x900")
        self.root.minsize(1400, 800)
        
        # 设置窗口图标（如果有的话）
        try:
            # 可以在这里设置图标
            pass
        except Exception:
            pass
            
    def _initialize_modules(self):
        """初始化所有模块"""
        log_info("初始化模块...", "INIT")
        
        # 核心基础模块
        self.state_manager = StateManager(self)
        self.data_manager = DataManager(self)
        self.hole_manager = HoleManager()
        
        # UI和事件模块
        self.ui_builder = UIBuilder(self)
        self.event_dispatcher = EventDispatcher(self)
        
        # 业务逻辑模块
        self.image_processor = ImageProcessor(self)
        self.navigation_controller = NavigationController(self)
        self.annotation_processor = AnnotationProcessor(self)
        
        # 控制和辅助模块
        self.slice_controller = SliceController(self)
        self.annotation_assistant = AnnotationAssistant(self)
        self.view_manager = ViewManager(self)
        self.dialog_factory = DialogFactory(self)
        
        log_info("所有模块初始化完成", "INIT")
        
    def _setup_module_connections(self):
        """设置模块间连接"""
        log_info("设置模块间连接...", "INIT")
        
        # 设置状态管理器监听器
        if self.state_manager:
            # 监听数据集变化
            self.state_manager.add_state_listener('current_dataset_path', self._on_dataset_changed)
            # 监听切片变化
            self.state_manager.add_state_listener('current_slice_index', self._on_slice_changed)
            # 监听标注变化
            self.state_manager.add_state_listener('current_annotation_modified', self._on_annotation_changed)
        
        # 设置导航控制器与状态管理器的连接
        if self.navigation_controller and self.state_manager:
            # 导航变化时更新状态
            def on_navigation_change():
                nav_info = self.navigation_controller.get_navigation_info()
                self.state_manager.update_navigation_state(nav_info)
            
            # 这里可以设置导航变化的回调
        
        # 设置图像处理器与视图管理器的连接
        if self.image_processor and self.view_manager:
            # 图像加载完成后更新视图
            pass
        
        # 设置标注处理器与状态管理器的连接
        if self.annotation_processor and self.state_manager:
            # 标注处理完成后更新状态
            pass
        
        log_info("模块间连接设置完成", "INIT")
        
    def _create_ui(self):
        """创建用户界面"""
        log_info("创建用户界面...", "INIT")
        
        # 创建主布局
        self.ui_builder.create_main_layout()
        
        # 设置ViewManager的画布引用
        if hasattr(self.ui_builder, 'panoramic_canvas') and hasattr(self.ui_builder, 'slice_canvas'):
            self.view_manager.set_canvas_references(
                self.ui_builder.panoramic_canvas,
                self.ui_builder.slice_canvas
            )
            log_info("ViewManager画布引用设置完成", "INIT")
        else:
            log_error("画布未正确创建", "INIT")
        
        log_info("用户界面创建完成", "INIT")
        
    def _setup_events(self):
        """设置事件绑定"""
        log_info("设置事件绑定...", "INIT")
        
        # 设置键盘和鼠标事件
        self.event_dispatcher.setup_bindings()
        
        # 绑定画布事件
        if hasattr(self.ui_builder, 'panoramic_canvas'):
            self.event_dispatcher.bind_panoramic_click(self.ui_builder.panoramic_canvas)
            
        if hasattr(self.ui_builder, 'slice_canvas'):
            self.event_dispatcher.bind_slice_click(self.ui_builder.slice_canvas)
            
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        log_info("事件绑定设置完成", "INIT")
        
    def run(self):
        """运行应用程序"""
        if not self.is_initialized:
            self.initialize()
            
        log_info("启动GUI主循环", "MAIN")
        self.root.mainloop()
        
    def _on_closing(self):
        """窗口关闭处理"""
        try:
            # 检查是否有未保存的数据
            if self._has_unsaved_data():
                if not self.dialog_factory.show_confirmation_dialog(
                    "有未保存的标注数据，确定要退出吗？",
                    "确认退出"
                ):
                    return
                    
            # 保存设置和数据
            self._save_before_exit()
            
            log_info("应用程序正常退出", "MAIN")
            self.root.destroy()
            
        except Exception as e:
            log_error(f"退出时发生错误: {e}", "MAIN")
            self.root.destroy()
            
    def _has_unsaved_data(self) -> bool:
        """检查是否有未保存的数据"""
        # 这里可以检查是否有未确认的标注等
        return False
        
    def _save_before_exit(self):
        """退出前保存数据"""
        try:
            if self.data_manager:
                self.data_manager.save_annotations()
        except Exception as e:
            log_warning(f"退出前保存失败: {e}", "MAIN")
            
    # === 业务方法 - 由事件分发器调用 ===
    
    def open_directory(self):
        """打开目录"""
        try:
            log_info("开始浏览目录操作", "FILE")
            directory = self.dialog_factory.show_directory_dialog()
            
            if directory:
                log_info(f"用户选择目录: {directory}", "FILE")
                
                # 更新目录显示
                if hasattr(self.ui_builder, 'panoramic_dir_var'):
                    self.ui_builder.panoramic_dir_var.set(directory)
                    log_debug("更新目录显示变量", "UI")
                
                # 加载数据
                log_info("开始加载目录数据...", "DATA")
                success = self.data_manager.load_directory(directory)
                
                if success:
                    log_info("目录数据加载成功", "DATA")
                    
                    # 更新UI显示
                    panoramic_ids = self.data_manager.get_panoramic_ids()
                    log_info(f"发现 {len(panoramic_ids)} 个全景图: {panoramic_ids}", "DATA")
                    
                    if panoramic_ids:
                        # 加载第一个全景图
                        first_panoramic = panoramic_ids[0]
                        log_info(f"准备加载第一个全景图: {first_panoramic}", "NAV")
                        
                        # 使用SliceController导航到第一个全景图
                        if self.slice_controller:
                            log_info("使用SliceController导航到全景图", "NAV")
                            success = self.slice_controller.navigate_to_panoramic(first_panoramic, 1)
                            
                            if success:
                                log_info("全景图导航成功", "NAV")
                                
                                # 更新状态管理器
                                if self.state_manager:
                                    log_debug("更新状态管理器", "STATE")
                                    self.state_manager.update_dataset_state(
                                        dataset_path=directory,
                                        panoramic_id=first_panoramic
                                    )
                                    self.state_manager.update_slice_state(
                                        slice_index=0,
                                        hole_number=1
                                    )
                                    log_debug("状态管理器更新完成", "STATE")
                                
                                self.update_status(f"已加载目录: {directory} (共{len(panoramic_ids)}个全景图)")
                                log_info(f"目录加载完成 - 路径: {directory}, 全景图数量: {len(panoramic_ids)}", "FILE")
                            else:
                                log_error("全景图导航失败", "NAV")
                                self.update_status("全景图加载失败")
                        else:
                            log_error("切片控制器不可用", "NAV")
                            self.update_status("切片控制器不可用")
                    else:
                        log_warning("目录中未找到全景图文件", "DATA")
                        self.update_status("目录中未找到全景图文件")
                else:
                    log_error("目录数据加载失败", "DATA")
                    self.update_status("目录加载失败")
            else:
                log_info("用户取消了目录选择", "FILE")
                    
        except Exception as e:
            log_error(f"打开目录失败: {e}", "FILE")
            self.update_status(f"打开目录失败: {e}")
            
    def load_annotations(self):
        """加载标注数据"""
        try:
            # 从当前目录加载现有标注
            if self.data_manager.current_directory:
                self.data_manager._load_existing_annotations()
                self.update_status("标注数据加载完成")
            else:
                self.update_status("请先选择工作目录")
        except Exception as e:
            log_error(f"加载标注失败: {e}", "FILE")
            self.update_status(f"加载标注失败: {e}")
            
    def import_model_suggestions(self):
        """导入模型建议"""
        try:
            file_path = self.dialog_factory.show_directory_dialog()
            if file_path:
                # 这里可以实现模型建议导入逻辑
                self.update_status("模型建议导入功能待实现")
        except Exception as e:
            log_error(f"导入模型建议失败: {e}", "FILE")
            self.update_status(f"导入模型建议失败: {e}")
            
    def batch_import_annotations(self):
        """批量导入标注"""
        try:
            # 这里可以实现批量导入逻辑
            self.update_status("批量导入功能待实现")
        except Exception as e:
            log_error(f"批量导入失败: {e}", "FILE")
            self.update_status(f"批量导入失败: {e}")
            
    def toggle_debug_logging(self):
        """切换调试日志开关"""
        try:
            # 这里可以实现日志开关逻辑
            current_state = self.ui_builder.debug_logging_enabled.get()
            status_text = "调试日志已开启" if current_state else "调试日志已关闭"
            self.update_status(status_text)
            log_info(f"调试日志开关已切换: {'开启' if current_state else '关闭'}", "DEBUG")
        except Exception as e:
            log_error(f"切换调试日志失败: {e}", "DEBUG")
            self.update_status(f"切换调试日志失败: {e}")
    
    def save_current_annotation(self):
        """保存当前标注"""
        try:
            if not self.slice_controller.current_panoramic_id or not self.slice_controller.current_hole_number:
                self.update_status("请先选择要标注的孔位")
                return
                
            # 获取当前选择的生长级别
            growth_level = self.ui_builder.growth_level_var.get()
            
            # 获取微生物类型
            microbe_type = self.ui_builder.microbe_type_var.get()
            
            # 获取干扰因素
            interference_factors = []
            for factor, var in self.ui_builder.interference_factors.items():
                if var.get():
                    interference_factors.append(factor)
            
            # 创建标注
            annotation = self.annotation_assistant.create_annotation(
                panoramic_id=self.slice_controller.current_panoramic_id,
                hole_number=self.slice_controller.current_hole_number,
                growth_level=growth_level,
                confidence=1.0,
                microbe_type=microbe_type,
                interference_factors=interference_factors,
                annotation_source="manual"
            )
            
            # 保存标注
            success = self.annotation_assistant.save_annotation(annotation)
            
            if success:
                self.update_status(f"已保存标注: {growth_level}")
            else:
                self.update_status("保存标注失败")
                
        except Exception as e:
            log_error(f"保存标注失败: {e}", "ANNOTATION")
            self.update_status(f"保存标注失败: {e}")
            
    def export_annotations(self):
        """导出标注数据"""
        try:
            result = self.dialog_factory.show_export_dialog()
            if result:
                self.update_status(f"导出完成: {result['path']}")
                
        except Exception as e:
            log_error(f"导出失败: {e}", "EXPORT")
            self.update_status(f"导出失败: {e}")
            
    def set_growth_level(self, level: str):
        """设置生长级别"""
        try:
            self.ui_builder.growth_level_var.set(level)
            self.update_status(f"生长级别设置为: {level}")
            
        except Exception as e:
            log_error(f"设置生长级别失败: {e}", "UI")
            
    def update_status(self, message: str):
        """更新状态栏"""
        try:
            if self.ui_builder:
                self.ui_builder.update_status(message)
            log_info(f"状态更新: {message}", "STATUS")
            
        except Exception as e:
            log_error(f"状态更新失败: {e}", "UI")
    
    # === 状态变化回调方法 ===
    
    def _on_dataset_changed(self, key: str, old_value: Any, new_value: Any):
        """数据集变化回调"""
        try:
            log_info(f"数据集变化: {old_value} -> {new_value}", "STATE")
            # 更新UI显示
            if self.ui_builder and hasattr(self.ui_builder, 'update_dataset_info'):
                self.ui_builder.update_dataset_info(new_value)
        except Exception as e:
            log_error(f"处理数据集变化失败: {e}", "STATE")
    
    def _on_slice_changed(self, key: str, old_value: Any, new_value: Any):
        """切片变化回调"""
        try:
            log_info(f"切片索引变化: {old_value} -> {new_value}", "STATE")
            # 更新导航按钮状态
            if self.state_manager:
                nav_info = {
                    'can_go_previous': new_value > 0,
                    'can_go_next': True  # 这里需要根据实际情况判断
                }
                self.state_manager.update_navigation_state(nav_info)
        except Exception as e:
            log_error(f"处理切片变化失败: {e}", "STATE")
    
    def _on_annotation_changed(self, key: str, old_value: Any, new_value: Any):
        """标注变化回调"""
        try:
            log_info(f"标注修改状态变化: {old_value} -> {new_value}", "STATE")
            # 更新保存按钮状态等
            if self.ui_builder and hasattr(self.ui_builder, 'update_save_button_state'):
                self.ui_builder.update_save_button_state(new_value)
        except Exception as e:
            log_error(f"处理标注变化失败: {e}", "STATE")
            
    # === 导航方法 ===
    
    def go_left(self):
        """向左导航"""
        try:
            if self.navigation_controller:
                from src.ui.modules.navigation_controller import NavigationDirection
                self.navigation_controller.navigate_by_direction(NavigationDirection.LEFT)
            elif self.slice_controller:
                self.slice_controller.go_left()
        except Exception as e:
            log_error(f"向左导航失败: {e}", "NAV")
            
    def go_right(self):
        """向右导航"""
        try:
            if self.navigation_controller:
                from src.ui.modules.navigation_controller import NavigationDirection
                self.navigation_controller.navigate_by_direction(NavigationDirection.RIGHT)
            elif self.slice_controller:
                self.slice_controller.go_right()
        except Exception as e:
            log_error(f"向右导航失败: {e}", "NAV")
            
    def go_up(self):
        """向上导航"""
        try:
            if self.navigation_controller:
                from src.ui.modules.navigation_controller import NavigationDirection
                self.navigation_controller.navigate_by_direction(NavigationDirection.UP)
            elif self.slice_controller:
                self.slice_controller.go_up()
        except Exception as e:
            log_error(f"向上导航失败: {e}", "NAV")
            
    def go_down(self):
        """向下导航"""
        try:
            if self.navigation_controller:
                from src.ui.modules.navigation_controller import NavigationDirection
                self.navigation_controller.navigate_by_direction(NavigationDirection.DOWN)
            elif self.slice_controller:
                self.slice_controller.go_down()
        except Exception as e:
            log_error(f"向下导航失败: {e}", "NAV")
            
    def go_first_hole(self):
        """跳转到第一个孔位"""
        try:
            if self.navigation_controller:
                self.navigation_controller.navigate_first()
            elif self.slice_controller:
                self.slice_controller.go_first_hole()
        except Exception as e:
            log_error(f"跳转到第一个孔位失败: {e}", "NAV")
            
    def go_last_hole(self):
        """跳转到最后一个孔位"""
        try:
            if self.navigation_controller:
                self.navigation_controller.navigate_last()
            elif self.slice_controller:
                self.slice_controller.go_last_hole()
        except Exception as e:
            log_error(f"跳转到最后一个孔位失败: {e}", "NAV")
            
    def go_next_hole(self):
        """下一个孔位"""
        try:
            if self.navigation_controller:
                self.navigation_controller.navigate_next()
            elif self.slice_controller:
                self.slice_controller.go_next_hole()
        except Exception as e:
            log_error(f"下一个孔位导航失败: {e}", "NAV")
            
    def go_prev_hole(self):
        """上一个孔位"""
        try:
            if self.navigation_controller:
                self.navigation_controller.navigate_previous()
            elif self.slice_controller:
                self.slice_controller.go_prev_hole()
        except Exception as e:
            log_error(f"上一个孔位导航失败: {e}", "NAV")
            
    def go_next_panoramic(self):
        """下一个全景图"""
        if self.slice_controller:
            self.slice_controller.go_next_panoramic()
            
    def go_prev_panoramic(self):
        """上一个全景图"""
        if self.slice_controller:
            self.slice_controller.go_prev_panoramic()
            
    # === 其他方法 ===
    
    def batch_import_annotations(self):
        """批量导入标注"""
        try:
            # 调用批量导入对话框
            if self.dialog_factory:
                result = self.dialog_factory.show_batch_import_dialog()
                if result:
                    self.update_status(f"批量导入完成: {result.get('count', 0)} 条标注")
                else:
                    self.update_status("批量导入已取消")
        except Exception as e:
            log_error(f"批量导入失败: {e}", "IMPORT")
            self.update_status(f"批量导入失败: {e}")
    
    def toggle_debug_logging(self):
        """切换调试日志"""
        try:
            current_state = self.ui_builder.debug_logging_enabled.get()
            # 这里可以实现调试日志的开关逻辑
            self.update_status(f"调试日志已{'开启' if current_state else '关闭'}")
        except Exception as e:
            log_error(f"切换调试日志失败: {e}", "DEBUG")
            self.update_status(f"切换调试日志失败: {e}")
    
    def navigate_to_hole(self, hole_number: int):
        """导航到指定孔位"""
        try:
            if self.navigation_controller:
                success = self.navigation_controller.navigate_to_hole(hole_number)
                if success:
                    self.update_status(f"已导航到孔位 {hole_number}")
                else:
                    self.update_status(f"导航到孔位 {hole_number} 失败")
            elif self.slice_controller:
                # 使用SliceController的导航方法
                if self.slice_controller.current_panoramic_id:
                    success = self.slice_controller.navigate_to_hole(
                        self.slice_controller.current_panoramic_id, hole_number
                    )
                    if success:
                        self.update_status(f"已导航到孔位 {hole_number}")
                    else:
                        self.update_status(f"导航到孔位 {hole_number} 失败")
                else:
                    self.update_status("请先加载全景图")
        except Exception as e:
            log_error(f"导航到孔位 {hole_number} 失败: {e}", "NAV")
            self.update_status(f"导航失败: {e}")
            
    def show_help_dialog(self):
        """显示帮助对话框"""
        if self.dialog_factory:
            self.dialog_factory.show_help_dialog()
            
    def show_about_dialog(self):
        """显示关于对话框"""
        if self.dialog_factory:
            self.dialog_factory.show_about_dialog()
            
    def analyze_window_resize_log(self):
        """分析窗口调整日志"""
        # 这里可以实现日志分析功能
        self.update_status("窗口调整日志分析功能待实现")
    
    # === 视图模式和标注相关方法 ===
    
    def on_view_mode_changed(self):
        """视图模式变更事件处理"""
        if hasattr(self.ui_builder, 'view_mode_var'):
            mode_value = self.ui_builder.view_mode_var.get()
            log_debug(f"视图模式切换到: {mode_value}", "VIEW")
            # 这里可以添加视图模式切换逻辑
            
    def on_enhanced_annotation_change(self, annotation_data=None):
        """增强标注变化回调"""
        log_debug("增强标注数据发生变化", "ANN")
        # 这里可以添加标注变化处理逻辑
        
    def skip_current(self):
        """跳过当前标注"""
        log_debug("跳过当前标注", "ANN")
        # 这里可以添加跳过逻辑
        
    def clear_current_annotation(self):
        """清除当前标注"""
        log_debug("清除当前标注", "ANN")
        # 这里可以添加清除标注逻辑
        
    # === 数据加载相关方法 ===
    
    def open_directory(self):
        """打开目录选择对话框并加载数据"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="选择全景图目录")
        if directory:
            # 更新目录显示
            if hasattr(self.ui_builder, 'panoramic_dir_var'):
                self.ui_builder.panoramic_dir_var.set(directory)
            
            # 开始数据加载
            self.load_directory_data(directory)
    
    def load_directory_data(self, directory_path: str):
        """加载目录数据"""
        try:
            log_info(f"开始加载目录: {directory_path}", "LOAD")
            
            # 显示进度对话框
            progress_dialog = self.create_progress_dialog("正在加载全景图数据", "正在扫描目录...")
            
            try:
                # 使用数据管理器加载数据
                success = self.data_manager.load_directory_with_progress(directory_path, progress_dialog)
                
                if success:
                    # 加载成功，更新界面
                    self.update_after_data_load()
                    log_info("数据加载完成", "LOAD")
                else:
                    # 加载失败
                    log_error("数据加载失败", "LOAD")
                    
            finally:
                # 确保关闭进度对话框
                if progress_dialog:
                    progress_dialog.close()
                    
        except Exception as e:
            log_error(f"加载目录数据失败: {e}", "LOAD")
            
    def create_progress_dialog(self, title: str, message: str):
        """创建进度对话框"""
        return ProgressDialog(self.root, title, message)
        
    def update_after_data_load(self):
        """数据加载完成后更新界面"""
        try:
            # 更新全景图列表
            if self.slice_controller:
                self.slice_controller.update_panoramic_list()
                
            # 加载第一个切片
            if self.slice_controller:
                self.slice_controller.load_first_slice()
                
            # 更新统计信息
            self.update_statistics()
            
            # 更新状态栏
            slice_count = len(self.data_manager.slice_files) if self.data_manager else 0
            self.update_status(f"已加载 {slice_count} 个切片文件")
            
        except Exception as e:
            log_error(f"界面更新失败: {e}", "LOAD")
            
    def update_statistics(self):
        """更新统计信息"""
        try:
            if not hasattr(self.ui_builder, 'stats_label'):
                return
                
            # 计算统计数据
            total_count = len(self.data_manager.slice_files) if self.data_manager else 0
            
            # 统计各类型标注数量
            unannotated_count = 0
            negative_count = 0
            weak_growth_count = 0
            positive_count = 0
            
            if self.data_manager and self.data_manager.annotations:
                for panoramic_data in self.data_manager.annotations.values():
                    for annotation in panoramic_data.values():
                        growth_level = getattr(annotation, 'growth_level', 'unannotated')
                        if growth_level == 'negative':
                            negative_count += 1
                        elif growth_level == 'weak_growth':
                            weak_growth_count += 1
                        elif growth_level == 'positive':
                            positive_count += 1
                        else:
                            unannotated_count += 1
            else:
                unannotated_count = total_count
            
            # 更新统计标签
            stats_text = f"统计: 未标注 {unannotated_count}, 阴性 {negative_count}, 弱生长 {weak_growth_count}, 阳性 {positive_count}"
            self.ui_builder.stats_label.config(text=stats_text)
            
        except Exception as e:
            log_error(f"更新统计信息失败: {e}", "STATS")
        
    # === 日志方法 ===
    
    def log_debug(self, message: str, tag: str = "DEBUG"):
        """记录调试日志"""
        log_debug(message, tag)
        
    def log_info(self, message: str, tag: str = "INFO"):
        """记录信息日志"""
        log_info(message, tag)
        
    def log_warning(self, message: str, tag: str = "WARNING"):
        """记录警告日志"""
        log_warning(message, tag)
        
    def log_error(self, message: str, tag: str = "ERROR"):
        """记录错误日志"""
        log_error(message, tag)


def create_main_app():
    """创建主应用程序"""
    try:
        app = ModularAnnotationGUI()
        app.initialize()
        return app.root, app
    except Exception as e:
        print(f"创建应用程序失败: {e}")
        raise


def main():
    """主函数"""
    try:
        root, app = create_main_app()
        app.run()
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
