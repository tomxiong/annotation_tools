"""
工具类模块

提供通用的工具函数和类，支持：
- 文件操作工具
- 数据验证工具
- 时间日期工具
- 字符串处理工具
- 数学计算工具
- 系统工具
- 编码转换工具
"""

import os
import sys
import json
import base64
import hashlib
import uuid
import time
import re
import threading
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps, lru_cache
from contextlib import contextmanager
import tempfile
import shutil

from .logger import get_logger
from .exceptions import ValidationError, SystemError

logger = get_logger(__name__)

T = TypeVar('T')


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """
        确保目录存在
        
        Args:
            path: 目录路径
            
        Returns:
            目录路径对象
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def safe_delete(path: Union[str, Path]) -> bool:
        """
        安全删除文件或目录
        
        Args:
            path: 文件或目录路径
            
        Returns:
            是否删除成功
        """
        try:
            path = Path(path)
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                return True
            return False
        except Exception as e:
            logger.error(f"删除文件失败: {path} - {e}")
            return False
    
    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """
        获取文件大小
        
        Args:
            path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            return Path(path).stat().st_size
        except Exception as e:
            logger.error(f"获取文件大小失败: {path} - {e}")
            return 0
    
    @staticmethod
    def get_file_hash(path: Union[str, Path], algorithm: str = 'md5') -> str:
        """
        获取文件哈希值
        
        Args:
            path: 文件路径
            algorithm: 哈希算法
            
        Returns:
            哈希值
        """
        try:
            hash_obj = hashlib.new(algorithm)
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {path} - {e}")
            return ''
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否复制成功
        """
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"复制文件失败: {src} -> {dst} - {e}")
            return False
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否移动成功
        """
        try:
            shutil.move(str(src), str(dst))
            return True
        except Exception as e:
            logger.error(f"移动文件失败: {src} -> {dst} - {e}")
            return False
    
    @staticmethod
    def read_file_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        读取文本文件
        
        Args:
            path: 文件路径
            encoding: 编码格式
            
        Returns:
            文件内容
        """
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {path} - {e}")
            return ''
    
    @staticmethod
    def write_file_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """
        写入文本文件
        
        Args:
            path: 文件路径
            content: 文件内容
            encoding: 编码格式
            
        Returns:
            是否写入成功
        """
        try:
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"写入文件失败: {path} - {e}")
            return False
    
    @staticmethod
    def read_file_json(path: Union[str, Path], encoding: str = 'utf-8') -> Any:
        """
        读取JSON文件
        
        Args:
            path: 文件路径
            encoding: 编码格式
            
        Returns:
            JSON数据
        """
        try:
            with open(path, 'r', encoding=encoding) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取JSON文件失败: {path} - {e}")
            return None
    
    @staticmethod
    def write_file_json(path: Union[str, Path], data: Any, encoding: str = 'utf-8', indent: int = 2) -> bool:
        """
        写入JSON文件
        
        Args:
            path: 文件路径
            data: JSON数据
            encoding: 编码格式
            indent: 缩进空格数
            
        Returns:
            是否写入成功
        """
        try:
            with open(path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"写入JSON文件失败: {path} - {e}")
            return False
    
    @staticmethod
    @contextmanager
    def temporary_file(mode: str = 'w', suffix: str = None, prefix: str = None, delete: bool = True):
        """
        临时文件上下文管理器
        
        Args:
            mode: 文件模式
            suffix: 文件后缀
            prefix: 文件前缀
            delete: 是否删除临时文件
            
        Yields:
            临时文件对象
        """
        temp_file = tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, prefix=prefix, delete=delete)
        try:
            yield temp_file
        finally:
            if delete and not temp_file.closed:
                temp_file.close()


class ValidationUtils:
    """数据验证工具类"""
    
    @staticmethod
    def is_not_empty(value: Any) -> bool:
        """
        验证值是否非空
        
        Args:
            value: 要验证的值
            
        Returns:
            是否非空
        """
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ''
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) > 0
        return True
    
    @staticmethod
    def is_email(email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否是有效的邮箱格式
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_phone(phone: str) -> bool:
        """
        验证手机号格式
        
        Args:
            phone: 手机号
            
        Returns:
            是否是有效的手机号格式
        """
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def is_url(url: str) -> bool:
        """
        验证URL格式
        
        Args:
            url: URL地址
            
        Returns:
            是否是有效的URL格式
        """
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def is_ip_address(ip: str) -> bool:
        """
        验证IP地址格式
        
        Args:
            ip: IP地址
            
        Returns:
            是否是有效的IP地址格式
        """
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return re.match(pattern, ip) is not None
    
    @staticmethod
    def is_numeric(value: Any) -> bool:
        """
        验证是否为数字
        
        Args:
            value: 要验证的值
            
        Returns:
            是否为数字
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_integer(value: Any) -> bool:
        """
        验证是否为整数
        
        Args:
            value: 要验证的值
            
        Returns:
            是否为整数
        """
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_positive_number(value: Any) -> bool:
        """
        验证是否为正数
        
        Args:
            value: 要验证的值
            
        Returns:
            是否为正数
        """
        return ValidationUtils.is_numeric(value) and float(value) > 0
    
    @staticmethod
    def is_positive_integer(value: Any) -> bool:
        """
        验证是否为正整数
        
        Args:
            value: 要验证的值
            
        Returns:
            是否为正整数
        """
        return ValidationUtils.is_integer(value) and int(value) > 0
    
    @staticmethod
    def is_in_range(value: Any, min_val: Any, max_val: Any) -> bool:
        """
        验证值是否在指定范围内
        
        Args:
            value: 要验证的值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            是否在范围内
        """
        try:
            num_value = float(value)
            return min_val <= num_value <= max_val
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """
        验证必填字段
        
        Args:
            value: 要验证的值
            field_name: 字段名
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if not ValidationUtils.is_not_empty(value):
            raise ValidationError(f"字段 {field_name} 不能为空", field=field_name, value=value)
    
    @staticmethod
    def validate_length(value: str, min_len: int, max_len: int, field_name: str) -> None:
        """
        验证字符串长度
        
        Args:
            value: 要验证的值
            min_len: 最小长度
            max_len: 最大长度
            field_name: 字段名
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if not (min_len <= len(value) <= max_len):
            raise ValidationError(f"字段 {field_name} 长度必须在 {min_len}-{max_len} 之间", field=field_name, value=value)


