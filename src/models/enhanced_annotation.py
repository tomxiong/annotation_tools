"""
增强标注模型
支持复合特征标注，如"阴性带气孔"等复杂标注场景
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# 日志导入
try:
    from src.utils.logger import log_debug, log_info, log_warning, log_error
except ImportError:
    # 如果日志模块不可用，使用print作为后备
    def log_debug(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_info(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_warning(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_error(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)


class GrowthLevel(Enum):
    """生长级别枚举"""
    NEGATIVE = "negative"
    WEAK_GROWTH = "weak_growth"
    POSITIVE = "positive"


class InterferenceType(Enum):
    """干扰因素类型枚举 - 使用标准英文术语"""
    PORES = "pores"               # 气孔
    ARTIFACTS = "artifacts"       # 伪影/气孔重叠
    DEBRIS = "debris"             # 杂质/碎片
    CONTAMINATION = "contamination"  # 污染


class GrowthPattern(Enum):
    """生长模式枚举"""
    # 阴性模式
    CLEAN = "clean"              # 无干扰的阴性
    
    # 弱生长模式
    SMALL_DOTS = "small_dots"    # 较小的点状弱生长
    LIGHT_GRAY = "light_gray"    # 整体较淡的灰色弱生长
    IRREGULAR_AREAS = "irregular_areas"  # 不规则淡区域弱生长
    
    # 阳性模式
    CLUSTERED = "clustered"      # 聚集型生长
    SCATTERED = "scattered"      # 分散型生长
    HEAVY_GROWTH = "heavy_growth"  # 重度生长
    FOCAL = "focal"              # 聚焦性生长（真菌）
    DIFFUSE = "diffuse"          # 弥漫性生长（真菌）


@dataclass
class FeatureCombination:
    """特征组合类"""
    growth_level: GrowthLevel
    growth_pattern: Optional[GrowthPattern] = None
    interference_factors: Set[InterferenceType] = field(default_factory=set)
    confidence: float = 1.0
    
    def to_label(self) -> str:
        """生成标签字符串"""
        parts = [self.growth_level.value]
        
        if self.growth_pattern:
            parts.append(self.growth_pattern.value)
        
        if self.interference_factors:
            interference_str = "_".join(sorted([f.value for f in self.interference_factors]))
            parts.append(f"with_{interference_str}")
        
        return "_".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""        
        return {
            'growth_level': self.growth_level.value,
            'growth_pattern': self.growth_pattern.value if self.growth_pattern else None,
            'interference_factors': [f.value for f in self.interference_factors],
            'confidence': self.confidence,
            'label': self.to_label()  # Call the method, not reference it
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureCombination':
        """从字典创建"""
        # 处理干扰因素 - 支持中文和英文值
        interference_factors = set()
        for f in data.get('interference_factors', []):
            try:
                # 尝试直接创建枚举
                interference_factors.add(InterferenceType(f))
            except ValueError:
                # 如果失败，尝试映射到英文值
                interference_mapping = {
                    # 中文到英文的映射
                    '气孔': 'pores',
                    '气孔重叠': 'artifacts',
                    '伪影': 'artifacts',
                    '杂质': 'debris',
                    '污染': 'contamination',
                    '污渍': 'contamination',
                    # 英文别名兼容
                    'pores': 'pores',
                    'debris': 'debris',
                    'contamination': 'contamination',
                    'artifacts': 'artifacts',
                    'noise': 'artifacts',     # 噪声 -> 伪影
                    'edge_blur': 'pores',     # 兼容旧的边缘模糊值
                    'scratches': 'debris'      # 划痕 -> 杂质
                }
                if f in interference_mapping:
                    try:
                        interference_factors.add(InterferenceType(interference_mapping[f]))
                    except ValueError:
                        log_warning(f"无法映射干扰因素: {f}")
                else:
                    log_warning(f"未知的干扰因素: {f}")
        
        # 处理生长模式 - 支持默认值映射
        growth_pattern = None
        if data.get('growth_pattern'):
            pattern_str = data['growth_pattern']
            try:
                # 首先尝试直接创建枚举
                growth_pattern = GrowthPattern(pattern_str)
            except ValueError:
                # 如果失败，处理特殊的默认值
                default_pattern_mapping = {
                    'default_positive': 'clustered',      # 默认阳性映射到聚集型
                    'default_weak_growth': 'small_dots',  # 默认弱生长映射到小点状
                }
                if pattern_str in default_pattern_mapping:
                    try:
                        growth_pattern = GrowthPattern(default_pattern_mapping[pattern_str])
                        log_debug(f"映射默认生长模式: {pattern_str} -> {default_pattern_mapping[pattern_str]}", "MAPPING")
                    except ValueError:
                        log_warning(f"无法映射默认生长模式: {pattern_str}")
                else:
                    log_warning(f"未知的生长模式: {pattern_str}")
        
        return cls(
            growth_level=GrowthLevel(data['growth_level']),
            growth_pattern=growth_pattern,
            interference_factors=interference_factors,
            confidence=data.get('confidence', 1.0)
        )


class EnhancedPanoramicAnnotation:
    """
    增强全景标注类
    支持复合特征标注和多层级分类
    """
    
    def __init__(self, image_path: str, bbox: List[float], 
                 panoramic_image_id: str = "", hole_number: int = 0, 
                 hole_row: int = 0, hole_col: int = 0,
                 microbe_type: str = "bacteria", 
                 feature_combination: Optional[FeatureCombination] = None,
                 annotation_source: str = "manual", is_confirmed: bool = True,
                 metadata: Optional[Dict[str, Any]] = None, **kwargs):
        
        self.image_path = image_path
        self.bbox = bbox
        self.panoramic_image_id = panoramic_image_id
        self.hole_number = hole_number
        self.hole_row = hole_row
        self.hole_col = hole_col
        self.microbe_type = microbe_type
        self.feature_combination = feature_combination or FeatureCombination(GrowthLevel.NEGATIVE)
        self.annotation_source = annotation_source
        self.is_confirmed = is_confirmed
        self.metadata = metadata or {}
                
        # 向后兼容性字段
        # Handle both method and property for to_label
        if hasattr(self.feature_combination.to_label, '__call__'):
            self.label = self.feature_combination.to_label()  # Method call
        else:
            self.label = self.feature_combination.to_label  # Property access
        self.confidence = self.feature_combination.confidence
        # 处理growth_level - 可能是字符串或枚举
        if hasattr(self.feature_combination.growth_level, 'value'):
            self.growth_level = self.feature_combination.growth_level.value
        else:
            self.growth_level = self.feature_combination.growth_level
        # 处理interference_factors - 可能是字符串集合或枚举集合
        self.interference_factors = []
        for f in self.feature_combination.interference_factors:
            if hasattr(f, 'value'):
                self.interference_factors.append(f.value)
            else:
                self.interference_factors.append(f)
    
    def update_feature_combination(self, feature_combination: FeatureCombination):
        """更新特征组合"""
        self.feature_combination = feature_combination
        # 同步更新兼容性字段
        # Handle both method and property for to_label
        if hasattr(feature_combination.to_label, '__call__'):
            self.label = feature_combination.to_label()  # Method call
        else:
            self.label = feature_combination.to_label  # Property access
        self.confidence = feature_combination.confidence
        # 处理growth_level - 可能是字符串或枚举
        if hasattr(feature_combination.growth_level, 'value'):
            self.growth_level = feature_combination.growth_level.value
        else:
            self.growth_level = feature_combination.growth_level
        # 处理interference_factors - 可能是字符串集合或枚举集合
        self.interference_factors = []
        for f in feature_combination.interference_factors:
            if hasattr(f, 'value'):
                self.interference_factors.append(f.value)
            else:
                self.interference_factors.append(f)
    
    def add_interference_factor(self, factor: InterferenceType):
        """添加干扰因素"""
        self.feature_combination.interference_factors.add(factor)
        self._sync_fields()
    
    def remove_interference_factor(self, factor: InterferenceType):
        """移除干扰因素"""
        self.feature_combination.interference_factors.discard(factor)
        self._sync_fields()
    
    def set_growth_pattern(self, pattern: GrowthPattern):
        """设置生长模式"""
        self.feature_combination.growth_pattern = pattern
        self._sync_fields()
    
    def _sync_fields(self):
        """同步兼容性字段"""
        # Handle both method and property for to_label
        if hasattr(self.feature_combination.to_label, '__call__'):
            self.label = self.feature_combination.to_label()  # Method call
        else:
            self.label = self.feature_combination.to_label  # Property access
        # 处理interference_factors - 可能是字符串集合或枚举集合
        self.interference_factors = []
        for f in self.feature_combination.interference_factors:
            if hasattr(f, 'value'):
                self.interference_factors.append(f.value)
            else:
                self.interference_factors.append(f)
        
    def get_training_label(self) -> str:
        """获取训练用标签"""
        # Handle both method and property for to_label
        if hasattr(self.feature_combination.to_label, '__call__'):
            return self.feature_combination.to_label()  # Method call
        else:
            return self.feature_combination.to_label  # Property access
    
    def get_simple_label(self) -> str:
        """获取简化标签（向后兼容）"""
        # 处理growth_level - 可能是字符串或枚举
        if hasattr(self.feature_combination.growth_level, 'value'):
            return self.feature_combination.growth_level.value
        else:
            return self.feature_combination.growth_level
    
    def get_detailed_description(self) -> str:
        """获取详细描述"""
        desc_parts = []
        
        # 基础生长级别
        growth_desc = {
            GrowthLevel.NEGATIVE: "阴性",
            GrowthLevel.WEAK_GROWTH: "弱生长", 
            GrowthLevel.POSITIVE: "阳性"
        }
        desc_parts.append(growth_desc[self.feature_combination.growth_level])
        
        # 生长模式
        if self.feature_combination.growth_pattern:
            pattern_desc = {
                GrowthPattern.CLEAN: "无干扰",
                GrowthPattern.SMALL_DOTS: "小点状",
                GrowthPattern.LIGHT_GRAY: "淡灰色",
                GrowthPattern.IRREGULAR_AREAS: "不规则区域",
                GrowthPattern.CLUSTERED: "聚集型",
                GrowthPattern.SCATTERED: "分散型",
                GrowthPattern.HEAVY_GROWTH: "重度生长",
                GrowthPattern.FOCAL: "聚焦性",
                GrowthPattern.DIFFUSE: "弥漫性"
            }
            desc_parts.append(pattern_desc[self.feature_combination.growth_pattern])
        
        # 干扰因素
        if self.feature_combination.interference_factors:
            interference_desc = {
                InterferenceType.PORES: "气孔",
                InterferenceType.ARTIFACTS: "气孔重叠",
                InterferenceType.DEBRIS: "杂质",
                InterferenceType.CONTAMINATION: "污染"
            }
            factors = [interference_desc[f] for f in self.feature_combination.interference_factors]
            desc_parts.append(f"含{'/'.join(factors)}")
        
        return " - ".join(desc_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'image_path': self.image_path,
            'bbox': self.bbox,
            'panoramic_image_id': self.panoramic_image_id,
            'hole_number': self.hole_number,
            'hole_row': self.hole_row,
            'hole_col': self.hole_col,
            'microbe_type': self.microbe_type,
            'feature_combination': self.feature_combination.to_dict(),
            'annotation_source': self.annotation_source,
            'is_confirmed': self.is_confirmed,
            'metadata': self.metadata,
            # 向后兼容字段
            'label': self.label,
            'confidence': self.confidence,
            'growth_level': self.growth_level,
            'interference_factors': self.interference_factors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedPanoramicAnnotation':
        """从字典创建"""
        feature_combination = None
        if 'feature_combination' in data:
            feature_combination = FeatureCombination.from_dict(data['feature_combination'])
        else:
            # 向后兼容：从旧格式创建
            growth_level = GrowthLevel(data.get('growth_level', 'negative'))
            
            # 处理干扰因素 - 支持中文和英文值
            interference_factors = set()
            for f in data.get('interference_factors', []):
                try:
                    # 尝试直接创建枚举
                    interference_factors.add(InterferenceType(f))
                except ValueError:
                    # 如果失败，尝试映射到英文值
                    interference_mapping = {
                        # 中文到英文的映射
                        '气孔': 'pores',
                        '气孔重叠': 'artifacts',
                        '伪影': 'artifacts',
                        '杂质': 'debris',
                        '污染': 'contamination',
                        '污渍': 'contamination',
                        # 英文别名兼容
                        'pores': 'pores',
                        'debris': 'debris',
                        'contamination': 'contamination',
                        'artifacts': 'artifacts',
                        'noise': 'artifacts',     # 噪声 -> 伪影
                        'edge_blur': 'pores',     # 兼容旧的边缘模糊值
                        'scratches': 'debris'      # 划痕 -> 杂质
                    }
                    if f in interference_mapping:
                        try:
                            interference_factors.add(InterferenceType(interference_mapping[f]))
                        except ValueError:
                            log_warning(f"无法映射干扰因素: {f}")
                    else:
                        log_warning(f"未知的干扰因素: {f}")
            
            feature_combination = FeatureCombination(
                growth_level=growth_level,
                interference_factors=interference_factors,
                confidence=data.get('confidence', 1.0)
            )
        
        return cls(
            image_path=data['image_path'],
            bbox=data['bbox'],
            panoramic_image_id=data.get('panoramic_image_id', ''),
            hole_number=data.get('hole_number', 0),
            hole_row=data.get('hole_row', 0),
            hole_col=data.get('hole_col', 0),
            microbe_type=data.get('microbe_type', 'bacteria'),
            feature_combination=feature_combination,
            annotation_source=data.get('annotation_source', 'manual'),
            is_confirmed=data.get('is_confirmed', True),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_simple_annotation(cls, simple_ann) -> 'EnhancedPanoramicAnnotation':
        """从简单标注转换"""
        # 解析干扰因素 - 支持中文和英文值
        interference_factors = set()
        for factor_str in getattr(simple_ann, 'interference_factors', []):
            try:
                # 尝试直接创建枚举
                interference_factors.add(InterferenceType(factor_str))
            except ValueError:
                # 如果失败，尝试映射到英文值
                interference_mapping = {
                    # 中文到英文的映射
                    '气孔': 'pores',
                    '气孔重叠': 'artifacts',
                    '伪影': 'artifacts',
                    '杂质': 'debris',
                    '污染': 'contamination',
                    '污渍': 'contamination',
                    # 英文别名兼容
                    'pores': 'pores',
                    'debris': 'debris',
                    'contamination': 'contamination',
                    'artifacts': 'artifacts',
                    'noise': 'artifacts',     # 噪声 -> 伪影
                    'edge_blur': 'pores',     # 兼容旧的边缘模糊值
                    'scratches': 'debris'      # 划痕 -> 杂质
                }
                if factor_str in interference_mapping:
                    try:
                        interference_factors.add(InterferenceType(interference_mapping[factor_str]))
                    except ValueError:
                        log_warning(f"无法映射干扰因素: {factor_str}")
                else:
                    log_warning(f"未知的干扰因素: {factor_str}")
        
        # 创建特征组合
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel(getattr(simple_ann, 'growth_level', 'negative')),
            interference_factors=interference_factors,
            confidence=getattr(simple_ann, 'confidence', 1.0)
        )
        
        return cls(
            image_path=simple_ann.image_path,
            bbox=simple_ann.bbox,
            panoramic_image_id=getattr(simple_ann, 'panoramic_image_id', ''),
            hole_number=getattr(simple_ann, 'hole_number', 0),
            hole_row=getattr(simple_ann, 'hole_row', 0),
            hole_col=getattr(simple_ann, 'hole_col', 0),
            microbe_type=getattr(simple_ann, 'microbe_type', 'bacteria'),
            feature_combination=feature_combination,
            annotation_source=getattr(simple_ann, 'annotation_source', 'manual'),
            is_confirmed=getattr(simple_ann, 'is_confirmed', True)
        )


class FeatureAnnotationRules:
    """
    特征标注规则类
    定义特征组合的有效性和优先级
    """
    
    # 有效的特征组合规则
    VALID_COMBINATIONS = {
        # 阴性组合
        (GrowthLevel.NEGATIVE, None): [InterferenceType.PORES, InterferenceType.ARTIFACTS, InterferenceType.DEBRIS, InterferenceType.CONTAMINATION],
        (GrowthLevel.NEGATIVE, GrowthPattern.CLEAN): [],
        
        # 弱生长组合
        (GrowthLevel.WEAK_GROWTH, GrowthPattern.SMALL_DOTS): [InterferenceType.PORES, InterferenceType.ARTIFACTS],
        (GrowthLevel.WEAK_GROWTH, GrowthPattern.LIGHT_GRAY): [InterferenceType.PORES, InterferenceType.ARTIFACTS, InterferenceType.DEBRIS],
        (GrowthLevel.WEAK_GROWTH, GrowthPattern.IRREGULAR_AREAS): [InterferenceType.PORES, InterferenceType.ARTIFACTS],
        
        # 阳性组合
        (GrowthLevel.POSITIVE, GrowthPattern.CLUSTERED): [InterferenceType.PORES, InterferenceType.ARTIFACTS],
        (GrowthLevel.POSITIVE, GrowthPattern.SCATTERED): [InterferenceType.ARTIFACTS],
        (GrowthLevel.POSITIVE, GrowthPattern.HEAVY_GROWTH): [InterferenceType.ARTIFACTS],
        (GrowthLevel.POSITIVE, GrowthPattern.FOCAL): [InterferenceType.PORES, InterferenceType.ARTIFACTS],  # 真菌
        (GrowthLevel.POSITIVE, GrowthPattern.DIFFUSE): [InterferenceType.ARTIFACTS]  # 真菌
    }
    
    @classmethod
    def is_valid_combination(cls, growth_level: GrowthLevel, 
                           growth_pattern: Optional[GrowthPattern],
                           interference_factors: Set[InterferenceType]) -> bool:
        """检查特征组合是否有效"""
        key = (growth_level, growth_pattern)
        if key not in cls.VALID_COMBINATIONS:
            return False
        
        allowed_factors = set(cls.VALID_COMBINATIONS[key])
        return interference_factors.issubset(allowed_factors)
    
    @classmethod
    def get_recommended_patterns(cls, growth_level: GrowthLevel, 
                               microbe_type: str) -> List[GrowthPattern]:
        """获取推荐的生长模式"""
        if growth_level == GrowthLevel.NEGATIVE:
            return [GrowthPattern.CLEAN]
        elif growth_level == GrowthLevel.WEAK_GROWTH:
            return [GrowthPattern.SMALL_DOTS, GrowthPattern.LIGHT_GRAY, GrowthPattern.IRREGULAR_AREAS]
        elif growth_level == GrowthLevel.POSITIVE:
            if microbe_type == "bacteria":
                return [GrowthPattern.CLUSTERED, GrowthPattern.SCATTERED, GrowthPattern.HEAVY_GROWTH]
            else:  # fungi
                return [GrowthPattern.FOCAL, GrowthPattern.DIFFUSE, GrowthPattern.HEAVY_GROWTH]
        
        return []
    
    @classmethod
    def get_allowed_interference(cls, growth_level: GrowthLevel,
                               growth_pattern: Optional[GrowthPattern]) -> List[InterferenceType]:
        """获取允许的干扰因素"""
        key = (growth_level, growth_pattern)
        return cls.VALID_COMBINATIONS.get(key, [])


class TrainingDataGenerator:
    """
    训练数据生成器
    将复合特征标注转换为模型训练所需的格式
    """
    
    def __init__(self):
        self.label_encodings = self._create_label_encodings()
    
    def _create_label_encodings(self) -> Dict[str, int]:
        """创建标签编码映射"""
        # 基础三分类
        base_labels = ['negative', 'weak_growth', 'positive']
        
        # 扩展标签（包含特征组合）
        extended_labels = []
        
        # 生成所有可能的标签组合
        for growth_level in GrowthLevel:
            for growth_pattern in [None] + list(GrowthPattern):
                for interference_combo in self._get_interference_combinations():
                    if FeatureAnnotationRules.is_valid_combination(
                        growth_level, growth_pattern, interference_combo
                    ):
                        feature_combo = FeatureCombination(
                            growth_level, growth_pattern, interference_combo
                        )
                        # Handle both method and property for to_label
                        if hasattr(feature_combo.to_label, '__call__'):
                            extended_labels.append(feature_combo.to_label())  # Method call
                        else:
                            extended_labels.append(feature_combo.to_label)  # Property access
        
        # 创建编码映射
        all_labels = base_labels + extended_labels
        return {label: idx for idx, label in enumerate(sorted(set(all_labels)))}
    
    def _get_interference_combinations(self) -> List[Set[InterferenceType]]:
        """获取所有干扰因素组合"""
        factors = list(InterferenceType)
        combinations = [set()]  # 空集
        
        # 单个因素
        for factor in factors:
            combinations.append({factor})
        
        # 两个因素的组合
        for i in range(len(factors)):
            for j in range(i + 1, len(factors)):
                combinations.append({factors[i], factors[j]})
        
        return combinations
    
    def encode_annotation(self, annotation: EnhancedPanoramicAnnotation) -> Dict[str, Any]:
        """编码标注为训练数据"""
        # 基础标签
        base_label = annotation.get_simple_label()
        base_label_id = self.label_encodings.get(base_label, 0)
        
        # 详细标签
        detailed_label = annotation.get_training_label()
        detailed_label_id = self.label_encodings.get(detailed_label, 0)
        
        # 特征向量
        feature_vector = self._create_feature_vector(annotation)
        
        return {
            'image_path': annotation.image_path,
            'base_label': base_label,
            'base_label_id': base_label_id,
            'detailed_label': detailed_label,
            'detailed_label_id': detailed_label_id,
            'feature_vector': feature_vector,
            'bbox': annotation.bbox,
            'confidence': annotation.confidence,
            'microbe_type': annotation.microbe_type
        }
    
    def _create_feature_vector(self, annotation: EnhancedPanoramicAnnotation) -> List[float]:
        """创建特征向量"""
        vector = []
        
        # 生长级别 one-hot
        for level in GrowthLevel:
            vector.append(1.0 if annotation.feature_combination.growth_level == level else 0.0)
        
        # 生长模式 one-hot
        for pattern in GrowthPattern:
            vector.append(1.0 if annotation.feature_combination.growth_pattern == pattern else 0.0)
        
        # 干扰因素 multi-hot
        for factor in InterferenceType:
            vector.append(1.0 if factor in annotation.feature_combination.interference_factors else 0.0)
        
        # 置信度
        vector.append(annotation.feature_combination.confidence)
        
        return vector
    
    def generate_training_dataset(self, annotations: List[EnhancedPanoramicAnnotation],
                                output_format: str = 'json') -> Dict[str, Any]:
        """生成训练数据集"""
        encoded_data = []
        
        for ann in annotations:
            if ann.is_confirmed:  # 只使用已确认的标注
                encoded_data.append(self.encode_annotation(ann))
        
        dataset = {
            'metadata': {
                'total_samples': len(encoded_data),
                'label_encodings': self.label_encodings,
                'feature_vector_size': len(encoded_data[0]['feature_vector']) if encoded_data else 0,
                'generation_timestamp': str(Path().cwd())
            },
            'data': encoded_data
        }
        
        return dataset