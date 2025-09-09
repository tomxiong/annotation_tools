"""
标注管理器模块

负责标注数据的管理、保存和加载
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
import logging
import json
from datetime import datetime

if TYPE_CHECKING:
    from .main_controller import MainController

logger = logging.getLogger(__name__)


class AnnotationManager:
    """标注管理器 - 负责标注数据管理"""

    def __init__(self, controller: 'MainController'):
        self.controller = controller

        # 标注状态
        self.current_microbe_type = "bacteria"
        self.current_growth_level = "negative"
        self.interference_factors = {
            'pores': False,
            'artifacts': False,
            'edge_blur': False
        }

        # 视图模式
        self.view_mode = "manual"  # "manual" or "model"
        self.model_suggestion_loaded = False

        # 自动保存
        self.auto_save_enabled = True
        self.last_annotation_time = {}

    def initialize(self):
        """初始化标注管理器"""
        logger.info("AnnotationManager initialized")

    def save_current_annotation(self, save_type: str = "manual"):
        """保存当前标注"""
        try:
            # 获取当前标注数据
            annotation_data = self._get_current_annotation_data()

            if not annotation_data:
                logger.debug("没有标注数据需要保存")
                return

            # 创建标注对象
            annotation = self._create_annotation_object(annotation_data)

            # 保存到数据集
            if self.controller.current_dataset:
                # 检查是否已存在相同标注
                existing_ann = self.controller.current_dataset.get_annotation_by_hole(
                    self.controller.current_panoramic_id,
                    self.controller.current_hole_number
                )
                if existing_ann:
                    self.controller.current_dataset.annotations.remove(existing_ann)

                # 添加新标注
                self.controller.current_dataset.add_annotation(annotation)

                # 更新时间戳
                annotation_key = f"{self.controller.current_panoramic_id}_{self.controller.current_hole_number}"
                self.last_annotation_time[annotation_key] = datetime.now()

                # 重置修改标记
                self.controller.is_modified = False

                logger.debug(f"标注已保存: {self.controller.current_panoramic_id}_{self.controller.current_hole_number}")

        except Exception as e:
            logger.error(f"保存当前标注失败: {str(e)}")

    def load_existing_annotation(self):
        """加载现有标注"""
        if not self.controller.current_dataset:
            return

        existing_ann = self.controller.current_dataset.get_annotation_by_hole(
            self.controller.current_panoramic_id,
            self.controller.current_hole_number
        )

        if existing_ann:
            # 设置标注数据到UI组件
            if hasattr(existing_ann, 'microbe_type'):
                self.current_microbe_type = existing_ann.microbe_type

            if hasattr(existing_ann, 'growth_level'):
                self.current_growth_level = existing_ann.growth_level

            # 设置干扰因素
            if hasattr(existing_ann, 'interference_factors') and existing_ann.interference_factors:
                for factor in self.interference_factors:
                    self.interference_factors[factor] = factor in existing_ann.interference_factors

            logger.debug(f"已加载现有标注: {self.controller.current_panoramic_id}_{self.controller.current_hole_number}")

    def load_model_view_data(self):
        """加载模型视图数据"""
        try:
            if not hasattr(self.controller, 'hole_manager') or not self.controller.hole_manager:
                return

            suggestion = self.controller.hole_manager.get_hole_suggestion(self.controller.current_hole_number)
            if suggestion:
                # 设置模型预测结果到UI组件
                logger.debug(f"加载模型建议: {self.controller.current_hole_number}")
            else:
                # 无预测结果时，重置面板
                logger.debug(f"无模型预测结果: {self.controller.current_hole_number}")

        except Exception as e:
            logger.error(f"加载模型视图数据失败: {str(e)}")

    def get_annotation_status_text(self) -> str:
        """获取标注状态文本"""
        # 获取CFG配置信息
        config_data = self._get_current_panoramic_config()
        cfg_growth_level = None
        if config_data and self.controller.current_hole_number in config_data:
            cfg_growth_level = config_data[self.controller.current_hole_number]

        # 检查当前视图模式
        if self.view_mode == "model":
            # 模型视图模式：优先显示人工标注状态，如果没有标注则显示CFG信息
            existing_ann = self.controller.current_dataset.get_annotation_by_hole(
                self.controller.current_panoramic_id,
                self.controller.current_hole_number
            ) if self.controller.current_dataset else None

            if existing_ann:
                # 检查是否为增强标注
                has_enhanced = (hasattr(existing_ann, 'enhanced_data') and
                              existing_ann.enhanced_data and
                              existing_ann.annotation_source == 'enhanced_manual')

                if has_enhanced:
                    # 增强标注 - 显示已标注状态，包含CFG信息
                    annotation_key = f"{self.controller.current_panoramic_id}_{self.controller.current_hole_number}"

                    # 优先尝试从标注对象获取保存的时间戳
                    if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                        try:
                            import datetime
                            if isinstance(existing_ann.timestamp, str):
                                # 处理ISO格式时间戳
                                saved_timestamp = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                            else:
                                saved_timestamp = existing_ann.timestamp

                            # 同步到内存缓存
                            self.last_annotation_time[annotation_key] = saved_timestamp
                            datetime_str = saved_timestamp.strftime("%m-%d %H:%M:%S")

                            # 包含CFG信息
                            if cfg_growth_level:
                                status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                            else:
                                status_text = f"已标注 ({datetime_str})"

                            return status_text
                        except Exception as e:
                            logger.error(f"解析保存的时间戳失败: {e}")

                    # 如果标注对象中没有时间戳，尝试从内存缓存获取
                    if annotation_key in self.last_annotation_time:
                        import datetime
                        datetime_str = self.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")

                        # 包含CFG信息
                        if cfg_growth_level:
                            status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                        else:
                            status_text = f"已标注 ({datetime_str})"

                        return status_text

                    # 如果都没有时间戳，显示基本状态
                    if cfg_growth_level:
                        status_text = f"cfg-{cfg_growth_level} 已标注"
                    else:
                        status_text = "已标注"
                    return status_text
                else:
                    # 配置导入或其他类型 - 显示为配置导入状态
                    if cfg_growth_level:
                        return f"cfg-{cfg_growth_level} 配置导入"
                    else:
                        return "配置导入"
            else:
                # 无标注时显示CFG信息或模型预测状态
                if cfg_growth_level:
                    return f"cfg-{cfg_growth_level} 未标注"
                else:
                    # 没有CFG配置时显示模型预测状态
                    if hasattr(self.controller, 'hole_manager') and self.controller.hole_manager:
                        if self.controller.hole_manager.has_hole_suggestion(self.controller.current_hole_number):
                            return "模型预测"
                        else:
                            return "无模型预测"
                    else:
                        return "模型数据未加载"

        else:
            # 人工视图模式：显示人工标注状态，集成CFG信息，不显示"配置导入"
            existing_ann = self.controller.current_dataset.get_annotation_by_hole(
                self.controller.current_panoramic_id,
                self.controller.current_hole_number
            ) if self.controller.current_dataset else None

            if existing_ann:
                # 检查是否为增强标注
                has_enhanced = (hasattr(existing_ann, 'enhanced_data') and
                              existing_ann.enhanced_data and
                              existing_ann.annotation_source == 'enhanced_manual')

                if has_enhanced:
                    # 增强标注 - 显示已标注状态，包含CFG信息
                    annotation_key = f"{self.controller.current_panoramic_id}_{self.controller.current_hole_number}"

                    # 优先尝试从标注对象获取保存的时间戳
                    if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                        try:
                            import datetime
                            if isinstance(existing_ann.timestamp, str):
                                # 处理ISO格式时间戳
                                saved_timestamp = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                            else:
                                saved_timestamp = existing_ann.timestamp

                            # 同步到内存缓存
                            self.last_annotation_time[annotation_key] = saved_timestamp
                            datetime_str = saved_timestamp.strftime("%m-%d %H:%M:%S")

                            # 包含CFG信息
                            if cfg_growth_level:
                                status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                            else:
                                status_text = f"已标注 ({datetime_str})"

                            return status_text
                        except Exception as e:
                            logger.error(f"解析保存的时间戳失败: {e}")

                    # 如果标注对象中没有时间戳，尝试从内存缓存获取
                    if annotation_key in self.last_annotation_time:
                        import datetime
                        datetime_str = self.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")

                        # 包含CFG信息
                        if cfg_growth_level:
                            status_text = f"cfg-{cfg_growth_level} 已标注 ({datetime_str})"
                        else:
                            status_text = f"已标注 ({datetime_str})"

                        return status_text

                    # 如果都没有时间戳，显示基本状态
                    if cfg_growth_level:
                        status_text = f"cfg-{cfg_growth_level} 已标注"
                    else:
                        status_text = "已标注"
                    return status_text
                else:
                    # 配置导入或其他类型 - 显示CFG信息，不显示"配置导入"
                    if cfg_growth_level:
                        return f"cfg-{cfg_growth_level} 配置导入"
                    else:
                        return "配置导入"
            else:
                # 无标注时显示CFG信息
                if cfg_growth_level:
                    return f"cfg-{cfg_growth_level} 未标注"
                else:
                    return "无CFG"

    def get_detailed_annotation_info(self) -> str:
        """获取详细标注信息"""
        # 检查当前视图模式
        if self.view_mode == "model":
            # 模型视图模式：显示模型预测结果
            if hasattr(self.controller, 'hole_manager') and self.controller.hole_manager:
                suggestion = self.controller.hole_manager.get_hole_suggestion(self.controller.current_hole_number)
                if suggestion:
                    details = []

                    # 微生物类型
                    if hasattr(suggestion, 'microbe_type') and suggestion.microbe_type:
                        microbe_text = "细菌" if suggestion.microbe_type == "bacteria" else "真菌"
                        details.append(microbe_text)

                    # 生长级别
                    if hasattr(suggestion, 'growth_level') and suggestion.growth_level:
                        growth_map = {
                            'negative': '阴性',
                            'weak_growth': '弱生长',
                            'positive': '阳性'
                        }
                        growth_text = growth_map.get(suggestion.growth_level, suggestion.growth_level)
                        details.append(growth_text)

                    # 生长模式
                    if hasattr(suggestion, 'growth_pattern') and suggestion.growth_pattern:
                        pattern_map = {
                            'clean': '清亮',
                            'small_dots': '中心小点',
                            'light_gray': '浅灰色',
                            'irregular_areas': '不规则区域',
                            'clustered': '聚集型',
                            'scattered': '分散型',
                            'heavy_growth': '重度生长',
                            'focal': '聚焦性',
                            'diffuse': '弥漫性',
                            'default_positive': '阳性默认',
                            'default_weak_growth': '弱生长默认'
                        }
                        if isinstance(suggestion.growth_pattern, list):
                            pattern_texts = [pattern_map.get(p, p) for p in suggestion.growth_pattern]
                            pattern_text = ", ".join(pattern_texts)
                        else:
                            pattern_text = pattern_map.get(suggestion.growth_pattern, suggestion.growth_pattern)
                        details.append(pattern_text)

                    # 置信度
                    if hasattr(suggestion, 'model_confidence') and suggestion.model_confidence is not None:
                        details.append(f"{suggestion.model_confidence:.2f}")

                    # 干扰因素 + 预测标识
                    if hasattr(suggestion, 'interference_factors') and suggestion.interference_factors:
                        interference_map = {
                            'pores': '气孔',
                            'artifacts': '气孔重叠',
                            'noise': '气孔重叠',
                            'debris': '杂质',
                            'contamination': '污染'
                        }
                        if isinstance(suggestion.interference_factors, list) and suggestion.interference_factors:
                            interference_text = ", ".join([interference_map.get(f, f) for f in suggestion.interference_factors])
                        else:
                            interference_text = "无干扰"
                        details.append(f"{interference_text} 预测")
                    else:
                        details.append("无干扰 预测")

                    return " | ".join(details)
                else:
                    return "当前切片无模型预测结果"
            else:
                return "模型数据未加载"

        else:
            # 人工视图模式：只显示人工标注结果，无则不显示
            existing_ann = self.controller.current_dataset.get_annotation_by_hole(
                self.controller.current_panoramic_id,
                self.controller.current_hole_number
            ) if self.controller.current_dataset else None

            if existing_ann:
                # 构建详细标注信息
                details = []

                # 微生物类型
                if hasattr(existing_ann, 'microbe_type') and existing_ann.microbe_type:
                    microbe_text = "细菌" if existing_ann.microbe_type == "bacteria" else "真菌"
                    details.append(microbe_text)

                # 生长级别
                if hasattr(existing_ann, 'growth_level') and existing_ann.growth_level:
                    growth_map = {
                        'negative': '阴性',
                        'weak_growth': '弱生长',
                        'positive': '阳性'
                    }
                    growth_text = growth_map.get(existing_ann.growth_level, existing_ann.growth_level)
                    details.append(growth_text)

                # 生长模式（如果是增强标注）
                if hasattr(existing_ann, 'growth_pattern') and existing_ann.growth_pattern:
                    pattern_map = {
                        'clean': '清亮',
                        'small_dots': '中心小点',
                        'light_gray': '浅灰色',
                        'irregular_areas': '不规则区域',
                        'clustered': '聚集型',
                        'scattered': '分散型',
                        'heavy_growth': '重度生长',
                        'focal': '聚焦性',
                        'diffuse': '弥漫性',
                        'default_positive': '阳性默认',
                        'default_weak_growth': '弱生长默认'
                    }
                    pattern_text = pattern_map.get(existing_ann.growth_pattern, existing_ann.growth_pattern)
                    details.append(pattern_text)

                # 置信度
                if hasattr(existing_ann, 'confidence') and existing_ann.confidence:
                    details.append(f"{existing_ann.confidence:.2f}")

                # 干扰因素
                if hasattr(existing_ann, 'interference_factors') and existing_ann.interference_factors:
                    interference_map = {
                        'pores': '气孔',
                        'artifacts': '气孔重叠',
                        'noise': '气孔重叠',
                        'debris': '杂质',
                        'contamination': '污染'
                    }
                    if existing_ann.interference_factors:
                        interference_text = ", ".join([interference_map.get(f, f) for f in existing_ann.interference_factors])
                    else:
                        interference_text = "无干扰"
                    details.append(interference_text)
                else:
                    details.append("无干扰")

                return " | ".join(details)
            else:
                # 人工视图无标注时，不显示任何结果
                return ""

    def _get_current_annotation_data(self) -> Optional[Dict[str, Any]]:
        """获取当前标注数据"""
        # 这里应该从UI组件获取当前标注数据
        # 暂时返回示例数据
        return {
            'microbe_type': self.current_microbe_type,
            'growth_level': self.current_growth_level,
            'interference_factors': [k for k, v in self.interference_factors.items() if v],
            'panoramic_id': self.controller.current_panoramic_id,
            'hole_number': self.controller.current_hole_number
        }

    def _create_annotation_object(self, annotation_data: Dict[str, Any]):
        """创建标注对象"""
        from models.enhanced_annotation import EnhancedPanoramicAnnotation

        annotation = EnhancedPanoramicAnnotation(
            panoramic_image_id=annotation_data['panoramic_id'],
            hole_number=annotation_data['hole_number'],
            microbe_type=annotation_data['microbe_type'],
            growth_level=annotation_data['growth_level'],
            interference_factors=annotation_data['interference_factors'],
            annotation_source='enhanced_manual'
        )

        return annotation

    def _get_current_panoramic_config(self) -> Optional[Dict[int, str]]:
        """获取当前全景图的配置数据"""
        # 这里应该实现从配置文件加载配置数据的逻辑
        # 暂时返回空字典
        return {}

    def set_view_mode(self, mode: str):
        """设置视图模式"""
        if mode in ["manual", "model"]:
            self.view_mode = mode
            logger.debug(f"视图模式已设置为: {mode}")

    def toggle_auto_save(self):
        """切换自动保存"""
        self.auto_save_enabled = not self.auto_save_enabled
        logger.debug(f"自动保存已{'启用' if self.auto_save_enabled else '禁用'}")

    def has_unsaved_changes(self) -> bool:
        """检查是否有未保存的更改"""
        return self.controller.is_modified

    def get_annotation_count(self) -> int:
        """获取标注数量"""
        if self.controller.current_dataset:
            return len(self.controller.current_dataset.annotations)
        return 0