class DateTimeUtils:
    """时间日期工具类"""
    
    @staticmethod
    def now() -> datetime:
        """
        获取当前时间
        
        Returns:
            当前时间
        """
        return datetime.now()
    
    @staticmethod
    def now_timestamp() -> int:
        """
        获取当前时间戳
        
        Returns:
            当前时间戳
        """
        return int(time.time())
    
    @staticmethod
    def now_isoformat() -> str:
        """
        获取当前时间的ISO格式字符串
        
        Returns:
            ISO格式时间字符串
        """
        return datetime.now().isoformat()
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """
        格式化时间
        
        Args:
            dt: 时间对象
            format_str: 格式字符串
            
        Returns:
            格式化后的时间字符串
        """
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> datetime:
        """
        解析时间字符串
        
        Args:
            date_str: 时间字符串
            format_str: 格式字符串
            
        Returns:
            时间对象
        """
        try:
            return datetime.strptime(date_str, format_str)
        except ValueError as e:
            raise ValidationError(f"时间格式错误: {date_str}", field='date_str', value=date_str) from e
    
    @staticmethod
    def add_days(dt: datetime, days: int) -> datetime:
        """
        添加天数
        
        Args:
            dt: 时间对象
            days: 天数
            
        Returns:
            新的时间对象
        """
        return dt + timedelta(days=days)
    
    @staticmethod
    def add_hours(dt: datetime, hours: int) -> datetime:
        """
        添加小时数
        
        Args:
            dt: 时间对象
            hours: 小时数
            
        Returns:
            新的时间对象
        """
        return dt + timedelta(hours=hours)
    
    @staticmethod
    def add_minutes(dt: datetime, minutes: int) -> datetime:
        """
        添加分钟数
        
        Args:
            dt: 时间对象
            minutes: 分钟数
            
        Returns:
            新的时间对象
        """
        return dt + timedelta(minutes=minutes)
    
    @staticmethod
    def add_seconds(dt: datetime, seconds: int) -> datetime:
        """
        添加秒数
        
        Args:
            dt: 时间对象
            seconds: 秒数
            
        Returns:
            新的时间对象
        """
        return dt + timedelta(seconds=seconds)
    
    @staticmethod
    def date_diff(dt1: datetime, dt2: datetime) -> timedelta:
        """
        计算时间差
        
        Args:
            dt1: 时间1
            dt2: 时间2
            
        Returns:
            时间差
        """
        return dt2 - dt1
    
    @staticmethod
    def get_age(birth_date: datetime) -> int:
        """
        计算年龄
        
        Args:
            birth_date: 出生日期
            
        Returns:
            年龄
        """
        today = datetime.now()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age
    
    @staticmethod
    def is_weekend(dt: datetime) -> bool:
        """
        判断是否为周末
        
        Args:
            dt: 时间对象
            
        Returns:
            是否为周末
        """
        return dt.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    @staticmethod
    def get_weekday_name(dt: datetime) -> str:
        """
        获取星期名称
        
        Args:
            dt: 时间对象
            
        Returns:
            星期名称
        """
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return weekdays[dt.weekday()]
    
    @staticmethod
    def get_month_name(dt: datetime) -> str:
        """
        获取月份名称
        
        Args:
            dt: 时间对象
            
        Returns:
            月份名称
        """
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        return months[dt.month - 1]


