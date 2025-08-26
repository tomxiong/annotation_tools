"""
配置文件服务
处理.cfg文件的读取和解析
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import re


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
            print(f"查找配置文件失败: {e}")
            return None
    
    def parse_config_file(self, config_file_path: str) -> Optional[Dict[int, str]]:
        """
        解析配置文件，返回孔位标注映射
        
        Args:
            config_file_path: 配置文件路径
            
        Returns:
            Dict[int, str]: 孔位编号 -> 标注结果 ('positive'/'negative')
        """
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 尝试不同的解析方法
            annotations = self._parse_annotation_string(content)
            
            if annotations:
                return annotations
            
            # 如果直接解析失败，尝试查找包含+/-的行
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if self._contains_annotation_pattern(line):
                    annotations = self._parse_annotation_string(line)
                    if annotations:
                        return annotations
            
            return None
            
        except Exception as e:
            print(f"解析配置文件失败: {e}")
            return None
    
    def _parse_annotation_string(self, annotation_string: str) -> Optional[Dict[int, str]]:
        """
        解析标注字符串
        
        Args:
            annotation_string: 包含+/-的标注字符串
            
        Returns:
            Dict[int, str]: 孔位编号 -> 标注结果
        """
        try:
            # 清理字符串，只保留+、-、w等有效字符
            cleaned = re.sub(r'[^+\-w]', '', annotation_string)
            
            if len(cleaned) != 120:
                # 如果不是120个字符，尝试查找连续的120个+/-字符
                pattern = r'[+\-w]{120}'
                match = re.search(pattern, annotation_string)
                if match:
                    cleaned = match.group()
                else:
                    print(f"标注字符串长度不正确: {len(cleaned)}, 期望120")
                    return None
            
            annotations = {}
            for i, char in enumerate(cleaned):
                hole_number = i + 1
                if char == '+':
                    annotations[hole_number] = 'positive'
                elif char == '-':
                    annotations[hole_number] = 'negative'
                elif char == 'w':
                    annotations[hole_number] = 'weak_growth'
                else:
                    # 未知字符，跳过
                    continue
            
            return annotations
            
        except Exception as e:
            print(f"解析标注字符串失败: {e}")
            return None
    
    def _contains_annotation_pattern(self, text: str) -> bool:
        """
        检查文本是否包含标注模式
        """
        # 查找包含大量+/-字符的行
        plus_minus_count = text.count('+') + text.count('-') + text.count('w')
        return plus_minus_count >= 50  # 至少包含50个标注字符
    
    def export_to_config_file(self, annotations: Dict[int, str], output_path: str) -> bool:
        """
        导出标注到配置文件
        
        Args:
            annotations: 孔位标注映射
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 创建120个字符的标注字符串
            annotation_chars = []
            for hole_number in range(1, 121):
                if hole_number in annotations:
                    growth_level = annotations[hole_number]
                    if growth_level == 'positive':
                        annotation_chars.append('+')
                    elif growth_level == 'negative':
                        annotation_chars.append('-')
                    elif growth_level == 'weak_growth':
                        annotation_chars.append('w')
                    else:
                        annotation_chars.append('-')  # 默认为阴性
                else:
                    annotation_chars.append('-')  # 未标注默认为阴性
            
            annotation_string = ''.join(annotation_chars)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# 全景图标注结果\n")
                f.write(f"# + = 阳性, - = 阴性, w = 弱生长\n")
                f.write(f"# 共120个孔位，按行优先排列 (12列×10行)\n")
                f.write(f"{annotation_string}\n")
            
            return True
            
        except Exception as e:
            print(f"导出配置文件失败: {e}")
            return False
    
    def validate_annotation_string(self, annotation_string: str) -> Tuple[bool, str]:
        """
        验证标注字符串的有效性
        
        Args:
            annotation_string: 标注字符串
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 清理字符串
            cleaned = re.sub(r'[^+\-w]', '', annotation_string)
            
            if len(cleaned) == 0:
                return False, "未找到有效的标注字符"
            
            if len(cleaned) != 120:
                return False, f"标注字符数量不正确: {len(cleaned)}, 期望120"
            
            # 检查字符有效性
            invalid_chars = set(cleaned) - {'+', '-', 'w'}
            if invalid_chars:
                return False, f"包含无效字符: {invalid_chars}"
            
            return True, "标注字符串有效"
            
        except Exception as e:
            return False, f"验证失败: {e}"
    
    def get_annotation_statistics(self, annotations: Dict[int, str]) -> Dict[str, int]:
    def get_annotation(self, hole_number: int = None) -> Optional[str]:
        """
        获取指定孔位的标注数据
        
        Args:
            hole_number: 孔位编号，如果为None则返回当前孔位的标注
            
        Returns:
            标注数据字符串，如果没有找到则返回None
        """
        # 暂时返回None，实际实现需要根据具体需求
        return None
    
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
        return None
    
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
            Tuple[int, int]: (行号, 列号) 从0开始
        """
        if not (1 <= hole_number <= 120):
            raise ValueError(f"孔位编号超出范围: {hole_number}")
        
        row = (hole_number - 1) // 12
        col = (hole_number - 1) % 12
        
        return row, col
    
    def convert_position_to_hole_number(self, row: int, col: int) -> int:
        """
        将行列位置转换为孔位编号
        
        Args:
            row: 行号 (0-9)
            col: 列号 (0-11)
            
        Returns:
            int: 孔位编号 (1-120)
        """
        if not (0 <= row <= 9):
            raise ValueError(f"行号超出范围: {row}")
        if not (0 <= col <= 11):
            raise ValueError(f"列号超出范围: {col}")
        
        return row * 12 + col + 1