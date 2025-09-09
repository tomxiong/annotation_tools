"""
事件系统模块

提供事件驱动的组件间通信机制，降低耦合度
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    # 图像相关事件
    IMAGE_LOADED = "image_loaded"
    IMAGE_PROCESSED = "image_processed"
    IMAGE_DISPLAY_CHANGED = "image_display_changed"
    
    # 导航相关事件
    NAVIGATION_CHANGED = "navigation_changed"
    HOLE_SELECTED = "hole_selected"
    HOLE_HOVERED = "hole_hovered"
    GRID_UPDATED = "grid_updated"
    
    # 标注相关事件
    ANNOTATION_ADDED = "annotation_added"
    ANNOTATION_UPDATED = "annotation_updated"
    ANNOTATION_DELETED = "annotation_deleted"
    ANNOTATION_SELECTED = "annotation_selected"
    ANNOTATION_SAVED = "annotation_saved"
    
    # 文件相关事件
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_EXPORTED = "file_exported"
    
    # UI状态事件
    UI_STATE_CHANGED = "ui_state_changed"
    VIEW_MODE_CHANGED = "view_mode_changed"
    SETTINGS_CHANGED = "settings_changed"
    
    # 应用事件
    APP_STARTED = "app_started"
    APP_CLOSING = "app_closing"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """事件数据结构"""
    type: EventType
    data: Any = None
    source: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class EventListener:
    """事件监听器"""
    
    def __init__(self, event_type: EventType, callback: Callable[[Event], None], 
                 source_filter: Optional[str] = None):
        self.event_type = event_type
        self.callback = callback
        self.source_filter = source_filter
        self.is_active = True
    
    def handle_event(self, event: Event):
        """处理事件"""
        if not self.is_active:
            return
        
        if self.source_filter and event.source != self.source_filter:
            return
        
        try:
            self.callback(event)
        except Exception as e:
            logger.error(f"Error handling event {event.type}: {e}")
    
    def deactivate(self):
        """停用监听器"""
        self.is_active = False


class EventBus:
    """事件总线 - 核心事件分发系统"""
    
    def __init__(self):
        self.listeners: Dict[EventType, List[EventListener]] = {}
        self.event_queue = queue.Queue()
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None], 
                  source_filter: Optional[str] = None) -> EventListener:
        """订阅事件"""
        listener = EventListener(event_type, callback, source_filter)
        
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(listener)
        self.logger.debug(f"Subscribed to {event_type}")
        return listener
    
    def unsubscribe(self, listener: EventListener):
        """取消订阅"""
        listener.deactivate()
        if listener.event_type in self.listeners:
            try:
                self.listeners[listener.event_type].remove(listener)
                self.logger.debug(f"Unsubscribed from {listener.event_type}")
            except ValueError:
                pass
    
    def publish(self, event_type: EventType, data: Any = None, 
                source: Optional[str] = None):
        """发布事件"""
        event = Event(event_type, data, source)
        self.event_queue.put(event)
        self.logger.debug(f"Published event: {event_type}")
    
    def start(self):
        """启动事件处理线程"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self.worker_thread.start()
            self.logger.info("Event bus started")
    
    def stop(self):
        """停止事件处理"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
        self.logger.info("Event bus stopped")
    
    def _process_events(self):
        """处理事件队列"""
        while self.is_running:
            try:
                event = self.event_queue.get(timeout=0.1)
                self._dispatch_event(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
    
    def _dispatch_event(self, event: Event):
        """分发事件给监听器"""
        if event.type in self.listeners:
            # 创建副本以避免在迭代时修改列表
            listeners = self.listeners[event.type].copy()
            for listener in listeners:
                if listener.is_active:
                    listener.handle_event(event)


class EventManager:
    """事件管理器 - 提供便捷的事件管理接口"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.listeners: List[EventListener] = []
    
    def subscribe_to_all(self, callback: Callable[[Event], None], 
                        source_filter: Optional[str] = None):
        """订阅所有事件"""
        all_listeners = []
        for event_type in EventType:
            listener = self.event_bus.subscribe(event_type, callback, source_filter)
            all_listeners.append(listener)
        self.listeners.extend(all_listeners)
        return all_listeners
    
    def subscribe_to_multiple(self, event_types: List[EventType], 
                            callback: Callable[[Event], None],
                            source_filter: Optional[str] = None):
        """订阅多个事件类型"""
        listeners = []
        for event_type in event_types:
            listener = self.event_bus.subscribe(event_type, callback, source_filter)
            listeners.append(listener)
        self.listeners.extend(listeners)
        return listeners
    
    def cleanup(self):
        """清理所有监听器"""
        for listener in self.listeners:
            self.event_bus.unsubscribe(listener)
        self.listeners.clear()


# 全局事件总线实例
global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    return global_event_bus


def subscribe(event_type: EventType, callback: Callable[[Event], None], 
              source_filter: Optional[str] = None) -> EventListener:
    """便捷的订阅函数"""
    return global_event_bus.subscribe(event_type, callback, source_filter)


def publish(event_type: EventType, data: Any = None, 
            source: Optional[str] = None):
    """便捷的发布函数"""
    global_event_bus.publish(event_type, data, source)


def start_event_bus():
    """启动全局事件总线"""
    global_event_bus.start()


def stop_event_bus():
    """停止全局事件总线"""
    global_event_bus.stop()