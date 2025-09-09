"""
主应用程序模块

应用程序的核心入口和依赖注入容器
"""

import tkinter as tk
from typing import Dict, Any, Optional, List
import logging
import sys
import os


from src.ui.utils.event_bus import EventBus, EventType, start_event_bus, stop_event_bus
from src.ui.utils.base_components import BaseController
from src.ui.models.ui_state import UIStateManager, initialize_ui_state
from src.ui.controllers import MainController, ImageController, AnnotationController
from src.services.panoramic_image_service import PanoramicImageService
from src.services.annotation_engine import AnnotationEngine
from src.services.config_file_service import ConfigFileService
from src.core.config import Config
from src.core.logger import setup_logger

logger = logging.getLogger(__name__)


class ServiceContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, name: str, service: Any, singleton: bool = False):
        """注册服务"""
        if singleton:
            self._singletons[name] = service
        else:
            self._services[name] = service
    
    def get(self, name: str) -> Any:
        """获取服务"""
        if name in self._singletons:
            return self._singletons[name]
        elif name in self._services:
            return self._services[name]
        else:
            raise ValueError(f"Service '{name}' not found")
    
    def has(self, name: str) -> bool:
        """检查服务是否存在"""
        return name in self._singletons or name in self._services

    def clear(self):
        """清空所有服务"""
        self._services.clear()
        self._singletons.clear()
    
    def setup_core_services(self):
        """设置核心服务"""
        # 事件总线
        event_bus = EventBus()
        self.register('event_bus', event_bus, singleton=True)

        # 核心服务
        config = Config()
        self.register('config', config, singleton=True)

        # 日志服务
        logger_instance = setup_logger()
        self.register('logger', logger_instance, singleton=True)

        # UI状态管理器
        ui_state_manager = UIStateManager(event_bus)
        self.register('ui_state_manager', ui_state_manager, singleton=True)

        # 业务服务
        image_service = PanoramicImageService()
        self.register('image_service', image_service, singleton=True)

        annotation_engine = AnnotationEngine(config, logger_instance)
        self.register('annotation_engine', annotation_engine, singleton=True)

        config_service = ConfigFileService()
        self.register('config_service', config_service, singleton=True)
    
    def setup_controllers(self, controllers: List[BaseController]):
        """设置控制器"""
        for controller in controllers:
            controller_name = controller.__class__.__name__.lower().replace('controller', '')
            self.register(f'{controller_name}_controller', controller)


