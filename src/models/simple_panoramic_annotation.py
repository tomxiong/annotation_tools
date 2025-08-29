"""
简化的全景图像标注数据模型
避免继承带来的参数顺序问题
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pathlib import Path


@dataclass
class SimplePanoramicAnnotation:
    """
    简化的全景图像标注类
    """
    image_path: str
    label: str
    bbox: List[int]
    panoramic_image_id: str
    hole_number: int
    hole_row: int
    hole_col: int
    microbe_type: str
    growth_level: str
    confidence: Optional[float] = None
    interference_factors: List[str] = field(default_factory=list)
    gradient_context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        # 验证孔位编号
        if not (1 <= self.hole_number <= 120):
            raise ValueError(f"孔位编号必须在1-120之间，当前值: {self.hole_number}")
        
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
    def from_filename(cls, filename: str, label: str = "unknown", bbox: List[int] = None, 
                     confidence: Optional[float] = None, microbe_type: str = "bacteria", 
                     growth_level: str = "negative", interference_factors: List[str] = None, 
                     **kwargs) -> 'SimplePanoramicAnnotation':
        """
        从文件名创建标注对象
        文件名格式：EB10000026_hole_108.png
        """
        stem = Path(filename).stem
        parts = stem.split('_')
        
        if len(parts) != 3 or parts[1] != 'hole':
            raise ValueError(f"文件名格式错误，期望格式：EB10000026_hole_108.png，实际：{filename}")
        
        panoramic_id = parts[0]
        hole_number = int(parts[2])
        
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
            panoramic_image_id=panoramic_id,
            hole_number=hole_number,
            hole_row=hole_row,
            hole_col=hole_col,
            microbe_type=microbe_type,
            growth_level=growth_level,
            confidence=confidence,
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
        return {
            'image_path': self.image_path,
            'label': self.label,
            'bbox': self.bbox,
            'confidence': self.confidence,
            'panoramic_image_id': self.panoramic_image_id,
            'hole_number': self.hole_number,
            'hole_row': self.hole_row,
            'hole_col': self.hole_col,
            'microbe_type': self.microbe_type,
            'growth_level': self.growth_level,
            'interference_factors': self.interference_factors,
            'gradient_context': self.gradient_context,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimplePanoramicAnnotation':
        """从字典创建对象"""
        # 解析created_at
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            image_path=data.get('image_path', data.get('image_id', '')),
            label=data['label'],
            bbox=data['bbox'],
            panoramic_image_id=data['panoramic_image_id'],
            hole_number=data['hole_number'],
            hole_row=data['hole_row'],
            hole_col=data['hole_col'],
            microbe_type=data['microbe_type'],
            growth_level=data['growth_level'],
            confidence=data.get('confidence'),
            interference_factors=data.get('interference_factors', []),
            gradient_context=data.get('gradient_context'),
            metadata=data.get('metadata', {}),
            created_at=created_at
        )


class SimplePanoramicDataset:
    """
    简化的全景图像数据集管理类
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.created_at = datetime.now().isoformat()
        self.annotations: List[SimplePanoramicAnnotation] = []
        self.panoramic_images: Dict[str, Dict[str, Any]] = {}  # 全景图信息
    
    def add_annotation(self, annotation: SimplePanoramicAnnotation):
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
    
    def get_annotations_by_panoramic_id(self, panoramic_id: str) -> List[SimplePanoramicAnnotation]:
        """获取指定全景图的所有标注"""
        return [ann for ann in self.annotations if ann.panoramic_image_id == panoramic_id]
    
    def get_annotation_by_hole(self, panoramic_id: str, hole_number: int) -> Optional[SimplePanoramicAnnotation]:
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
    
    def save_to_json(self, filepath: str):
        """保存为JSON格式"""
        data = {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'panoramic_images': {
                pid: {
                    **info,
                    'annotated_holes': list(info['annotated_holes'])
                }
                for pid, info in self.panoramic_images.items()
            },
            'annotations': [ann.to_dict() for ann in self.annotations],
            'statistics': self.get_statistics()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_json(cls, filepath: str) -> 'SimplePanoramicDataset':
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
            annotation = SimplePanoramicAnnotation.from_dict(ann_data)
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