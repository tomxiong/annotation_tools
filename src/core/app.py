"""
应用核心模块

提供应用程序的核心管理功能，支持：
- 应用生命周期管理
- 服务容器管理
- 事件系统
- 插件系统
- 状态管理
- 资源管理
"""

import os
import sys
import time
import signal
import threading
import atexit
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Type, TypeVar
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum

from .config import get_config, AppConfig
from .logger import get_logger, shutdown_logging
from .exceptions import SystemError, ConfigError, ServiceError
from .utils import FileUtils, SystemUtils, DateTimeUtils, get_global_cache

logger = get_logger(__name__)

T = TypeVar('T')


class AppState(Enum):
    """应用状态枚举"""
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    instance: Any
    dependencies: List[str] = field(default_factory=list)
    initialized: bool = False
    started: bool = False
    priority: int = 0


class EventManager:
    """事件管理器"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        with self._lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                except ValueError:
                    pass
    
    def emit(self, event_type: str, *args, **kwargs) -> None:
        """
        发送事件
        
        Args:
            event_type: 事件类型
            *args: 位置参数
            **kwargs: 关键字参数
        """
        with self._lock:
            handlers = self._handlers.get(event_type, []).copy()
        
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {event_type} - {e}")
    
    def clear(self) -> None:
        """清空所有事件处理器"""
        with self._lock:
            self._handlers.clear()


class ServiceContainer:
    """服务容器"""
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._lock = threading.RLock()
    
    def register(self, name: str, factory: Callable, dependencies: List[str] = None, 
                 singleton: bool = True, priority: int = 0) -> None:
        """
        注册服务
        
        Args:
            name: 服务名称
            factory: 服务工厂函数
            dependencies: 依赖服务列表
            singleton: 是否为单例
            priority: 优先级
        """
        with self._lock:
            if name in self._services:
                logger.warning(f"服务已存在，将被覆盖: {name}")
            
            self._services[name] = ServiceInfo(
                name=name,
                instance=None,
                dependencies=dependencies or [],
                priority=priority
            )
            
            if singleton:
                self._singletons[name] = factory
            else:
                self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            ServiceError: 服务不存在时抛出
        """
        with self._lock:
            if name not in self._services:
                raise ServiceError(f"服务不存在: {name}")
            
            service_info = self._services[name]
            
            # 返回单例实例
            if name in self._singletons:
                if service_info.instance is None:
                    service_info.instance = self._create_service(name)
                return service_info.instance
            
            # 创建新实例
            return self._create_service(name)
    
    def _create_service(self, name: str) -> Any:
        """
        创建服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            ServiceError: 服务创建失败时抛出
        """
        service_info = self._services[name]
        
        # 检查依赖
        for dep in service_info.dependencies:
            if dep not in self._services or not self._services[dep].initialized:
                raise ServiceError(f"依赖服务未初始化: {dep}")
        
        try:
            if name in self._singletons:
                instance = self._singletons[name]()
            else:
                instance = self._factories[name]()
            
            service_info.instance = instance
            service_info.initialized = True
            
            logger.debug(f"服务创建成功: {name}")
            return instance
            
        except Exception as e:
            raise ServiceError(f"服务创建失败: {name} - {e}") from e
    
    def start_service(self, name: str) -> None:
        """
        启动服务
        
        Args:
            name: 服务名称
        """
        with self._lock:
            if name not in self._services:
                raise ServiceError(f"服务不存在: {name}")
            
            service_info = self._services[name]
            
            if service_info.started:
                return
            
            # 启动依赖服务
            for dep in service_info.dependencies:
                if not self._services[dep].started:
                    self.start_service(dep)
            
            # 获取服务实例
            instance = self.get(name)
            
            # 调用启动方法
            if hasattr(instance, 'start'):
                try:
                    instance.start()
                    service_info.started = True
                    logger.info(f"服务启动成功: {name}")
                except Exception as e:
                    raise ServiceError(f"服务启动失败: {name} - {e}") from e
            else:
                service_info.started = True
    
    def stop_service(self, name: str) -> None:
        """
        停止服务
        
        Args:
            name: 服务名称
        """
        with self._lock:
            if name not in self._services:
                return
            
            service_info = self._services[name]
            
            if not service_info.started:
                return
            
            # 停止依赖服务
            for dep in service_info.dependencies:
                if self._services[dep].started:
                    self.stop_service(dep)
            
            # 调用停止方法
            instance = service_info.instance
            if instance and hasattr(instance, 'stop'):
                try:
                    instance.stop()
                    service_info.started = False
                    logger.info(f"服务停止成功: {name}")
                except Exception as e:
                    logger.error(f"服务停止失败: {name} - {e}")
            else:
                service_info.started = False
    
    def start_all_services(self) -> None:
        """启动所有服务"""
        with self._lock:
            # 按优先级排序
            services = sorted(
                self._services.values(),
                key=lambda s: s.priority,
                reverse=True
            )
            
            for service_info in services:
                if not service_info.started:
                    self.start_service(service_info.name)
    
    def stop_all_services(self) -> None:
        """停止所有服务"""
        with self._lock:
            # 按优先级逆序停止
            services = sorted(
                self._services.values(),
                key=lambda s: s.priority
            )
            
            for service_info in services:
                if service_info.started:
                    self.stop_service(service_info.name)
    
    def list_services(self) -> List[str]:
        """
        列出所有服务
        
        Returns:
            服务名称列表
        """
        with self._lock:
            return list(self._services.keys())
    
    def get_service_info(self, name: str) -> Optional[ServiceInfo]:
        """
        获取服务信息
        
        Args:
            name: 服务名称
            
        Returns:
            服务信息
        """
        with self._lock:
            return self._services.get(name)


