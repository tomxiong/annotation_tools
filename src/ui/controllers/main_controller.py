"""
主控制器模块

负责应用程序的主要逻辑协调
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any, List
import logging
import os
from pathlib import Path
from PIL import Image, ImageTk

from src.ui.utils.base_components import BaseController
from src.ui.utils.event_bus import EventBus, EventType, Event, get_event_bus
from src.ui.models.ui_state import UIStateManager, get_ui_state_manager
from src.models.panoramic_annotation import PanoramicAnnotation, PanoramicDataset
from src.models.enhanced_annotation import EnhancedPanoramicAnnotation, FeatureCombination
from src.services.panoramic_image_service import PanoramicImageService
from src.services.annotation_engine import AnnotationEngine
from src.services.config_file_service import ConfigFileService
from src.services.model_suggestion_import_service import ModelSuggestionImportService
from src.core.config import Config

from src.ui.hole_manager import HoleManager
from src.ui.hole_config_panel import HoleConfigPanel
from src.ui.enhanced_annotation_panel import EnhancedAnnotationPanel
from src.ui.components.navigation_panel import NavigationPanel
from src.ui.components.annotation_panel import AnnotationPanel
from src.ui.components.image_canvas import ImageCanvas
from src.utils.logger import enable_debug_logging, disable_debug_logging, is_debug_logging_enabled

# Import new manager classes
from .ui_manager import UIManager
from .navigation_manager import NavigationManager
from .annotation_manager import AnnotationManager
from .statistics_manager import StatisticsManager
from .file_manager import FileManager

logger = logging.getLogger(__name__)


class MainController(BaseController):
    """主控制器"""
    
    def __init__(self, container=None):
        super().__init__()
        self.container = container
        self.root: Optional[tk.Tk] = None

        # 服务实例
        self.image_service: Optional[PanoramicImageService] = None
        self.annotation_engine: Optional[AnnotationEngine] = None
        self.config_service: Optional[ConfigFileService] = None
        self.hole_manager: Optional[HoleManager] = None
        self.model_suggestion_service: Optional[ModelSuggestionImportService] = None

        # 配置
        self.config: Optional[Config] = None

        # 应用状态
        self.current_image_path: Optional[str] = None
        self.is_modified = False
        self.panoramic_directory = ""

        # 数据状态
        self.current_dataset = None
        self.slice_files: List[Dict[str, Any]] = []
        self.panoramic_image = None
        self.slice_image = None
        self.panoramic_photo = None
        self.slice_photo = None
        self.current_panoramic_id = ""
        self.current_hole_number = 1

        # 视图模式
        self.view_mode = "manual"  # "manual" or "model"
        self.model_suggestion_loaded = False
        self.current_suggestions_map = None

        # 自动保存
        self.auto_save_enabled = tk.BooleanVar(value=True)
        self.last_annotation_time = {}

        # 窗口尺寸跟踪
        self.window_resize_log = []
        self.initial_geometry = "1600x900"
        self.current_geometry = "1600x900"

        # 坐标定位调试配置
        self.debug_coordinate_offset = False  # 是否启用坐标偏移调试
        self.coordinate_offset_x = 0.0  # X轴坐标偏移调整
        self.coordinate_offset_y = 0.0  # Y轴坐标偏移调整
        self.coordinate_scale_adjust = 1.0  # 缩放比例调整因子

        # 状态变量
        self.panoramic_dir_var = tk.StringVar()
        self.hole_number_var = tk.StringVar(value="1")
        self.view_mode_var = tk.StringVar(value="manual")

        # 标注状态
        self.current_microbe_type = tk.StringVar(value="bacteria")
        self.current_growth_level = tk.StringVar(value="negative")
        self.interference_factors = {
            'pores': tk.BooleanVar(),
            'artifacts': tk.BooleanVar(),
            'edge_blur': tk.BooleanVar()
        }

        # 初始化管理器
        self.ui_manager = UIManager(self)
        self.navigation_manager = NavigationManager(self)
        self.annotation_manager = AnnotationManager(self)
        self.statistics_manager = StatisticsManager(self)
        self.file_manager = FileManager(self)
        
    def initialize(self) -> None:
        """初始化控制器"""
        try:
            logger.info("Initializing MainController...")

            # 获取服务实例 - 确保依赖注入正确
            if self.container:
                try:
                    self.image_service = self.container.get('image_service')
                    self.annotation_engine = self.container.get('annotation_engine')
                    self.config_service = self.container.get('config_service')
                    self.config = self.container.get('config')
                    logger.info("Services injected successfully")
                except ValueError as e:
                    logger.warning(f"Some services not available in container: {e}")
                    # 设置默认值
                    self.image_service = None
                    self.annotation_engine = None
                    self.config_service = None
                    self.config = None

            # 创建UI相关服务
            self.hole_manager = HoleManager()
            self.model_suggestion_service = ModelSuggestionImportService()

            # 初始化数据集
            self.current_dataset = PanoramicDataset("新数据集", "全景图像标注数据集")

            # 获取根窗口
            self.root = self._get_root_window()

            # 初始化管理器 - 按依赖顺序
            logger.info("Initializing managers...")
            self.ui_manager.initialize(self.root)
            self.navigation_manager.initialize()
            self.annotation_manager.initialize()
            self.statistics_manager.initialize()
            self.file_manager.initialize()

            # 连接组件
            self._connect_components()

            # 订阅事件
            self._subscribe_events()

            # 加载配置
            self._load_configuration()

            self._mark_initialized()
            logger.info("MainController initialized successfully")

        except Exception as e:
            self.handle_error(e, "MainController initialization")
            raise
    
    def cleanup(self) -> None:
        """清理资源"""
        logger.info("Cleaning up MainController...")
        
        # 清理事件监听器
        self.cleanup_listeners()
        
        # 保存配置
        self._save_configuration()
        
        # 保存当前标注
        if self.is_modified:
            self._save_current_annotations()
    
    def _get_root_window(self) -> tk.Tk:
        """获取根窗口"""
        if self.container:
            # 尝试从容器获取
            try:
                app = self.container.get('app')
                if hasattr(app, 'root'):
                    return app.root
            except ValueError:
                pass  # Service not found, continue to create default

        # 如果没有找到，创建一个默认的
        root = tk.Tk()
        root.title("全景标注工具")
        root.geometry("1600x900")
        root.minsize(1400, 800)  # 设置最小尺寸
        return root
    
    # UI组件创建已移至UIManager，移除重复方法

    # UI创建方法已移至UIManager，移除重复方法
    
    def _connect_components(self):
        """连接组件"""
        logger.info("Connecting components...")

        # 确保UI管理器已正确初始化
        if not hasattr(self, 'ui_manager') or not self.ui_manager:
            logger.warning("UIManager not available for component connection")
            return

        # 设置视图模式变更回调
        if hasattr(self, 'view_mode_var'):
            self._on_view_mode_changed()

        # 连接增强标注面板的回调
        if hasattr(self, 'annotation_panel') and self.annotation_panel:
            self.annotation_panel.on_annotation_change = self._on_enhanced_annotation_change

        logger.info("Components connected successfully")
    
    def _subscribe_events(self):
        """订阅事件"""
        # 文件事件
        self.subscribe(EventType.FILE_OPENED, self._on_file_opened)
        self.subscribe(EventType.FILE_SAVED, self._on_file_saved)
        self.subscribe(EventType.FILE_EXPORTED, self._on_file_exported)
        
        # 图像事件
        self.subscribe(EventType.IMAGE_LOADED, self._on_image_loaded)
        
        # 导航事件
        self.subscribe(EventType.NAVIGATION_CHANGED, self._on_navigation_changed)
        
        # 标注事件
        self.subscribe(EventType.ANNOTATION_SAVED, self._on_annotation_saved)
        self.subscribe(EventType.ANNOTATION_DELETED, self._on_annotation_deleted)
        
        # 应用事件
        self.subscribe(EventType.APP_CLOSING, self._on_app_closing)
    
    def _load_configuration(self):
        """加载配置"""
        if self.config_service:
            try:
                self.config_service.load_config()
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load configuration: {e}")
    
    def _save_configuration(self):
        """保存配置"""
        if self.config_service:
            try:
                self.config_service.save_config()
                logger.info("Configuration saved successfully")
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
    
    def _on_file_opened(self, event: Event):
        """文件打开事件"""
        data = event.data
        if not data:
            return
        
        action = data.get('action')
        
        if action == 'add_images':
            self._add_images()
        elif action == 'import_annotations':
            self._import_annotations()
        elif 'file_path' in data:
            file_path = data['file_path']
            file_type = data.get('file_type', 'image')
            
            if file_type == 'image':
                self._load_image(file_path)
    
    def _on_file_saved(self, event: Event):
        """文件保存事件"""
        data = event.data
        if data and 'file_path' in data:
            logger.info(f"File saved: {data['file_path']}")
            self.is_modified = False
    
    def _on_file_exported(self, event: Event):
        """文件导出事件"""
        data = event.data
        if data:
            action = data.get('action')
            
            if action == 'export_annotations':
                self._export_annotations()
    
    def _on_image_loaded(self, event: Event):
        """图像加载事件"""
        data = event.data
        if data and 'image_path' in data:
            self.current_image_path = data['image_path']
            logger.info(f"Image loaded: {self.current_image_path}")
    
    def _on_navigation_changed(self, event: Event):
        """导航变更事件"""
        data = event.data
        if data:
            logger.debug(f"Navigation changed: {data}")
    
    def _on_annotation_saved(self, event: Event):
        """标注保存事件"""
        data = event.data
        if data and 'hole_id' in data:
            self.is_modified = True
            logger.debug(f"Annotation saved for hole {data['hole_id']}")
    
    def _on_annotation_deleted(self, event: Event):
        """标注删除事件"""
        data = event.data
        if data and 'hole_id' in data:
            self.is_modified = True
            logger.debug(f"Annotation deleted for hole {data['hole_id']}")
    
    def _on_app_closing(self, event: Event):
        """应用关闭事件"""
        logger.info("Application closing event received")
        
        # 检查是否有未保存的更改
        if self.is_modified:
            result = messagebox.askyesnocancel(
                "保存更改",
                "您有未保存的标注更改，是否保存？"
            )
            
            if result is True:  # 是
                self._save_current_annotations()
            elif result is None:  # 取消
                # 取消关闭
                return
        
        # 继续关闭流程
        self.cleanup()
    
    def _add_images(self):
        """添加图像"""
        if not self.root:
            return
        
        file_types = [
            ("图像文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("所有文件", "*.*")
        ]
        
        file_paths = filedialog.askopenfilenames(
            title="选择图像文件",
            filetypes=file_types,
            initialdir=self._get_last_directory()
        )
        
        if file_paths:
            for file_path in file_paths:
                self._load_image(file_path)
            
            # 更新最后目录
            self._update_last_directory(os.path.dirname(file_paths[0]))
    
    def _load_image(self, image_path: str):
        """加载图像"""
        try:
            # 使用图像服务加载图像
            if self.image_service:
                success = self.image_service.load_image(image_path)
                if success:
                    # 在画布上显示图像
                    if self.image_canvas:
                        self.image_canvas.load_image(image_path)
                    
                    # 添加到导航面板
                    if self.navigation_panel:
                        self.navigation_panel.add_image_to_list(image_path)
                    
                    # 设置为当前图像
                    if self.navigation_panel:
                        self.navigation_panel.set_current_image(image_path)
                    
                    logger.info(f"Image loaded successfully: {image_path}")
                else:
                    messagebox.showerror("错误", f"无法加载图像: {image_path}")
            else:
                # 直接使用画布加载
                if self.image_canvas:
                    self.image_canvas.load_image(image_path)
                    
                    if self.navigation_panel:
                        self.navigation_panel.add_image_to_list(image_path)
                        self.navigation_panel.set_current_image(image_path)
                    
                    logger.info(f"Image loaded directly: {image_path}")
                    
        except Exception as e:
            self.handle_error(e, f"Failed to load image {image_path}")
            messagebox.showerror("错误", f"加载图像时出错: {str(e)}")
    
    def _save_current_annotations(self):
        """保存当前标注"""
        if not hasattr(self, 'annotation_panel') or not self.annotation_panel:
            return

        try:
            annotations = self.annotation_panel.get_all_annotations()

            if not annotations:
                return

            # 选择保存位置
            file_path = filedialog.asksaveasfilename(
                title="保存标注",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialdir=self._get_last_directory()
            )

            if file_path:
                if self.annotation_engine:
                    success = self.annotation_engine.save_annotations(annotations, file_path)
                    if success:
                        self.is_modified = False
                        self._update_last_directory(os.path.dirname(file_path))
                        messagebox.showinfo("成功", "标注已保存")
                    else:
                        messagebox.showerror("错误", "保存标注失败")
                else:
                    # 简单的JSON保存
                    import json
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(annotations, f, indent=2, ensure_ascii=False)

                    self.is_modified = False
                    self._update_last_directory(os.path.dirname(file_path))
                    messagebox.showinfo("成功", "标注已保存")

        except Exception as e:
            self.handle_error(e, "Failed to save annotations")
            messagebox.showerror("错误", f"保存标注时出错: {str(e)}")

    def _save_current_annotation(self):
        """保存当前标注并导航到下一个"""
        try:
            # 保存当前标注
            self._save_current_annotation_internal("manual")

            # 导航到下一个孔位
            self._go_next_hole()

            # 更新状态
            self.update_status("已保存并跳转到下一个孔位")

        except Exception as e:
            logger.error(f"保存并下一个失败: {str(e)}")
            messagebox.showerror("错误", f"保存并下一个失败: {str(e)}")

    def _skip_current(self):
        """跳过当前孔位"""
        try:
            # 导航到下一个孔位
            self._go_next_hole()

            # 更新状态
            self.update_status("已跳过当前孔位")

        except Exception as e:
            logger.error(f"跳过当前孔位失败: {str(e)}")
            messagebox.showerror("错误", f"跳过当前孔位失败: {str(e)}")

    def _clear_current_annotation(self):
        """清除当前标注"""
        try:
            # 清除当前孔位的标注
            if hasattr(self, 'current_dataset') and self.current_dataset:
                existing_ann = self.current_dataset.get_annotation_by_hole(
                    self.current_panoramic_id,
                    self.current_hole_number
                )
                if existing_ann:
                    self.current_dataset.annotations.remove(existing_ann)
                    self.is_modified = True

            # 重置增强标注面板
            if hasattr(self, 'annotation_panel') and self.annotation_panel:
                self.annotation_panel.reset_annotation()

            # 更新显示
            self._update_slice_info_display()
            self._update_statistics()

            # 更新状态
            self.update_status("已清除当前标注")

        except Exception as e:
            logger.error(f"清除当前标注失败: {str(e)}")
            messagebox.showerror("错误", f"清除当前标注失败: {str(e)}")
    
    def _export_annotations(self):
        """导出标注"""
        if not hasattr(self, 'annotation_panel') or not self.annotation_panel:
            return

        try:
            annotations = self.annotation_panel.get_all_annotations()
            
            if not annotations:
                messagebox.showinfo("提示", "没有标注数据可导出")
                return
            
            # 选择导出位置
            file_path = filedialog.asksaveasfilename(
                title="导出标注",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
                initialdir=self._get_last_directory()
            )
            
            if file_path:
                if file_path.endswith('.csv'):
                    self._export_annotations_csv(annotations, file_path)
                else:
                    self._export_annotations_json(annotations, file_path)
                
                self._update_last_directory(os.path.dirname(file_path))
                messagebox.showinfo("成功", "标注已导出")
                
        except Exception as e:
            self.handle_error(e, "Failed to export annotations")
            messagebox.showerror("错误", f"导出标注时出错: {str(e)}")
    
    def _export_annotations_json(self, annotations: Dict[str, Any], file_path: str):
        """导出为JSON格式"""
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(annotations, f, indent=2, ensure_ascii=False)
    
    def _export_annotations_csv(self, annotations: Dict[str, Any], file_path: str):
        """导出为CSV格式"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入标题
            writer.writerow(['孔位', '行', '列', '生长级别', '微生物类型', '备注'])
            
            # 写入数据
            for hole_id, annotation in annotations.items():
                row = int(hole_id[:2])
                col = int(hole_id[2:4])
                row_letter = chr(ord('A') + row)
                col_number = col + 1
                
                writer.writerow([
                    f"{row_letter}{col_number}",
                    row_letter,
                    col_number,
                    annotation.get('growth_level', ''),
                    annotation.get('microbe_type', ''),
                    annotation.get('notes', '')
                ])
    
    def _import_annotations(self):
        """导入标注"""
        if not hasattr(self, 'annotation_panel') or not self.annotation_panel:
            return

        try:
            # 选择导入文件
            file_path = filedialog.askopenfilename(
                title="导入标注",
                filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
                initialdir=self._get_last_directory()
            )

            if file_path:
                if file_path.endswith('.csv'):
                    annotations = self._import_annotations_csv(file_path)
                else:
                    annotations = self._import_annotations_json(file_path)

                if annotations:
                    self.annotation_panel.clear_all_annotations()

                    for hole_id, annotation in annotations.items():
                        self.annotation_panel.set_annotation(hole_id, annotation)
                    
                    self._update_last_directory(os.path.dirname(file_path))
                    messagebox.showinfo("成功", f"已导入 {len(annotations)} 个标注")
                else:
                    messagebox.showwarning("警告", "没有找到有效的标注数据")
                    
        except Exception as e:
            self.handle_error(e, "Failed to import annotations")
            messagebox.showerror("错误", f"导入标注时出错: {str(e)}")
    
    def _import_annotations_json(self, file_path: str) -> Dict[str, Any]:
        """导入JSON格式标注"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _import_annotations_csv(self, file_path: str) -> Dict[str, Any]:
        """导入CSV格式标注"""
        import csv
        
        annotations = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # 解析孔位
                hole_pos = row.get('孔位', '')
                if hole_pos:
                    # 转换为内部格式
                    if len(hole_pos) >= 2:
                        row_letter = hole_pos[0].upper()
                        col_number = int(hole_pos[1:])
                        
                        row_idx = ord(row_letter) - ord('A')
                        col_idx = col_number - 1
                        
                        hole_id = f"{row_idx:02d}{col_idx:02d}"
                        
                        annotations[hole_id] = {
                            'growth_level': row.get('生长级别', ''),
                            'microbe_type': row.get('微生物类型', ''),
                            'notes': row.get('备注', '')
                        }
        
        return annotations
    
    def _get_last_directory(self) -> str:
        """获取最后使用的目录"""
        if self.ui_state_manager:
            state = self.ui_state_manager.get_state()
            return state.last_open_directory or os.path.expanduser("~")
        return os.path.expanduser("~")
    
    def _update_last_directory(self, directory: str):
        """更新最后使用的目录"""
        if self.ui_state_manager:
            self.ui_state_manager.update_state(last_open_directory=directory)
    
    def get_current_image_path(self) -> Optional[str]:
        """获取当前图像路径"""
        return self.current_image_path
    
    def is_image_loaded(self) -> bool:
        """检查是否有图像加载"""
        return self.current_image_path is not None
    
    def get_annotation_count(self) -> int:
        """获取标注数量"""
        if hasattr(self, 'annotation_panel') and self.annotation_panel:
            return len(self.annotation_panel.get_all_annotations())
        return 0
    
    def has_unsaved_changes(self) -> bool:
        """检查是否有未保存的更改"""
        return self.is_modified
    
    def show_about_dialog(self):
        """显示关于对话框"""
        if not self.root:
            return
        
        about_text = """全景标注工具 v1.0

