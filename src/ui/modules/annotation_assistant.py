"""
标注助手模块
负责标注验证、自动建议、状态管理
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from ..modules.data_manager import AnnotationData


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class AnnotationAssistant:
    """标注助手 - 负责标注验证和自动建议"""
    
    def __init__(self, parent_gui):
        """
        初始化标注助手
        
        Args:
            parent_gui: 主GUI实例
        """
        self.gui = parent_gui
        self.current_annotation = None
        self.annotation_history = []
        self.validation_rules = self._init_validation_rules()
        
    def _init_validation_rules(self) -> Dict[str, Any]:
        """初始化验证规则"""
        return {
            'required_fields': ['panoramic_id', 'hole_number', 'growth_level'],
            'valid_growth_levels': ['negative', 'weak_growth', 'positive'],
            'confidence_range': (0.0, 1.0),
            'max_interference_factors': 5
        }
        
    def create_annotation(self, panoramic_id: str, hole_number: int, 
                         growth_level: str, confidence: float = 1.0,
                         microbe_type: str = "unknown",
                         interference_factors: List[str] = None,
                         annotation_source: str = "manual") -> AnnotationData:
        """
        创建新的标注数据
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 孔位号
            growth_level: 生长级别
            confidence: 置信度
            microbe_type: 微生物类型
            interference_factors: 干扰因素列表
            annotation_source: 标注来源
            
        Returns:
            AnnotationData: 标注数据对象
        """
        if interference_factors is None:
            interference_factors = []
            
        # 获取图像路径
        slice_files = self.gui.data_manager.get_slice_files_by_panoramic(panoramic_id)
        image_path = ""
        for file_info in slice_files:
            if file_info['hole_number'] == hole_number:
                image_path = file_info['filepath']
                break
                
        annotation = AnnotationData(
            panoramic_id=panoramic_id,
            hole_number=hole_number,
            growth_level=growth_level,
            confidence=confidence,
            microbe_type=microbe_type,
            interference_factors=interference_factors,
            annotation_source=annotation_source,
            is_confirmed=False,
            image_path=image_path,
            timestamp=datetime.now().isoformat()
        )
        
        self.current_annotation = annotation
        self.gui.log_info(f"创建标注: {panoramic_id}_{hole_number} -> {growth_level}", "ANNOTATION")
        
        return annotation
        
    def validate_annotation(self, annotation: AnnotationData) -> ValidationResult:
        """
        验证标注数据
        
        Args:
            annotation: 标注数据
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        
        # 检查必需字段
        for field in self.validation_rules['required_fields']:
            value = getattr(annotation, field, None)
            if value is None or value == "":
                errors.append(f"缺少必需字段: {field}")
                
        # 检查生长级别有效性
        if annotation.growth_level not in self.validation_rules['valid_growth_levels']:
            errors.append(f"无效的生长级别: {annotation.growth_level}")
            
        # 检查置信度范围
        min_conf, max_conf = self.validation_rules['confidence_range']
        if not (min_conf <= annotation.confidence <= max_conf):
            errors.append(f"置信度超出范围 [{min_conf}, {max_conf}]: {annotation.confidence}")
            
        # 检查干扰因素数量
        if len(annotation.interference_factors) > self.validation_rules['max_interference_factors']:
            warnings.append(f"干扰因素过多: {len(annotation.interference_factors)}")
            
        # 检查图像文件是否存在
        if annotation.image_path and not self._check_image_exists(annotation.image_path):
            warnings.append(f"图像文件不存在: {annotation.image_path}")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    def _check_image_exists(self, image_path: str) -> bool:
        """检查图像文件是否存在"""
        try:
            from pathlib import Path
            return Path(image_path).exists()
        except Exception:
            return False
            
    def save_annotation(self, annotation: AnnotationData) -> bool:
        """
        保存标注数据
        
        Args:
            annotation: 标注数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 验证标注
            validation_result = self.validate_annotation(annotation)
            
            if not validation_result.is_valid:
                error_msg = "; ".join(validation_result.errors)
                self.gui.log_error(f"标注验证失败: {error_msg}", "ANNOTATION")
                return False
                
            # 记录警告
            if validation_result.warnings:
                warning_msg = "; ".join(validation_result.warnings)
                self.gui.log_warning(f"标注警告: {warning_msg}", "ANNOTATION")
                
            # 确认标注
            annotation.is_confirmed = True
            annotation.timestamp = datetime.now().isoformat()
            
            # 添加到数据管理器
            self.gui.data_manager.add_annotation(annotation)
            
            # 保存到历史记录
            self.annotation_history.append(annotation)
            
            # 保存到文件
            success = self.gui.data_manager.save_annotations()
            
            if success:
                self.gui.log_info(f"保存标注成功: {annotation.panoramic_id}_{annotation.hole_number}", "ANNOTATION")
                
                # 更新UI显示
                if hasattr(self.gui, 'slice_controller'):
                    self.gui.slice_controller._update_panoramic_display()
                    self.gui.slice_controller._update_info_display()
                    
            return success
            
        except Exception as e:
            self.gui.log_error(f"保存标注失败: {e}", "ANNOTATION")
            return False
            
    def get_annotation_suggestions(self, panoramic_id: str, hole_number: int) -> List[Dict[str, Any]]:
        """
        获取标注建议
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 孔位号
            
        Returns:
            List[Dict]: 建议列表
        """
        suggestions = []
        
        # 基于周围孔位的模式识别
        neighbor_suggestions = self._get_neighbor_pattern_suggestions(panoramic_id, hole_number)
        suggestions.extend(neighbor_suggestions)
        
        # 基于历史标注的统计建议
        history_suggestions = self._get_history_based_suggestions(panoramic_id, hole_number)
        suggestions.extend(history_suggestions)
        
        # 基于图像特征的建议（占位符，可以集成机器学习模型）
        image_suggestions = self._get_image_based_suggestions(panoramic_id, hole_number)
        suggestions.extend(image_suggestions)
        
        return suggestions
        
    def _get_neighbor_pattern_suggestions(self, panoramic_id: str, hole_number: int) -> List[Dict[str, Any]]:
        """基于邻近孔位模式的建议"""
        suggestions = []
        
        try:
            # 获取当前孔位的行列
            if hasattr(self.gui, 'slice_controller'):
                positions = self.gui.slice_controller.hole_positions
                if hole_number in positions:
                    row, col = positions[hole_number]
                    
                    # 检查邻近孔位的标注
                    neighbor_annotations = []
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                                
                            neighbor_row = row + dr
                            neighbor_col = col + dc
                            
                            if (0 <= neighbor_row < 10 and 0 <= neighbor_col < 12):
                                neighbor_hole = neighbor_row * 12 + neighbor_col + 1
                                annotation = self.gui.data_manager.get_annotation(panoramic_id, neighbor_hole)
                                if annotation:
                                    neighbor_annotations.append(annotation)
                                    
                    # 分析邻近标注模式
                    if neighbor_annotations:
                        growth_counts = {}
                        for ann in neighbor_annotations:
                            growth_counts[ann.growth_level] = growth_counts.get(ann.growth_level, 0) + 1
                            
                        # 找出最常见的生长级别
                        most_common = max(growth_counts.items(), key=lambda x: x[1])
                        
                        suggestions.append({
                            'type': 'neighbor_pattern',
                            'growth_level': most_common[0],
                            'confidence': min(0.8, most_common[1] / len(neighbor_annotations)),
                            'reason': f"邻近{len(neighbor_annotations)}个孔位中{most_common[1]}个为{most_common[0]}"
                        })
                        
        except Exception as e:
            self.gui.log_error(f"邻近模式分析失败: {e}", "ANNOTATION")
            
        return suggestions
        
    def _get_history_based_suggestions(self, panoramic_id: str, hole_number: int) -> List[Dict[str, Any]]:
        """基于历史标注的建议"""
        suggestions = []
        
        try:
            # 统计同一位置的历史标注
            position_history = []
            for ann in self.annotation_history:
                if ann.hole_number == hole_number:
                    position_history.append(ann)
                    
            if position_history:
                # 计算每种生长级别的概率
                growth_counts = {}
                for ann in position_history:
                    growth_counts[ann.growth_level] = growth_counts.get(ann.growth_level, 0) + 1
                    
                total = len(position_history)
                for growth_level, count in growth_counts.items():
                    probability = count / total
                    if probability > 0.3:  # 只推荐概率大于30%的
                        suggestions.append({
                            'type': 'history_based',
                            'growth_level': growth_level,
                            'confidence': probability,
                            'reason': f"历史数据显示该位置{count}/{total}次为{growth_level}"
                        })
                        
        except Exception as e:
            self.gui.log_error(f"历史分析失败: {e}", "ANNOTATION")
            
        return suggestions
        
    def _get_image_based_suggestions(self, panoramic_id: str, hole_number: int) -> List[Dict[str, Any]]:
        """基于图像特征的建议（占位符）"""
        # 这里可以集成机器学习模型进行图像分析
        # 目前返回空列表
        return []
        
    def undo_last_annotation(self) -> bool:
        """撤销最后一次标注"""
        try:
            if not self.annotation_history:
                self.gui.log_warning("没有可撤销的标注", "ANNOTATION")
                return False
                
            last_annotation = self.annotation_history.pop()
            
            # 从数据管理器中移除
            success = self.gui.data_manager.remove_annotation(
                last_annotation.panoramic_id,
                last_annotation.hole_number
            )
            
            if success:
                # 保存更改
                self.gui.data_manager.save_annotations()
                
                self.gui.log_info(f"撤销标注: {last_annotation.panoramic_id}_{last_annotation.hole_number}", "ANNOTATION")
                
                # 更新UI显示
                if hasattr(self.gui, 'slice_controller'):
                    self.gui.slice_controller._update_panoramic_display()
                    self.gui.slice_controller._update_info_display()
                    
                return True
                
        except Exception as e:
            self.gui.log_error(f"撤销标注失败: {e}", "ANNOTATION")
            
        return False
        
    def get_annotation_progress(self) -> Dict[str, Any]:
        """获取标注进度信息"""
        try:
            stats = self.gui.data_manager.get_statistics()
            
            # 计算质量指标
            confirmed_rate = (stats['confirmed_annotations'] / stats['total_annotations'] * 100) if stats['total_annotations'] > 0 else 0
            
            # 计算标注速度（基于时间戳）
            recent_annotations = []
            current_time = datetime.now()
            
            for panoramic_annotations in self.gui.data_manager.annotations.values():
                for annotation in panoramic_annotations.values():
                    try:
                        ann_time = datetime.fromisoformat(annotation.timestamp)
                        time_diff = (current_time - ann_time).total_seconds() / 3600  # 小时
                        if time_diff <= 24:  # 最近24小时
                            recent_annotations.append(annotation)
                    except Exception:
                        pass
                        
            speed = len(recent_annotations)  # 每24小时的标注数量
            
            return {
                'total_progress': stats['progress_percent'],
                'confirmed_rate': confirmed_rate,
                'annotation_speed': speed,
                'quality_score': self._calculate_quality_score(),
                'distribution': stats['growth_level_distribution']
            }
            
        except Exception as e:
            self.gui.log_error(f"获取进度信息失败: {e}", "ANNOTATION")
            return {}
            
    def _calculate_quality_score(self) -> float:
        """计算标注质量分数"""
        try:
            total_score = 0
            annotation_count = 0
            
            for panoramic_annotations in self.gui.data_manager.annotations.values():
                for annotation in panoramic_annotations.values():
                    # 基于多个因素计算质量分数
                    score = 1.0
                    
                    # 置信度因子
                    score *= annotation.confidence
                    
                    # 确认状态因子
                    if annotation.is_confirmed:
                        score *= 1.0
                    else:
                        score *= 0.7
                        
                    # 来源可靠性因子
                    if annotation.annotation_source == "manual":
                        score *= 1.0
                    elif annotation.annotation_source == "model":
                        score *= 0.8
                    else:
                        score *= 0.9
                        
                    total_score += score
                    annotation_count += 1
                    
            return (total_score / annotation_count) if annotation_count > 0 else 0.0
            
        except Exception as e:
            self.gui.log_error(f"计算质量分数失败: {e}", "ANNOTATION")
            return 0.0
            
    def export_annotation_report(self, file_path: str) -> bool:
        """导出标注报告"""
        try:
            progress = self.get_annotation_progress()
            stats = self.gui.data_manager.get_statistics()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'statistics': stats,
                'progress': progress,
                'validation_rules': self.validation_rules,
                'annotation_history_count': len(self.annotation_history)
            }
            
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            self.gui.log_info(f"导出标注报告: {file_path}", "ANNOTATION")
            return True
            
        except Exception as e:
            self.gui.log_error(f"导出报告失败: {e}", "ANNOTATION")
            return False