class ResourceManager:
    """资源管理器"""
    
    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._cleanup_handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
    
    def register(self, name: str, resource: Any, cleanup_handler: Callable = None) -> None:
        """
        注册资源
        
        Args:
            name: 资源名称
            resource: 资源对象
            cleanup_handler: 清理处理器
        """
        with self._lock:
            if name in self._resources:
                self._cleanup_resource(name)
            
            self._resources[name] = resource
            self._cleanup_handlers[name] = cleanup_handler
    
    def get(self, name: str) -> Any:
        """
        获取资源
        
        Args:
            name: 资源名称
            
        Returns:
            资源对象
        """
        with self._lock:
            return self._resources.get(name)
    
    def release(self, name: str) -> None:
        """
        释放资源
        
        Args:
            name: 资源名称
        """
        with self._lock:
            self._cleanup_resource(name)
            if name in self._resources:
                del self._resources[name]
            if name in self._cleanup_handlers:
                del self._cleanup_handlers[name]
    
    def _cleanup_resource(self, name: str) -> None:
        """
        清理资源
        
        Args:
            name: 资源名称
        """
        if name in self._cleanup_handlers and self._cleanup_handlers[name]:
            try:
                self._cleanup_handlers[name](self._resources[name])
            except Exception as e:
                logger.error(f"资源清理失败: {name} - {e}")
    
    def cleanup_all(self) -> None:
        """清理所有资源"""
        with self._lock:
            resource_names = list(self._resources.keys())
            for name in resource_names:
                self.release(name)


