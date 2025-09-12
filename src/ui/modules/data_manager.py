"""
数据管理器模块
负责数据加载、保存、导入导出、CFG处理
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AnnotationData:
    """标注数据结构"""
    panoramic_id: str
    hole_number: int
    growth_level: str
    confidence: float
    microbe_type: str
    interference_factors: List[str]
    annotation_source: str
    is_confirmed: bool
    image_path: str
    timestamp: str


class DataManager:
    """数据管理器 - 负责所有数据操作"""
    
    def __init__(self, parent_gui):
        """
        初始化数据管理器
        
        Args:
            parent_gui: 主GUI实例
        """
        self.gui = parent_gui
        self.current_directory = None
        self.annotations = {}  # panoramic_id -> hole_number -> AnnotationData
        self.slice_files = []
        self.panoramic_files = []
        self.cfg_data = {}
        
    def load_directory_with_progress(self, directory_path: str, progress_dialog=None) -> bool:
        """
        带进度显示的目录加载 - 按照原始PanoramicImageService的逻辑
        
        加载顺序：
        1. 扫描全景图文件
        2. 根据每个全景图查找对应的子目录和切片文件
        3. 加载对应的CFG文件和阴阳性数据
        4. 加载现有标注
        
        Args:
            directory_path: 目录路径
            progress_dialog: 进度对话框实例
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.current_directory = Path(directory_path)
            
            # 更新进度
            if progress_dialog:
                progress_dialog.update_progress(5, "正在初始化...")
            
            # 清空当前数据
            self.annotations.clear()
            self.slice_files.clear()
            self.panoramic_files.clear()
            self.cfg_data.clear()
            
            # 第一步：扫描全景图文件
            if progress_dialog:
                progress_dialog.update_progress(10, "正在扫描全景图文件...")
            panoramic_files = self._scan_panoramic_files_first()
            
            if not panoramic_files:
                self.gui.log_warning("未找到任何全景图文件", "DATA")
                if progress_dialog:
                    progress_dialog.update_progress(100, "未找到全景图文件")
                return False
            
            # 第二步：为每个全景图加载相关数据
            total_panoramic = len(panoramic_files)
            for idx, panoramic_info in enumerate(panoramic_files):
                panoramic_id = panoramic_info['panoramic_id']
                progress = 20 + (idx / total_panoramic) * 60  # 20%-80%
                
                if progress_dialog:
                    progress_dialog.update_progress(int(progress), f"正在加载全景图 {panoramic_id}...")
                
                # 加载CFG文件
                cfg_loaded = self._load_cfg_file_for_panoramic(panoramic_id)
                
                # 扫描对应的切片文件
                slice_count = self._scan_slice_files_for_panoramic(panoramic_id)
                
                self.gui.log_info(f"全景图 {panoramic_id}: CFG{'已加载' if cfg_loaded else '未找到'}, 切片文件 {slice_count} 个", "DATA")
            
            # 第三步：加载现有标注
            if progress_dialog:
                progress_dialog.update_progress(85, "正在加载现有标注...")
            self._load_existing_annotations()
            
            # 第四步：整理数据
            if progress_dialog:
                progress_dialog.update_progress(95, "正在整理数据...")
            
            # 按全景ID和孔号排序
            self.slice_files.sort(key=lambda x: (x.get('panoramic_id', ''), x.get('hole_number', 0)))
            
            if progress_dialog:
                progress_dialog.update_progress(100, "加载完成")
            
            self.gui.log_info(f"成功加载目录: {directory_path}", "DATA")
            self.gui.log_info(f"发现全景图: {len(self.panoramic_files)}个", "DATA")
            self.gui.log_info(f"发现切片文件: {len(self.slice_files)}个", "DATA")
            self.gui.log_info(f"加载CFG文件: {len(self.cfg_data)}个", "DATA")
            
            return True
            
        except Exception as e:
            self.gui.log_error(f"加载目录失败: {e}", "DATA")
            if progress_dialog:
                progress_dialog.update_progress(100, f"加载失败: {e}")
            return False
        
    def get_panoramic_ids(self):
        """获取所有全景图ID"""
        panoramic_ids = set()
        for slice_file in self.slice_files:
            panoramic_id = slice_file.get('panoramic_id')
            if panoramic_id:
                panoramic_ids.add(panoramic_id)
        return list(panoramic_ids)
    
    def get_panoramic_config_data(self, panoramic_id: str):
        """获取指定全景图的配置数据"""
        return self.cfg_data.get(panoramic_id, {})
    
    def _scan_panoramic_files_first(self) -> List[Dict[str, Any]]:
        """
        第一步：扫描全景图文件
        按照原始逻辑，先找到所有全景图文件，然后为每个全景图处理相关数据
        
        Returns:
            List[Dict]: 全景图文件信息列表
        """
        panoramic_files = []
        if not self.current_directory:
            return panoramic_files
            
        # 支持的全景图格式
        panoramic_formats = ['.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
        
        # 扫描目录中的全景图文件
        for file_path in self.current_directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in panoramic_formats:
                panoramic_id = file_path.stem
                
                # 检查是否有对应的子目录（子目录模式的必要条件）
                subdir = self.current_directory / panoramic_id
                if subdir.exists() and subdir.is_dir():
                    panoramic_info = {
                        'panoramic_id': panoramic_id,
                        'file_path': str(file_path),
                        'subdir_path': str(subdir)
                    }
                    panoramic_files.append(panoramic_info)
                    self.panoramic_files.append(panoramic_info)
                    self.gui.log_debug(f"找到全景图: {panoramic_id} (有对应子目录)", "DATA")
                else:
                    self.gui.log_debug(f"跳过全景图 {panoramic_id}：无对应子目录", "DATA")
        
        self.gui.log_info(f"全景图扫描完成: 共 {len(panoramic_files)} 个全景图", "DATA")
        return panoramic_files
    
    def _scan_slice_files_for_panoramic(self, panoramic_id: str) -> int:
        """
        为指定全景图扫描切片文件
        
        Args:
            panoramic_id: 全景图ID
            
        Returns:
            int: 找到的切片文件数量
        """
        slice_count = 0
        subdir = self.current_directory / panoramic_id
        
        if not subdir.exists() or not subdir.is_dir():
            return slice_count
        
        # 确定孔位范围：SE开头的全景图前4个孔是空的（5-120号），其他是1-120号
        if panoramic_id.upper().startswith('SE'):
            min_hole = 5
            max_hole = 120
        else:
            min_hole = 1
            max_hole = 120
        self.gui.log_debug(f"扫描全景图 {panoramic_id} 的切片文件，孔位范围: {min_hole}-{max_hole}", "DATA")
        
        # 在子目录中查找 hole_*.png 文件
        for slice_file in subdir.iterdir():
            if (slice_file.is_file() and 
                slice_file.name.startswith('hole_') and 
                slice_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']):
                
                try:
                    # 解析孔号：hole_1.png -> 1
                    hole_str = slice_file.stem[5:]  # 去掉 'hole_' 前缀
                    if hole_str.isdigit():
                        hole_number = int(hole_str)
                        if min_hole <= hole_number <= max_hole:
                            self.slice_files.append({
                                'filename': slice_file.name,
                                'filepath': str(slice_file),
                                'panoramic_id': panoramic_id,
                                'hole_number': hole_number,
                                'structure_type': 'subdirectory'
                            })
                            slice_count += 1
                            # self.gui.log_debug(f"找到切片: {panoramic_id}/hole_{hole_number}", "DATA")
                        else:
                            self.gui.log_debug(f"跳过孔位 {hole_number}：超出范围({min_hole}-{max_hole})", "DATA")
                except Exception as e:
                    self.gui.log_warning(f"解析切片文件失败 {slice_file}: {e}", "DATA")
        
        self.gui.log_info(f"全景图 {panoramic_id} 找到 {slice_count} 个切片文件 (孔位范围: {min_hole}-{max_hole})", "DATA")
        return slice_count
    
    def _load_cfg_file_for_panoramic(self, panoramic_id: str) -> bool:
        """
        为指定全景图加载CFG配置文件
        
        Args:
            panoramic_id: 全景图ID
            
        Returns:
            bool: 是否成功加载CFG文件
        """
        cfg_file = self.current_directory / f"{panoramic_id}.cfg"
        
        if not cfg_file.exists():
            self.gui.log_debug(f"CFG文件不存在: {panoramic_id}.cfg", "DATA")
            return False
        
        try:
            self.gui.log_debug(f"加载CFG文件: {panoramic_id}", "DATA")
            cfg_data = self._parse_cfg_file(cfg_file, panoramic_id)
            
            if cfg_data:
                self.cfg_data[panoramic_id] = cfg_data
                
                # 确定孔位范围：SE开头的全景图前4个孔是空的（5-120号），其他是1-120号
                if panoramic_id.upper().startswith('SE'):
                    min_hole = 5
                    max_hole = 120
                else:
                    min_hole = 1
                    max_hole = 120
                
                # 根据CFG数据创建初始标注数据结构
                if panoramic_id not in self.annotations:
                    self.annotations[panoramic_id] = {}
                
                # 为每个孔位创建标注条目（如果CFG中有数据）
                for hole_number, hole_data in cfg_data.get('holes', {}).items():
                    # 处理孔位编号，可能是整数或字符串
                    if isinstance(hole_number, int):
                        hole_num = hole_number
                    elif isinstance(hole_number, str) and hole_number.isdigit():
                        hole_num = int(hole_number)
                    else:
                        continue
                    
                    if min_hole <= hole_num <= max_hole:
                        # 从CFG数据中提取阴阳性信息
                        growth_level = self._determine_growth_level_from_cfg(hole_data)
                        
                        if growth_level != 'unannotated':
                            annotation = AnnotationData(
                                panoramic_id=panoramic_id,
                                hole_number=hole_num,
                                growth_level=growth_level,
                                confidence=1.0,  # CFG数据默认高置信度
                                microbe_type='unknown',
                                interference_factors=[],
                                annotation_source='cfg',
                                is_confirmed=True,
                                image_path='',
                                timestamp=''
                            )
                            self.annotations[panoramic_id][hole_num] = annotation
                
                self.gui.log_debug(f"CFG文件加载成功: {panoramic_id}", "DATA")
                return True
            else:
                self.gui.log_warning(f"CFG文件解析失败: {panoramic_id}.cfg", "DATA")
                return False
                
        except Exception as e:
            self.gui.log_error(f"加载CFG文件失败 {panoramic_id}: {e}", "DATA")
            return False
    
    def _determine_growth_level_from_cfg(self, hole_data: Dict[str, Any]) -> str:
        """
        根据CFG数据确定孔位的生长级别
        
        Args:
            hole_data: CFG中的孔位数据
            
        Returns:
            str: 生长级别 ('negative', 'weak_growth', 'positive', 'unannotated')
        """
        # 检查直接的growth字段
        if 'growth' in hole_data:
            growth_value = hole_data['growth']
            
            # 处理字符串类型的生长级别
            if isinstance(growth_value, str):
                growth_lower = growth_value.lower()
                if growth_lower == 'positive' or growth_lower == '+':
                    return 'positive'
                elif growth_lower == 'negative' or growth_lower == '-':
                    return 'negative'
                elif 'weak' in growth_lower:
                    return 'weak_growth'
                elif growth_lower == '0':
                    return 'negative'
                elif growth_lower == '1':
                    return 'weak_growth'
                elif growth_lower in ['2', '3']:
                    return 'positive'
            
            # 处理数值类型的生长级别
            elif isinstance(growth_value, (int, float)):
                if growth_value == 0:
                    return 'negative'
                elif growth_value == 1:
                    return 'weak_growth'
                elif growth_value >= 2:
                    return 'positive'
        
        # 检查其他可能的字段名
        for field in ['result', 'status', 'level']:
            if field in hole_data:
                value = str(hole_data[field]).lower()
                if value == 'negative' or value == '-' or value == '0':
                    return 'negative'
                elif value == 'positive' or value == '+' or value in ['2', '3']:
                    return 'positive'
                elif 'weak' in value or value == '1':
                    return 'weak_growth'
        
        return 'unannotated'
            
    def load_directory(self, directory_path: str) -> bool:
        """
        简单的目录加载（无进度显示）
        """
        return self.load_directory_with_progress(directory_path, None)
        
    def get_panoramic_file_path(self, panoramic_id: str):
        """获取全景图文件路径"""
        for panoramic_file in self.panoramic_files:
            if panoramic_file.get('panoramic_id') == panoramic_id:
                return panoramic_file.get('file_path')
        return None
        
    def get_slice_files_by_panoramic(self, panoramic_id: str):
        """获取指定全景图的所有切片文件"""
        return [f for f in self.slice_files if f.get('panoramic_id') == panoramic_id]
                
    def load_directory(self, directory_path: str) -> bool:
        """
        加载工作目录
        
        Args:
            directory_path: 目录路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.current_directory = Path(directory_path)
            
            # 清空当前数据
            self.annotations.clear()
            self.slice_files.clear()
            self.panoramic_files.clear()
            
            # 扫描切片文件
            self._scan_slice_files()
            
            # 扫描全景图文件
            self._scan_panoramic_files()
            
            # 加载CFG配置
            self._load_cfg_files()
            
            # 加载现有标注
            self._load_existing_annotations()
            
            self.gui.log_info(f"成功加载目录: {directory_path}", "DATA")
            self.gui.log_info(f"发现切片文件: {len(self.slice_files)}个", "DATA")
            self.gui.log_info(f"发现全景图: {len(self.panoramic_files)}个", "DATA")
            
            return True
            
        except Exception as e:
            self.gui.log_error(f"加载目录失败: {e}", "DATA")
            return False
            
    def _scan_slice_files(self):
        """
        扫描切片文件 - 仅支持子目录模式
        目录结构：<全景ID>/hole_<孔序号>.png
        """
        if not self.current_directory:
            return
            
        # 遍历所有子目录
        for item in self.current_directory.iterdir():
            if item.is_dir():
                panoramic_id = item.name
                self.gui.log_debug(f"扫描切片目录: {panoramic_id}", "DATA")
                
                # 确定孔位范围：SE开头的全景图前4个孔是空的（5-120号），其他是1-120号
                if panoramic_id.upper().startswith('SE'):
                    min_hole = 5
                    max_hole = 120
                else:
                    min_hole = 1
                    max_hole = 120
                
                # 在子目录中查找 hole_*.png 文件
                slice_count = 0
                for slice_file in item.iterdir():
                    if (slice_file.is_file() and 
                        slice_file.name.startswith('hole_') and 
                        slice_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']):
                        
                        try:
                            # 解析孔号：hole_1.png -> 1
                            hole_str = slice_file.stem[5:]  # 去掉 'hole_' 前缀
                            if hole_str.isdigit():
                                hole_number = int(hole_str)
                                if min_hole <= hole_number <= max_hole:
                                    self.slice_files.append({
                                        'filename': slice_file.name,
                                        'filepath': str(slice_file),
                                        'panoramic_id': panoramic_id,
                                        'hole_number': hole_number,
                                        'structure_type': 'subdirectory'
                                    })
                                    slice_count += 1
                                    self.gui.log_debug(f"找到切片: {panoramic_id}/hole_{hole_number}", "DATA")
                        except Exception as e:
                            self.gui.log_warning(f"解析切片文件失败 {slice_file}: {e}", "DATA")
                
                if slice_count > 0:
                    self.gui.log_info(f"目录 {panoramic_id} 找到 {slice_count} 个切片文件", "DATA")
        
        # 按全景ID和孔号排序
        self.slice_files.sort(key=lambda x: (x['panoramic_id'], x['hole_number']))
        
        self.gui.log_info(f"切片扫描完成: 共 {len(self.slice_files)} 个切片文件", "DATA")
    
    def _scan_panoramic_files(self):
        """
        扫描全景图文件 - 仅支持子目录模式
        查找目录中的全景图文件，验证是否有对应的子目录
        """
        if not self.current_directory:
            return
            
        # 支持的全景图格式
        panoramic_formats = ['.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
        
        # 扫描目录中的全景图文件
        for file_path in self.current_directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in panoramic_formats:
                panoramic_id = file_path.stem
                
                # 检查是否有对应的子目录（子目录模式的必要条件）
                subdir = self.current_directory / panoramic_id
                if subdir.exists() and subdir.is_dir():
                    # 检查子目录中是否有切片文件
                    has_slices = any(slice_info['panoramic_id'] == panoramic_id for slice_info in self.slice_files)
                    
                    if has_slices:
                        self.panoramic_files.append({
                            'panoramic_id': panoramic_id,
                            'file_path': str(file_path)
                        })
                        self.gui.log_debug(f"找到全景图: {panoramic_id} (子目录模式)", "DATA")
                    else:
                        self.gui.log_warning(f"全景图 {panoramic_id} 的子目录中未找到有效切片", "DATA")
                else:
                    self.gui.log_debug(f"跳过全景图 {panoramic_id}：无对应子目录", "DATA")
        
        self.gui.log_info(f"全景图扫描完成: 共 {len(self.panoramic_files)} 个全景图", "DATA")
        
    def _parse_slice_filename(self, file_path: Path, panoramic_id: str = None) -> Optional[Dict]:
        """
        解析切片文件名
        
        Args:
            file_path: 文件路径
            panoramic_id: 全景图ID（用于确定孔位数）
            
        Returns:
            Dict: 文件信息字典，包含panoramic_id, hole_number等
        """
        try:
            filename = file_path.stem
            
            # 格式: panoramic_id_hole_number 例如: EB10000026_hole_108
            parts = filename.split('_')
            
            # 检查是否符合 panoramic_id_hole_number 格式
            if len(parts) == 3 and parts[1] == 'hole' and parts[2].isdigit():
                file_panoramic_id = parts[0]
                hole_number = int(parts[2])
                
                # 确定孔位范围：SE开头的全景图前4个孔是空的（5-120号），其他是1-120号
                if file_panoramic_id.upper().startswith('SE'):
                    min_hole = 5
                    max_hole = 120
                else:
                    min_hole = 1
                    max_hole = 120
                
                # 验证孔号范围
                if min_hole <= hole_number <= max_hole:
                    return {
                        'filename': file_path.name,
                        'filepath': str(file_path),
                        'panoramic_id': file_panoramic_id,
                        'hole_number': hole_number
                    }
                        
        except Exception as e:
            self.gui.log_warning(f"解析文件名失败 {file_path}: {e}", "DATA")
            
        return None
    
    def _parse_cfg_file(self, cfg_file_path: Path, panoramic_id: str = None) -> Optional[Dict[str, Any]]:
        """
        解析CFG配置文件
        
        Args:
            cfg_file_path: CFG文件路径
            panoramic_id: 全景图ID（用于确定孔位数）
            
        Returns:
            Dict: 解析后的配置数据
        """
        try:
            if not cfg_file_path.exists():
                return None
            
            cfg_data = {}
            holes_data = {}
            
            with open(cfg_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 检查是否是一行格式：filename,result_string
            if ',' in content and len(content.split('\n')) == 1:
                # 解析单行格式：EB10000026.bmp,-++--+----+-+-++++-++--++++++-----+++...
                parts = content.split(',', 1)
                if len(parts) == 2:
                    filename, result_string = parts
                    result_string = result_string.strip()
                    
                    # 确定孔位映射：SE开头的全景图前4个孔是空的（5-120号），其他是1-120号
                    if filename.upper().startswith('SE'):
                        start_hole = 5  # SE从第5个孔开始
                        max_holes = 116  # SE有116个有效孔位（5-120）
                    else:
                        start_hole = 1  # 普通全景图从第1个孔开始
                        max_holes = 120  # 普通全景图有120个孔位（1-120）
                    
                    self.gui.log_debug(f"CFG解析: 文件名={filename}, 孔位范围={start_hole}-{start_hole + max_holes - 1}", "DATA")
                    
                    # 解析结果字符串，每个字符代表一个孔位
                    for i, char in enumerate(result_string[:max_holes]):
                        hole_number = start_hole + i  # 计算实际孔位编号
                        if char == '+':
                            holes_data[hole_number] = {'growth': 'positive'}
                        elif char == '-':
                            holes_data[hole_number] = {'growth': 'negative'}
                        elif char.isdigit():
                            # 数字格式：0=阴性，1=弱生长，2+=阳性
                            growth_value = int(char)
                            if growth_value == 0:
                                holes_data[hole_number] = {'growth': 'negative'}
                            elif growth_value == 1:
                                holes_data[hole_number] = {'growth': 'weak_growth'}
                            elif growth_value >= 2:
                                holes_data[hole_number] = {'growth': 'positive'}
                    
                    cfg_data['format'] = 'single_line'
                    cfg_data['filename'] = filename
                    cfg_data['result_string'] = result_string
                    cfg_data['start_hole'] = start_hole
                    cfg_data['max_holes'] = max_holes
            else:
                # 尝试解析多行格式
                lines = content.split('\n')
                current_section = None
                
                # 确定孔位范围：SE开头的全景图前4个孔是空的（5-120号），其他是1-120号
                if panoramic_id and panoramic_id.upper().startswith('SE'):
                    min_hole = 5
                    max_hole = 120
                else:
                    min_hole = 1
                    max_hole = 120
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # 检查是否是节标题 [section]
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        continue
                    
                    # 检查是否是键值对
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 尝试转换数值
                        try:
                            if value.isdigit():
                                value = int(value)
                            elif '.' in value and value.replace('.', '').replace('-', '').isdigit():
                                value = float(value)
                        except:
                            pass
                        
                        # 如果是孔位相关的数据
                        if key.startswith('hole_') or key.startswith('H'):
                            # 提取孔位编号
                            if key.startswith('hole_'):
                                hole_num_str = key[5:]
                            elif key.startswith('H'):
                                hole_num_str = key[1:]
                            else:
                                hole_num_str = ''
                            
                            if hole_num_str.isdigit():
                                hole_num = int(hole_num_str)
                                if min_hole <= hole_num <= max_hole:
                                    if hole_num not in holes_data:
                                        holes_data[hole_num] = {}
                                    holes_data[hole_num]['growth'] = value
                        else:
                            cfg_data[key] = value
                
                # 也尝试解析简单的数字列表格式（每行一个孔位的结果）
                if not holes_data and lines:
                    try:
                        # 为SE类型从第5个孔开始，为普通类型从第1个孔开始
                        for i, line in enumerate(lines):
                            line = line.strip()
                            if line and line.isdigit():
                                hole_num = min_hole + i
                                if hole_num <= max_hole:
                                    holes_data[hole_num] = {'growth': int(line)}
                    except:
                        pass
                
                cfg_data['format'] = 'multi_line'
                cfg_data['min_hole'] = min_hole
                cfg_data['max_hole'] = max_hole
            
            cfg_data['holes'] = holes_data
            return cfg_data
            
        except Exception as e:
            self.gui.log_error(f"解析CFG文件失败 {cfg_file_path}: {e}", "DATA")
            return None
        
    def _scan_panoramic_files(self):
        """
        扫描全景图文件
        支持子目录模式：直接扫描目录中的全景图文件
        """
        if not self.current_directory:
            return
            
        # 支持的全景图格式
        panoramic_formats = ['.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
        
        # 直接扫描目录中的全景图文件
        for file_path in self.current_directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in panoramic_formats:
                panoramic_id = file_path.stem
                
                # 检查是否有对应的子目录（子目录模式的标志）
                subdir = self.current_directory / panoramic_id
                has_subdir = subdir.exists() and subdir.is_dir()
                
                # 检查是否有对应的切片文件（独立模式的标志）
                has_slices = any(slice_info['panoramic_id'] == panoramic_id for slice_info in self.slice_files)
                
                # 如果有子目录或有切片文件，则认为是有效的全景图
                if has_subdir or has_slices:
                    self.panoramic_files.append({
                        'panoramic_id': panoramic_id,
                        'file_path': str(file_path)
                    })
                    self.gui.log_debug(f"找到全景图: {panoramic_id} ({'子目录模式' if has_subdir else '独立模式'})", "DATA")
                
    def _find_panoramic_file(self, panoramic_id: str) -> Optional[str]:
        """查找全景图文件"""
        if not self.current_directory:
            return None
            
        # 根据原始代码逻辑：在全景图目录中查找对应文件
        # 尝试不同的文件扩展名
        supported_formats = ['.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
        
        for ext in supported_formats:
            panoramic_file = self.current_directory / f"{panoramic_id}{ext}"
            if panoramic_file.exists():
                return str(panoramic_file)
                
        # 如果直接匹配失败，尝试在子目录中查找
        for file_path in self.current_directory.rglob(f"{panoramic_id}.*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                return str(file_path)
                
        return None
        
    def _load_cfg_files(self):
        """
        加载CFG配置文件
        支持子目录模式：查找与全景图同名的CFG文件
        """
        if not self.current_directory:
            return
            
        # 对于每个全景图，查找对应的CFG文件
        for panoramic_info in self.panoramic_files:
            panoramic_id = panoramic_info['panoramic_id']
            cfg_file = self.current_directory / f"{panoramic_id}.cfg"
            
            if cfg_file.exists():
                try:
                    with open(cfg_file, 'r', encoding='utf-8') as f:
                        cfg_content = f.read()
                        self.cfg_data[panoramic_id] = cfg_content
                        self.gui.log_debug(f"加载CFG文件: {panoramic_id}", "DATA")
                except Exception as e:
                    self.gui.log_warning(f"加载CFG文件失败 {cfg_file}: {e}", "DATA")
        
        # 额外扫描其他CFG文件
        for cfg_file in self.current_directory.glob('*.cfg'):
            panoramic_id = cfg_file.stem
            if panoramic_id not in self.cfg_data:
                try:
                    with open(cfg_file, 'r', encoding='utf-8') as f:
                        cfg_content = f.read()
                        self.cfg_data[panoramic_id] = cfg_content
                        self.gui.log_debug(f"加载额外CFG文件: {panoramic_id}", "DATA")
                except Exception as e:
                    self.gui.log_warning(f"加载CFG文件失败 {cfg_file}: {e}", "DATA")
                
    def _load_existing_annotations(self):
        """加载现有标注数据"""
        if not self.current_directory:
            return
            
        annotation_file = self.current_directory / 'annotations.json'
        if annotation_file.exists():
            try:
                with open(annotation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    annotation = AnnotationData(**item)
                    self.add_annotation(annotation)
                    
                self.gui.log_info(f"加载现有标注: {len(data)}条", "DATA")
                
            except Exception as e:
                self.gui.log_error(f"加载标注文件失败: {e}", "DATA")
                
    def add_annotation(self, annotation: AnnotationData):
        """添加标注数据"""
        panoramic_id = annotation.panoramic_id
        hole_number = annotation.hole_number
        
        if panoramic_id not in self.annotations:
            self.annotations[panoramic_id] = {}
            
        self.annotations[panoramic_id][hole_number] = annotation
        
    def get_annotation(self, panoramic_id: str, hole_number: int) -> Optional[AnnotationData]:
        """获取标注数据"""
        return self.annotations.get(panoramic_id, {}).get(hole_number)
        
    def remove_annotation(self, panoramic_id: str, hole_number: int) -> bool:
        """删除标注数据"""
        if panoramic_id in self.annotations and hole_number in self.annotations[panoramic_id]:
            del self.annotations[panoramic_id][hole_number]
            return True
        return False
        
    def save_annotations(self) -> bool:
        """保存标注数据"""
        if not self.current_directory:
            return False
            
        try:
            annotation_file = self.current_directory / 'annotations.json'
            
            # 转换为可序列化格式
            data = []
            for panoramic_annotations in self.annotations.values():
                for annotation in panoramic_annotations.values():
                    data.append(asdict(annotation))
                    
            with open(annotation_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.gui.log_info(f"保存标注数据: {len(data)}条", "DATA")
            return True
            
        except Exception as e:
            self.gui.log_error(f"保存标注失败: {e}", "DATA")
            return False
            

        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_annotations = sum(len(panoramic_annotations) 
                              for panoramic_annotations in self.annotations.values())
        
        confirmed_annotations = sum(
            1 for panoramic_annotations in self.annotations.values()
            for annotation in panoramic_annotations.values()
            if annotation.is_confirmed
        )
        
        growth_level_stats = {}
        for panoramic_annotations in self.annotations.values():
            for annotation in panoramic_annotations.values():
                level = annotation.growth_level
                growth_level_stats[level] = growth_level_stats.get(level, 0) + 1
                
        return {
            'total_slices': len(self.slice_files),
            'total_annotations': total_annotations,
            'confirmed_annotations': confirmed_annotations,
            'progress_percent': (total_annotations / len(self.slice_files) * 100) if self.slice_files else 0,
            'growth_level_distribution': growth_level_stats,
            'panoramic_count': len(self.panoramic_files)
        }
        
    def get_slice_files_by_panoramic(self, panoramic_id: str) -> List[Dict]:
        """获取指定全景图的切片文件"""
        return [f for f in self.slice_files if f['panoramic_id'] == panoramic_id]
        
    def get_panoramic_ids(self) -> List[str]:
        """获取所有全景图ID"""
        return [p['panoramic_id'] for p in self.panoramic_files]
        
    def get_panoramic_file_path(self, panoramic_id: str) -> Optional[str]:
        """获取全景图文件路径"""
        for panoramic in self.panoramic_files:
            if panoramic['panoramic_id'] == panoramic_id:
                return panoramic['file_path']
        return None
