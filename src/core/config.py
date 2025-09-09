"""
配置管理模块

提供统一的配置管理功能，支持：
- 配置文件的读取和写入
- 环境变量配置
- 默认配置管理
- 配置验证和类型转换
- 配置变更通知
"""

import os
import json
import yaml
from typing import Any, Dict, Optional, Union, List, TypeVar, Generic, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict
import threading
from functools import wraps

# 延迟导入避免循环依赖

# logger = get_logger(__name__)  # 延迟初始化

T = TypeVar('T')


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "annotation_tool"
    username: str = ""
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class ImageConfig:
    """图像处理配置"""
    max_image_size: int = 50 * 1024 * 1024  # 50MB
    supported_formats: List[str] = field(default_factory=lambda: [".jpg", ".jpeg", ".png", ".bmp", ".tiff"])
    default_zoom_level: float = 1.0
    max_zoom_level: float = 5.0
    min_zoom_level: float = 0.1
    grid_color: str = "#FF0000"
    grid_width: int = 2
    cache_size: int = 100  # 缓存图像数量


@dataclass
class AnnotationConfig:
    """标注配置"""
    auto_save_interval: int = 60  # 自动保存间隔（秒）
    backup_count: int = 5  # 备份文件数量
    growth_levels: List[str] = field(default_factory=lambda: ["negative", "weak", "positive"])
    microbe_types: List[str] = field(default_factory=lambda: ["bacteria", "fungi"])
    grid_rows: int = 12
    grid_cols: int = 10
    template_dir: str = "templates"
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv"])


@dataclass
class UIConfig:
    """用户界面配置"""
    theme: str = "default"
    window_width: int = 1200
    window_height: int = 800
    font_size: int = 12
    font_family: str = "Arial"
    show_grid: bool = True
    show_coordinates: bool = True
    auto_hide_panels: bool = False
    shortcut_enabled: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True


@dataclass
class ModelConfig:
    """模型配置"""
    path: str = ""
    confidence_threshold: float = 0.5
    device: str = "cpu"