class StateManager:
    """状态管理器"""
    
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
    
    def set(self, key: str, value: Any) -> None:
        """
        设置状态
        
        Args:
            key: 状态键
            value: 状态值
        """
        with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value
            
            # 通知监听器
            if key in self._listeners and old_value != value:
                for listener in self._listeners[key]:
                    try:
                        listener(key, old_value, value)
                    except Exception as e:
                        logger.error(f"状态监听器执行失败: {key} - {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取状态
        
        Args:
            key: 状态键
            default: 默认值
            
        Returns:
            状态值
        """
        with self._lock:
            return self._state.get(key, default)
    
    def has(self, key: str) -> bool:
        """
        检查状态是否存在
        
        Args:
            key: 状态键
            
        Returns:
            是否存在
        """
        with self._lock:
            return key in self._state
    
    def delete(self, key: str) -> None:
        """
        删除状态
        
        Args:
            key: 状态键
        """
        with self._lock:
            if key in self._state:
                del self._state[key]
    
    def listen(self, key: str, listener: Callable) -> None:
        """
        监听状态变化
        
        Args:
            key: 状态键
            listener: 监听器
        """
        with self._lock:
            if key not in self._listeners:
                self._listeners[key] = []
            self._listeners[key].append(listener)
    
    def unlisten(self, key: str, listener: Callable) -> None:
        """
        取消监听状态变化
        
        Args:
            key: 状态键
            listener: 监听器
        """
        with self._lock:
            if key in self._listeners:
                try:
                    self._listeners[key].remove(listener)
                except ValueError:
                    pass
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有状态
        
        Returns:
            所有状态
        """
        with self._lock:
            return self._state.copy()


class Application:
    """应用程序核心类"""
    
    def __init__(self, config: AppConfig = None):
        """
        初始化应用程序
        
        Args:
            config: 应用配置
        """
        self._config = config or get_config()
        self._state = AppState.INITIALIZING
        self._start_time = None
        self._stop_time = None
        
        # 核心组件
        self._event_manager = EventManager()
        self._service_container = ServiceContainer()
        self._resource_manager = ResourceManager()
        self._state_manager = StateManager()
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 注册核心服务
        self._register_core_services()
        
        # 注册信号处理器
        self._register_signal_handlers()
        
        # 注册退出处理器
        atexit.register(self._cleanup)
        
        logger.info("应用程序核心初始化完成")
    
    def _register_core_services(self) -> None:
        """注册核心服务"""
        # 注册配置服务
        self._service_container.register(
            'config',
            lambda: self._config,
            singleton=True,
            priority=100
        )
        
        # 注册事件管理器
        self._service_container.register(
            'event_manager',
            lambda: self._event_manager,
            singleton=True,
            priority=90
        )
        
        # 注册资源管理器
        self._service_container.register(
            'resource_manager',
            lambda: self._resource_manager,
            singleton=True,
            priority=80
        )
        
        # 注册状态管理器
        self._service_container.register(
            'state_manager',
            lambda: self._state_manager,
            singleton=True,
            priority=70
        )
        
        # 注册应用实例
        self._service_container.register(
            'app',
            lambda: self,
            singleton=True,
            priority=60
        )
    
    def _register_signal_handlers(self) -> None:
        """注册信号处理器"""
        if os.name == 'nt':  # Windows
            try:
                import win32api
                win32api.SetConsoleCtrlHandler(self._signal_handler, True)
            except ImportError:
                logger.warning("无法注册Windows信号处理器")
        else:  # Unix/Linux/Mac
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame) -> None:
        """
        信号处理器
        
        Args:
            signum: 信号编号
            frame: 栈帧
        """
        logger.info(f"接收到信号: {signum}")
        self.stop()
    
    def _cleanup(self) -> None:
        """清理资源"""
        if self._state not in [AppState.STOPPED, AppState.ERROR]:
            self.stop()
    
    @property
    def config(self) -> AppConfig:
        """获取应用配置"""
        return self._config
    
    @property
    def state(self) -> AppState:
        """获取应用状态"""
        return self._state
    
    @property
    def event_manager(self) -> EventManager:
        """获取事件管理器"""
        return self._event_manager
    
    @property
    def service_container(self) -> ServiceContainer:
        """获取服务容器"""
        return self._service_container
    
    @property
    def resource_manager(self) -> ResourceManager:
        """获取资源管理器"""
        return self._resource_manager
    
    @property
    def state_manager(self) -> StateManager:
        """获取状态管理器"""
        return self._state_manager
    
    def start(self) -> None:
        """启动应用程序"""
        with self._lock:
            if self._state == AppState.RUNNING:
                logger.warning("应用程序已在运行")
                return
            
            self._state = AppState.STARTING
            self._start_time = DateTimeUtils.now()
            
            try:
                logger.info("正在启动应用程序...")
                
                # 发送启动事件
                self._event_manager.emit('app_starting')
                
                # 启动所有服务
                self._service_container.start_all_services()
                
                # 更新状态
                self._state = AppState.RUNNING
                
                # 发送运行事件
                self._event_manager.emit('app_started')
                
                logger.info(f"应用程序启动成功，耗时: {(DateTimeUtils.now() - self._start_time).total_seconds():.2f}s")
                
            except Exception as e:
                self._state = AppState.ERROR
                logger.error(f"应用程序启动失败: {e}")
                self._event_manager.emit('app_error', error=e)
                raise SystemError(f"应用程序启动失败: {e}") from e
    
    def stop(self) -> None:
        """停止应用程序"""
        with self._lock:
            if self._state in [AppState.STOPPED, AppState.ERROR]:
                logger.warning("应用程序已停止")
                return
            
            old_state = self._state
            self._state = AppState.STOPPING
            
            try:
                logger.info("正在停止应用程序...")
                
                # 发送停止事件
                self._event_manager.emit('app_stopping')
                
                # 停止所有服务
                self._service_container.stop_all_services()
                
                # 清理资源
                self._resource_manager.cleanup_all()
                
                # 清理缓存
                get_global_cache().clear()
                
                # 更新状态
                self._state = AppState.STOPPED
                self._stop_time = DateTimeUtils.now()
                
                # 发送停止事件
                self._event_manager.emit('app_stopped')
                
                runtime = self._stop_time - self._start_time if self._start_time else timedelta(0)
                logger.info(f"应用程序停止成功，运行时间: {runtime.total_seconds():.2f}s")
                
            except Exception as e:
                self._state = AppState.ERROR
                logger.error(f"应用程序停止失败: {e}")
                self._event_manager.emit('app_error', error=e)
                raise SystemError(f"应用程序停止失败: {e}") from e
    
    def pause(self) -> None:
        """暂停应用程序"""
        with self._lock:
            if self._state != AppState.RUNNING:
                logger.warning("应用程序未运行")
                return
            
            self._state = AppState.PAUSED
            self._event_manager.emit('app_paused')
            logger.info("应用程序已暂停")
    
    def resume(self) -> None:
        """恢复应用程序"""
        with self._lock:
            if self._state != AppState.PAUSED:
                logger.warning("应用程序未暂停")
                return
            
            self._state = AppState.RUNNING
            self._event_manager.emit('app_resumed')
            logger.info("应用程序已恢复")
    
    def restart(self) -> None:
        """重启应用程序"""
        logger.info("正在重启应用程序...")
        self.stop()
        time.sleep(1)  # 等待完全停止
        self.start()
    
    def register_service(self, name: str, factory: Callable, dependencies: List[str] = None,
                        singleton: bool = True, priority: int = 0) -> None:
        """
        注册服务
        
        Args:
            name: 服务名称
            factory: 服务工厂函数
            dependencies: 依赖服务列表
            singleton: 是否为单例
            priority: 优先级
        """
        self._service_container.register(name, factory, dependencies, singleton, priority)
        logger.info(f"服务注册成功: {name}")
    
    def get_service(self, name: str) -> Any:
        """
        获取服务
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
        """
        return self._service_container.get(name)
    
    def register_resource(self, name: str, resource: Any, cleanup_handler: Callable = None) -> None:
        """
        注册资源
        
        Args:
            name: 资源名称
            resource: 资源对象
            cleanup_handler: 清理处理器
        """
        self._resource_manager.register(name, resource, cleanup_handler)
        logger.info(f"资源注册成功: {name}")
    
    def get_resource(self, name: str) -> Any:
        """
        获取资源
        
        Args:
            name: 资源名称
            
        Returns:
            资源对象
        """
        return self._resource_manager.get(name)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        设置状态
        
        Args:
            key: 状态键
            value: 状态值
        """
        self._state_manager.set(key, value)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        获取状态
        
        Args:
            key: 状态键
            default: 默认值
            
        Returns:
            状态值
        """
        return self._state_manager.get(key, default)
    
    def subscribe_event(self, event_type: str, handler: Callable) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        self._event_manager.subscribe(event_type, handler)
    
    def unsubscribe_event(self, event_type: str, handler: Callable) -> None:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        self._event_manager.unsubscribe(event_type, handler)
    
    def emit_event(self, event_type: str, *args, **kwargs) -> None:
        """
        发送事件
        
        Args:
            event_type: 事件类型
            *args: 位置参数
            **kwargs: 关键字参数
        """
        self._event_manager.emit(event_type, *args, **kwargs)
    
    def get_uptime(self) -> timedelta:
        """
        获取运行时间
        
        Returns:
            运行时间
        """
        if self._start_time is None:
            return timedelta(0)
        
        end_time = self._stop_time or DateTimeUtils.now()
        return end_time - self._start_time
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            系统信息
        """
        return {
            'app_state': self._state.value,
            'uptime': str(self.get_uptime()),
            'start_time': self._start_time.isoformat() if self._start_time else None,
            'stop_time': self._stop_time.isoformat() if self._stop_time else None,
            'services': self._service_container.list_services(),
            'platform': SystemUtils.get_platform_info(),
            'process': SystemUtils.get_process_info(),
            'memory': SystemUtils.get_memory_usage(),
            'disk': SystemUtils.get_disk_usage()
        }
    
    def run(self) -> None:
        """运行应用程序（阻塞）"""
        self.start()
        
        try:
            # 保持运行状态
            while self._state == AppState.RUNNING:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("接收到中断信号")
        finally:
            self.stop()
    
    @contextmanager
    def context(self):
        """
        应用上下文管理器
        
        Yields:
            应用实例
        """
        self.start()
        try:
            yield self
        finally:
            self.stop()


# 全局应用实例
_global_app: Optional[Application] = None
_app_lock = threading.RLock()


def get_app() -> Application:
    """
    获取全局应用实例
    
    Returns:
        应用实例
    """
    global _global_app
    if _global_app is None:
        with _app_lock:
            if _global_app is None:
                _global_app = Application()
    return _global_app


def create_app(config: AppConfig = None) -> Application:
    """
    创建应用实例
    
    Args:
        config: 应用配置
        
    Returns:
        应用实例
    """
    global _global_app
    with _app_lock:
        if _global_app is not None:
            logger.warning("全局应用实例已存在，将被替换")
        _global_app = Application(config)
    return _global_app


def destroy_app() -> None:
    """销毁全局应用实例"""
    global _global_app
    with _app_lock:
        if _global_app is not None:
            _global_app.stop()
            _global_app = None


# 应用装饰器
def app_service(name: str = None, dependencies: List[str] = None, 
                singleton: bool = True, priority: int = 0):
    """
    应用服务装饰器
    
    Args:
        name: 服务名称
        dependencies: 依赖服务列表
        singleton: 是否为单例
        priority: 优先级
        
    Returns:
        装饰器函数
    """
    def decorator(cls):
        service_name = name or cls.__name__
        
        def factory():
            return cls()
        
        # 在应用启动时注册服务
        def register_service():
            app = get_app()
            app.register_service(service_name, factory, dependencies, singleton, priority)
        
        # 延迟注册
        atexit.register(register_service)
        
        return cls
    
    return decorator


def event_handler(event_type: str):
    """
    事件处理器装饰器
    
    Args:
        event_type: 事件类型
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 在应用启动时注册事件处理器
        def register_handler():
            app = get_app()
            app.subscribe_event(event_type, wrapper)
        
        # 延迟注册
        atexit.register(register_handler)
        
        return wrapper
    
    return decorator


def resource(name: str, cleanup_handler: Callable = None):
    """
    资源装饰器
    
    Args:
        name: 资源名称
        cleanup_handler: 清理处理器
        
    Returns:
        装饰器函数
    """
    def decorator(cls):
        def factory():
            return cls()
        
        # 在应用启动时注册资源
        def register_resource():
            app = get_app()
            resource_instance = factory()
            app.register_resource(name, resource_instance, cleanup_handler)
        
        # 延迟注册
        atexit.register(register_resource)
        
        return cls
    
    return decorator