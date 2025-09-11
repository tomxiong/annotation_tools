"""
状态管理模块
负责应用程序状态的统一管理、状态同步、状态持久化等
"""

import json
import os
from typing import Dict, Any, Optional, List, Callable
from threading import Lock
from enum import Enum
from datetime import datetime

# 日志导入
try:
    from src.utils.logger import log_debug, log_info, log_warning, log_error
except ImportError:
    def log_debug(msg, category=""): print(f"[DEBUG] {msg}")
    def log_info(msg, category=""): print(f"[INFO] {msg}")
    def log_warning(msg, category=""): print(f"[WARNING] {msg}")
    def log_error(msg, category=""): print(f"[ERROR] {msg}")

class StateChangeType(Enum):
    """状态变更类型枚举"""
    DATASET_LOADED = "dataset_loaded"
    SLICE_CHANGED = "slice_changed"
    ANNOTATION_MODIFIED = "annotation_modified"
    ANNOTATION_SAVED = "annotation_saved"
    VIEW_CHANGED = "view_changed"
    SETTINGS_CHANGED = "settings_changed"
    NAVIGATION_CHANGED = "navigation_changed"
    PROCESSING_STATUS_CHANGED = "processing_status_changed"

class ProcessingStatus(Enum):
    """处理状态枚举"""
    IDLE = "idle"
    LOADING = "loading"
    PROCESSING = "processing"
    SAVING = "saving"
    ERROR = "error"

