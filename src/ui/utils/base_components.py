"""
基础抽象类模块

定义所有UI组件的基础接口和通用功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable
import tkinter as tk
from tkinter import ttk
import logging

from .event_bus import EventBus, Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class BaseController(ABC):
    """控制器基类"""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_initialized = False
        self._event_listeners: List = []
    
    @abstractmethod
    def initialize(self) -> None:
        """初始化控制器"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None], 
                 source_filter: Optional[str] = None):
        """订阅事件"""
        listener = self.event_bus.subscribe(event_type, callback, source_filter)
        self._event_listeners.append(listener)
        return listener
    
    def publish(self, event_type: EventType, data: Any = None, 
                source: Optional[str] = None):
        """发布事件"""
        self.event_bus.publish(event_type, data, source or self.__class__.__name__)
    
    def handle_error(self, error: Exception, context: str = ""):
        """错误处理"""
        # 更详细的错误信息
        error_type = type(error).__name__
        error_msg = f"{context}: {error_type} - {error}" if context else f"{error_type}: {error}"
        self.logger.error(error_msg)
        # 只在非测试环境下发布错误事件，避免循环
        if not hasattr(self, '_is_test') or not self._is_test:
            self.publish(EventType.ERROR_OCCURRED, {"error": error_msg, "context": context})
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._is_initialized
    
    def _mark_initialized(self):
        """标记为已初始化"""
        self._is_initialized = True
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    def cleanup_listeners(self):
        """清理事件监听器"""
        for listener in self._event_listeners:
            self.event_bus.unsubscribe(listener)
        self._event_listeners.clear()


class BaseView(ABC):
    """视图基类"""
    
    def __init__(self, parent: tk.Widget, controller: Optional[BaseController] = None):
        self.parent = parent
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.widget: Optional[tk.Widget] = None
        self._is_built = False
        self._child_views: List['BaseView'] = []
    
    @abstractmethod
    def build_ui(self) -> tk.Widget:
        """构建UI界面"""
        pass
    
    @abstractmethod
    def setup_layout(self) -> None:
        """设置布局"""
        pass
    
    @abstractmethod
    def bind_events(self) -> None:
        """绑定事件"""
        pass
    
    def get_widget(self) -> tk.Widget:
        """获取主widget"""
        if not self._is_built:
            self.widget = self.build_ui()
            self.setup_layout()
            self.bind_events()
            self._is_built = True
            self.logger.info(f"{self.__class__.__name__} UI built")
        return self.widget
    
    def add_child_view(self, child_view: 'BaseView'):
        """添加子视图"""
        self._child_views.append(child_view)
    
    def remove_child_view(self, child_view: 'BaseView'):
        """移除子视图"""
        if child_view in self._child_views:
            self._child_views.remove(child_view)
    
    def show(self):
        """显示视图"""
        if self.widget:
            self.widget.pack()
    
    def hide(self):
        """隐藏视图"""
        if self.widget:
            self.widget.pack_forget()
    
    def enable(self):
        """启用视图"""
        if self.widget:
            self.widget.configure(state='normal')
    
    def disable(self):
        """禁用视图"""
        if self.widget:
            self.widget.configure(state='disabled')
    
    def destroy(self):
        """销毁视图"""
        for child in self._child_views:
            child.destroy()
        if self.widget:
            self.widget.destroy()
        self.widget = None
        self._is_built = False


class BaseFrameView(BaseView):
    """基于Frame的视图基类"""
    
    def build_ui(self) -> tk.Widget:
        """创建Frame"""
        self.widget = ttk.Frame(self.parent)
        return self.widget


class BaseDialogView(BaseView):
    """对话框基类"""
    
    def __init__(self, parent: tk.Widget, controller: Optional[BaseController] = None,
                 title: str = "", modal: bool = True):
        super().__init__(parent, controller)
        self.title = title
        self.modal = modal
        self.result: Optional[Any] = None
        self.dialog: Optional[tk.Toplevel] = None
    
    def build_ui(self) -> tk.Widget:
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.transient(self.parent)
        self.dialog.grab_set() if self.modal else None
        
        # 对话框关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        return self.dialog
    
    def setup_layout(self) -> None:
        """设置对话框布局"""
        if self.dialog:
            # 创建内容框架
            content_frame = ttk.Frame(self.dialog, padding="10")
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # 创建按钮框架
            button_frame = ttk.Frame(self.dialog)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            # 添加默认按钮
            ok_button = ttk.Button(button_frame, text="确定", command=self._on_ok)
            ok_button.pack(side=tk.RIGHT, padx=(5, 0))
            
            cancel_button = ttk.Button(button_frame, text="取消", command=self._on_cancel)
            cancel_button.pack(side=tk.RIGHT)
    
    def _on_ok(self):
        """确定按钮处理"""
        self.on_ok()
    
    def _on_cancel(self):
        """取消按钮处理"""
        self.on_cancel()
    
    def _on_close(self):
        """关闭对话框"""
        self.on_cancel()
    
    def on_ok(self):
        """确定按钮事件 - 子类可重写"""
        self.close()
    
    def on_cancel(self):
        """取消按钮事件 - 子类可重写"""
        self.close()
    
    def close(self, result: Any = None):
        """关闭对话框"""
        self.result = result
        if self.dialog:
            self.dialog.destroy()
        self.dialog = None
    
    def show_dialog(self) -> Any:
        """显示对话框并返回结果"""
        self.get_widget()
        if self.modal:
            self.dialog.wait_window()
        return self.result


class ComponentMixin:
    """组件混入类 - 提供通用功能"""
    
    def create_tooltip(self, widget: tk.Widget, text: str):
        """创建工具提示"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief=tk.SOLID, borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def set_widget_state(self, widget: tk.Widget, enabled: bool):
        """设置widget状态"""
        state = 'normal' if enabled else 'disabled'
        try:
            widget.configure(state=state)
        except tk.TclError:
            # 某些widget不支持state属性
            pass
    
    def center_window(self, window: tk.Toplevel):
        """居中窗口"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')