用于微生物药敏试验的全景图像标注工具

支持功能：
• 120孔位标注
• 多种微生物类型
• 批量标注操作
• 数据导入导出

开发者：Claude Code"""
        
        messagebox.showinfo("关于", about_text)
    
    def show_help_dialog(self):
        """显示帮助对话框"""
        if not self.root:
            return
        
        help_text = """使用帮助：

1. 加载图像
   • 点击"添加图像"按钮选择图像文件
   • 支持JPG、PNG、BMP等格式

2. 标注操作
   • 点击孔位进行选择
   • 在标注面板中填写信息
   • 点击"保存标注"完成标注

3. 批量操作
   • 设置批量标注选项
   • 选择应用到所有孔位、行或列

4. 导入导出
   • 支持JSON和CSV格式
   • 可保存和加载标注数据

快捷键：
• Ctrl + +：放大
• Ctrl + -：缩小
• Ctrl + 0：重置缩放"""
        
        messagebox.showinfo("帮助", help_text)

    # ==================== 新增的GUI方法 ====================

    def _select_panoramic_directory(self):
        """选择全景图目录"""
        try:
            logger.info("开始选择全景图目录")

            # 检查UI是否已初始化
            if not hasattr(self, 'ui_manager') or not self.ui_manager:
                logger.warning("UI管理器未初始化，无法选择全景图目录")
                messagebox.showerror("错误", "UI未完全初始化，请稍后再试")
                return

            self.file_manager.select_panoramic_directory()
            logger.info("全景图目录选择完成")
        except AttributeError as e:
            logger.error(f"panoramic_combobox属性错误: {e}", exc_info=True)
            messagebox.showerror("错误", f"'MainController' object has no attribute 'panoramic_combobox': {str(e)}")
        except Exception as e:
            logger.error(f"选择全景图目录失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"选择全景图目录失败: {str(e)}")

    def _load_data(self):
        """加载数据 - 使用子目录结构"""
        if not self.panoramic_directory:
            logger.warning("未选择全景图目录")
            messagebox.showerror("错误", "请先选择全景图目录")
            return False

        try:
            logger.info(f"开始加载数据，目录: {self.panoramic_directory}")

            # 使用子目录模式：直接使用全景目录下的子目录
            self.slice_files = self.image_service.get_slice_files_from_directory(
                self.panoramic_directory, self.panoramic_directory)
            structure_msg = '子目录模式'

            if not self.slice_files:
                logger.error("未找到有效的切片文件")
                messagebox.showerror("错误",
                    "未找到有效的切片文件。\n请检查：\n" +
                    "1. 目录下是否存在全景图文件（.bmp, .png, .jpg等）\n" +
                    "2. 是否存在包含切片的子目录\n" +
                    "3. 切片文件应在 <全景文件>/hole_<孔序号>.png 位置")
                return False

            logger.info(f"找到 {len(self.slice_files)} 个切片文件")

            # 更新全景图列表
            self._update_panoramic_list()

            # 重置状态
            self.current_dataset = PanoramicDataset("新数据集",
                f"从 {self.panoramic_directory} 加载的数据集 ({structure_msg})")

            # 找到第一个有效孔位的索引（从起始孔位开始）
            self.current_slice_index = self._find_first_valid_slice_index()

            # 只有在UI已初始化时才加载切片
            if hasattr(self, 'ui_manager') and self.ui_manager:
                # 加载第一个有效切片
                self._load_current_slice()

                # 自动切换视图模式
                self._auto_switch_view_mode()

                self.update_status(f"已加载 {len(self.slice_files)} 个切片文件 ({structure_msg})")
                self._update_progress()
            else:
                logger.info("UI未初始化，跳过切片加载")

            logger.info("数据加载完成")
            return True

        except Exception as e:
            logger.error(f"加载数据失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
            return False

    def _load_annotations(self):
        """加载标注结果进行review"""
        self.file_manager.load_annotations()

    def _save_annotations(self):
        """保存标注"""
        self.file_manager.save_annotations()

    def _import_model_suggestions(self):
        """导入模型预测结果文件"""
        self.file_manager.import_model_suggestions()



    def _on_panoramic_click(self, event):
        """全景图点击事件"""
        if not self.panoramic_image or not self.hole_manager:
            return

        try:
            # 获取点击位置
            canvas_x = event.x
            canvas_y = event.y

            # 获取画布尺寸
            if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_canvas') and self.ui_manager.panoramic_canvas:
                canvas_width = self.ui_manager.panoramic_canvas.winfo_width()
                canvas_height = self.ui_manager.panoramic_canvas.winfo_height()
            else:
                logger.warning("panoramic_canvas not available for click handling")
                return

            # 计算缩放比例和偏移
            img_width, img_height = self.panoramic_image.size
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y)

            # 计算图像在画布上的偏移（居中显示）
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            offset_x = (canvas_width - scaled_width) / 2
            offset_y = (canvas_height - scaled_height) / 2

            # 转换为图像坐标
            img_x = (canvas_x - offset_x) / scale
            img_y = (canvas_y - offset_y) / scale

            # Debug日志：点击坐标转换
            logger.debug(f"[PANORAMIC_CLICK] 点击画布坐标: ({canvas_x}, {canvas_y})")
            logger.debug(f"[PANORAMIC_CLICK] 转换为图像坐标: ({img_x:.1f}, {img_y:.1f})")
            logger.debug(f"[PANORAMIC_CLICK] 缩放比例: {scale:.3f}, 偏移: ({offset_x:.1f}, {offset_y:.1f})")

            # 查找点击位置对应的孔位
            clicked_hole = None
            min_distance = float('inf')

            for row in range(10):  # 10行
                for col in range(12):  # 12列
                    hole_number = row * 12 + col + 1

                    # 获取孔位位置
                    hole_pos = self.hole_manager.get_hole_center_coordinates(hole_number)
                    if hole_pos:
                        hole_x, hole_y = hole_pos

                        # 坐标调整功能已禁用，直接使用原始坐标
                        adjusted_hole_x, adjusted_hole_y = hole_x, hole_y

                        # 检查点击是否在孔位范围内（使用调整后的坐标进行比较）
                        distance = ((img_x - adjusted_hole_x) ** 2 + (img_y - adjusted_hole_y) ** 2) ** 0.5
                        if distance <= 15:  # 15像素半径
                            if distance < min_distance:
                                min_distance = distance
                                clicked_hole = hole_number

            if clicked_hole:
                logger.debug(f"[PANORAMIC_CLICK] 找到最近孔位: {clicked_hole}, 距离: {min_distance:.1f}")
                self._switch_to_hole(clicked_hole)
                self.update_status(f"跳转到孔位: {clicked_hole}")
            else:
                logger.debug(f"[PANORAMIC_CLICK] 未找到有效孔位，最近距离: {min_distance:.1f}")
                self.update_status("点击位置未找到有效孔位")

        except Exception as e:
            logger.error(f"全景图点击处理失败: {str(e)}")

    def _on_panoramic_selected(self, event=None):
        """全景图选择事件"""
        if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_combobox') and self.ui_manager.panoramic_combobox:
            selected = self.ui_manager.panoramic_combobox.get()
            if selected and selected != self.current_panoramic_id:
                self._switch_to_panoramic(selected)
        else:
            logger.warning("panoramic_combobox not available")

    def _on_view_mode_changed(self):
        """视图模式变更"""
        mode = self.view_mode_var.get()
        self.view_mode = mode

        if mode == "model":
            # 切换到模型视图
            self._load_model_view_data()
        else:
            # 切换到人工视图
            self._load_existing_annotation()

        # 更新显示
        self._update_slice_info_display()

        mode_name = "人工视图" if mode == "manual" else "模型视图"
        self.update_status(f"已切换到{mode_name}")

    def _go_prev_panoramic(self):
        """上一张全景图"""
        if not self.panoramic_ids:
            return

        # 保存当前标注
        self._save_current_annotation_internal("navigation")

        # 计算上一个全景图索引（循环）
        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)

        prev_index = (current_index - 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[prev_index]

        # 导航到目标全景图
        self._switch_to_panoramic(target_panoramic_id)

    def _go_next_panoramic(self):
        """下一张全景图"""
        if not self.panoramic_ids:
            return

        # 保存当前标注
        self._save_current_annotation_internal("navigation")

        # 计算下一个全景图索引（循环）
        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)

        next_index = (current_index + 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[next_index]

        # 导航到目标全景图
        self._switch_to_panoramic(target_panoramic_id)

    def _go_to_hole(self, event=None):
        """跳转到指定孔位"""
        hole_number = self.hole_number_var.get()
        try:
            hole_num = int(hole_number)
            if 1 <= hole_num <= 120:
                self._switch_to_hole(hole_num)
                self.update_status(f"跳转到孔位: {hole_num}")
            else:
                self.update_status("孔位编号必须在1-120之间")
        except ValueError:
            self.update_status("无效的孔位编号")

    def _go_first_hole(self):
        """跳转到第一个孔位"""
        start_hole = self.hole_manager.start_hole_number if self.hole_manager else 25
        self._switch_to_hole(start_hole)
        self.update_status(f"跳转到第一个孔位: {start_hole}")

    def _go_prev_hole(self):
        """跳转到上一个孔位"""
        if not self.slice_files:
            return

        # 保存当前标注
        self._save_current_annotation_internal("navigation")

        # 计算上一个孔位
        current_hole = self.current_hole_number
        prev_hole = current_hole - 1

        # 如果到达最小孔位，循环到最大孔位
        if prev_hole < 1:
            prev_hole = 120

        self._switch_to_hole(prev_hole)
        self.update_status(f"跳转到上一个孔位: {prev_hole}")

    def _go_next_hole(self):
        """跳转到下一个孔位"""
        if not self.slice_files:
            return

        # 保存当前标注
        self._save_current_annotation_internal("navigation")

        # 计算下一个孔位
        current_hole = self.current_hole_number
        next_hole = current_hole + 1

        # 如果到达最大孔位，循环到最小孔位
        if next_hole > 120:
            next_hole = 1

        self._switch_to_hole(next_hole)
        self.update_status(f"跳转到下一个孔位: {next_hole}")

    def _go_last_hole(self):
        """跳转到最后一个孔位"""
        self._switch_to_hole(120)
        self.update_status("跳转到最后一个孔位: 120")

    def _on_view_mode_changed(self):
        """视图模式变更"""
        mode = self.view_mode_var.get()
        mode_name = "人工视图" if mode == "manual" else "模型视图"
        self.update_status(f"已切换到{mode_name}")

    def update_status(self, message: str):
        """更新状态栏"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
            self.root.update_idletasks()

    def _update_panoramic_list(self):
        """更新全景图列表"""
        try:
            # 从切片文件中提取唯一的全景图ID
            panoramic_ids = set()
            for slice_file in self.slice_files:
                panoramic_ids.add(slice_file['panoramic_id'])

            self.panoramic_ids = sorted(list(panoramic_ids))
            logger.debug(f"找到 {len(self.panoramic_ids)} 个全景图: {self.panoramic_ids[:5]}...")

            # 初始化current_panoramic_id如果不存在
            if not hasattr(self, 'current_panoramic_id') or self.current_panoramic_id is None:
                if self.panoramic_ids:
                    self.current_panoramic_id = self.panoramic_ids[0]
                    logger.debug(f"设置默认全景图ID: {self.current_panoramic_id}")

            # 更新下拉列表
            if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_combobox') and self.ui_manager.panoramic_combobox:
                self.ui_manager.panoramic_combobox['values'] = self.panoramic_ids

                # 设置当前选中项
                if hasattr(self, 'current_panoramic_id') and self.current_panoramic_id in self.panoramic_ids:
                    self.ui_manager.panoramic_combobox.set(self.current_panoramic_id)
                elif self.panoramic_ids:
                    self.ui_manager.panoramic_combobox.set(self.panoramic_ids[0])
            else:
                logger.debug("panoramic_combobox not available for updating list")

        except Exception as e:
            logger.error(f"更新全景图列表失败: {e}", exc_info=True)

    def _find_first_valid_slice_index(self) -> int:
        """找到第一个有效孔位的切片索引"""
        if not self.slice_files:
            return 0

        start_hole = self.hole_manager.start_hole_number if self.hole_manager else 25

        # 查找第一个孔位号大于等于起始孔位的切片
        for i, slice_file in enumerate(self.slice_files):
            hole_number = slice_file.get('hole_number', 1)
            if hole_number >= start_hole:
                return i

        # 如果没找到有效孔位，返回0
        return 0

    def _load_current_slice(self):
        """加载当前切片"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return

        current_file = self.slice_files[self.current_slice_index]

        try:
            # 检查全景图是否改变
            old_panoramic_id = getattr(self, 'current_panoramic_id', None)
            new_panoramic_id = current_file['panoramic_id']
            panoramic_changed = (not hasattr(self, 'current_panoramic_id') or
                               self.current_panoramic_id != current_file['panoramic_id'])

            # 如果全景图改变，重置标注状态以避免从上一个全景图复制设置
            if panoramic_changed:
                self.current_growth_level.set("negative")
                self.current_microbe_type.set("bacteria")
                # 重置干扰因素
                for factor in self.interference_factors:
                    self.interference_factors[factor].set(False)

            # 更新当前信息
            self.current_panoramic_id = current_file['panoramic_id']
            self.current_hole_number = current_file['hole_number']
            self.hole_number_var.set(str(self.current_hole_number))

            # 更新hole_manager的panoramic_id，确保模型建议正确显示
            if hasattr(self, 'hole_manager') and self.hole_manager:
                self.hole_manager._current_panoramic_id = self.current_panoramic_id

            # 更新全景图下拉列表选中项
            if self.current_panoramic_id and self.current_panoramic_id in self.panoramic_ids:
                if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_combobox') and self.ui_manager.panoramic_combobox:
                    try:
                        self.ui_manager.panoramic_combobox.set(self.current_panoramic_id)
                        logger.debug(f"设置panoramic_combobox为: {self.current_panoramic_id}")
                    except Exception as e:
                        logger.error(f"设置panoramic_combobox失败: {e}", exc_info=True)
                else:
                    logger.debug("panoramic_combobox not available for setting current panoramic_id")

            # 加载切片图像
            self.slice_image = self.image_service.load_slice_image(current_file['filepath'])
            if self.slice_image:
                # 增强显示效果
                enhanced_slice = self.image_service.enhance_slice_image(self.slice_image)

                # 获取画布尺寸用于缩放
                if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'slice_canvas') and self.ui_manager.slice_canvas:
                    canvas_width = self.ui_manager.slice_canvas.winfo_width() or 200
                    canvas_height = self.ui_manager.slice_canvas.winfo_height() or 200
                else:
                    canvas_width = 200
                    canvas_height = 200
                    logger.debug("slice_canvas not available, using default dimensions")

                # 计算合适的缩放比例，充分利用可视区域
                img_width, img_height = enhanced_slice.size
                scale_factor = min((canvas_width - 20) / img_width, (canvas_height - 20) / img_height)
                scale_factor = min(scale_factor, 2.5)  # 最大放大2.5倍，避免过度模糊

                # 缩放图像以更好地利用空间
                if scale_factor > 1.0:  # 只有当需要放大时才缩放
                    new_width = int(img_width * scale_factor)
                    new_height = int(img_height * scale_factor)
                    enhanced_slice = enhanced_slice.resize((new_width, new_height))

                self.slice_photo = ImageTk.PhotoImage(enhanced_slice)

                # 显示在画布上
                if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'slice_canvas') and self.ui_manager.slice_canvas:
                    self.ui_manager.slice_canvas.delete("all")
                    if canvas_width > 1 and canvas_height > 1:  # 确保画布已初始化
                        x = canvas_width // 2
                        y = canvas_height // 2
                        self.ui_manager.slice_canvas.create_image(x, y, image=self.slice_photo)
                        logger.debug("成功在slice_canvas上显示图像")
                    else:
                        logger.debug("画布尺寸无效，跳过图像显示")
                else:
                    logger.error("slice_canvas不可用，无法显示图像", exc_info=True)

            # 加载对应的全景图（强制每次都加载以确保刷新）
            self._load_panoramic_image()

            # 更新当前孔位指示框
            self._draw_current_hole_indicator()

            # 更新切片信息，包含标注状态
            self._update_slice_info_display()

            # 根据视图模式加载相应的标注数据
            if self.view_mode == "model":
                # 模型视图：不加载已有标注，显示模型预测结果
                self._load_model_view_data()
            else:
                # 人工视图：只显示人工标注结果，无则不显示任何结果
                self._load_existing_annotation()

            # 重置修改标记
            self.is_modified = False

            # 尝试加载配置文件标注（仅在非模型视图时）
            if self.view_mode != "model":
                self._load_config_annotations()

        except Exception as e:
            logger.error(f"加载切片失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"加载切片失败: {str(e)}")

    def _auto_switch_view_mode(self):
        """自动切换视图模式"""
        try:
            # 检查是否有人工标注数据
            has_manual_annotations = False
            for annotation in self.current_dataset.annotations:
                if hasattr(annotation, 'annotation_source'):
                    if annotation.annotation_source in ['enhanced_manual', 'manual']:
                        has_manual_annotations = True
                        break

            if has_manual_annotations:
                self.view_mode = "manual"
                self.view_mode_var.set("manual")
            elif hasattr(self, 'model_suggestion_loaded') and self.model_suggestion_loaded:
                self.view_mode = "model"
                self.view_mode_var.set("model")
            else:
                self.view_mode = "manual"
                self.view_mode_var.set("manual")

        except Exception as e:
            logger.error(f"自动切换视图模式失败: {str(e)}")

    def _update_progress(self):
        """更新进度显示"""
        if self.slice_files:
            current = self.current_slice_index + 1
            total = len(self.slice_files)
            if hasattr(self, 'progress_label'):
                self.progress_label.config(text=f"{current}/{total}")
        else:
            if hasattr(self, 'progress_label'):
                self.progress_label.config(text="0/0")

    def _load_panoramic_image(self):
        """加载全景图"""
        if not self.current_panoramic_id:
            return

        try:
            # 查找全景图文件 - 使用子目录模式
            panoramic_file = self.image_service.find_panoramic_image(
                f"{self.current_panoramic_id}/hole_1.png",
                self.panoramic_directory
            )

            if not panoramic_file:
                if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_info_label') and self.ui_manager.panoramic_info_label:
                    self.ui_manager.panoramic_info_label.config(text=f"未找到全景图: {self.current_panoramic_id}")
                else:
                    logger.debug("panoramic_info_label not available")
                return

            # 加载全景图
            self.panoramic_image = self.image_service.load_panoramic_image(panoramic_file)
            if self.panoramic_image:
                # 调整图像大小以适应画布
                if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_canvas') and self.ui_manager.panoramic_canvas:
                    canvas_width = self.ui_manager.panoramic_canvas.winfo_width() or 800
                    canvas_height = self.ui_manager.panoramic_canvas.winfo_height() or 600
                else:
                    canvas_width = 800
                    canvas_height = 600
                    logger.debug("panoramic_canvas not available, using default dimensions")

                # 获取原始图像尺寸（在缩放之前）
                original_img_width, original_img_height = self.panoramic_image.size

                # 坐标调整功能已禁用 - 注释掉相关调用
                # if hasattr(self, 'hole_manager') and self.hole_manager:
                #     self.hole_manager.adjust_coordinates_for_canvas(
                #         canvas_width, canvas_height, original_img_width, original_img_height
                #     )

                # 计算缩放比例
                scale_factor = min(canvas_width / original_img_width, canvas_height / original_img_height)

                # 保存缩放后的图像尺寸用于后续计算
                if scale_factor < 1.0:
                    new_width = int(original_img_width * scale_factor)
                    new_height = int(original_img_height * scale_factor)
                    self.panoramic_image = self.panoramic_image.resize((new_width, new_height))
                    # 更新图像尺寸为缩放后的尺寸
                    img_width, img_height = new_width, new_height
                else:
                    img_width, img_height = original_img_width, original_img_height

                self.panoramic_photo = ImageTk.PhotoImage(self.panoramic_image)

                # 显示在画布上
                if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_canvas') and self.ui_manager.panoramic_canvas:
                    self.ui_manager.panoramic_canvas.delete("all")
                    x = canvas_width // 2
                    y = canvas_height // 2
                    self.ui_manager.panoramic_canvas.create_image(x, y, image=self.panoramic_photo)
                    logger.debug("成功在panoramic_canvas上显示图像")
                else:
                    logger.error("panoramic_canvas不可用，无法显示图像", exc_info=True)

                # 绘制孔位网格
                self._draw_hole_grid()

            if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_info_label') and self.ui_manager.panoramic_info_label:
                self.ui_manager.panoramic_info_label.config(text=f"全景图: {self.current_panoramic_id}")
            else:
                logger.debug("panoramic_info_label not available for setting panoramic_id")

        except Exception as e:
            logger.error(f"加载全景图失败: {e}", exc_info=True)

    def _draw_hole_grid(self):
        """绘制孔位网格"""
        if not self.panoramic_image or not self.hole_manager:
            return

        try:
            if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_canvas') and self.ui_manager.panoramic_canvas:
                canvas_width = self.ui_manager.panoramic_canvas.winfo_width()
                canvas_height = self.ui_manager.panoramic_canvas.winfo_height()
                img_width, img_height = self.panoramic_image.size
            else:
                logger.warning("panoramic_canvas not available for drawing hole grid")
                return

            # 坐标调整功能已禁用 - 注释掉相关调用
            # if hasattr(self, 'hole_manager') and self.hole_manager:
            #     self.hole_manager.adjust_coordinates_for_canvas(
            #         canvas_width, canvas_height, img_width, img_height
            #     )

            # 计算缩放比例和偏移
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y)

            # 计算图像在画布上的偏移（居中显示）
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            offset_x = (canvas_width - scaled_width) / 2
            offset_y = (canvas_height - scaled_height) / 2

            # Debug日志：输出坐标转换参数
            logger.debug(f"[HOLE_GRID] 画布尺寸: {canvas_width}x{canvas_height}")
            logger.debug(f"[HOLE_GRID] 图像尺寸: {img_width}x{img_height}")
            logger.debug(f"[HOLE_GRID] 缩放比例: {scale:.3f} (scale_x={scale_x:.3f}, scale_y={scale_y:.3f})")
            logger.debug(f"[HOLE_GRID] 缩放后尺寸: {scaled_width:.1f}x{scaled_height:.1f}")
            logger.debug(f"[HOLE_GRID] 居中偏移: offset_x={offset_x:.1f}, offset_y={offset_y:.1f}")
            logger.debug(f"[HOLE_GRID] HoleManager坐标: first_hole=({self.hole_manager.first_hole_x},{self.hole_manager.first_hole_y})")

            # 绘制孔位
            drawn_count = 0
            for row in range(10):  # 10行
                for col in range(12):  # 12列
                    hole_number = row * 12 + col + 1

                    # 获取孔位位置
                    hole_pos = self.hole_manager.get_hole_center_coordinates(hole_number)
                    if hole_pos:
                        # 原始图像坐标
                        orig_x, orig_y = hole_pos

                        # 坐标调整功能已禁用，直接使用缩放后的坐标
                        adjusted_x, adjusted_y = orig_x * scale, orig_y * scale

                        # 转换到画布坐标：缩放 + 偏移
                        x = int(adjusted_x + offset_x)
                        y = int(adjusted_y + offset_y)

                        # Debug日志：每个孔位的坐标转换
                        if hole_number <= 5 or hole_number % 20 == 0:  # 只记录前5个和每20个孔位
                            logger.debug(f"[HOLE_GRID] 孔位{hole_number}: 原始({orig_x:.1f},{orig_y:.1f}) -> 调整后({adjusted_x:.1f},{adjusted_y:.1f}) -> 画布({x},{y})")

                        # 绘制孔位圆圈
                        radius = 8
                        self.ui_manager.panoramic_canvas.create_oval(
                            x - radius, y - radius, x + radius, y + radius,
                            outline='red', width=2
                        )

                        # Debug日志：孔位编号字体和定位信息
                        if hole_number <= 5 or hole_number % 20 == 0:  # 只记录前5个和每20个孔位
                            logger.debug(f"[HOLE_GRID_FONT] 孔位{hole_number}: 位置({x},{y}), 字体大小=12, 颜色=red, 画布=panoramic_canvas")

                        # 绘制孔位编号
                        self.ui_manager.panoramic_canvas.create_text(
                            x, y, text=str(hole_number),
                            fill='red', font=('Arial', 16, 'bold')
                        )

                        drawn_count += 1

            logger.debug(f"[HOLE_GRID] 成功绘制 {drawn_count} 个孔位")

        except Exception as e:
            logger.error(f"绘制孔位网格失败: {e}", exc_info=True)

    def _draw_current_hole_indicator(self):
        """绘制当前孔位指示框"""
        if not self.panoramic_image or not self.hole_manager:
            return

        try:
            if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_canvas') and self.ui_manager.panoramic_canvas:
                canvas_width = self.ui_manager.panoramic_canvas.winfo_width()
                canvas_height = self.ui_manager.panoramic_canvas.winfo_height()
                img_width, img_height = self.panoramic_image.size
            else:
                logger.warning("panoramic_canvas not available for drawing current hole indicator")
                return

            # 计算缩放比例和偏移
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y)

            # 计算图像在画布上的偏移（居中显示）
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            offset_x = (canvas_width - scaled_width) / 2
            offset_y = (canvas_height - scaled_height) / 2

            # 获取当前孔位位置
            hole_pos = self.hole_manager.get_hole_center_coordinates(self.current_hole_number)
            if hole_pos:
                # 原始图像坐标
                orig_x, orig_y = hole_pos

                # 坐标调整功能已禁用，直接使用缩放后的坐标
                adjusted_x, adjusted_y = orig_x * scale, orig_y * scale

                # 转换到画布坐标：缩放 + 偏移
                x = int(adjusted_x + offset_x)
                y = int(adjusted_y + offset_y)

                # Debug日志：当前孔位坐标转换
                logger.debug(f"[CURRENT_HOLE] 当前孔位{self.current_hole_number}: 原始({orig_x:.1f},{orig_y:.1f}) -> 调整后({adjusted_x:.1f},{adjusted_y:.1f}) -> 画布({x},{y})")
                logger.debug(f"[CURRENT_HOLE] 缩放比例: {scale:.3f}, 偏移: ({offset_x:.1f},{offset_y:.1f})")

                # 绘制指示框
                size = 12
                self.ui_manager.panoramic_canvas.create_rectangle(
                    x - size, y - size, x + size, y + size,
                    outline='yellow', width=3
                )

                logger.debug(f"[CURRENT_HOLE] 绘制黄色指示框: ({x-size},{y-size}) to ({x+size},{y+size})")

        except Exception as e:
            logger.error(f"绘制当前孔位指示框失败: {e}", exc_info=True)

    def _update_slice_info_display(self):
        """更新切片信息显示"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return

        current_file = self.slice_files[self.current_slice_index]
        hole_label = f"A{self.current_hole_number}" if self.current_hole_number <= 12 else f"其他孔位"

        # 更新切片信息标签
        if hasattr(self, 'slice_info_label'):
            self.slice_info_label.config(text=f"{current_file['filename']} - {hole_label}({self.current_hole_number})")

        # 更新标注预览标签
        annotation_status = self._get_annotation_status_text()
        if hasattr(self, 'annotation_preview_label'):
            self.annotation_preview_label.config(text=f"标注状态: {annotation_status}")

        # 更新详细标注信息
        detailed_info = self._get_detailed_annotation_info()
        if hasattr(self, 'detailed_annotation_label'):
            self.detailed_annotation_label.config(text=detailed_info)

    def _get_annotation_status_text(self):
        """获取标注状态文本"""
        # 获取CFG配置信息
        config_data = self._get_current_panoramic_config()
        cfg_growth_level = None
        if config_data and self.current_hole_number in config_data:
            cfg_growth_level = config_data[self.current_hole_number]

        # 检查当前视图模式
        if self.view_mode == "model":
            # 模型视图模式：优先显示人工标注状态，如果没有标注则显示CFG信息
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
                    # 增强标注 - 显示已标注状态，包含CFG信息
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

                            # 包含CFG信息
                            if cfg_growth_level:
                                status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                            else:
                                status_text = f"已标注 ({datetime_str})"

                            return status_text
                        except Exception as e:
                            logger.error(f"解析保存的时间戳失败: {e}")

                    # 如果标注对象中没有时间戳，尝试从内存缓存获取
                    if annotation_key in self.last_annotation_time:
                        import datetime
                        datetime_str = self.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")

                        # 包含CFG信息
                        if cfg_growth_level:
                            status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                        else:
                            status_text = f"已标注 ({datetime_str})"

                        return status_text

                    # 如果都没有时间戳，显示基本状态
                    if cfg_growth_level:
                        status_text = f"cfg-{cfg_growth_level} 已标注"
                    else:
                        status_text = "已标注"
                    return status_text
                else:
                    # 配置导入或其他类型 - 显示为配置导入状态
                    if cfg_growth_level:
                        return f"cfg-{cfg_growth_level} 配置导入"
                    else:
                        return "配置导入"
            else:
                # 无标注时显示CFG信息或模型预测状态
                if cfg_growth_level:
                    return f"cfg-{cfg_growth_level} 未标注"
                else:
                    # 没有CFG配置时显示模型预测状态
                    if hasattr(self, 'hole_manager') and self.hole_manager:
                        if self.hole_manager.has_hole_suggestion(self.current_hole_number):
                            return "模型预测"
                        else:
                            return "无模型预测"
                    else:
                        return "模型数据未加载"

        else:
            # 人工视图模式：显示人工标注状态，集成CFG信息，不显示"配置导入"
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
                    # 增强标注 - 显示已标注状态，包含CFG信息
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

                            # 包含CFG信息
                            if cfg_growth_level:
                                status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                            else:
                                status_text = f"已标注 ({datetime_str})"

                            return status_text
                        except Exception as e:
                            logger.error(f"解析保存的时间戳失败: {e}")

                    # 如果标注对象中没有时间戳，尝试从内存缓存获取
                    if annotation_key in self.last_annotation_time:
                        import datetime
                        datetime_str = self.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")

                        # 包含CFG信息
                        if cfg_growth_level:
                            status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                        else:
                            status_text = f"已标注 ({datetime_str})"

                        return status_text

                    # 如果都没有时间戳，显示基本状态
                    if cfg_growth_level:
                        status_text = f"cfg-{cfg_growth_level} 已标注"
                    else:
                        status_text = "已标注"
                    return status_text
                else:
                    # 配置导入或其他类型 - 显示CFG信息，不显示"配置导入"
                    if cfg_growth_level:
                        return f"cfg-{cfg_growth_level} 配置导入"
                    else:
                        return "配置导入"
            else:
                # 无标注时显示CFG信息
                if cfg_growth_level:
                    return f"cfg-{cfg_growth_level} 未标注"
                else:
                    return "无CFG"

    def _get_detailed_annotation_info(self):
        """获取详细标注信息用于显示"""
        # 检查当前视图模式
        if self.view_mode == "model":
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
                        growth_map = {
                            'negative': '阴性',
                            'weak_growth': '弱生长',
                            'positive': '阳性'
                        }
                        growth_text = growth_map.get(suggestion.growth_level, suggestion.growth_level)
                        details.append(growth_text)

                    # 生长模式
                    if hasattr(suggestion, 'growth_pattern') and suggestion.growth_pattern:
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
                    growth_map = {
                        'negative': '阴性',
                        'weak_growth': '弱生长',
                        'positive': '阳性'
                    }
                    growth_text = growth_map.get(existing_ann.growth_level, existing_ann.growth_level)
                    details.append(growth_text)

                # 生长模式（如果是增强标注）
                if hasattr(existing_ann, 'growth_pattern') and existing_ann.growth_pattern:
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

    def _get_current_panoramic_config(self):
        """获取当前全景图的配置数据"""
        # 这里应该实现从配置文件加载配置数据的逻辑
        # 暂时返回空字典
        return {}

    def _load_existing_annotation(self):
        """加载现有标注"""
        if not self.current_dataset:
            return

        existing_ann = self.current_dataset.get_annotation_by_hole(
            self.current_panoramic_id,
            self.current_hole_number
        )

        if existing_ann and hasattr(self, 'annotation_panel') and self.annotation_panel:
            # 设置标注数据到增强标注面板
            if hasattr(existing_ann, 'microbe_type'):
                self.annotation_panel.microbe_type_var.set(existing_ann.microbe_type)

            if hasattr(existing_ann, 'growth_level'):
                self.annotation_panel.current_growth_level.set(existing_ann.growth_level)

            # 设置干扰因素
            if hasattr(existing_ann, 'interference_factors') and existing_ann.interference_factors:
                for factor in self.annotation_panel.interference_vars:
                    self.annotation_panel.interference_vars[factor].set(factor in existing_ann.interference_factors)

    def _load_config_annotations(self):
        """加载配置文件标注"""
        # 这里应该实现从配置文件加载标注的逻辑
        pass

    def _load_model_view_data(self):
        """加载模型视图数据 - 显示模型预测结果"""
        try:
            if not hasattr(self, 'hole_manager') or not self.hole_manager:
                return

            suggestion = self.hole_manager.get_hole_suggestion(self.current_hole_number)
            if suggestion and hasattr(self, 'annotation_panel') and self.annotation_panel:
                # 设置模型预测结果到增强标注面板
                if hasattr(suggestion, 'microbe_type') and suggestion.microbe_type:
                    self.annotation_panel.microbe_type_var.set(suggestion.microbe_type)

                if hasattr(suggestion, 'growth_level') and suggestion.growth_level:
                    self.annotation_panel.current_growth_level.set(suggestion.growth_level)

                # 设置干扰因素
                if hasattr(suggestion, 'interference_factors') and suggestion.interference_factors:
                    for factor in self.annotation_panel.interference_vars:
                        self.annotation_panel.interference_vars[factor].set(factor in suggestion.interference_factors)
            else:
                # 无预测结果时，重置面板
                if hasattr(self, 'annotation_panel') and self.annotation_panel:
                    self.annotation_panel.reset_annotation()

        except Exception as e:
            logger.error(f"加载模型视图数据失败: {str(e)}")

    def _switch_to_panoramic(self, panoramic_id):
        """自动切换到指定全景图（用于继续标注功能，不显示错误消息框）"""
        if panoramic_id not in self.panoramic_ids:
            logger.debug(f"全景图 {panoramic_id} 不在可用列表中")
            return False

        # 保存当前标注
        self._save_current_annotation_internal("navigation")

        # 查找目标全景图的第一个孔位
        target_slice_index = None
        start_hole = self.hole_manager.start_hole_number if self.hole_manager else 25

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
            if hasattr(self, 'ui_manager') and self.ui_manager and hasattr(self.ui_manager, 'panoramic_combobox') and self.ui_manager.panoramic_combobox:
                self.ui_manager.panoramic_combobox.set(panoramic_id)
            else:
                logger.debug("panoramic_combobox not available for setting panoramic_id in switch_to_panoramic")

            # 加载新的切片
            self._load_current_slice()
            self._update_progress()
            self._update_statistics()

            # 保留关键的用户提示信息
            logger.info(f"已切换到全景图: {panoramic_id}")
            return True
        else:
            logger.debug(f"未找到全景图 {panoramic_id} 的切片文件")
            return False

    def _switch_to_hole(self, hole_number):
        """切换到指定孔位"""
        if not self.slice_files:
            return

        # 查找指定孔位的切片
        target_index = None
        for i, slice_file in enumerate(self.slice_files):
            if (slice_file['panoramic_id'] == self.current_panoramic_id and
                slice_file['hole_number'] == hole_number):
                target_index = i
                break

        if target_index is not None:
            self.current_slice_index = target_index
            self.current_hole_number = hole_number
            self.hole_number_var.set(str(hole_number))

            # 加载切片
            self._load_current_slice()
            self._update_progress()

            logger.debug(f"已切换到孔位: {hole_number}")

    def _save_current_annotation_internal(self, save_type="manual"):
        """内部保存当前标注的方法"""
        try:
            # 这里应该实现保存当前标注的逻辑
            pass
        except Exception as e:
            logger.error(f"保存当前标注失败: {str(e)}")

    def _update_statistics(self):
        """更新统计信息"""
        if not self.current_dataset:
            return

        # 计算统计数据
        total_annotations = len(self.current_dataset.annotations)
        negative_count = 0
        weak_growth_count = 0
        positive_count = 0

        for annotation in self.current_dataset.annotations:
            if hasattr(annotation, 'growth_level'):
                if annotation.growth_level == 'negative':
                    negative_count += 1
                elif annotation.growth_level == 'weak_growth':
                    weak_growth_count += 1
                elif annotation.growth_level == 'positive':
                    positive_count += 1

        # 更新统计标签
        stats_text = f"统计: 未标注 {120 - total_annotations}, 阴性 {negative_count}, 弱生长 {weak_growth_count}, 阳性 {positive_count}"
        if hasattr(self, 'stats_label'):
            self.stats_label.config(text=stats_text)

    def _force_timestamp_sync_after_load(self):
        """强制时间戳同步 - 修复加载标注后时间戳显示问题"""
        try:
            logger.debug(f"强制同步孔位{self.current_hole_number}的时间戳")

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
                    logger.debug(f"成功同步时间戳: {annotation_key} -> {dt.strftime('%m-%d %H:%M:%S')}")

                    # 再次刷新显示以确保时间戳正确显示
                    self._update_slice_info_display()

                except Exception as e:
                    logger.debug(f"时间戳解析失败: {e}")
            else:
                logger.debug(f"孔位{self.current_hole_number}无有效时间戳")

        except Exception as e:
            logger.error(f"强制时间戳同步失败: {str(e)}")

    def _verify_timestamp_sync_after_load(self):
        """验证时间戳同步状态 - 确保加载后显示正确的时间戳"""
        try:
            logger.debug(f"验证孔位{self.current_hole_number}的时间戳同步状态")

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

                logger.debug(f"内存中有时间戳: {has_memory_timestamp}")
                logger.debug(f"标注对象有时间戳: {has_annotation_timestamp}")

                if has_memory_timestamp:
                    memory_time = self.last_annotation_time[annotation_key]
                    logger.debug(f"内存时间戳: {memory_time.strftime('%m-%d %H:%M:%S')}")
                elif has_annotation_timestamp:
                    logger.debug(f"标注对象时间戳: {current_ann.timestamp}")
                    # 如果内存中没有但标注对象有，再次强制同步
                    self._force_timestamp_sync_after_load()

                # 最终刷新显示
                self._update_slice_info_display()
                logger.debug(f"验证完成，刷新显示")
            else:
                logger.debug(f"孔位{self.current_hole_number}无标注")

        except Exception as e:
            logger.error(f"时间戳验证失败: {str(e)}")

    def _verify_load_refresh(self):
        """验证加载后的刷新状态，确保当前孔位完全同步"""
        try:
            logger.debug(f"验证孔位{self.current_hole_number}刷新状态")

            # 再次检查当前孔位的标注状态
            current_ann = self.current_dataset.get_annotation_by_hole(
                self.current_panoramic_id,
                self.current_hole_number
            )

            if current_ann and hasattr(self, 'annotation_panel') and self.annotation_panel:
                logger.debug(f"发现当前孔位有标注，验证增强面板同步状态")

                # 检查增强面板状态是否正确
                if hasattr(current_ann, 'enhanced_data') and current_ann.enhanced_data:
                    logger.debug(f"验证增强数据同步状态")
                    # 确保增强数据已正确加载到面板

                # 强制一次最终的状态更新
                self._update_slice_info_display()
                self._update_statistics()

                logger.debug(f"孔位{self.current_hole_number}状态验证完成")
            else:
                logger.debug(f"孔位{self.current_hole_number}无需验证或无增强面板")

        except Exception as e:
            logger.error(f"加载后验证失败: {str(e)}")

    def _on_enhanced_annotation_change(self, annotation_data=None):
        """增强标注变化回调"""
        # 标记当前标注已修改
        self.is_modified = True

        # 更新详细标注信息显示
        detailed_info = self._get_detailed_annotation_info()
        if hasattr(self, 'detailed_annotation_label'):
            self.detailed_annotation_label.config(text=detailed_info)

        # 可以在这里添加实时预览或验证逻辑
        pass

    def _update_hole_suggestion_display(self):
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

            # 更新hole_config_panel的建议显示
            if hasattr(self, 'hole_config_panel'):
                if suggestion:
                    self.hole_config_panel.update_suggestion(suggestion)
                else:
                    self.hole_config_panel.clear_suggestion()

        except Exception as e:
            logger.error(f"更新孔位建议显示失败: {str(e)}")



    # ==================== 坐标定位调试方法 ====================

    def set_coordinate_debug_mode(self, enabled: bool):
        """设置坐标调试模式"""
        self.debug_coordinate_offset = enabled
        logger.info(f"坐标调试模式: {'启用' if enabled else '禁用'}")

    def set_coordinate_offset(self, offset_x: float, offset_y: float):
        """设置坐标偏移调整"""
        self.coordinate_offset_x = offset_x
        self.coordinate_offset_y = offset_y
        logger.info(f"设置坐标偏移: X={offset_x}, Y={offset_y}")

    def set_coordinate_scale_adjust(self, scale_adjust: float):
        """设置缩放比例调整因子"""
        self.coordinate_scale_adjust = scale_adjust
        logger.info(f"设置缩放调整因子: {scale_adjust}")

    # 坐标调整功能已禁用
    # def reset_coordinate_adjustments(self):
    #     """重置所有坐标调整参数"""
    #     self.coordinate_offset_x = 0.0
    #     self.coordinate_offset_y = 0.0
    #     self.coordinate_scale_adjust = 1.0
    #     logger.info("重置所有坐标调整参数")

    def get_coordinate_debug_info(self) -> dict:
        """获取坐标调试信息"""
        return {
            'debug_mode': self.debug_coordinate_offset,
            'offset_x': self.coordinate_offset_x,
            'offset_y': self.coordinate_offset_y,
            'scale_adjust': self.coordinate_scale_adjust
        }

    # 坐标调整功能已禁用
    # def _apply_coordinate_adjustments(self, x: float, y: float, scale: float) -> tuple:
    #     """应用坐标调整参数"""
    #     if not self.debug_coordinate_offset:
    #         return x * scale, y * scale

    #     # 应用缩放调整
    #     adjusted_scale = scale * self.coordinate_scale_adjust

    #     # 应用偏移调整
    #     adjusted_x = x * adjusted_scale + self.coordinate_offset_x
    #     adjusted_y = y * adjusted_scale + self.coordinate_offset_y

        return adjusted_x, adjusted_y

    def refresh_panoramic_display(self):
        """刷新全景图显示，重新绘制所有元素"""
        try:
            logger.info("刷新全景图显示...")

            # 重新加载全景图
            self._load_panoramic_image()

            # 重新绘制当前孔位指示框
            self._draw_current_hole_indicator()

            logger.info("全景图显示刷新完成")

        except Exception as e:
            logger.error(f"刷新全景图显示失败: {str(e)}")

    # ==================== 日志控制方法 ====================

    def toggle_debug_logging(self):
        """切换调试日志开关"""
        try:
            if is_debug_logging_enabled():
                disable_debug_logging()
                self.update_status("调试日志已关闭")
            else:
                enable_debug_logging()
                self.update_status("调试日志已开启")
        except Exception as e:
            logger.error(f"切换调试日志失败: {str(e)}")
            self.update_status(f"切换调试日志失败: {str(e)}")

    def enable_debug_logging(self):
        """启用调试日志"""
        try:
            enable_debug_logging()
            self.update_status("调试日志已开启")
        except Exception as e:
            logger.error(f"启用调试日志失败: {str(e)}")
            self.update_status(f"启用调试日志失败: {str(e)}")

    def disable_debug_logging(self):
        """禁用调试日志"""
        try:
            disable_debug_logging()
            self.update_status("调试日志已关闭")
        except Exception as e:
            logger.error(f"禁用调试日志失败: {str(e)}")
            self.update_status(f"禁用调试日志失败: {str(e)}")

    def is_debug_enabled(self) -> bool:
        """检查调试日志是否启用"""
        return is_debug_logging_enabled()