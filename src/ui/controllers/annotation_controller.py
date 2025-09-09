"""
标注控制器模块

负责标注数据的管理和操作
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any, List, Set
import logging
import json
from datetime import datetime

from src.ui.utils.base_components import BaseController
from src.ui.utils.event_bus import EventBus, EventType, Event, get_event_bus
from src.ui.components import AnnotationPanel, ImageCanvas
from src.services.annotation_engine import AnnotationEngine

logger = logging.getLogger(__name__)


class AnnotationController(BaseController):
    """标注控制器"""
    
    def __init__(self, annotation_engine: Optional[AnnotationEngine] = None):
        super().__init__()
        self.annotation_engine = annotation_engine
        
        # UI组件
        self.annotation_panel: Optional[AnnotationPanel] = None
        self.image_canvas: Optional[ImageCanvas] = None
        
        # 标注数据
        self.annotations: Dict[str, Dict[str, Any]] = {}
        self.annotation_history: List[Dict[str, Any]] = []
        self.current_session_id: Optional[str] = None
        
        # 批量操作状态
        self.batch_mode = False
        self.selected_holes: Set[str] = set()
        
        # 标注模板
        self.annotation_templates: Dict[str, Dict[str, Any]] = {}
        
    def initialize(self) -> None:
        """初始化控制器"""
        try:
            logger.info("Initializing AnnotationController...")
            
            # 创建新会话
            self._create_new_session()
            
            # 订阅事件
            self._subscribe_events()
            
            self._mark_initialized()
            logger.info("AnnotationController initialized successfully")
            
        except Exception as e:
            self.handle_error(e, "AnnotationController initialization")
            raise
    
    def cleanup(self) -> None:
        """清理资源"""
        logger.info("Cleaning up AnnotationController...")
        self.cleanup_listeners()
        
        # 保存会话数据
        self._save_session_data()
    
    def set_annotation_panel(self, panel: AnnotationPanel):
        """设置标注面板"""
        self.annotation_panel = panel
    
    def set_image_canvas(self, canvas: ImageCanvas):
        """设置图像画布"""
        self.image_canvas = canvas
    
    def _subscribe_events(self):
        """订阅事件"""
        self.subscribe(EventType.HOLE_SELECTED, self._on_hole_selected)
        self.subscribe(EventType.ANNOTATION_SAVED, self._on_annotation_saved)
        self.subscribe(EventType.ANNOTATION_DELETED, self._on_annotation_deleted)
        self.subscribe(EventType.ANNOTATION_UPDATED, self._on_annotation_updated)
    
    def _create_new_session(self):
        """创建新会话"""
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.annotations.clear()
        self.annotation_history.clear()
        self.selected_holes.clear()
        logger.info(f"Created new annotation session: {self.current_session_id}")
    
    def _save_session_data(self):
        """保存会话数据"""
        if not self.current_session_id or not self.annotations:
            return
        
        try:
            session_data = {
                'session_id': self.current_session_id,
                'timestamp': datetime.now().isoformat(),
                'annotations': self.annotations,
                'history': self.annotation_history
            }
            
            # 这里可以保存到文件或数据库
            logger.debug(f"Session data prepared for {self.current_session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save session data: {e}")
    
    def _on_hole_selected(self, event: Event):
        """孔位选择事件"""
        data = event.data
        if data and 'hole_id' in data:
            hole_id = data['hole_id']
            
            # 更新当前孔位
            if self.annotation_panel:
                self.annotation_panel.set_current_hole(hole_id)
            
            # 如果是批量模式，添加到选择集合
            if self.batch_mode:
                self.selected_holes.add(hole_id)
                logger.debug(f"Added hole {hole_id} to batch selection")
    
    def _on_annotation_saved(self, event: Event):
        """标注保存事件"""
        data = event.data
        if data and 'hole_id' in data and 'annotation' in data:
            hole_id = data['hole_id']
            annotation = data['annotation']
            
            # 保存到数据存储
            self._save_annotation_to_storage(hole_id, annotation)
            
            # 添加到历史记录
            self._add_to_history('save', hole_id, annotation)
    
    def _on_annotation_deleted(self, event: Event):
        """标注删除事件"""
        data = event.data
        if data and 'hole_id' in data:
            hole_id = data['hole_id']
            
            # 从数据存储中删除
            self._delete_annotation_from_storage(hole_id)
            
            # 添加到历史记录
            self._add_to_history('delete', hole_id, None)
    
    def _on_annotation_updated(self, event: Event):
        """标注更新事件"""
        data = event.data
        if data:
            action = data.get('action')
            
            if action == 'batch_apply':
                self._handle_batch_apply(data)
            elif action == 'batch_apply_row':
                self._handle_batch_apply_row(data)
            elif action == 'batch_apply_column':
                self._handle_batch_apply_column(data)
            elif action == 'clear_all':
                self._handle_clear_all(data)
    
    def _save_annotation_to_storage(self, hole_id: str, annotation: Dict[str, Any]):
        """保存标注到存储"""
        try:
            # 添加时间戳
            annotation['timestamp'] = datetime.now().isoformat()
            annotation['session_id'] = self.current_session_id
            
            # 保存到内存
            self.annotations[hole_id] = annotation
            
            # 使用标注引擎保存
            if self.annotation_engine:
                self.annotation_engine.add_annotation(hole_id, annotation)
            
            logger.debug(f"Annotation saved for hole {hole_id}")
            
        except Exception as e:
            self.handle_error(e, f"Failed to save annotation for hole {hole_id}")
    
    def _delete_annotation_from_storage(self, hole_id: str):
        """从存储中删除标注"""
        try:
            # 从内存中删除
            if hole_id in self.annotations:
                del self.annotations[hole_id]
            
            # 使用标注引擎删除
            if self.annotation_engine:
                self.annotation_engine.remove_annotation(hole_id)
            
            logger.debug(f"Annotation deleted for hole {hole_id}")
            
        except Exception as e:
            self.handle_error(e, f"Failed to delete annotation for hole {hole_id}")
    
    def _add_to_history(self, action: str, hole_id: str, annotation: Optional[Dict[str, Any]]):
        """添加到历史记录"""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'hole_id': hole_id,
            'annotation': annotation.copy() if annotation else None
        }
        
        self.annotation_history.append(history_entry)
        
        # 限制历史记录数量
        if len(self.annotation_history) > 1000:
            self.annotation_history = self.annotation_history[-1000:]
    
    def _handle_batch_apply(self, data: Dict[str, Any]):
        """处理批量应用"""
        try:
            applied_count = data.get('applied_count', 0)
            logger.info(f"Batch annotation applied to {applied_count} holes")
            
            # 添加到历史记录
            self._add_to_history('batch_apply', 'multiple', {'count': applied_count})
            
        except Exception as e:
            self.handle_error(e, "Failed to handle batch apply")
    
    def _handle_batch_apply_row(self, data: Dict[str, Any]):
        """处理批量应用到行"""
        try:
            row = data.get('row', '')
            applied_count = data.get('applied_count', 0)
            logger.info(f"Batch annotation applied to row {row}, {applied_count} holes")
            
            # 添加到历史记录
            self._add_to_history('batch_apply_row', row, {'count': applied_count})
            
        except Exception as e:
            self.handle_error(e, "Failed to handle batch apply row")
    
    def _handle_batch_apply_column(self, data: Dict[str, Any]):
        """处理批量应用到列"""
        try:
            column = data.get('column', '')
            applied_count = data.get('applied_count', 0)
            logger.info(f"Batch annotation applied to column {column}, {applied_count} holes")
            
            # 添加到历史记录
            self._add_to_history('batch_apply_column', column, {'count': applied_count})
            
        except Exception as e:
            self.handle_error(e, "Failed to handle batch apply column")
    
    def _handle_clear_all(self, data: Dict[str, Any]):
        """处理清除所有标注"""
        try:
            self.annotations.clear()
            logger.info("All annotations cleared")
            
            # 添加到历史记录
            self._add_to_history('clear_all', 'all', None)
            
        except Exception as e:
            self.handle_error(e, "Failed to handle clear all")
    
    def get_annotation(self, hole_id: str) -> Optional[Dict[str, Any]]:
        """获取标注数据"""
        return self.annotations.get(hole_id)
    
    def get_all_annotations(self) -> Dict[str, Dict[str, Any]]:
        """获取所有标注数据"""
        return self.annotations.copy()
    
    def get_annotations_by_filter(self, filter_dict: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """根据过滤条件获取标注"""
        filtered = {}
        
        for hole_id, annotation in self.annotations.items():
            match = True
            
            for key, value in filter_dict.items():
                if key not in annotation or annotation[key] != value:
                    match = False
                    break
            
            if match:
                filtered[hole_id] = annotation
        
        return filtered
    
    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注统计信息"""
        stats = {
            'total_annotations': len(self.annotations),
            'growth_levels': {},
            'microbe_types': {},
            'annotated_rows': set(),
            'annotated_columns': set()
        }
        
        for hole_id, annotation in self.annotations.items():
            # 生长级别统计
            growth_level = annotation.get('growth_level', '未知')
            stats['growth_levels'][growth_level] = stats['growth_levels'].get(growth_level, 0) + 1
            
            # 微生物类型统计
            microbe_type = annotation.get('microbe_type', '未知')
            stats['microbe_types'][microbe_type] = stats['microbe_types'].get(microbe_type, 0) + 1
            
            # 行列统计
            row = hole_id[:2]
            col = hole_id[2:4]
            stats['annotated_rows'].add(row)
            stats['annotated_columns'].add(col)
        
        # 转换集合为计数
        stats['annotated_rows'] = len(stats['annotated_rows'])
        stats['annotated_columns'] = len(stats['annotated_columns'])
        
        return stats
    
    def validate_annotation(self, annotation: Dict[str, Any]) -> bool:
        """验证标注数据"""
        required_fields = ['growth_level', 'microbe_type']
        
        for field in required_fields:
            if field not in annotation or not annotation[field]:
                return False
        
        return True
    
    def export_annotations(self, file_path: str, format_type: str = 'json') -> bool:
        """导出标注数据"""
        try:
            if format_type.lower() == 'json':
                return self._export_json(file_path)
            elif format_type.lower() == 'csv':
                return self._export_csv(file_path)
            else:
                logger.error(f"Unsupported export format: {format_type}")
                return False
                
        except Exception as e:
            self.handle_error(e, f"Failed to export annotations to {file_path}")
            return False
    
    def _export_json(self, file_path: str) -> bool:
        """导出为JSON格式"""
        try:
            export_data = {
                'session_id': self.current_session_id,
                'export_timestamp': datetime.now().isoformat(),
                'annotations': self.annotations,
                'statistics': self.get_annotation_statistics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Annotations exported to JSON: {file_path}")
            return True
            
        except Exception as e:
            self.handle_error(e, f"Failed to export JSON to {file_path}")
            return False
    
    def _export_csv(self, file_path: str) -> bool:
        """导出为CSV格式"""
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入标题
                writer.writerow([
                    '孔位', '行', '列', '生长级别', '微生物类型', 
                    '备注', '标注时间', '会话ID'
                ])
                
                # 写入数据
                for hole_id, annotation in self.annotations.items():
                    row = int(hole_id[:2])
                    col = int(hole_id[2:4])
                    row_letter = chr(ord('A') + row)
                    col_number = col + 1
                    
                    writer.writerow([
                        f"{row_letter}{col_number}",
                        row_letter,
                        col_number,
                        annotation.get('growth_level', ''),
                        annotation.get('microbe_type', ''),
                        annotation.get('notes', ''),
                        annotation.get('timestamp', ''),
                        annotation.get('session_id', '')
                    ])
            
            logger.info(f"Annotations exported to CSV: {file_path}")
            return True
            
        except Exception as e:
            self.handle_error(e, f"Failed to export CSV to {file_path}")
            return False
    
    def import_annotations(self, file_path: str) -> bool:
        """导入标注数据"""
        try:
            if file_path.lower().endswith('.json'):
                return self._import_json(file_path)
            elif file_path.lower().endswith('.csv'):
                return self._import_csv(file_path)
            else:
                logger.error(f"Unsupported import format: {file_path}")
                return False
                
        except Exception as e:
            self.handle_error(e, f"Failed to import annotations from {file_path}")
            return False
    
    def _import_json(self, file_path: str) -> bool:
        """导入JSON格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            
            if 'annotations' in data:
                for hole_id, annotation in data['annotations'].items():
                    if self.validate_annotation(annotation):
                        self.annotations[hole_id] = annotation
                        imported_count += 1
            
            logger.info(f"Imported {imported_count} annotations from JSON: {file_path}")
            
            # 更新UI
            if self.annotation_panel:
                self.annotation_panel._update_annotation_list()
            
            return True
            
        except Exception as e:
            self.handle_error(e, f"Failed to import JSON from {file_path}")
            return False
    
    def _import_csv(self, file_path: str) -> bool:
        """导入CSV格式"""
        try:
            import csv
            
            imported_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # 解析孔位
                    hole_pos = row.get('孔位', '')
                    if hole_pos and len(hole_pos) >= 2:
                        row_letter = hole_pos[0].upper()
                        col_number = int(hole_pos[1:])
                        
                        row_idx = ord(row_letter) - ord('A')
                        col_idx = col_number - 1
                        
                        hole_id = f"{row_idx:02d}{col_idx:02d}"
                        
                        # 构建标注数据
                        annotation = {
                            'growth_level': row.get('生长级别', ''),
                            'microbe_type': row.get('微生物类型', ''),
                            'notes': row.get('备注', ''),
                            'timestamp': row.get('标注时间', datetime.now().isoformat()),
                            'session_id': self.current_session_id
                        }
                        
                        if self.validate_annotation(annotation):
                            self.annotations[hole_id] = annotation
                            imported_count += 1
            
            logger.info(f"Imported {imported_count} annotations from CSV: {file_path}")
            
            # 更新UI
            if self.annotation_panel:
                self.annotation_panel._update_annotation_list()
            
            return True
            
        except Exception as e:
            self.handle_error(e, f"Failed to import CSV from {file_path}")
            return False
    
    def toggle_batch_mode(self):
        """切换批量模式"""
        self.batch_mode = not self.batch_mode
        
        if not self.batch_mode:
            self.selected_holes.clear()
        
        logger.info(f"Batch mode {'enabled' if self.batch_mode else 'disabled'}")
        
        # 发布模式切换事件
        self.publish(EventType.ANNOTATION_UPDATED, {
            'action': 'toggle_batch_mode',
            'enabled': self.batch_mode
        })
    
    def get_batch_mode(self) -> bool:
        """获取批量模式状态"""
        return self.batch_mode
    
    def get_selected_holes(self) -> Set[str]:
        """获取选中的孔位"""
        return self.selected_holes.copy()
    
    def clear_selected_holes(self):
        """清除选中的孔位"""
        self.selected_holes.clear()
    
    def create_template(self, template_name: str, template_data: Dict[str, Any]):
        """创建标注模板"""
        if self.validate_annotation(template_data):
            self.annotation_templates[template_name] = template_data.copy()
            logger.info(f"Created annotation template: {template_name}")
        else:
            logger.warning(f"Invalid template data for: {template_name}")
    
    def apply_template(self, template_name: str, hole_ids: List[str]):
        """应用模板到指定孔位"""
        if template_name not in self.annotation_templates:
            logger.warning(f"Template not found: {template_name}")
            return
        
        template = self.annotation_templates[template_name]
        applied_count = 0
        
        for hole_id in hole_ids:
            annotation = template.copy()
            annotation['timestamp'] = datetime.now().isoformat()
            annotation['session_id'] = self.current_session_id
            annotation['template'] = template_name
            
            self.annotations[hole_id] = annotation
            applied_count += 1
        
        logger.info(f"Applied template '{template_name}' to {applied_count} holes")
        
        # 更新UI
        if self.annotation_panel:
            self.annotation_panel._update_annotation_list()
    
    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模板"""
        return self.annotation_templates.copy()
    
    def delete_template(self, template_name: str):
        """删除模板"""
        if template_name in self.annotation_templates:
            del self.annotation_templates[template_name]
            logger.info(f"Deleted template: {template_name}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            'session_id': self.current_session_id,
            'start_time': self.annotation_history[0]['timestamp'] if self.annotation_history else None,
            'annotation_count': len(self.annotations),
            'history_count': len(self.annotation_history),
            'statistics': self.get_annotation_statistics()
        }