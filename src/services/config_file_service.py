"""
配置文件服务
处理.cfg文件的读取和解析
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import re

# 日志导入
try:
    from src.utils.logger import log_info, log_error, log_debug
except ImportError:
    # 如果日志模块不可用，使用print作为后备
    def log_info(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_error(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_debug(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)


class ConfigFileService:
    """
    配置文件服务类
    处理全景图对应的.cfg文件
    """
    
    def __init__(self):
        self.supported_formats = {'.cfg', '.txt', '.config'}
    
    def find_config_file(self, panoramic_image_path: str) -> Optional[str]:
        """
        查找全景图对应的配置文件
        """
        try:
            panoramic_path = Path(panoramic_image_path)
            config_file = panoramic_path.with_suffix('.cfg')
            
            if config_file.exists():
                return str(config_file)
            
            # 尝试其他可能的扩展名
            for ext in ['.txt', '.config']:
                alt_config = panoramic_path.with_suffix(ext)
                if alt_config.exists():
                    return str(alt_config)
            
            return None
            
        except Exception as e:
            log_error(f"查找配置文件失败: {e}", "CONFIG")
            return None
    
    def parse_config_file(self, config_file_path: str) -> Optional[Dict[int, str]]:
        """
        解析配置文件，返回孔位标注映射
        
        Args:
            config_file_path: 配置文件路径
            
        Returns:
            Dict[int, str]: 孔位编号到标注的映射，失败时返回None
        """
        try:
            if not os.path.exists(config_file_path):
                log_error(f"配置文件不存在: {config_file_path}", "CONFIG")
                return None
            
            annotations = {}
            
            with open(config_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                if not content:
                    log_error(f"配置文件为空: {config_file_path}", "CONFIG")
                    return {}
                
                # 尝试不同的解析格式
                # 优先尝试复杂格式（JSON），然后是简单格式
                annotations = self._parse_format_json(content) or \
                             self._parse_format_enhanced(content) or \
                             self._parse_format_1(content) or \
                             self._parse_format_2(content) or \
                             self._parse_format_3(content) or \
                             self._parse_format_symbol_string(content)
                
                if annotations is None:
                    log_error(f"无法解析配置文件格式: {config_file_path}", "CONFIG")
                    return None
                
                # 提取全景图ID用于日志
                panoramic_id = Path(config_file_path).stem
                log_debug(f"解析配置文件: {panoramic_id}，共 {len(annotations)} 个标注", "CONFIG")
                return annotations
                
        except Exception as e:
            log_error(f"解析配置文件失败: {e}", "CONFIG")
            return None
    
    def _parse_format_json(self, content: str) -> Optional[Dict[int, str]]:
        """
        解析JSON格式配置文件
        支持包含干扰因素的复杂标注
        """
        try:
            import json
            data = json.loads(content)
            
            if isinstance(data, dict):
                annotations = {}
                for key, value in data.items():
                    try:
                        hole_num = int(key)
                        if 1 <= hole_num <= 120:
                            # 如果值是字典，解析复杂标注
                            if isinstance(value, dict):
                                annotation_str = self._complex_annotation_to_string(value)
                            else:
                                annotation_str = str(value)
                            annotations[hole_num] = annotation_str
                    except ValueError:
                        continue
                
                return annotations if annotations else None
            
        except Exception:
            return None
    
    def _parse_format_enhanced(self, content: str) -> Optional[Dict[int, str]]:
        """
        解析增强格式: hole_number:complex_annotation
        例如: 1:positive_with_artifacts, 2:negative_with_pores
        """
        try:
            annotations = {}
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        try:
                            hole_num = int(parts[0].strip())
                            annotation = parts[1].strip()
                            
                            # 如果是复杂标注格式，直接使用
                            if 1 <= hole_num <= 120:
                                annotations[hole_num] = annotation
                        except ValueError:
                            continue
            
            return annotations if annotations else None
            
        except Exception:
            return None
    
    def _complex_annotation_to_string(self, annotation_dict: dict) -> str:
        """
        将复杂标注字典转换为字符串
        """
        try:
            growth_level = annotation_dict.get('growth_level', 'negative')
            interference_factors = annotation_dict.get('interference_factors', [])
            
            # 构建标注字符串
            if interference_factors:
                # 支持中文和英文干扰因素
                factors_str = '_'.join(interference_factors)
                return f"{growth_level}_with_{factors_str}"
            else:
                return growth_level
                
        except Exception:
            return str(annotation_dict)
    
    def _parse_format_1(self, content: str) -> Optional[Dict[int, str]]:
        """
        解析格式1: hole_number:annotation
        例如: 1:positive, 2:negative
        """
        try:
            annotations = {}
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        try:
                            hole_num = int(parts[0].strip())
                            annotation = parts[1].strip()
                            if 1 <= hole_num <= 120:  # 验证孔位范围
                                annotations[hole_num] = annotation
                        except ValueError:
                            continue
            
            return annotations if annotations else None
            
        except Exception:
            return None
    
    def _parse_format_2(self, content: str) -> Optional[Dict[int, str]]:
        """
        解析格式2: JSON格式
        """
        try:
            import json
            data = json.loads(content)
            
            if isinstance(data, dict):
                annotations = {}
                for key, value in data.items():
                    try:
                        hole_num = int(key)
                        if 1 <= hole_num <= 120:
                            annotations[hole_num] = str(value)
                    except ValueError:
                        continue
                
                return annotations if annotations else None
            
        except Exception:
            return None
    
    def _parse_format_3(self, content: str) -> Optional[Dict[int, str]]:
        """
        解析格式3: 简单的数字-标注对
        例如: 1 positive, 2 negative
        """
        try:
            annotations = {}
            
            # 使用正则表达式匹配数字和标注
            pattern = r'(\d+)\s+([^\s,\n]+)'
            matches = re.findall(pattern, content)
            
            for match in matches:
                try:
                    hole_num = int(match[0])
                    annotation = match[1].strip()
                    if 1 <= hole_num <= 120:
                        annotations[hole_num] = annotation
                except ValueError:
                    continue
            
            return annotations if annotations else None
        
        except Exception:
            return None

    
    def _parse_format_symbol_string(self, content: str) -> Optional[Dict[int, str]]:
        """
        解析格式4: 文件名,符号串格式
        例如: EB10000026.bmp,-++--+----+-+-++++-++--++++++-----++++++++++++++++++++++++++++++---+++++++++++++++--++++++++++--++------++++-++++-++++++
        其中 + 表示阳性，- 表示阴性
        """
        try:
            annotations = {}
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 检查是否包含逗号分隔的格式
                if ',' in line:
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        filename = parts[0].strip()
                        symbols = parts[1]  # 不去除符号串的空格，保持原始格式
                        
                        # 解析符号串，每个符号对应一个孔位
                        for i, symbol in enumerate(symbols):
                            hole_num = i + 1
                            if hole_num > 120:  # 最多120个孔位
                                break
                            
                            # 根据符号映射标注
                            if symbol == '+':
                                annotations[hole_num] = 'positive'
                            elif symbol == '-':
                                annotations[hole_num] = 'negative'
                            elif symbol == '?':
                                annotations[hole_num] = 'uncertain'
                            elif symbol == 'w' or symbol == 'W':
                                annotations[hole_num] = 'weak_growth'
                            elif symbol == ' ':
                                annotations[hole_num] = 'invalid'
                            # 其他符号忽略或设为未标注
                        
                        return annotations if annotations else None
            
            return None
            
        except Exception:
            return None
    
    def save_config_file(self, config_file_path: str, annotations: Dict[int, str]) -> bool:
        """
        保存标注数据到配置文件
        
        Args:
            config_file_path: 配置文件路径
            annotations: 孔位标注映射
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
            
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write("# 孔位标注配置文件\n")
                f.write("# 格式: 孔位编号:标注\n\n")
                
                for hole_num in sorted(annotations.keys()):
                    annotation = annotations[hole_num]
                    f.write(f"{hole_num}:{annotation}\n")
            
            log_info(f"配置文件保存成功: {config_file_path}", "CONFIG")
            return True
            
        except Exception as e:
            log_error(f"保存配置文件失败: {e}", "CONFIG")
            return False
    
    def validate_annotation_format(self, annotation: str) -> Tuple[bool, str]:
        """
        验证标注格式是否有效
        
        Args:
            annotation: 标注字符串
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if not annotation:
                return False, "标注不能为空"
            
            # 检查长度
            if len(annotation) > 50:
                return False, "标注长度不能超过50个字符"
            
            # 检查是否包含无效字符
            invalid_chars = set(annotation) & {'\n', '\r', '\t', ':', ';'}
            if invalid_chars:
                return False, f"包含无效字符: {invalid_chars}"
            
            return True, "标注字符串有效"
            
        except Exception as e:
            return False, f"验证失败: {e}"
    
    def get_annotation(self, panoramic_id: str = None, hole_number: int = None) -> Optional[str]:
        """
        获取指定孔位的标注数据
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 孔位编号，如果为None则返回当前孔位的标注
            
        Returns:
            标注数据字符串，如果没有找到则返回None
        """
        # 暂时返回None，实际实现需要根据具体需求
        return None
    
    def save_window_state(self, state_data: dict) -> bool:
        """
        保存窗口状态
        
        Args:
            state_data: 窗口状态数据
            
        Returns:
            bool: 保存是否成功
        """
        # 暂时返回True，实际实现需要根据具体需求
        return True
    
    def get_annotation_statistics(self, annotations: Dict[int, str]) -> Dict[str, int]:
        """
        获取标注统计信息
        
        Args:
            annotations: 孔位标注映射
            
        Returns:
            Dict[str, int]: 统计信息
        """
        stats = {
            'total': len(annotations),
            'positive': 0,
            'negative': 0,
            'weak_growth': 0
        }
        
        for growth_level in annotations.values():
            if growth_level in stats:
                stats[growth_level] += 1
        
        stats['unannotated'] = 120 - stats['total']
        
        return stats
    
    def convert_hole_number_to_position(self, hole_number: int) -> Tuple[int, int]:
        """
        将孔位编号转换为行列位置
        
        Args:
            hole_number: 孔位编号 (1-120)
            
        Returns:
            Tuple[int, int]: (行, 列) 位置，从1开始
        """
        if not (1 <= hole_number <= 120):
            raise ValueError(f"孔位编号必须在1-120之间，当前值: {hole_number}")
        
        row = ((hole_number - 1) // 12) + 1
        col = ((hole_number - 1) % 12) + 1
        
        return row, col
    
    def convert_position_to_hole_number(self, row: int, col: int) -> int:
        """
        将行列位置转换为孔位编号
        
        Args:
            row: 行位置 (1-10)
            col: 列位置 (1-12)
            
        Returns:
            int: 孔位编号 (1-120)
        """
        if not (1 <= row <= 10):
            raise ValueError(f"行位置必须在1-10之间，当前值: {row}")
        if not (1 <= col <= 12):
            raise ValueError(f"列位置必须在1-12之间，当前值: {col}")
        
        return (row - 1) * 12 + col