class StringUtils:
    """字符串处理工具类"""
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = '...') -> str:
        """
        截断字符串
        
        Args:
            text: 原字符串
            max_length: 最大长度
            suffix: 后缀
            
        Returns:
            截断后的字符串
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def camel_to_snake(name: str) -> str:
        """
        驼峰命名转下划线命名
        
        Args:
            name: 驼峰命名字符串
            
        Returns:
            下划线命名字符串
        """
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def snake_to_camel(name: str) -> str:
        """
        下划线命名转驼峰命名
        
        Args:
            name: 下划线命名字符串
            
        Returns:
            驼峰命名字符串
        """
        components = name.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    @staticmethod
    def to_title_case(text: str) -> str:
        """
        转换为标题格式
        
        Args:
            text: 原字符串
            
        Returns:
            标题格式字符串
        """
        return text.title()
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        标准化空白字符
        
        Args:
            text: 原字符串
            
        Returns:
            标准化后的字符串
        """
        return ' '.join(text.split())
    
    @staticmethod
    def remove_html_tags(text: str) -> str:
        """
        移除HTML标签
        
        Args:
            text: 包含HTML标签的字符串
            
        Returns:
            纯文本字符串
        """
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        转义HTML特殊字符
        
        Args:
            text: 原字符串
            
        Returns:
            转义后的字符串
        """
        escape_map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }
        return ''.join(escape_map.get(char, char) for char in text)
    
    @staticmethod
    def generate_random_string(length: int = 8, include_digits: bool = True, include_special: bool = False) -> str:
        """
        生成随机字符串
        
        Args:
            length: 字符串长度
            include_digits: 是否包含数字
            include_special: 是否包含特殊字符
            
        Returns:
            随机字符串
        """
        import random
        import string
        
        chars = string.ascii_letters
        if include_digits:
            chars += string.digits
        if include_special:
            chars += '!@#$%^&*'
        
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def is_chinese(text: str) -> bool:
        """
        判断是否为中文字符
        
        Args:
            text: 要判断的字符串
            
        Returns:
            是否为中文字符
        """
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """
        提取字符串中的数字
        
        Args:
            text: 原字符串
            
        Returns:
            数字列表
        """
        return [int(num) for num in re.findall(r'\d+', text)]
    
    @staticmethod
    def mask_sensitive_info(text: str, mask_char: str = '*', keep_start: int = 2, keep_end: int = 2) -> str:
        """
        脱敏处理敏感信息
        
        Args:
            text: 原字符串
            mask_char: 掩码字符
            keep_start: 保留开头字符数
            keep_end: 保留结尾字符数
            
        Returns:
            脱敏后的字符串
        """
        if len(text) <= keep_start + keep_end:
            return mask_char * len(text)
        
        start = text[:keep_start]
        end = text[-keep_end:] if keep_end > 0 else ''
        middle = mask_char * (len(text) - keep_start - keep_end)
        
        return start + middle + end


class MathUtils:
    """数学计算工具类"""
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """
        限制数值范围
        
        Args:
            value: 原值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            限制后的值
        """
        return max(min_val, min(max_val, value))
    
    @staticmethod
    def lerp(start: float, end: float, t: float) -> float:
        """
        线性插值
        
        Args:
            start: 起始值
            end: 结束值
            t: 插值因子 (0-1)
            
        Returns:
            插值结果
        """
        return start + (end - start) * t
    
    @staticmethod
    def normalize(value: float, min_val: float, max_val: float) -> float:
        """
        归一化
        
        Args:
            value: 原值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            归一化后的值 (0-1)
        """
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)
    
    @staticmethod
    def percentage(value: float, total: float) -> float:
        """
        计算百分比
        
        Args:
            value: 当前值
            total: 总值
            
        Returns:
            百分比
        """
        if total == 0:
            return 0.0
        return (value / total) * 100
    
    @staticmethod
    def round_to(value: float, decimal_places: int) -> float:
        """
        四舍五入到指定小数位
        
        Args:
            value: 原值
            decimal_places: 小数位数
            
        Returns:
            四舍五入后的值
        """
        return round(value, decimal_places)
    
    @staticmethod
    def floor_to(value: float, decimal_places: int) -> float:
        """
        向下取整到指定小数位
        
        Args:
            value: 原值
            decimal_places: 小数位数
            
        Returns:
            向下取整后的值
        """
        factor = 10 ** decimal_places
        return math.floor(value * factor) / factor
    
    @staticmethod
    def ceil_to(value: float, decimal_places: int) -> float:
        """
        向上取整到指定小数位
        
        Args:
            value: 原值
            decimal_places: 小数位数
            
        Returns:
            向上取整后的值
        """
        factor = 10 ** decimal_places
        return math.ceil(value * factor) / factor
    
    @staticmethod
    def average(values: List[float]) -> float:
        """
        计算平均值
        
        Args:
            values: 数值列表
            
        Returns:
            平均值
        """
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    @staticmethod
    def median(values: List[float]) -> float:
        """
        计算中位数
        
        Args:
            values: 数值列表
            
        Returns:
            中位数
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]
    
    @staticmethod
    def standard_deviation(values: List[float]) -> float:
        """
        计算标准差
        
        Args:
            values: 数值列表
            
        Returns:
            标准差
        """
        if not values:
            return 0.0
        
        avg = MathUtils.average(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    @staticmethod
    def format_bytes(bytes_count: int) -> str:
        """
        格式化字节数
        
        Args:
            bytes_count: 字节数
            
        Returns:
            格式化后的字符串
        """
        if bytes_count == 0:
            return '0 B'
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        
        while bytes_count >= 1024 and unit_index < len(units) - 1:
            bytes_count /= 1024
            unit_index += 1
        
        return f'{bytes_count:.2f} {units[unit_index]}'
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        格式化持续时间
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的字符串
        """
        if seconds < 60:
            return f'{seconds:.1f}s'
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f'{int(minutes)}m {remaining_seconds:.1f}s'
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            remaining_seconds = seconds % 60
            return f'{int(hours)}h {int(remaining_minutes)}m {remaining_seconds:.1f}s'


class SystemUtils:
    """系统工具类"""
    
    @staticmethod
    def get_hostname() -> str:
        """
        获取主机名
        
        Returns:
            主机名
        """
        import socket
        return socket.gethostname()
    
    @staticmethod
    def get_ip_address() -> str:
        """
        获取本机IP地址
        
        Returns:
            IP地址
        """
        import socket
        try:
            # 连接到外部服务器获取本机IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
            return ip
        except Exception:
            return '127.0.0.1'
    
    @staticmethod
    def get_mac_address() -> str:
        """
        获取MAC地址
        
        Returns:
            MAC地址
        """
        import uuid
        return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 8 * 6, 8)][::-1])
    
    @staticmethod
    def get_cpu_usage() -> float:
        """
        获取CPU使用率
        
        Returns:
            CPU使用率
        """
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """
        获取内存使用情况
        
        Returns:
            内存使用信息
        """
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free,
                'percent': memory.percent
            }
        except ImportError:
            return {'total': 0, 'available': 0, 'used': 0, 'free': 0, 'percent': 0}
    
    @staticmethod
    def get_disk_usage(path: str = '/') -> Dict[str, float]:
        """
        获取磁盘使用情况
        
        Args:
            path: 路径
            
        Returns:
            磁盘使用信息
        """
        try:
            import psutil
            disk = psutil.disk_usage(path)
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        except ImportError:
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
    
    @staticmethod
    def get_platform_info() -> Dict[str, str]:
        """
        获取平台信息
        
        Returns:
            平台信息
        """
        import platform
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
    
    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """
        获取当前进程信息
        
        Returns:
            进程信息
        """
        import os
        import psutil
        
        try:
            process = psutil.Process(os.getpid())
            return {
                'pid': process.pid,
                'name': process.name(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'create_time': process.create_time(),
                'status': process.status()
            }
        except Exception:
            return {'pid': os.getpid(), 'name': 'unknown', 'cpu_percent': 0, 'memory_percent': 0}
    
    @staticmethod
    def is_admin() -> bool:
        """
        检查是否具有管理员权限
        
        Returns:
            是否为管理员
        """
        try:
            import os
            if os.name == 'nt':  # Windows
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:  # Unix/Linux/Mac
                return os.getuid() == 0
        except Exception:
            return False
    
    @staticmethod
    def execute_command(command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        执行系统命令
        
        Args:
            command: 命令字符串
            timeout: 超时时间（秒）
            
        Returns:
            (返回码, 标准输出, 标准错误)
        """
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, '', 'Command timeout'
        except Exception as e:
            return -1, '', str(e)


class EncodingUtils:
    """编码转换工具类"""
    
    @staticmethod
    def base64_encode(data: Union[str, bytes]) -> str:
        """
        Base64编码
        
        Args:
            data: 要编码的数据
            
        Returns:
            Base64编码字符串
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def base64_decode(data: str) -> bytes:
        """
        Base64解码
        
        Args:
            data: Base64编码字符串
            
        Returns:
            解码后的字节数据
        """
        return base64.b64decode(data)
    
    @staticmethod
    def url_encode(data: str) -> str:
        """
        URL编码
        
        Args:
            data: 要编码的数据
            
        Returns:
            URL编码字符串
        """
        import urllib.parse
        return urllib.parse.quote(data)
    
    @staticmethod
    def url_decode(data: str) -> str:
        """
        URL解码
        
        Args:
            data: URL编码字符串
            
        Returns:
            解码后的字符串
        """
        import urllib.parse
        return urllib.parse.unquote(data)
    
    @staticmethod
    def json_encode(data: Any, indent: int = 2) -> str:
        """
        JSON编码
        
        Args:
            data: 要编码的数据
            indent: 缩进
            
        Returns:
            JSON字符串
        """
        return json.dumps(data, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def json_decode(data: str) -> Any:
        """
        JSON解码
        
        Args:
            data: JSON字符串
            
        Returns:
            解码后的数据
        """
        return json.loads(data)
    
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            编码格式
        """
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024)  # 读取前1024字节用于检测编码
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except ImportError:
            return 'utf-8'
    
    @staticmethod
    def convert_encoding(input_file: str, output_file: str, from_encoding: str, to_encoding: str = 'utf-8') -> bool:
        """
        转换文件编码
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            from_encoding: 原编码
            to_encoding: 目标编码
            
        Returns:
            是否转换成功
        """
        try:
            with open(input_file, 'r', encoding=from_encoding) as infile:
                content = infile.read()
            
            with open(output_file, 'w', encoding=to_encoding) as outfile:
                outfile.write(content)
            
            return True
        except Exception as e:
            logger.error(f"编码转换失败: {e}")
            return False


