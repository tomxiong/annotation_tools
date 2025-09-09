"""
UI状态管理模块

管理应用程序的UI状态，提供状态变更通知和持久化功能
"""

from typing import Any, Dict, Optional, List, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import logging
from pathlib import Path

from src.ui.utils.event_bus import EventBus, Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class ViewMode(Enum):
    """视图模式"""
    SINGLE_IMAGE = "single_image"
    COMPARISON = "comparison"
    GRID = "grid"


class NavigationMode(Enum):
    """导航模式"""
    CENTERED = "centered"
    TRADITIONAL = "traditional"


@dataclass
class AnnotationState:
    """标注状态"""
    current_hole_id: Optional[str] = None
    growth_level: Optional[str] = None
    microbe_type: Optional[str] = None
    is_annotating: bool = False
    batch_mode: bool = False
    selected_holes: Set[str] = field(default_factory=set)


@dataclass
class ImageState:
    """图像状态"""
    current_image_path: Optional[str] = None
    image_loaded: bool = False
    zoom_level: float = 1.0
    pan_position: tuple[float, float] = (0.0, 0.0)
    display_size: tuple[int, int] = (800, 600)
    image_format: Optional[str] = None


@dataclass
class UIState:
    """完整的UI状态"""
    # 基本状态
    window_title: str = "全景标注工具"
    window_size: tuple[int, int] = (1200, 800)
    window_position: tuple[int, int] = (100, 100)
    is_maximized: bool = False
    
    # 视图模式
    view_mode: ViewMode = ViewMode.SINGLE_IMAGE
    navigation_mode: NavigationMode = NavigationMode.CENTERED
    
    # 功能状态
    auto_save: bool = True
    show_grid: bool = True
    show_annotations: bool = True
    show_hole_numbers: bool = True
    image_enhancement: bool = True
    
    # 路径状态
    last_open_directory: str = ""
    last_save_directory: str = ""
    panoramic_directory: str = ""
    
    # 标注状态
    annotation: AnnotationState = field(default_factory=AnnotationState)
    
    # 图像状态
    image: ImageState = field(default_factory=ImageState)
    
    # 其他设置
    theme: str = "default"
    language: str = "zh_CN"
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10