class StateManager:
    """状态管理器 - 负责应用程序状态的统一管理"""
    
    def __init__(self, gui_instance, state_file_path: str = "ui_state.json"):
        """
        初始化状态管理器
        
        Args:
            gui_instance: 主GUI实例
            state_file_path: 状态文件路径
        """
        self.gui = gui_instance
        self.state_file_path = state_file_path
        self._state_lock = Lock()
        
        # 状态变更监听器
        self._state_listeners = {}
        
        # 应用程序状态
        self._app_state = {
            # 当前数据状态
            'current_dataset_path': None,
            'current_panoramic_id': None,
            'current_hole_number': None,
            'current_slice_index': 0,
            'total_slices': 0,
            
            # 当前视图状态
            'current_view_mode': 'slice',  # slice, panoramic, dual
            'zoom_level': 1.0,
            'canvas_offset_x': 0,
            'canvas_offset_y': 0,
            'slice_canvas_size': (800, 600),
            'panoramic_canvas_size': (400, 300),
            
            # 标注状态
            'current_annotation_modified': False,
            'annotation_count': 0,
            'total_holes': 0,
            'completed_holes': 0,
            'progress_percentage': 0.0,
            
            # 处理状态
            'processing_status': ProcessingStatus.IDLE.value,
            'processing_message': '',
            'error_message': '',
            
            # 导航状态
            'navigation_history_size': 0,
            'can_go_back': False,
            'can_go_forward': False,
            'can_go_previous': False,
            'can_go_next': False,
            
            # UI状态
            'window_geometry': '1200x800+100+100',
            'panels_visible': {
                'slice_panel': True,
                'panoramic_panel': True,
                'annotation_panel': True,
                'info_panel': True
            },
            'splitter_positions': {},
            
            # 应用设置状态
            'auto_save_enabled': True,
            'auto_backup_enabled': True,
            'show_grid': True,
            'show_coordinates': True,
            'slice_display_mode': 'fit',  # fit, fill, stretch
            'annotation_auto_confirm': False,
            
            # 性能监控状态
            'memory_usage': 0,
            'load_time': 0,
            'last_action_time': None,
            
            # 时间戳
            'last_updated': None,
            'session_start_time': datetime.now().isoformat()
        }
        
        # 加载保存的状态
        self._load_state()
        
        log_debug("状态管理器初始化完成", "STATE_MANAGER")
    
    def get_state(self, key: str = None) -> Any:
        """
        获取状态值
        
        Args:
            key: 状态键，如果为None则返回整个状态字典
            
        Returns:
            状态值或状态字典
        """
        with self._state_lock:
            if key is None:
                return self._app_state.copy()
            return self._app_state.get(key)
    
    def set_state(self, key: str, value: Any, notify: bool = True) -> bool:
        """
        设置状态值
        
        Args:
            key: 状态键
            value: 状态值
            notify: 是否通知状态变更监听器
            
        Returns:
            如果状态发生变化返回True，否则返回False
        """
        try:
            with self._state_lock:
                old_value = self._app_state.get(key)
                
                if old_value == value:
                    return False  # 状态未变化
                
                self._app_state[key] = value
                self._app_state['last_updated'] = datetime.now().isoformat()
            
            # 通知状态变更
            if notify:
                self._notify_state_change(key, old_value, value)
            
            log_debug(f"状态更新: {key} = {value}", "STATE_MANAGER")
            return True
            
        except Exception as e:
            log_error(f"设置状态 {key} 失败: {str(e)}", "STATE_MANAGER")
            return False
    
    def update_state(self, state_dict: Dict[str, Any], notify: bool = True) -> bool:
        """
        批量更新状态
        
        Args:
            state_dict: 状态字典
            notify: 是否通知状态变更监听器
            
        Returns:
            如果有状态发生变化返回True，否则返回False
        """
        try:
            changed_keys = []
            
            with self._state_lock:
                for key, value in state_dict.items():
                    old_value = self._app_state.get(key)
                    if old_value != value:
                        self._app_state[key] = value
                        changed_keys.append((key, old_value, value))
                
                if changed_keys:
                    self._app_state['last_updated'] = datetime.now().isoformat()
            
            # 通知状态变更
            if notify and changed_keys:
                for key, old_value, new_value in changed_keys:
                    self._notify_state_change(key, old_value, new_value)
            
            if changed_keys:
                log_debug(f"批量状态更新: {len(changed_keys)} 项", "STATE_MANAGER")
            
            return len(changed_keys) > 0
            
        except Exception as e:
            log_error(f"批量更新状态失败: {str(e)}", "STATE_MANAGER")
            return False
    
    def reset_state(self, preserve_session: bool = True):
        """
        重置状态到初始值
        
        Args:
            preserve_session: 是否保留会话相关状态
        """
        try:
            with self._state_lock:
                session_data = {}
                if preserve_session:
                    session_data = {
                        'session_start_time': self._app_state.get('session_start_time'),
                        'window_geometry': self._app_state.get('window_geometry'),
                        'panels_visible': self._app_state.get('panels_visible'),
                        'splitter_positions': self._app_state.get('splitter_positions')
                    }
                
                # 重置到初始状态
                self._app_state = {
                    'current_dataset_path': None,
                    'current_panoramic_id': None,
                    'current_hole_number': None,
                    'current_slice_index': 0,
                    'total_slices': 0,
                    'current_view_mode': 'slice',
                    'zoom_level': 1.0,
                    'canvas_offset_x': 0,
                    'canvas_offset_y': 0,
                    'slice_canvas_size': (800, 600),
                    'panoramic_canvas_size': (400, 300),
                    'current_annotation_modified': False,
                    'annotation_count': 0,
                    'total_holes': 0,
                    'completed_holes': 0,
                    'progress_percentage': 0.0,
                    'processing_status': ProcessingStatus.IDLE.value,
                    'processing_message': '',
                    'error_message': '',
                    'navigation_history_size': 0,
                    'can_go_back': False,
                    'can_go_forward': False,
                    'can_go_previous': False,
                    'can_go_next': False,
                    'window_geometry': '1200x800+100+100',
                    'panels_visible': {
                        'slice_panel': True,
                        'panoramic_panel': True,
                        'annotation_panel': True,
                        'info_panel': True
                    },
                    'splitter_positions': {},
                    'auto_save_enabled': True,
                    'auto_backup_enabled': True,
                    'show_grid': True,
                    'show_coordinates': True,
                    'slice_display_mode': 'fit',
                    'annotation_auto_confirm': False,
                    'memory_usage': 0,
                    'load_time': 0,
                    'last_action_time': None,
                    'last_updated': datetime.now().isoformat(),
                    'session_start_time': datetime.now().isoformat()
                }
                
                # 恢复会话数据
                if preserve_session:
                    self._app_state.update(session_data)
            
            # 通知状态重置
            self._notify_state_change('__reset__', None, None)
            log_info("应用状态已重置", "STATE_MANAGER")
            
        except Exception as e:
            log_error(f"重置状态失败: {str(e)}", "STATE_MANAGER")
    
    def add_state_listener(self, state_key: str, callback: Callable[[str, Any, Any], None]):
        """
        添加状态变更监听器
        
        Args:
            state_key: 状态键，使用'*'监听所有状态变更
            callback: 回调函数，参数为(key, old_value, new_value)
        """
        try:
            if state_key not in self._state_listeners:
                self._state_listeners[state_key] = []
            
            self._state_listeners[state_key].append(callback)
            log_debug(f"添加状态监听器: {state_key}", "STATE_MANAGER")
            
        except Exception as e:
            log_error(f"添加状态监听器失败: {str(e)}", "STATE_MANAGER")
    
    def remove_state_listener(self, state_key: str, callback: Callable[[str, Any, Any], None]):
        """
        移除状态变更监听器
        
        Args:
            state_key: 状态键
            callback: 回调函数
        """
        try:
            if state_key in self._state_listeners:
                if callback in self._state_listeners[state_key]:
                    self._state_listeners[state_key].remove(callback)
                    
                if not self._state_listeners[state_key]:
                    del self._state_listeners[state_key]
                    
                log_debug(f"移除状态监听器: {state_key}", "STATE_MANAGER")
            
        except Exception as e:
            log_error(f"移除状态监听器失败: {str(e)}", "STATE_MANAGER")
    
    def update_dataset_state(self, dataset_path: str = None, panoramic_id: str = None, 
                           total_holes: int = 0, completed_holes: int = 0):
        """
        更新数据集状态
        
        Args:
            dataset_path: 数据集路径
            panoramic_id: 当前全景图ID
            total_holes: 总孔位数
            completed_holes: 已完成孔位数
        """
        try:
            updates = {}
            
            if dataset_path is not None:
                updates['current_dataset_path'] = dataset_path
            
            if panoramic_id is not None:
                updates['current_panoramic_id'] = panoramic_id
            
            if total_holes >= 0:
                updates['total_holes'] = total_holes
            
            if completed_holes >= 0:
                updates['completed_holes'] = completed_holes
                if total_holes > 0:
                    updates['progress_percentage'] = (completed_holes / total_holes) * 100
            
            if updates:
                self.update_state(updates)
                self._notify_state_change_type(StateChangeType.DATASET_LOADED)
            
        except Exception as e:
            log_error(f"更新数据集状态失败: {str(e)}", "STATE_MANAGER")
    
    def update_slice_state(self, slice_index: int, hole_number: int = None, total_slices: int = None):
        """
        更新切片状态
        
        Args:
            slice_index: 当前切片索引
            hole_number: 当前孔位编号
            total_slices: 总切片数
        """
        try:
            updates = {
                'current_slice_index': slice_index
            }
            
            if hole_number is not None:
                updates['current_hole_number'] = hole_number
            
            if total_slices is not None:
                updates['total_slices'] = total_slices
            
            self.update_state(updates)
            self._notify_state_change_type(StateChangeType.SLICE_CHANGED)
            
        except Exception as e:
            log_error(f"更新切片状态失败: {str(e)}", "STATE_MANAGER")
    
    def update_annotation_state(self, modified: bool = None, annotation_count: int = None):
        """
        更新标注状态
        
        Args:
            modified: 标注是否已修改
            annotation_count: 标注数量
        """
        try:
            updates = {}
            
            if modified is not None:
                updates['current_annotation_modified'] = modified
            
            if annotation_count is not None:
                updates['annotation_count'] = annotation_count
            
            if updates:
                self.update_state(updates)
                
                if modified is not None:
                    change_type = StateChangeType.ANNOTATION_MODIFIED if modified else StateChangeType.ANNOTATION_SAVED
                    self._notify_state_change_type(change_type)
            
        except Exception as e:
            log_error(f"更新标注状态失败: {str(e)}", "STATE_MANAGER")
    
    def update_navigation_state(self, navigation_info: Dict[str, Any]):
        """
        更新导航状态
        
        Args:
            navigation_info: 导航信息字典
        """
        try:
            updates = {}
            
            if 'history_size' in navigation_info:
                updates['navigation_history_size'] = navigation_info['history_size']
            
            if 'can_go_back' in navigation_info:
                updates['can_go_back'] = navigation_info['can_go_back']
            
            if 'can_go_forward' in navigation_info:
                updates['can_go_forward'] = navigation_info['can_go_forward']
            
            if 'can_go_previous' in navigation_info:
                updates['can_go_previous'] = navigation_info['can_go_previous']
            
            if 'can_go_next' in navigation_info:
                updates['can_go_next'] = navigation_info['can_go_next']
            
            if updates:
                self.update_state(updates)
                self._notify_state_change_type(StateChangeType.NAVIGATION_CHANGED)
            
        except Exception as e:
            log_error(f"更新导航状态失败: {str(e)}", "STATE_MANAGER")
    
    def update_view_state(self, view_mode: str = None, zoom_level: float = None, 
                         canvas_size: tuple = None, offset: tuple = None):
        """
        更新视图状态
        
        Args:
            view_mode: 视图模式
            zoom_level: 缩放级别
            canvas_size: 画布大小
            offset: 画布偏移
        """
        try:
            updates = {}
            
            if view_mode is not None:
                updates['current_view_mode'] = view_mode
            
            if zoom_level is not None:
                updates['zoom_level'] = zoom_level
            
            if canvas_size is not None:
                if view_mode == 'slice':
                    updates['slice_canvas_size'] = canvas_size
                elif view_mode == 'panoramic':
                    updates['panoramic_canvas_size'] = canvas_size
            
            if offset is not None:
                updates['canvas_offset_x'] = offset[0]
                updates['canvas_offset_y'] = offset[1]
            
            if updates:
                self.update_state(updates)
                self._notify_state_change_type(StateChangeType.VIEW_CHANGED)
            
        except Exception as e:
            log_error(f"更新视图状态失败: {str(e)}", "STATE_MANAGER")
    
    def update_processing_status(self, status: ProcessingStatus, message: str = '', error: str = ''):
        """
        更新处理状态
        
        Args:
            status: 处理状态
            message: 状态消息
            error: 错误消息
        """
        try:
            updates = {
                'processing_status': status.value,
                'processing_message': message,
                'error_message': error
            }
            
            self.update_state(updates)
            self._notify_state_change_type(StateChangeType.PROCESSING_STATUS_CHANGED)
            
        except Exception as e:
            log_error(f"更新处理状态失败: {str(e)}", "STATE_MANAGER")
    
    def save_state(self) -> bool:
        """
        保存状态到文件
        
        Returns:
            如果保存成功返回True，否则返回False
        """
        try:
            with self._state_lock:
                state_data = self._app_state.copy()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.state_file_path)), exist_ok=True)
            
            # 保存到文件
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            log_debug(f"状态已保存到: {self.state_file_path}", "STATE_MANAGER")
            return True
            
        except Exception as e:
            log_error(f"保存状态失败: {str(e)}", "STATE_MANAGER")
            return False
    
    def _load_state(self) -> bool:
        """
        从文件加载状态
        
        Returns:
            如果加载成功返回True，否则返回False
        """
        try:
            if not os.path.exists(self.state_file_path):
                log_debug("状态文件不存在，使用默认状态", "STATE_MANAGER")
                return True
            
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                saved_state = json.load(f)
            
            # 合并保存的状态（只更新存在的键）
            with self._state_lock:
                for key, value in saved_state.items():
                    if key in self._app_state:
                        self._app_state[key] = value
            
            log_debug(f"状态已从文件加载: {self.state_file_path}", "STATE_MANAGER")
            return True
            
        except Exception as e:
            log_error(f"加载状态失败: {str(e)}", "STATE_MANAGER")
            return False
    
    def _notify_state_change(self, key: str, old_value: Any, new_value: Any):
        """通知状态变更监听器"""
        try:
            # 通知特定状态监听器
            if key in self._state_listeners:
                for callback in self._state_listeners[key]:
                    try:
                        callback(key, old_value, new_value)
                    except Exception as e:
                        log_error(f"状态监听器回调失败: {str(e)}", "STATE_MANAGER")
            
            # 通知全局监听器
            if '*' in self._state_listeners:
                for callback in self._state_listeners['*']:
                    try:
                        callback(key, old_value, new_value)
                    except Exception as e:
                        log_error(f"全局状态监听器回调失败: {str(e)}", "STATE_MANAGER")
            
        except Exception as e:
            log_error(f"通知状态变更失败: {str(e)}", "STATE_MANAGER")
    
    def _notify_state_change_type(self, change_type: StateChangeType):
        """通知特定类型的状态变更"""
        try:
            type_key = f"__{change_type.value}__"
            if type_key in self._state_listeners:
                for callback in self._state_listeners[type_key]:
                    try:
                        callback(change_type.value, None, None)
                    except Exception as e:
                        log_error(f"状态类型监听器回调失败: {str(e)}", "STATE_MANAGER")
            
        except Exception as e:
            log_error(f"通知状态类型变更失败: {str(e)}", "STATE_MANAGER")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            性能统计字典
        """
        try:
            import psutil
            process = psutil.Process()
            
            stats = {
                'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'threads_count': process.num_threads(),
                'session_duration': self._calculate_session_duration(),
                'state_listeners_count': sum(len(listeners) for listeners in self._state_listeners.values()),
                'last_action_time': self.get_state('last_action_time'),
                'load_time': self.get_state('load_time')
            }
            
            # 更新内存使用状态
            self.set_state('memory_usage', stats['memory_usage_mb'], notify=False)
            
            return stats
            
        except Exception as e:
            log_error(f"获取性能统计失败: {str(e)}", "STATE_MANAGER")
            return {}
    
    def _calculate_session_duration(self) -> float:
        """计算会话持续时间（秒）"""
        try:
            start_time_str = self.get_state('session_start_time')
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                duration = (datetime.now() - start_time).total_seconds()
                return duration
            return 0
            
        except Exception:
            return 0
    
    def cleanup(self):
        """清理资源"""
        try:
            # 保存当前状态
            self.save_state()
            
            # 清空监听器
            self._state_listeners.clear()
            
            log_debug("状态管理器资源已清理", "STATE_MANAGER")
            
        except Exception as e:
            log_error(f"状态管理器清理失败: {str(e)}", "STATE_MANAGER")
