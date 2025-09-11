"""
标注处理模块
负责标注的保存、加载、解析等核心业务逻辑
支持基础标注和增强标注两种模式，采用最新的标注分类系统
"""

from typing import Dict, Any, Optional, List, Tuple, Set
from pathlib import Path
from datetime import datetime
import tkinter as tk

# 日志导入
try:
    from src.utils.logger import (
        log_debug, log_info, log_warning, log_error,
        log_ann, log_timing
    )
except ImportError:
    def log_debug(msg, category=""): print(f"[DEBUG] {msg}")
    def log_info(msg, category=""): print(f"[INFO] {msg}")
    def log_warning(msg, category=""): print(f"[WARNING] {msg}")
    def log_error(msg, category=""): print(f"[ERROR] {msg}")
    def log_ann(msg): log_info(msg, "ANN")
    def log_timing(msg): log_info(msg, "TIMING")

# 模型导入
try:
    from src.models.panoramic_annotation import PanoramicAnnotation
    from src.models.enhanced_annotation import InterferenceType
    # 注意: enhanced_panoramic_annotation 模块不存在，使用 enhanced_annotation 代替
except ImportError as e:
    log_warning(f"标注模型导入失败: {e}")
    # 创建占位符类避免导入错误
    from dataclasses import dataclass, field
    
    @dataclass
    class PanoramicAnnotation:
        image_path: str = ""
        label: str = ""
        bbox: List[int] = field(default_factory=lambda: [0,0,100,100])
        panoramic_image_id: str = ""
        hole_number: int = 1
        growth_level: str = "negative"
        microbe_type: str = "bacteria"
        interference_factors: List[str] = field(default_factory=list)
        confidence: float = 1.0
        annotation_source: str = "manual"
        is_confirmed: bool = False
        hole_row: int = 0
        hole_col: int = 0
    
    @dataclass
    class EnhancedPanoramicAnnotation(PanoramicAnnotation):
        feature_combination: Any = None
        enhanced_data: Dict[str, Any] = field(default_factory=dict)
    
    # 干扰因素枚举的占位符
    class InterferenceType:
        PORES = "pores"
        ARTIFACTS = "artifacts"
        DEBRIS = "debris"
        CONTAMINATION = "contamination"

# 最新的标注分类系统
class GrowthLevel:
    """生长级别枚举"""
    NEGATIVE = "negative"
    POSITIVE = "positive"

class GrowthPattern:
    """生长模式枚举"""
    # 阴性模式
    CLEAN = "clean"                           # 无干扰的阴性
    WEAK_SCATTERED = "weak_scattered"         # 微弱分散
    LITTER_CENTER_DOTS = "litter_center_dots" # 弱中心点
    
    # 阳性模式
    FOCAL = "focal"                           # 聚焦
    STRONG_SCATTERED = "strong_scattered"     # 强分散
    HEAVY_GROWTH = "heavy_growth"             # 重度
    CENTER_DOTS = "center_dots"               # 强中心点
    WEAK_SCATTERED_POS = "weak_scattered_pos" # 弱分散
    IRREGULAR = "irregular"                   # 不规则
    
    # 真菌专用模式
    DIFFUSE = "diffuse"                       # 弥散（真菌）
    FILAMENTOUS_NON_FUSED = "filamentous_non_fused"  # 丝状非融合
    FILAMENTOUS_FUSED = "filamentous_fused"          # 丝状融合