class PanoramicAnnotationApp:
    """全景标注应用程序主类"""
    
    def __init__(self, container: Optional[ServiceContainer] = None):
        self.container = container or ServiceContainer()
        self.root: Optional[tk.Tk] = None
        self.controllers: List[BaseController] = []
        self.is_running = False

        # 设置核心服务
        self.container.setup_core_services()

        # 注册应用实例到容器
        self.container.register('app', self, singleton=True)

        # 获取核心服务
        self.event_bus = self.container.get('event_bus')
        self.ui_state_manager = self.container.get('ui_state_manager')
        self.config = self.container.get('config')

        # 设置日志
        self._setup_logging()

        # 订阅应用事件
        self._subscribe_to_events()
    
    def _setup_logging(self):
        """设置日志系统"""
        setup_logger()
        logger.info("Starting Panoramic Annotation Application")
    
    def _subscribe_to_events(self):
        """订阅应用级事件"""
        self.event_bus.subscribe(EventType.APP_CLOSING, self._on_app_closing)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._on_error_occurred)
    
    def initialize(self) -> bool:
        """初始化应用程序"""
        try:
            logger.info("Initializing application...")
            
            # 启动事件总线
            start_event_bus()
            
            # 创建主窗口
            self.root = tk.Tk()
            self.root.title("全景标注工具")
            self.root.geometry("1600x900")
            
            # 设置窗口图标和其他属性
            self._setup_window()
            
            # 初始化控制器
            self._initialize_controllers()
            
            # 加载UI状态
            self.ui_state_manager.load_state()
            
            # 应用窗口状态
            self._apply_window_state()
            
            # 发布应用启动事件
            self.event_bus.publish(EventType.APP_STARTED)
            
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            return False
    
    def _setup_window(self):
        """设置主窗口"""
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        
        # 设置最小窗口大小
        self.root.minsize(1400, 800)
        
        # 居中窗口
        self._center_window()
        
        # 设置主题
        self._setup_theme()
    
    def _center_window(self):
        """居中窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_theme(self):
        """设置主题"""
        # 使用ttk主题
        style = tk.ttk.Style()
        style.theme_use('clam')  # 使用clam主题作为基础
        
        # 自定义样式
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Action.TButton', font=('Arial', 9))
    
    def _initialize_controllers(self):
        """初始化控制器"""
        logger.info("Initializing controllers...")
        
        try:
            # 创建主控制器
            self.main_controller = MainController(self.container)
            self.main_controller.initialize()
            
            # 创建图像控制器
            image_service = self.container.get('image_service') if self.container.has('image_service') else None
            self.image_controller = ImageController(image_service)
            self.image_controller.initialize()
            
            # 创建标注控制器
            annotation_engine = self.container.get('annotation_engine') if self.container.has('annotation_engine') else None
            self.annotation_controller = AnnotationController(annotation_engine)
            self.annotation_controller.initialize()
            
            # 注册控制器
            self.controllers.extend([
                self.main_controller,
                self.image_controller,
                self.annotation_controller
            ])
            
            # 注册到容器
            if self.container:
                self.container.register('main_controller', self.main_controller, singleton=True)
                self.container.register('image_controller', self.image_controller, singleton=True)
                self.container.register('annotation_controller', self.annotation_controller, singleton=True)
            
            logger.info("Controllers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize controllers: {e}")
            raise
    
    def _apply_window_state(self):
        """应用窗口状态"""
        state = self.ui_state_manager.get_state()
        
        # 恢复窗口大小和位置
        self.root.geometry(f"{state.window_size[0]}x{state.window_size[1]}+{state.window_position[0]}+{state.window_position[1]}")
        
        # 恢复最大化状态
        if state.is_maximized:
            self.root.state('zoomed')
    
    def run(self):
        """运行应用程序"""
        if not self.initialize():
            logger.error("Failed to initialize application")
            return False
        
        try:
            self.is_running = True
            logger.info("Starting application main loop")
            
            # 运行主循环
            self.root.mainloop()
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.cleanup()
        
        return True
    
    def quit(self):
        """退出应用程序"""
        logger.info("Quitting application...")
        
        # 发布关闭事件
        self.event_bus.publish(EventType.APP_CLOSING)
        
        # 保存UI状态
        self._save_ui_state()
        
        # 清理资源
        self.cleanup()
        
        # 退出Tkinter
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def cleanup(self):
        """清理资源"""
        if not self.is_running:
            return
        
        logger.info("Cleaning up application resources...")
        
        # 清理控制器
        for controller in self.controllers:
            try:
                controller.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up controller {controller.__class__.__name__}: {e}")
        
        # 停止事件总线
        stop_event_bus()
        
        # 清理服务
        self.container.clear()
        
        self.is_running = False
        logger.info("Application cleanup completed")
    
    def _save_ui_state(self):
        """保存UI状态"""
        try:
            # 保存窗口状态
            if self.root:
                state = self.ui_state_manager.get_state()
                state.window_size = (self.root.winfo_width(), self.root.winfo_height())
                state.window_position = (self.root.winfo_x(), self.root.winfo_y())
                state.is_maximized = (self.root.state() == 'zoomed')
                
                self.ui_state_manager.update_state(
                    window_size=state.window_size,
                    window_position=state.window_position,
                    is_maximized=state.is_maximized
                )
            
            # 保存到文件
            self.ui_state_manager.save_state()
            
        except Exception as e:
            logger.error(f"Failed to save UI state: {e}")
    
    def _on_app_closing(self, event):
        """处理应用关闭事件"""
        logger.info("Application closing event received")
    
    def _on_error_occurred(self, event):
        """处理错误事件"""
        error_data = event.data
        if isinstance(error_data, dict):
            error_msg = error_data.get('error', 'Unknown error')
            context = error_data.get('context', '')
            logger.error(f"Application error: {error_msg} (context: {context})")
        else:
            logger.error(f"Application error: {error_data}")
    
    def restart(self):
        """重启应用程序"""
        logger.info("Restarting application...")
        
        # 清理当前实例
        self.cleanup()
        
        # 创建新实例
        new_app = PanoramicAnnotationApp()
        new_app.run()
    
    def get_controller(self, controller_name: str) -> Optional[BaseController]:
        """获取控制器实例"""
        full_name = f"{controller_name.lower()}_controller"
        if self.container.has(full_name):
            return self.container.get(full_name)
        return None
    
    def add_controller(self, controller: BaseController):
        """动态添加控制器"""
        controller_name = controller.__class__.__name__.lower().replace('controller', '')
        self.container.register(f'{controller_name}_controller', controller)
        self.controllers.append(controller)
        
        # 初始化控制器
        try:
            controller.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize controller {controller.__class__.__name__}: {e}")


def create_app() -> PanoramicAnnotationApp:
    """创建应用程序实例"""
    # 初始化UI状态管理器
    initialize_ui_state()
    
    # 创建应用程序
    app = PanoramicAnnotationApp()
    
    return app


def main():
    """主入口函数"""
    try:
        # 创建应用程序
        app = create_app()
        
        # 运行应用程序
        success = app.run()
        
        # 退出代码
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Fatal application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()