class CacheUtils:
    """缓存工具类"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间（秒）
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        设置缓存
        
        Args:
            key: 键
            value: 值
            ttl: 生存时间（秒）
        """
        with self._lock:
            if len(self._cache) >= self._max_size:
                # 删除最旧的条目
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['timestamp'])
                del self._cache[oldest_key]
            
            self._cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl or self._ttl
            }
    
    def get(self, key: str) -> Any:
        """
        获取缓存
        
        Args:
            key: 键
            
        Returns:
            值或None
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            current_time = time.time()
            
            # 检查是否过期
            if current_time - item['timestamp'] > item['ttl']:
                del self._cache[key]
                return None
            
            return item['value']
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            缓存条目数
        """
        with self._lock:
            return len(self._cache)
    
    def cleanup(self) -> None:
        """清理过期缓存"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, item in self._cache.items()
                if current_time - item['timestamp'] > item['ttl']
            ]
            
            for key in expired_keys:
                del self._cache[key]


# 常用装饰器
def timing_decorator(func):
    """
    计时装饰器
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"函数 {func.__name__} 执行时间: {end_time - start_time:.4f}s")
        return result
    return wrapper


def retry_decorator(max_attempts: int = 3, delay: float = 1.0, exceptions: Tuple = (Exception,)):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 延迟时间
        exceptions: 要捕获的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}")
                        time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


