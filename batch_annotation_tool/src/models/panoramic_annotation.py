"""
全景图像标注数据模型
支持三级分类和全景图关联
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pathlib import Path

from .annotation import Annotation


@dataclass
class PanoramicAnnotation(Annotation):
    """
    全景图像标注类，扩展基础标注功能
    """
    panoramic_image_id: str = ""  # 全景图ID，如 EB10000026
    hole_number: int = 1  # 孔位编号 1-120
    hole_row: int = 0  # 孔位行号 0-9
    hole_col: int = 0  # 孔位列号 0-11
    microbe_type: str = "bacteria"  # 微生物类型：bacteria/fungi
    growth_level: str = "negative"  # 生长级别：negative/weak_growth/positive
    interference_factors: List[str] = field(default_factory=list)  # 干扰因素：pores/artifacts/edge_blur等
    gradient_context: Optional[Dict[str, Any]] = field(default=None)  # 梯度上下文信息
    annotation_source: str = "manual"  # 标注来源：manual/config_import/batch_import
    is_confirmed: bool = False  # 是否已确认标注
    row: Optional[int] = field(default=None)  # 兼容性字段
    col: Optional[int] = field(default=None)  # 兼容性字段
        
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        
        # 验证孔位编号
        if not (1 <= self.hole_number <= 120):
            raise ValueError(f"孔位编号必须在1-120之间，当前值: {self.hole_number}")
    
    @property
    def panoramic_id(self):
        """兼容性属性：panoramic_id 映射到 panoramic_image_id"""
        return self.panoramic_image_id
    
    @panoramic_id.setter
    def panoramic_id(self, value):
        """兼容性属性：设置 panoramic_id 时更新 panoramic_image_id"""
        self.panoramic_image_id = value
        
        # 验证行列号
        if not (0 <= self.hole_row <= 9):
            raise ValueError(f"行号必须在0-9之间，当前值: {self.hole_row}")
        if not (0 <= self.hole_col <= 11):
            raise ValueError(f"列号必须在0-11之间，当前值: {self.hole_col}")
        
        # 验证微生物类型
        if self.microbe_type not in ['bacteria', 'fungi']:
            raise ValueError(f"微生物类型必须是bacteria或fungi，当前值: {self.microbe_type}")
        
        # 验证生长级别
        if self.growth_level not in ['negative', 'weak_growth', 'positive']:
            raise ValueError(f"生长级别必须是negative/weak_growth/positive之一，当前值: {self.growth_level}")
    
    @classmethod
    def from_filename(cls, filename: str, label: str = "unknown", bbox: List[float] = None, 
                     confidence: Optional[float] = None, microbe_type: str = "bacteria", 
                     growth_level: str = "negative", interference_factors: List[str] = None,
                     panoramic_id: str = None, **kwargs) -> 'PanoramicAnnotation':
        """
        从文件名创建标注对象
        支持两种文件名格式：
        1. 独立路径模式：EB10000026_hole_108.png
        2. 子目录模式：hole_108.png (需要提供panoramic_id参数)
        """
        stem = Path(filename).stem
        
        # 尝试解析独立路径模式
        if '_hole_' in stem:
            parts = stem.split('_')
            if len(parts) == 3 and parts[1] == 'hole':
                panoramic_id = parts[0]
                hole_number = int(parts[2])
            else:
                raise ValueError(f"文件名格式错误，期望格式：EB10000026_hole_108.png，实际：{filename}")
        
        # 尝试解析子目录模式
        elif stem.startswith('hole_'):
            if panoramic_id is None:
                raise ValueError(f"子目录模式需要提供panoramic_id参数，文件名：{filename}")
            hole_str = stem[5:]  # 去掉'hole_'前缀
            if hole_str.isdigit():
                hole_number = int(hole_str)
            else:
                raise ValueError(f"无效的孔位编号格式：{filename}")
        
        else:
            raise ValueError(f"不支持的文件名格式：{filename}，支持格式：EB10000026_hole_108.png 或 hole_108.png")
        
        # 验证孔位编号范围
        if not (1 <= hole_number <= 120):
            raise ValueError(f"孔位编号超出范围(1-120)：{hole_number}")
        
        # 计算行列号（孔位编号从1开始，按行优先排列）
        hole_row = (hole_number - 1) // 12
        hole_col = (hole_number - 1) % 12
        
        if bbox is None:
            bbox = [0, 0, 70, 70]  # 默认边界框
        
        if interference_factors is None:
            interference_factors = []
        
        return cls(
            image_path=filename,
            label=label,
            bbox=bbox,
            confidence=confidence,
            panoramic_image_id=panoramic_id,
            hole_number=hole_number,
            hole_row=hole_row,
            hole_col=hole_col,
            microbe_type=microbe_type,
            growth_level=growth_level,
            interference_factors=interference_factors,
            **kwargs
        )
    
    def get_hole_position(self) -> tuple:
        """获取孔位坐标 (row, col)"""
        return (self.hole_row, self.hole_col)
    
    def get_adjacent_holes(self) -> List[int]:
        """获取相邻孔位编号（用于梯度分析）"""
        adjacent = []
        
        # 左右相邻
        if self.hole_col > 0:
            adjacent.append(self.hole_number - 1)
        if self.hole_col < 11:
            adjacent.append(self.hole_number + 1)
        
        # 上下相邻
        if self.hole_row > 0:
            adjacent.append(self.hole_number - 12)
        if self.hole_row < 9:
            adjacent.append(self.hole_number + 12)
        
        return adjacent
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'panoramic_image_id': self.panoramic_image_id,
            'hole_number': self.hole_number,
            'hole_row': self.hole_row,
            'hole_col': self.hole_col,
            'microbe_type': self.microbe_type,
            'growth_level': self.growth_level,
            'interference_factors': self.interference_factors,
            'gradient_context': self.gradient_context,
            'annotation_source': self.annotation_source,
            'is_confirmed': self.is_confirmed
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PanoramicAnnotation':
        """从字典创建对象"""
        return cls(
            image_path=data.get('image_path', data.get('image_id', '')),
            label=data['label'],
            bbox=data['bbox'],
            confidence=data.get('confidence'),
            panoramic_image_id=data['panoramic_image_id'],
            hole_number=data['hole_number'],
            hole_row=data['hole_row'],
            hole_col=data['hole_col'],
            microbe_type=data['microbe_type'],
            growth_level=data['growth_level'],
            interference_factors=data.get('interference_factors', []),
            gradient_context=data.get('gradient_context'),
            annotation_source=data.get('annotation_source', 'manual'),
            is_confirmed=data.get('is_confirmed', False)
        )


class PanoramicDataset:
    """
    全景图像数据集管理类
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.created_at = datetime.now().isoformat()
        self.annotations: List[PanoramicAnnotation] = []
        self.panoramic_images: Dict[str, Dict[str, Any]] = {}  # 全景图信息
    
    def add_annotation(self, annotation: PanoramicAnnotation):
        """添加标注"""
        self.annotations.append(annotation)
        
        # 更新全景图信息
        panoramic_id = annotation.panoramic_image_id
        if panoramic_id not in self.panoramic_images:
            self.panoramic_images[panoramic_id] = {
                'id': panoramic_id,
                'hole_count': 0,
                'annotated_holes': set(),
                'microbe_type': annotation.microbe_type
            }
        
        self.panoramic_images[panoramic_id]['hole_count'] += 1
        self.panoramic_images[panoramic_id]['annotated_holes'].add(annotation.hole_number)
    
    def get_annotations_by_panoramic_id(self, panoramic_id: str) -> List[PanoramicAnnotation]:
        """获取指定全景图的所有标注"""
        return [ann for ann in self.annotations if ann.panoramic_image_id == panoramic_id]
    
    def get_annotation_by_hole(self, panoramic_id: str, hole_number: int) -> Optional[PanoramicAnnotation]:
        """获取指定孔位的标注"""
        for ann in self.annotations:
            if ann.panoramic_image_id == panoramic_id and ann.hole_number == hole_number:
                return ann
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据集统计信息"""
        stats = {
            'total_annotations': len(self.annotations),
            'panoramic_images': len(self.panoramic_images),
            'microbe_types': {},
            'growth_levels': {},
            'interference_factors': {}
        }
        
        for ann in self.annotations:
            # 微生物类型统计
            if ann.microbe_type not in stats['microbe_types']:
                stats['microbe_types'][ann.microbe_type] = 0
            stats['microbe_types'][ann.microbe_type] += 1
            
            # 生长级别统计
            if ann.growth_level not in stats['growth_levels']:
                stats['growth_levels'][ann.growth_level] = 0
            stats['growth_levels'][ann.growth_level] += 1
            
            # 干扰因素统计
            for factor in ann.interference_factors:
                if factor not in stats['interference_factors']:
                    stats['interference_factors'][factor] = 0
                stats['interference_factors'][factor] += 1
        
        return stats
    
    def save_to_json(self, filepath: str, confirmed_only: bool = True):
        """
        保存为JSON格式
        
        Args:
            filepath: 保存文件路径
            confirmed_only: 是否只保存已确认的标注
        """
        # 根据参数筛选标注
        annotations_to_save = []
        if confirmed_only:
            annotations_to_save = [ann for ann in self.annotations if ann.is_confirmed]
        else:
            annotations_to_save = self.annotations
        
        # 重新计算统计信息（基于要保存的标注）
        confirmed_stats = self._calculate_statistics(annotations_to_save)
        
        data = {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'save_mode': 'confirmed_only' if confirmed_only else 'all',
            'total_annotations': len(self.annotations),
            'saved_annotations': len(annotations_to_save),
            'panoramic_images': {
                pid: {
                    **info,
                    'annotated_holes': list(info['annotated_holes'])
                }
                for pid, info in self.panoramic_images.items()
            },
            'annotations': [ann.to_dict() for ann in annotations_to_save],
            'statistics': confirmed_stats
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _calculate_statistics(self, annotations: List[PanoramicAnnotation]) -> Dict[str, Any]:
        """计算指定标注列表的统计信息"""
        stats = {
            'total_annotations': len(annotations),
            'panoramic_images': len(set(ann.panoramic_image_id for ann in annotations)),
            'microbe_types': {},
            'growth_levels': {},
            'interference_factors': {},
            'annotation_sources': {},
            'confirmed_count': sum(1 for ann in annotations if ann.is_confirmed),
            'unconfirmed_count': sum(1 for ann in annotations if not ann.is_confirmed)
        }
        
        for ann in annotations:
            # 微生物类型统计
            if ann.microbe_type not in stats['microbe_types']:
                stats['microbe_types'][ann.microbe_type] = 0
            stats['microbe_types'][ann.microbe_type] += 1
            
            # 生长级别统计
            if ann.growth_level not in stats['growth_levels']:
                stats['growth_levels'][ann.growth_level] = 0
            stats['growth_levels'][ann.growth_level] += 1
            
            # 标注来源统计
            if ann.annotation_source not in stats['annotation_sources']:
                stats['annotation_sources'][ann.annotation_source] = 0
            stats['annotation_sources'][ann.annotation_source] += 1
            
            # 干扰因素统计
            for factor in ann.interference_factors:
                if factor not in stats['interference_factors']:
                    stats['interference_factors'][factor] = 0
                stats['interference_factors'][factor] += 1
        
        return stats
    
    @classmethod
    def load_from_json(cls, filepath: str) -> 'PanoramicDataset':
        """从JSON文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        dataset = cls(data['name'], data['description'])
        dataset.created_at = data['created_at']
        
        # 加载全景图信息
        for pid, info in data['panoramic_images'].items():
            dataset.panoramic_images[pid] = {
                **info,
                'annotated_holes': set(info['annotated_holes'])
            }
        
        # 加载标注
        for ann_data in data['annotations']:
            annotation = PanoramicAnnotation.from_dict(ann_data)
            dataset.annotations.append(annotation)
        
        return dataset
    
    def export_for_training(self, output_dir: str, microbe_type: str):
        """
        导出训练数据，按照数据集组织结构要求
        """
        output_path = Path(output_dir)
        
        # 创建目录结构
        base_dir = output_path / microbe_type
        for growth_level in ['negative', 'weak_growth', 'positive']:
            for subtype in ['clean', 'with_pores', 'with_artifacts']:
                (base_dir / growth_level / subtype).mkdir(parents=True, exist_ok=True)
        
        # 分类导出
        export_summary = {
            'total_exported': 0,
            'by_category': {}
        }
        
        for ann in self.annotations:
            if ann.microbe_type != microbe_type:
                continue
            
            # 确定子分类
            if 'pores' in ann.interference_factors:
                subtype = 'with_pores'
            elif 'artifacts' in ann.interference_factors:
                subtype = 'with_artifacts'
            else:
                subtype = 'clean'
            
            category = f"{ann.growth_level}/{subtype}"
            if category not in export_summary['by_category']:
                export_summary['by_category'][category] = 0
            export_summary['by_category'][category] += 1
            export_summary['total_exported'] += 1
        
        # 保存导出摘要
        summary_file = output_path / f"{microbe_type}_export_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(export_summary, f, indent=2, ensure_ascii=False)
        
        return export_summary