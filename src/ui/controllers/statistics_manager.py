"""
统计管理器模块

负责标注统计信息的计算和显示
"""

from typing import Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .main_controller import MainController

logger = logging.getLogger(__name__)


class StatisticsManager:
    """统计管理器 - 负责统计信息管理"""

    def __init__(self, controller: 'MainController'):
        self.controller = controller

    def initialize(self):
        """初始化统计管理器"""
        logger.info("StatisticsManager initialized")

    def update_statistics(self):
        """更新统计信息"""
        if not self.controller.current_dataset:
            return

        # 计算统计数据
        total_annotations = len(self.controller.current_dataset.annotations)
        negative_count = 0
        weak_growth_count = 0
        positive_count = 0

        for annotation in self.controller.current_dataset.annotations:
            if hasattr(annotation, 'growth_level'):
                if annotation.growth_level == 'negative':
                    negative_count += 1
                elif annotation.growth_level == 'weak_growth':
                    weak_growth_count += 1
                elif annotation.growth_level == 'positive':
                    positive_count += 1

        # 更新统计标签
        stats_text = f"统计: 未标注 {120 - total_annotations}, 阴性 {negative_count}, 弱生长 {weak_growth_count}, 阳性 {positive_count}"

        # 更新UI
        if hasattr(self.controller, 'ui_manager'):
            self.controller.ui_manager.update_statistics(stats_text)

    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        if not self.controller.current_dataset:
            return {}

        total_annotations = len(self.controller.current_dataset.annotations)
        negative_count = 0
        weak_growth_count = 0
        positive_count = 0

        for annotation in self.controller.current_dataset.annotations:
            if hasattr(annotation, 'growth_level'):
                if annotation.growth_level == 'negative':
                    negative_count += 1
                elif annotation.growth_level == 'weak_growth':
                    weak_growth_count += 1
                elif annotation.growth_level == 'positive':
                    positive_count += 1

        return {
            'total_annotations': total_annotations,
            'unannotated': 120 - total_annotations,
            'negative': negative_count,
            'weak_growth': weak_growth_count,
            'positive': positive_count,
            'completion_percentage': (total_annotations / 120) * 100 if total_annotations > 0 else 0
        }

    def get_detailed_statistics(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        if not self.controller.current_dataset:
            return {}

        stats = self.get_statistics_summary()

        # 按全景图分组的统计
        panoramic_stats = {}
        for annotation in self.controller.current_dataset.annotations:
            panoramic_id = annotation.panoramic_image_id
            if panoramic_id not in panoramic_stats:
                panoramic_stats[panoramic_id] = {
                    'total': 0,
                    'negative': 0,
                    'weak_growth': 0,
                    'positive': 0
                }

            panoramic_stats[panoramic_id]['total'] += 1
            if hasattr(annotation, 'growth_level'):
                growth_level = annotation.growth_level
                if growth_level in panoramic_stats[panoramic_id]:
                    panoramic_stats[panoramic_id][growth_level] += 1

        stats['panoramic_breakdown'] = panoramic_stats
        return stats

    def export_statistics(self, file_path: str) -> bool:
        """导出统计信息"""
        try:
            import json
            stats = self.get_detailed_statistics()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            logger.info(f"统计信息已导出到: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出统计信息失败: {str(e)}")
            return False

    def get_completion_status(self) -> str:
        """获取完成状态"""
        stats = self.get_statistics_summary()
        completion = stats.get('completion_percentage', 0)

        if completion == 0:
            return "未开始"
        elif completion < 25:
            return "刚开始"
        elif completion < 50:
            return "进行中"
        elif completion < 75:
            return "过半"
        elif completion < 100:
            return "即将完成"
        else:
            return "已完成"

    def get_productivity_metrics(self) -> Dict[str, Any]:
        """获取生产力指标"""
        if not hasattr(self.controller, 'last_annotation_time') or not self.controller.last_annotation_time:
            return {}

        # 计算标注速度（标注/分钟）
        total_annotations = len(self.controller.last_annotation_time)
        if total_annotations == 0:
            return {}

        # 计算总时间（分钟）
        timestamps = list(self.controller.last_annotation_time.values())
        if len(timestamps) < 2:
            return {'total_annotations': total_annotations}

        earliest = min(timestamps)
        latest = max(timestamps)
        time_diff = (latest - earliest).total_seconds() / 60  # 分钟

        if time_diff > 0:
            annotations_per_minute = total_annotations / time_diff
            return {
                'total_annotations': total_annotations,
                'time_span_minutes': time_diff,
                'annotations_per_minute': annotations_per_minute,
                'estimated_completion_time': (120 - total_annotations) / annotations_per_minute if annotations_per_minute > 0 else 0
            }

        return {'total_annotations': total_annotations}