@dataclass
class AppConfig:
    """应用程序主配置"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    annotation: AnnotationConfig = field(default_factory=AnnotationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # 模型配置
    models: Dict[str, ModelConfig] = field(default_factory=dict)

    # 其他配置
    debug: bool = False
    data_dir: str = "data"
    temp_dir: str = "temp"
    log_dir: str = "logs"
    config_file_path: str = "config/app.yaml"

    def __post_init__(self):
        """初始化后处理"""
        # 确保目录存在
        for dir_path in [self.data_dir, self.temp_dir, self.log_dir]:
            os.makedirs(dir_path, exist_ok=True)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self._config = AppConfig()
        self._config_file = config_file or self._config.config_file_path
        self._lock = threading.RLock()
        self._callbacks: List[Callable[[AppConfig], None]] = []
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            config_path = Path(self._config_file)
            if not config_path.exists():
                print(f"Config file not found: {self._config_file}, using default config")
                self.save_config()  # 保存默认配置
                return
            
            with self._lock:
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                
                # 更新配置
                self._update_config_from_dict(data)
                print(f"Config loaded successfully: {self._config_file}")
                
        except Exception as e:
            print(f"Failed to load config file: {e}")
            # 延迟导入避免循环依赖
            from .exceptions import ConfigError
            raise ConfigError(f"Failed to load config file: {e}")
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            config_path = Path(self._config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._lock:
                config_dict = asdict(self._config)
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                    else:
                        json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
                print(f"Config saved successfully: {self._config_file}")
                
        except Exception as e:
            print(f"Failed to save config file: {e}")
            raise ConfigError(f"Failed to save config file: {e}")
    
    def get_config(self) -> AppConfig:
        """获取配置对象"""
        with self._lock:
            return self._config
    
    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return self._config.database
    
    def get_image_config(self) -> ImageConfig:
        """获取图像配置"""
        return self._config.image
    
    def get_annotation_config(self) -> AnnotationConfig:
        """获取标注配置"""
        return self._config.annotation
    
    def get_ui_config(self) -> UIConfig:
        """获取UI配置"""
        return self._config.ui
    
    def get_logging_config(self) -> LoggingConfig:
        """获取日志配置"""
        return self._config.logging
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'database.host'
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set_value(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        try:
            keys = key.split('.')
            config_obj = self._config
            
            # 导航到父对象
            for k in keys[:-1]:
                if hasattr(config_obj, k):
                    config_obj = getattr(config_obj, k)
                else:
                    raise ConfigError(f"无效的配置键: {key}")
            
            # 设置值
            last_key = keys[-1]
            if hasattr(config_obj, last_key):
                setattr(config_obj, last_key, value)
                print(f"Config updated: {key} = {value}")
                
                # 触发回调
                self._notify_callbacks()
            else:
                raise ConfigError(f"无效的配置键: {key}")
                
        except Exception as e:
            print(f"Failed to set config value: {e}")
            raise ConfigError(f"设置配置值失败: {e}")
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """
        批量更新配置
        
        Args:
            config_dict: 配置字典
        """
        try:
            with self._lock:
                self._update_config_from_dict(config_dict)
                print("Config batch update successful")
                
                # 触发回调
                self._notify_callbacks()
                
        except Exception as e:
            print(f"Failed to batch update config: {e}")
            raise ConfigError(f"批量更新配置失败: {e}")
    
    def _update_config_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典更新配置"""
        if 'database' in data:
            self._update_dataclass(self._config.database, data['database'])
        
        if 'image' in data:
            self._update_dataclass(self._config.image, data['image'])
        
        if 'annotation' in data:
            self._update_dataclass(self._config.annotation, data['annotation'])
        
        if 'ui' in data:
            self._update_dataclass(self._config.ui, data['ui'])
        
        if 'logging' in data:
            self._update_dataclass(self._config.logging, data['logging'])
        
        # 更新其他配置
        for key, value in data.items():
            if hasattr(self._config, key) and key not in ['database', 'image', 'annotation', 'ui', 'logging']:
                setattr(self._config, key, value)
    
    def _update_dataclass(self, obj: Any, data: Dict[str, Any]) -> None:
        """更新数据类对象"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def add_callback(self, callback: Callable[[AppConfig], None]) -> None:
        """
        添加配置变更回调
        
        Args:
            callback: 回调函数
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[AppConfig], None]) -> None:
        """
        移除配置变更回调
        
        Args:
            callback: 回调函数
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self) -> None:
        """通知所有回调函数"""
        for callback in self._callbacks:
            try:
                callback(self._config)
            except Exception as e:
                print(f"Config callback execution failed: {e}")
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self.load_config()
        self._notify_callbacks()
    
    def reset_config(self) -> None:
        """重置为默认配置"""
        with self._lock:
            self._config = AppConfig()
            self.save_config()
            self._notify_callbacks()
    
    def validate_config(self) -> List[str]:
        """
        验证配置
        
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            # 验证数据库配置
            if not self._config.database.host:
                errors.append("数据库主机地址不能为空")
            
            if not (1 <= self._config.database.port <= 65535):
                errors.append("数据库端口号必须在1-65535之间")
            
            # 验证图像配置
            if self._config.image.max_image_size <= 0:
                errors.append("最大图像大小必须大于0")
            
            if not self._config.image.supported_formats:
                errors.append("必须支持至少一种图像格式")
            
            # 验证标注配置
            if self._config.annotation.auto_save_interval <= 0:
                errors.append("自动保存间隔必须大于0")
            
            if self._config.annotation.backup_count < 0:
                errors.append("备份文件数量不能为负数")
            
            # 验证UI配置
            if self._config.ui.window_width <= 0 or self._config.ui.window_height <= 0:
                errors.append("窗口尺寸必须大于0")
            
            # 验证日志配置
            if self._config.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                errors.append("日志级别无效")
            
            if self._config.logging.max_file_size <= 0:
                errors.append("日志文件大小必须大于0")
            
        except Exception as e:
            errors.append(f"配置验证过程中发生错误: {e}")
        
        return errors
    
    def export_config(self, file_path: str, format: str = 'yaml') -> None:
        """
        导出配置
        
        Args:
            file_path: 导出文件路径
            format: 导出格式 ('yaml' 或 'json')
        """
        try:
            config_dict = asdict(self._config)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"Config export successful: {file_path}")
            
        except Exception as e:
            print(f"Failed to export config: {e}")
            raise ConfigError(f"Failed to export config: {e}")


def config_callback(func: Callable) -> Callable:
    """
    配置回调装饰器
    
    用于标记配置变更回调函数，提供错误处理和日志记录
    """
    @wraps(func)
    def wrapper(config: AppConfig, *args, **kwargs):
        try:
            print(f"Executing config callback: {func.__name__}")
            return func(config, *args, **kwargs)
        except Exception as e:
            print(f"Config callback execution failed: {func.__name__} - {e}")
    
    return wrapper


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """获取全局配置"""
    return get_config_manager().get_config()


def get_value(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_config_manager().get_value(key, default)


def set_value(key: str, value: Any) -> None:
    """设置配置值"""
    get_config_manager().set_value(key, value)


def reload_config() -> None:
    """重新加载配置"""
    get_config_manager().reload_config()


def reset_config() -> None:
    """重置配置"""
    get_config_manager().reset_config()


# 向后兼容性别名
Config = AppConfig