class UIStateManager:
    """UI状态管理器"""
    
    def __init__(self, event_bus: Optional[EventBus] = None, 
                 config_file: Optional[str] = None):
        self.event_bus = event_bus or get_event_bus()
        self.config_file = config_file or "ui_state.json"
        self.current_state = UIState()
        self.previous_state = UIState()
        self.state_listeners: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 订阅事件
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """订阅相关事件"""
        self.event_bus.subscribe(EventType.UI_STATE_CHANGED, self._on_state_changed)
        self.event_bus.subscribe(EventType.VIEW_MODE_CHANGED, self._on_view_mode_changed)
        self.event_bus.subscribe(EventType.SETTINGS_CHANGED, self._on_settings_changed)
    
    def get_state(self) -> UIState:
        """获取当前状态"""
        return self.current_state
    
    def update_state(self, **kwargs) -> None:
        """更新状态"""
        # 保存之前的状态
        self.previous_state = UIState(**self.current_state.__dict__)
        
        # 更新状态
        for key, value in kwargs.items():
            if hasattr(self.current_state, key):
                setattr(self.current_state, key, value)
                self.logger.debug(f"State updated: {key} = {value}")
                
                # 通知特定状态监听器
                self._notify_state_listeners(key, value)
        
        # 发布状态变更事件
        self.event_bus.publish(EventType.UI_STATE_CHANGED, {
            'current_state': self.current_state,
            'changed_keys': list(kwargs.keys())
        })
    
    def get_annotation_state(self) -> AnnotationState:
        """获取标注状态"""
        return self.current_state.annotation
    
    def update_annotation_state(self, **kwargs) -> None:
        """更新标注状态"""
        annotation_dict = self.current_state.annotation.__dict__.copy()
        annotation_dict.update(kwargs)
        self.current_state.annotation = AnnotationState(**annotation_dict)
        
        self.event_bus.publish(EventType.UI_STATE_CHANGED, {
            'current_state': self.current_state,
            'changed_keys': ['annotation']
        })
    
    def get_image_state(self) -> ImageState:
        """获取图像状态"""
        return self.current_state.image
    
    def update_image_state(self, **kwargs) -> None:
        """更新图像状态"""
        image_dict = self.current_state.image.__dict__.copy()
        image_dict.update(kwargs)
        self.current_state.image = ImageState(**image_dict)
        
        self.event_bus.publish(EventType.UI_STATE_CHANGED, {
            'current_state': self.current_state,
            'changed_keys': ['image']
        })
    
    def add_recent_file(self, file_path: str) -> None:
        """添加最近使用的文件"""
        recent_files = self.current_state.recent_files.copy()
        
        # 移除重复项
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # 添加到开头
        recent_files.insert(0, file_path)
        
        # 限制数量
        max_files = self.current_state.max_recent_files
        recent_files = recent_files[:max_files]
        
        self.update_state(recent_files=recent_files)
    
    def set_view_mode(self, mode: ViewMode) -> None:
        """设置视图模式"""
        if self.current_state.view_mode != mode:
            self.update_state(view_mode=mode)
            self.event_bus.publish(EventType.VIEW_MODE_CHANGED, {'mode': mode})
    
    def set_navigation_mode(self, mode: NavigationMode) -> None:
        """设置导航模式"""
        if self.current_state.navigation_mode != mode:
            self.update_state(navigation_mode=mode)
    
    def toggle_auto_save(self) -> bool:
        """切换自动保存"""
        new_state = not self.current_state.auto_save
        self.update_state(auto_save=new_state)
        return new_state
    
    def toggle_grid(self) -> bool:
        """切换网格显示"""
        new_state = not self.current_state.show_grid
        self.update_state(show_grid=new_state)
        return new_state
    
    def toggle_annotations(self) -> bool:
        """切换标注显示"""
        new_state = not self.current_state.show_annotations
        self.update_state(show_annotations=new_state)
        return new_state
    
    def register_state_listener(self, state_key: str, callback: Callable[[Any], None]) -> None:
        """注册状态监听器"""
        if state_key not in self.state_listeners:
            self.state_listeners[state_key] = []
        self.state_listeners[state_key].append(callback)
    
    def unregister_state_listener(self, state_key: str, callback: Callable[[Any], None]) -> None:
        """注销状态监听器"""
        if state_key in self.state_listeners:
            try:
                self.state_listeners[state_key].remove(callback)
            except ValueError:
                pass
    
    def _notify_state_listeners(self, state_key: str, value: Any) -> None:
        """通知状态监听器"""
        if state_key in self.state_listeners:
            for callback in self.state_listeners[state_key]:
                try:
                    callback(value)
                except Exception as e:
                    self.logger.error(f"Error in state listener for {state_key}: {e}")
    
    def _on_state_changed(self, event: Event) -> None:
        """处理状态变更事件"""
        self.logger.debug("State changed event received")
    
    def _on_view_mode_changed(self, event: Event) -> None:
        """处理视图模式变更事件"""
        mode = event.data.get('mode')
        if mode:
            self.logger.info(f"View mode changed to {mode}")
    
    def _on_settings_changed(self, event: Event) -> None:
        """处理设置变更事件"""
        settings = event.data
        if settings:
            self.logger.info(f"Settings changed: {settings}")
    
    def save_state(self) -> bool:
        """保存状态到文件"""
        try:
            state_dict = self._state_to_dict(self.current_state)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            self.logger.info(f"UI state saved to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save UI state: {e}")
            return False
    
    def load_state(self) -> bool:
        """从文件加载状态"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    state_dict = json.load(f)
                
                self.current_state = self._dict_to_state(state_dict)
                self.logger.info(f"UI state loaded from {self.config_file}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to load UI state: {e}")
        
        return False
    
    def _state_to_dict(self, state: UIState) -> Dict[str, Any]:
        """将状态转换为字典"""
        result = {}
        for key, value in state.__dict__.items():
            if isinstance(value, (ViewMode, NavigationMode)):
                result[key] = value.value
            elif isinstance(value, (AnnotationState, ImageState)):
                # 处理嵌套对象的字典转换
                nested_dict = {}
                for nested_key, nested_value in value.__dict__.items():
                    if isinstance(nested_value, set):
                        # 将集合转换为列表以支持JSON序列化
                        nested_dict[nested_key] = list(nested_value)
                    else:
                        nested_dict[nested_key] = nested_value
                result[key] = nested_dict
            else:
                result[key] = value
        return result
    
    def _dict_to_state(self, state_dict: Dict[str, Any]) -> UIState:
        """将字典转换为状态"""
        # 处理枚举值
        if 'view_mode' in state_dict and isinstance(state_dict['view_mode'], str):
            state_dict['view_mode'] = ViewMode(state_dict['view_mode'])

        if 'navigation_mode' in state_dict and isinstance(state_dict['navigation_mode'], str):
            state_dict['navigation_mode'] = NavigationMode(state_dict['navigation_mode'])

        # 处理嵌套对象
        if 'annotation' in state_dict and isinstance(state_dict['annotation'], dict):
            annotation_dict = state_dict['annotation'].copy()
            # 将列表转换回集合
            if 'selected_holes' in annotation_dict and isinstance(annotation_dict['selected_holes'], list):
                annotation_dict['selected_holes'] = set(annotation_dict['selected_holes'])
            state_dict['annotation'] = AnnotationState(**annotation_dict)

        if 'image' in state_dict and isinstance(state_dict['image'], dict):
            state_dict['image'] = ImageState(**state_dict['image'])

        return UIState(**state_dict)
    
    def reset_to_defaults(self) -> None:
        """重置为默认状态"""
        self.current_state = UIState()
        self.event_bus.publish(EventType.UI_STATE_CHANGED, {
            'current_state': self.current_state,
            'changed_keys': ['all']
        })
    
    def export_state(self, file_path: str) -> bool:
        """导出状态到指定文件"""
        try:
            state_dict = self._state_to_dict(self.current_state)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)
            self.logger.info(f"UI state exported to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export UI state: {e}")
            return False
    
    def import_state(self, file_path: str) -> bool:
        """从指定文件导入状态"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
            
            self.current_state = self._dict_to_state(state_dict)
            self.event_bus.publish(EventType.UI_STATE_CHANGED, {
                'current_state': self.current_state,
                'changed_keys': ['all']
            })
            self.logger.info(f"UI state imported from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import UI state: {e}")
            return False


# 全局状态管理器实例
global_ui_state_manager = UIStateManager()


def get_ui_state_manager() -> UIStateManager:
    """获取全局UI状态管理器"""
    return global_ui_state_manager


def initialize_ui_state(config_file: Optional[str] = None):
    """初始化UI状态管理器"""
    global global_ui_state_manager
    global_ui_state_manager = UIStateManager(config_file=config_file)
    global_ui_state_manager.load_state()
    return global_ui_state_manager