def memoize_decorator(max_size: int = 128):
    """
    记忆化装饰器
    
    Args:
        max_size: 最大缓存大小
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(sorted(kwargs.items()))
            
            if key not in cache:
                if len(cache) >= max_size:
                    # 删除最旧的条目
                    cache.pop(next(iter(cache)))
                cache[key] = func(*args, **kwargs)
            
            return cache[key]
        
        return wrapper
    return decorator


# 便捷函数
def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()


def is_file_exists(path: Union[str, Path]) -> bool:
    """检查文件是否存在"""
    return Path(path).exists()


def get_file_size_formatted(path: Union[str, Path]) -> str:
    """获取格式化的文件大小"""
    size = FileUtils.get_file_size(path)
    return MathUtils.format_bytes(size)


def create_backup(file_path: Union[str, Path], backup_dir: str = 'backups') -> str:
    """
    创建文件备份
    
    Args:
        file_path: 原文件路径
        backup_dir: 备份目录
        
    Returns:
        备份文件路径
    """
    source_path = Path(file_path)
    backup_path = Path(backup_dir)
    
    # 确保备份目录存在
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # 生成备份文件名
    timestamp = DateTimeUtils.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
    backup_file_path = backup_path / backup_filename
    
    # 复制文件
    if FileUtils.copy_file(source_path, backup_file_path):
        logger.info(f"创建备份成功: {backup_file_path}")
        return str(backup_file_path)
    else:
        raise SystemError(f"创建备份失败: {file_path}")


def validate_file_type(file_path: Union[str, Path], allowed_extensions: List[str]) -> bool:
    """
    验证文件类型
    
    Args:
        file_path: 文件路径
        allowed_extensions: 允许的扩展名列表
        
    Returns:
        是否为允许的文件类型
    """
    extension = get_file_extension(file_path)
    return extension.lower() in [ext.lower() for ext in allowed_extensions]


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原文件名
        
    Returns:
        清理后的文件名
    """
    # 移除非法字符
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除首尾空格和点
    sanitized = sanitized.strip('. ')
    # 如果为空，使用默认名称
    if not sanitized:
        sanitized = 'unnamed'
    return sanitized


# 全局缓存实例
_global_cache = CacheUtils(max_size=1000, ttl=3600)

def get_global_cache() -> CacheUtils:
    """获取全局缓存实例"""
    return _global_cache