class AnnotationProcessor:
    """标注处理器 - 负责标注的保存、加载、解析等核心业务逻辑"""
    
    def __init__(self, parent_gui):
        """
        初始化标注处理器
        
        Args:
            parent_gui: 父GUI对象
        """
        self.gui = parent_gui
        log_info("AnnotationProcessor初始化完成", "INIT")
        
    def save_current_annotation_internal(self, save_type: str = "manual") -> bool:
        """
        保存当前标注的内部实现
        
        Args:
            save_type: 保存类型 ("manual", "auto", "navigation")
            
        Returns:
            bool: 保存是否成功
        """
        log_info(f"*** 进入 save_current_annotation_internal 方法，类型: {save_type} ***", "SAVE")
        
        # 检查基本条件
        if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
            log_debug("早期退出: 没有切片文件", "SAVE")
            return False
            
        if not hasattr(self.gui, 'current_slice_index') or self.gui.current_slice_index >= len(self.gui.slice_files):
            log_debug("早期退出: 索引超出范围", "SAVE")
            return False

        try:
            current_file = self.gui.slice_files[self.gui.current_slice_index]
            
            # 优先使用增强标注模式
            if self._has_enhanced_annotation_panel():
                return self._save_enhanced_annotation(current_file, save_type)
            else:
                return self._save_basic_annotation(current_file, save_type)
                
        except Exception as e:
            log_error(f"保存标注失败 (类型: {save_type}): {e}", "SAVE")
            return False

    def _has_enhanced_annotation_panel(self) -> bool:
        """检查是否有增强标注面板"""
        return (hasattr(self.gui, 'enhanced_annotation_panel') and 
                self.gui.enhanced_annotation_panel is not None)

    def _save_enhanced_annotation(self, current_file: Dict[str, Any], save_type: str) -> bool:
        """保存增强标注"""
        try:
            # 获取特征组合
            feature_combination = self.gui.enhanced_annotation_panel.get_current_feature_combination()
            log_debug(f"准备保存增强标注: {feature_combination.growth_level} [{feature_combination.confidence:.2f}]", "SAVE")
            
            # 创建增强标注对象
            enhanced_annotation = EnhancedPanoramicAnnotation(
                image_path=current_file['filepath'],
                label=f"{feature_combination.growth_level}_{self._get_current_microbe_type()}",
                bbox=[0, 0, 70, 70],  # 默认边界框
                panoramic_image_id=current_file.get('panoramic_id', ''),
                hole_number=getattr(self.gui, 'current_hole_number', 1),
                microbe_type=self._get_current_microbe_type(),
                growth_level=feature_combination.growth_level,
                interference_factors=self._get_current_interference_factors(),
                confidence=feature_combination.confidence,
                annotation_source=save_type,
                is_confirmed=True,
                hole_row=self._calculate_hole_row(),
                hole_col=self._calculate_hole_col(),
                feature_combination=feature_combination,
                enhanced_data=self.gui.enhanced_annotation_panel.get_annotation_data()
            )
            
            # 添加到数据集
            if hasattr(self.gui, 'current_dataset') and self.gui.current_dataset:
                self.gui.current_dataset.add_annotation(enhanced_annotation)
                log_info(f"增强标注已保存到数据集 (类型: {save_type})", "SAVE")
                self._update_ui_after_save()
                return True
            else:
                log_error("当前数据集不存在，无法保存增强标注", "SAVE")
                return False
                
        except Exception as e:
            log_error(f"保存增强标注失败: {e}", "SAVE")
            return False

    def _save_basic_annotation(self, current_file: Dict[str, Any], save_type: str) -> bool:
        """保存基础标注"""
        try:
            # 获取基础标注信息
            growth_level = self._get_current_growth_level()
            microbe_type = self._get_current_microbe_type()
            interference_factors = self._get_current_interference_factors()
            
            log_debug(f"准备保存基础标注: {growth_level} - {microbe_type}", "SAVE")
            
            # 创建基础标注对象
            annotation = PanoramicAnnotation(
                image_path=current_file['filepath'],
                label=f"{growth_level}_{microbe_type}",
                bbox=[0, 0, 100, 100],  # 默认边界框
                panoramic_image_id=current_file.get('panoramic_id', ''),
                hole_number=getattr(self.gui, 'current_hole_number', 1),
                growth_level=growth_level,
                microbe_type=microbe_type,
                interference_factors=interference_factors,
                confidence=1.0,
                annotation_source=save_type,
                is_confirmed=True,
                hole_row=self._calculate_hole_row(),
                hole_col=self._calculate_hole_col()
            )
            
            # 添加到数据集
            if hasattr(self.gui, 'current_dataset') and self.gui.current_dataset:
                self.gui.current_dataset.add_annotation(annotation)
                log_info(f"基础标注已保存到数据集 (类型: {save_type})", "SAVE")
                self._update_ui_after_save()
                return True
            else:
                log_error("当前数据集不存在，无法保存基础标注", "SAVE")
                return False
                
        except Exception as e:
            log_error(f"保存基础标注失败: {e}", "SAVE")
            return False

    def _get_current_growth_level(self) -> str:
        """获取当前生长级别"""
        if hasattr(self.gui, 'current_growth_level'):
            return self.gui.current_growth_level.get()
        return "negative"

    def _get_current_microbe_type(self) -> str:
        """获取当前微生物类型"""
        if hasattr(self.gui, 'current_microbe_type'):
            return self.gui.current_microbe_type.get()
        return "bacteria"

    def _get_current_interference_factors(self) -> List[str]:
        """获取当前干扰因素"""
        factors = []
        if hasattr(self.gui, 'interference_factors'):
            for factor_name, var in self.gui.interference_factors.items():
                if isinstance(var, tk.BooleanVar) and var.get():
                    factors.append(factor_name)
        return factors

    def _calculate_hole_row(self) -> int:
        """计算孔位行号"""
        hole_number = getattr(self.gui, 'current_hole_number', 1)
        return (hole_number - 1) // 12

    def _calculate_hole_col(self) -> int:
        """计算孔位列号"""
        hole_number = getattr(self.gui, 'current_hole_number', 1)
        return (hole_number - 1) % 12

    def _update_ui_after_save(self):
        """保存后更新UI"""
        try:
            if hasattr(self.gui, 'update_annotation_count'):
                self.gui.update_annotation_count()
            if hasattr(self.gui, 'current_annotation_modified'):
                self.gui.current_annotation_modified = False
        except Exception as e:
            log_warning(f"更新UI失败: {e}", "SAVE")

    def load_annotations_optimized(self) -> bool:
        """
        优化的标注加载方法
        
        Returns:
            bool: 加载是否成功
        """
        try:
            # 检查当前数据集
            if not hasattr(self.gui, 'current_dataset') or not self.gui.current_dataset:
                log_debug("没有当前数据集，跳过标注加载", "LOAD")
                return False
                
            # 获取当前位置信息
            panoramic_id = getattr(self.gui, 'current_panoramic_id', '')
            hole_number = getattr(self.gui, 'current_hole_number', 1)
            
            if not panoramic_id:
                log_debug("当前全景ID为空，跳过标注加载", "LOAD")
                return False
                
            # 查找现有标注
            existing_annotation = self.gui.current_dataset.get_annotation(panoramic_id, hole_number)
            
            if existing_annotation:
                self.apply_existing_annotation(existing_annotation)
                log_debug(f"已加载标注: {existing_annotation.growth_level}", "LOAD")
                return True
            else:
                # 尝试从配置文件加载
                config_annotation = self.get_config_annotation(panoramic_id, hole_number)
                if config_annotation:
                    self.apply_config_annotation(config_annotation)
                    log_debug(f"已加载配置标注", "LOAD")
                    return True
                else:
                    # 重置为默认状态
                    self.reset_to_default()
                    log_debug("重置为默认标注状态", "LOAD")
                    return True
                    
        except Exception as e:
            log_error(f"加载标注失败: {e}", "LOAD")
            return False

    def apply_existing_annotation(self, annotation):
        """
        应用已有的标注数据
        
        Args:
            annotation: 标注对象 (PanoramicAnnotation 或 EnhancedPanoramicAnnotation)
        """
        try:
            # 设置基础标注信息
            if hasattr(self.gui, 'current_growth_level'):
                self.gui.current_growth_level.set(annotation.growth_level)
            if hasattr(self.gui, 'current_microbe_type'):
                self.gui.current_microbe_type.set(annotation.microbe_type)
                
            # 设置干扰因素
            self._set_interference_factors(annotation.interference_factors)
                
            # 如果是增强标注，应用增强数据
            if isinstance(annotation, EnhancedPanoramicAnnotation):
                self._apply_enhanced_annotation_data(annotation)
            
            log_debug(f"标注应用完成: {annotation.growth_level}", "LOAD")
            
        except Exception as e:
            log_error(f"应用现有标注失败: {e}", "LOAD")

    def _set_interference_factors(self, factors: List[str]):
        """设置干扰因素"""
        if hasattr(self.gui, 'interference_factors'):
            # 先清除所有选择
            for var in self.gui.interference_factors.values():
                if isinstance(var, tk.BooleanVar):
                    var.set(False)
            
            # 设置指定的因素
            for factor in factors:
                if factor in self.gui.interference_factors:
                    var = self.gui.interference_factors[factor]
                    if isinstance(var, tk.BooleanVar):
                        var.set(True)

    def _apply_enhanced_annotation_data(self, annotation):
        """应用增强标注数据"""
        if self._has_enhanced_annotation_panel():
            try:
                if hasattr(annotation, 'enhanced_data') and annotation.enhanced_data:
                    self.gui.enhanced_annotation_panel.set_annotation_data(annotation.enhanced_data)
                    log_debug("已应用增强标注数据", "LOAD")
                if hasattr(annotation, 'feature_combination') and annotation.feature_combination:
                    self.gui.enhanced_annotation_panel.set_feature_combination(annotation.feature_combination)
                    log_debug("已应用特征组合", "LOAD")
            except Exception as e:
                log_warning(f"应用增强标注数据失败: {e}", "LOAD")

    def apply_config_annotation(self, config_data: Dict[str, Any]):
        """
        应用配置文件中的标注
        
        Args:
            config_data: 配置标注数据
        """
        try:
            parsed = self.parse_annotation_string(config_data.get('annotation', ''))
            if not parsed:
                return
                
            growth_level = parsed.get('growth_level', 'negative')
            microbe_type = parsed.get('microbe_type', 'bacteria')
            
            # 创建配置标注对象
            annotation = PanoramicAnnotation(
                image_path='',
                label=f"{growth_level}_{microbe_type}",
                bbox=[0, 0, 100, 100],
                panoramic_image_id=getattr(self.gui, 'current_panoramic_id', ''),
                hole_number=getattr(self.gui, 'current_hole_number', 1),
                growth_level=growth_level,
                microbe_type=microbe_type,
                interference_factors=parsed.get('interference_factors', []),
                confidence=0.8,  # 配置文件标注的置信度稍低
                annotation_source="config",
                is_confirmed=False,  # 需要用户确认
                hole_row=self._calculate_hole_row(),
                hole_col=self._calculate_hole_col()
            )
            
            # 添加到数据集并应用到界面
            if hasattr(self.gui, 'current_dataset') and self.gui.current_dataset:
                self.gui.current_dataset.add_annotation(annotation)
                self.apply_existing_annotation(annotation)
                log_debug(f"配置标注已导入: {growth_level}", "LOAD")

        except Exception as e:
            log_error(f"应用配置标注失败: {e}", "LOAD")

    def reset_to_default(self):
        """重置到默认标注状态"""
        try:
            # 重置基础标注状态
            if hasattr(self.gui, 'current_growth_level'):
                self.gui.current_growth_level.set(GrowthLevel.NEGATIVE)
            if hasattr(self.gui, 'current_microbe_type'):
                # 根据全景图ID自动判断微生物类型
                panoramic_id = getattr(self.gui, 'current_panoramic_id', '')
                default_type = self._get_default_microbe_type_by_id(panoramic_id)
                self.gui.current_microbe_type.set(default_type)
                
            # 重置干扰因素
            self._set_interference_factors([])
                
            # 重置增强标注面板
            if self._has_enhanced_annotation_panel():
                try:
                    # 使用新的增强标注默认值
                    self.gui.enhanced_annotation_panel.initialize_with_defaults(
                        growth_level=GrowthLevel.NEGATIVE,
                        microbe_type=self._get_default_microbe_type_by_id(
                            getattr(self.gui, 'current_panoramic_id', '')
                        ),
                        reset_interference=True
                    )
                    log_debug("已重置增强标注面板", "LOAD")
                except Exception as e:
                    log_warning(f"重置增强标注面板失败: {e}", "LOAD")
                    
            log_debug("已重置为默认标注状态", "LOAD")
            
        except Exception as e:
            log_error(f"重置默认状态失败: {e}", "LOAD")

    def _get_default_microbe_type_by_id(self, panoramic_id: str) -> str:
        """根据全景图ID获取默认微生物类型"""
        if panoramic_id and len(panoramic_id) >= 2:
            prefix = panoramic_id[:2].upper()
            if prefix == "FG":
                return "fungi"
        return "bacteria"

    def get_config_annotation(self, panoramic_id: str, hole_number: int) -> Optional[Dict[str, Any]]:
        """
        从配置文件获取标注信息
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 孔位编号
            
        Returns:
            配置标注数据或None
        """
        try:
            # TODO: 实现配置文件查找逻辑
            # 这里应该实现具体的配置文件读取逻辑
            return None
            
        except Exception as e:
            log_error(f"获取配置标注失败: {e}", "LOAD")
            return None

    def parse_annotation_string(self, annotation_str: str) -> Dict[str, Any]:
        """
        解析标注字符串，支持新的分类系统
        
        Args:
            annotation_str: 标注字符串，如 "positive_focal" 或 "negative_clean_with_pores"
            
        Returns:
            解析后的标注信息字典
        """
        try:
            if not annotation_str or annotation_str.strip() == "":
                return {
                    'growth_level': GrowthLevel.NEGATIVE,
                    'growth_pattern': GrowthPattern.CLEAN,
                    'microbe_type': 'bacteria',
                    'interference_factors': [],
                    'label': 'negative'
                }
            
            # 清理输入
            annotation_str = annotation_str.strip().lower()
            
            # 基础生长级别映射 (注意：移除了weak_growth)
            level_mapping = {
                'negative': GrowthLevel.NEGATIVE,
                'neg': GrowthLevel.NEGATIVE,
                'positive': GrowthLevel.POSITIVE,
                'pos': GrowthLevel.POSITIVE,
                # 兼容旧版本，weak_growth映射到positive
                'weak_growth': GrowthLevel.POSITIVE,
                'weak': GrowthLevel.POSITIVE
            }
            
            # 生长模式映射
            pattern_mapping = {
                # 阴性模式
                'clean': GrowthPattern.CLEAN,
                'weak_scattered': GrowthPattern.WEAK_SCATTERED,
                'litter_center_dots': GrowthPattern.LITTER_CENTER_DOTS,
                'filamentous_non_fused': GrowthPattern.FILAMENTOUS_NON_FUSED,
                
                # 阳性模式
                'focal': GrowthPattern.FOCAL,
                'strong_scattered': GrowthPattern.STRONG_SCATTERED,
                'heavy_growth': GrowthPattern.HEAVY_GROWTH,
                'center_dots': GrowthPattern.CENTER_DOTS,
                'weak_scattered_pos': GrowthPattern.WEAK_SCATTERED_POS,
                'irregular': GrowthPattern.IRREGULAR,
                'diffuse': GrowthPattern.DIFFUSE,
                'filamentous_fused': GrowthPattern.FILAMENTOUS_FUSED,
                
                # 中文映射
                '清亮': GrowthPattern.CLEAN,
                '微弱分散': GrowthPattern.WEAK_SCATTERED,
                '弱中心点': GrowthPattern.LITTER_CENTER_DOTS,
                '聚焦性': GrowthPattern.FOCAL,
                '聚焦': GrowthPattern.FOCAL,
                '强分散': GrowthPattern.STRONG_SCATTERED,
                '重度': GrowthPattern.HEAVY_GROWTH,
                '强中心点': GrowthPattern.CENTER_DOTS,
                '弱分散': GrowthPattern.WEAK_SCATTERED_POS,
                '不规则': GrowthPattern.IRREGULAR,
                '弥散': GrowthPattern.DIFFUSE,
                '丝状非融合': GrowthPattern.FILAMENTOUS_NON_FUSED,
                '丝状融合': GrowthPattern.FILAMENTOUS_FUSED
            }
            
            # 微生物类型推断
            microbe_type = 'bacteria'  # 默认
            if any(keyword in annotation_str for keyword in ['fungi', 'fungal', '真菌', 'yeast', '酵母']):
                microbe_type = 'fungi'
            
            # 干扰因素关键词映射（更新为新的分类）
            interference_mapping = {
                '气孔': InterferenceType.PORES,
                'pores': InterferenceType.PORES,
                '气孔重叠': InterferenceType.ARTIFACTS,
                'artifacts': InterferenceType.ARTIFACTS,
                '杂质': InterferenceType.DEBRIS,
                'debris': InterferenceType.DEBRIS,
                '污染': InterferenceType.CONTAMINATION,
                'contamination': InterferenceType.CONTAMINATION,
                
                # 兼容旧版本映射
                '气泡': InterferenceType.ARTIFACTS,
                'bubble': InterferenceType.ARTIFACTS,
                '划痕': InterferenceType.DEBRIS,
                'scratch': InterferenceType.DEBRIS,
                '边缘': InterferenceType.ARTIFACTS,
                'edge': InterferenceType.ARTIFACTS,
                '模糊': InterferenceType.ARTIFACTS,
                '污渍': InterferenceType.CONTAMINATION,
                'stain': InterferenceType.CONTAMINATION,
                '反光': InterferenceType.ARTIFACTS,
                'reflection': InterferenceType.ARTIFACTS
            }
            
            # 解析主要生长级别
            growth_level = GrowthLevel.NEGATIVE
            for level_key, level_value in level_mapping.items():
                if level_key in annotation_str:
                    growth_level = level_value
                    break
            
            # 解析生长模式
            growth_pattern = None
            for pattern_key, pattern_value in pattern_mapping.items():
                if pattern_key in annotation_str:
                    growth_pattern = pattern_value
                    break
            
            # 如果没有明确的生长模式，使用默认值
            if not growth_pattern:
                if growth_level == GrowthLevel.NEGATIVE:
                    growth_pattern = GrowthPattern.CLEAN
                else:
                    growth_pattern = GrowthPattern.FOCAL
            
            # 解析干扰因素
            interference_factors = []
            for factor_key, factor_value in interference_mapping.items():
                if factor_key in annotation_str:
                    if factor_value not in interference_factors:
                        interference_factors.append(factor_value)
            
            # 生成标签
            label_parts = [growth_level]
            if growth_pattern and growth_pattern != GrowthPattern.CLEAN:
                label_parts.append(growth_pattern)
            if interference_factors:
                factor_strs = []
                for factor in interference_factors:
                    if hasattr(factor, 'value'):
                        factor_strs.append(factor.value)
                    else:
                        factor_strs.append(str(factor))
                factor_str = "_".join(sorted(factor_strs))
                label_parts.append(f"with_{factor_str}")
            
            label = "_".join(label_parts)
            
            result = {
                'growth_level': growth_level,
                'growth_pattern': growth_pattern,
                'microbe_type': microbe_type,
                'interference_factors': interference_factors,
                'label': label
            }
            
            log_debug(f"解析标注字符串: '{annotation_str}' -> {result}", "PARSE")
            return result
            
        except Exception as e:
            log_error(f"解析标注字符串失败: {e}", "PARSE")
            return {
                'growth_level': GrowthLevel.NEGATIVE,
                'growth_pattern': GrowthPattern.CLEAN,
                'microbe_type': 'bacteria',
                'interference_factors': [],
                'label': 'negative'
            }

    def get_annotation_summary(self) -> Dict[str, Any]:
        """
        获取当前标注的摘要信息
        
        Returns:
            标注摘要字典
        """
        try:
            summary = {
                'growth_level': self._get_current_growth_level(),
                'microbe_type': self._get_current_microbe_type(),
                'interference_factors': self._get_current_interference_factors(),
                'has_enhanced_data': self._has_enhanced_annotation_panel(),
                'panoramic_id': getattr(self.gui, 'current_panoramic_id', ''),
                'hole_number': getattr(self.gui, 'current_hole_number', 1),
                'timestamp': datetime.now().isoformat()
            }
            
            # 如果有增强标注数据，添加额外信息
            if self._has_enhanced_annotation_panel():
                try:
                    feature_combination = self.gui.enhanced_annotation_panel.get_current_feature_combination()
                    summary['enhanced_confidence'] = feature_combination.confidence
                    summary['enhanced_growth_level'] = feature_combination.growth_level
                    summary['enhanced_growth_pattern'] = feature_combination.growth_pattern
                    
                    # 转换干扰因素为字符串列表
                    interference_strs = []
                    for factor in feature_combination.interference_factors:
                        if hasattr(factor, 'value'):
                            interference_strs.append(factor.value)
                        else:
                            interference_strs.append(str(factor))
                    summary['enhanced_interference_factors'] = interference_strs
                    
                except Exception as e:
                    log_warning(f"获取增强标注摘要失败: {e}", "SUMMARY")
            
            return summary
            
        except Exception as e:
            log_error(f"获取标注摘要失败: {e}", "SUMMARY")
            return {}

    def validate_current_annotation(self) -> Tuple[bool, List[str]]:
        """
        验证当前标注的有效性
        
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            # 检查基本字段
            growth_level = self._get_current_growth_level()
            if growth_level not in [GrowthLevel.NEGATIVE, GrowthLevel.POSITIVE]:
                errors.append(f"无效的生长级别: {growth_level}")
            
            microbe_type = self._get_current_microbe_type()
            if microbe_type not in ['bacteria', 'fungi']:
                errors.append(f"无效的微生物类型: {microbe_type}")
            
            # 检查生长模式（如果有增强标注面板）
            if self._has_enhanced_annotation_panel():
                try:
                    feature_combination = self.gui.enhanced_annotation_panel.get_current_feature_combination()
                    growth_pattern = feature_combination.growth_pattern
                    
                    # 验证生长模式是否匹配生长级别和微生物类型
                    if growth_level == GrowthLevel.NEGATIVE:
                        valid_negative_patterns = [
                            GrowthPattern.CLEAN, 
                            GrowthPattern.WEAK_SCATTERED, 
                            GrowthPattern.LITTER_CENTER_DOTS
                        ]
                        if microbe_type == 'fungi':
                            valid_negative_patterns.append(GrowthPattern.FILAMENTOUS_NON_FUSED)
                        
                        if growth_pattern and growth_pattern not in valid_negative_patterns:
                            errors.append(f"阴性生长模式无效: {growth_pattern}")
                    
                    elif growth_level == GrowthLevel.POSITIVE:
                        valid_positive_patterns = [
                            GrowthPattern.FOCAL,
                            GrowthPattern.STRONG_SCATTERED,
                            GrowthPattern.HEAVY_GROWTH,
                            GrowthPattern.CENTER_DOTS,
                            GrowthPattern.WEAK_SCATTERED_POS,
                            GrowthPattern.IRREGULAR
                        ]
                        if microbe_type == 'fungi':
                            valid_positive_patterns.extend([
                                GrowthPattern.DIFFUSE,
                                GrowthPattern.FILAMENTOUS_FUSED
                            ])
                        
                        if growth_pattern and growth_pattern not in valid_positive_patterns:
                            errors.append(f"阳性生长模式无效: {growth_pattern}")
                    
                    # 检查置信度
                    if not (0.0 <= feature_combination.confidence <= 1.0):
                        errors.append(f"置信度超出范围: {feature_combination.confidence}")
                        
                except Exception as e:
                    errors.append(f"增强标注数据无效: {e}")
            
            # 检查孔位号
            hole_number = getattr(self.gui, 'current_hole_number', 1)
            if not (1 <= hole_number <= 120):
                errors.append(f"孔位号超出范围: {hole_number}")
            
            # 检查全景图ID
            panoramic_id = getattr(self.gui, 'current_panoramic_id', '')
            if not panoramic_id:
                errors.append("缺少全景图ID")
            
            is_valid = len(errors) == 0
            log_debug(f"标注验证结果: {'有效' if is_valid else '无效'}, 错误数: {len(errors)}", "VALIDATE")
            
            return is_valid, errors
            
        except Exception as e:
            log_error(f"标注验证失败: {e}", "VALIDATE")
            return False, [f"验证过程出错: {e}"]
