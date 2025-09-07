"""模型建议导入服务
处理m16_inference_results.json格式的模型预测结果导入
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
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


@dataclass
class Suggestion:
    """模型建议数据结构"""
    growth_level: Optional[str] = None  # positive/negative/trace等
    growth_pattern: Optional[List[str]] = None  # clustered等
    interference_factors: Optional[List[str]] = None  # pores/artifacts/edge_blur等
    model_confidence: Optional[float] = None  # 模型置信度
    model_name: Optional[str] = None  # 模型名称
    model_version: Optional[str] = None  # 模型版本
    
    def __post_init__(self):
        """初始化后处理"""
        if self.growth_pattern is None:
            self.growth_pattern = []
        if self.interference_factors is None:
            self.interference_factors = []


class SuggestionsMap:
    """模型建议映射表"""
    
    def __init__(self):
        self._suggestions: Dict[Tuple[str, int], Suggestion] = {}
        
    def add_suggestion(self, panoramic_id: str, hole_number: int, suggestion: Suggestion):
        """添加建议"""
        key = (panoramic_id, hole_number)
        self._suggestions[key] = suggestion
        
    def get_suggestion(self, panoramic_id: str, hole_number: int) -> Optional[Suggestion]:
        """获取建议"""
        key = (panoramic_id, hole_number)
        return self._suggestions.get(key)
        
    def has_suggestion(self, panoramic_id: str, hole_number: int) -> bool:
        """检查是否有建议"""
        key = (panoramic_id, hole_number)
        return key in self._suggestions
        
    def get_all_suggestions(self) -> Dict[Tuple[str, int], Suggestion]:
        """获取所有建议"""
        return self._suggestions.copy()
        
    def count(self) -> int:
        """获取建议数量"""
        return len(self._suggestions)
        
    def clear(self):
        """清空所有建议"""
        self._suggestions.clear()


class ModelSuggestionImportService:
    """模型建议导入服务"""
    
    def __init__(self):
        self.log_debug = log_debug
        self.log_info = log_info
        self.log_warning = log_warning
        self.log_error = log_error
        
    def load_from_json(self, file_path: str) -> Tuple[SuggestionsMap, List[str]]:
        """
        从JSON文件加载模型建议
        
        Args:
            file_path: m16_inference_results.json文件路径
            
        Returns:
            Tuple[SuggestionsMap, List[str]]: (建议映射表, 警告信息列表)
            
        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON格式错误
            ValueError: 数据格式不符合预期
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"模型结果文件不存在: {file_path}")
            
        # 保留关键的用户提示信息
        self.log_info(f"开始加载模型建议文件: {file_path}", "ModelImport")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.log_error(f"JSON解析失败: {e}", "ModelImport")
            raise json.JSONDecodeError(f"模型结果文件JSON格式错误: {e}", f.name, e.pos)
            
        return self._parse_json_data(data)
        
    def _parse_json_data(self, data: Dict[str, Any]) -> Tuple[SuggestionsMap, List[str]]:
        """
        解析JSON数据
        
        Args:
            data: 解析后的JSON数据
            
        Returns:
            Tuple[SuggestionsMap, List[str]]: (建议映射表, 警告信息列表)
        """
        warnings = []
        suggestions_map = SuggestionsMap()
        
        # 验证基本结构
        if 'annotations' not in data:
            raise ValueError("模型结果文件缺少'annotations'字段")
            
        annotations = data['annotations']
        if not isinstance(annotations, list):
            raise ValueError("'annotations'字段必须是数组")
            
        # 提取模型信息
        model_info = data.get('model_info', {})
        model_name = model_info.get('model_path', 'Unknown Model')
        if model_name != 'Unknown Model':
            # 从路径中提取模型名称
            model_name = Path(model_name).stem
            
        # 处理每个标注
        processed_count = 0
        duplicate_count = 0
        invalid_count = 0
        path_mapping_warnings = 0
        
        for i, annotation in enumerate(annotations):
            try:
                suggestion, warning = self._parse_annotation(annotation, model_name)
                if warning:
                    warnings.append(f"第{i+1}条记录: {warning}")
                    
                if suggestion is None:
                    invalid_count += 1
                    continue
                    
                panoramic_id = annotation.get('panoramic_id')
                hole_number = annotation.get('hole_number')
                image_path = annotation.get('image_path', '')
                
                if not panoramic_id or not isinstance(hole_number, int):
                    warnings.append(f"第{i+1}条记录: 缺少有效的panoramic_id或hole_number")
                    invalid_count += 1
                    continue
                
                # 暂时跳过路径验证，专注于模型建议数据的正确加载
                # path_warning = self._validate_image_path_mapping(image_path, panoramic_id, hole_number)
                # if path_warning:
                #     warnings.append(f"第{i+1}条记录: {path_warning}")
                #     path_mapping_warnings += 1
                    
                # 检查孔位编号范围
                if not (1 <= hole_number <= 120):
                    warnings.append(f"第{i+1}条记录: 孔位编号{hole_number}超出范围(1-120)，已忽略")
                    invalid_count += 1
                    continue
                    
                # 检查重复记录
                if suggestions_map.has_suggestion(panoramic_id, hole_number):
                    warnings.append(f"第{i+1}条记录: 重复的孔位({panoramic_id}, {hole_number})，以最后一条为准")
                    duplicate_count += 1
                    
                suggestions_map.add_suggestion(panoramic_id, hole_number, suggestion)
                processed_count += 1
                
            except Exception as e:
                warnings.append(f"第{i+1}条记录解析失败: {str(e)}")
                invalid_count += 1
                continue
                
        # 记录统计信息
        total_count = len(annotations)
        # 保留关键的用户提示信息
        self.log_info(f"模型建议导入完成: 总计{total_count}条，成功{processed_count}条，重复{duplicate_count}条，无效{invalid_count}条", "ModelImport")
        
        if warnings:
            self.log_warning(f"导入过程中发现{len(warnings)}个警告", "ModelImport")
            for warning in warnings[:10]:  # 只记录前10个警告
                self.log_warning(warning, "ModelImport")
            if len(warnings) > 10:
                self.log_warning(f"...还有{len(warnings)-10}个警告未显示", "ModelImport")
        
        # 添加统计信息到警告
        summary_warnings = []
        if processed_count > 0:
            summary_warnings.append(f"成功处理 {processed_count} 条记录")
        if duplicate_count > 0:
            summary_warnings.append(f"发现 {duplicate_count} 条重复记录")
        if path_mapping_warnings > 0:
            summary_warnings.append(f"发现 {path_mapping_warnings} 条路径映射不一致")
        if invalid_count > 0:
            summary_warnings.append(f"忽略 {invalid_count} 条无效记录")
        
        # 将统计信息插入到警告列表开头
        warnings = summary_warnings + warnings
                
        return suggestions_map, warnings
        
    def _parse_annotation(self, annotation: Dict[str, Any], model_name: str) -> Tuple[Optional[Suggestion], Optional[str]]:
        """
        解析单个标注记录
        
        Args:
            annotation: 标注数据
            model_name: 模型名称
            
        Returns:
            Tuple[Optional[Suggestion], Optional[str]]: (建议对象, 警告信息)
        """
        warning = None
        
        try:
            features = annotation.get('features', {})
            metadata = annotation.get('annotation_metadata', {})
            
            # 提取基本特征
            growth_level = features.get('growth_level')
            growth_pattern = features.get('growth_pattern')
            interference_factors = features.get('interference_factors')
            confidence = features.get('confidence')
            
            # 处理growth_pattern
            if growth_pattern and not isinstance(growth_pattern, list):
                growth_pattern = [str(growth_pattern)]
            elif growth_pattern:
                growth_pattern = [str(p) for p in growth_pattern]
                
            # 处理interference_factors
            if interference_factors and not isinstance(interference_factors, list):
                interference_factors = [str(interference_factors)]
            elif interference_factors:
                interference_factors = [str(f) for f in interference_factors]
                
            # 提取模型版本
            model_version = metadata.get('model_version')
            
            # 验证置信度
            if confidence is not None:
                try:
                    confidence = float(confidence)
                    if not (0.0 <= confidence <= 1.0):
                        warning = f"置信度{confidence}超出范围[0,1]，已保留原值"
                except (ValueError, TypeError):
                    warning = f"置信度格式无效: {confidence}，已设为None"
                    confidence = None
                    
            suggestion = Suggestion(
                growth_level=str(growth_level) if growth_level is not None else None,
                growth_pattern=growth_pattern,
                interference_factors=interference_factors,
                model_confidence=confidence,
                model_name=model_name,
                model_version=str(model_version) if model_version else None
            )
            
            return suggestion, warning
            
        except Exception as e:
            return None, f"解析特征失败: {str(e)}"
            
    def _validate_image_path_mapping(self, image_path: str, panoramic_id: str, hole_number: int) -> Optional[str]:
        """
        验证image_path与panoramic_id和hole_number的一致性
        
        Args:
            image_path: 图像路径
            panoramic_id: 全景图ID
            hole_number: 孔位编号
            
        Returns:
            Optional[str]: 如果不一致返回警告信息，否则返回None
        """
        if not image_path:
            return None
            
        try:
            path_obj = Path(image_path)
            filename = path_obj.stem
            full_path = str(path_obj)
            
            # 检查路径中是否包含panoramic_id（可能在目录名或文件名中）
            if panoramic_id not in full_path:
                return f"图像路径 {image_path} 与全景图ID {panoramic_id} 不匹配"
                
            # 检查文件名是否包含hole_number
            # 支持多种格式：hole_25, hole25, 25等
            hole_str_formats = [
                f"hole_{hole_number}", f"hole{hole_number}", 
                f"_{hole_number}_", f"_{hole_number:02d}_", f"_{hole_number:03d}_",
                f"-{hole_number}-", f"-{hole_number:02d}-", f"-{hole_number:03d}-",
                f"_{hole_number}", f"_{hole_number:02d}", f"_{hole_number:03d}",
                f"-{hole_number}", f"-{hole_number:02d}", f"-{hole_number:03d}",
                str(hole_number)
            ]
            
            # 检查文件名是否匹配任何一种格式
            if not any(fmt in filename for fmt in hole_str_formats):
                return f"图像路径 {image_path} 与孔位编号 {hole_number} 不匹配"
                
        except Exception as e:
            return f"验证图像路径映射时出错: {str(e)}"
            
        return None
            
    def merge_into_session(self, session_data: Any, suggestions_map: SuggestionsMap) -> int:
        """
        将建议合并到会话中
        
        Args:
            session_data: 会话数据对象（预留接口）
            suggestions_map: 建议映射表
            
        Returns:
            int: 成功合并的建议数量
        """
        # 这个方法将在HoleManager扩展后实现具体逻辑
        # 目前只返回建议数量
        # 保留关键的用户提示信息
        count = suggestions_map.count()
        # 保留关键的用户提示信息
        self.log_info(f"准备将{count}条模型建议合并到会话中", "ModelImport")
        return count
        
    def validate_json_structure(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        验证JSON文件结构是否符合预期
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return False, ["文件不存在"]
        except json.JSONDecodeError as e:
            return False, [f"JSON格式错误: {e}"]
        except Exception as e:
            return False, [f"读取文件失败: {e}"]
            
        # 检查必需字段
        required_fields = ['annotations']
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")
                
        if 'annotations' in data:
            annotations = data['annotations']
            if not isinstance(annotations, list):
                errors.append("'annotations'字段必须是数组")
            elif len(annotations) == 0:
                errors.append("'annotations'数组为空")
            else:
                # 检查第一个标注的结构
                first_annotation = annotations[0]
                required_annotation_fields = ['panoramic_id', 'hole_number']
                for field in required_annotation_fields:
                    if field not in first_annotation:
                        errors.append(f"标注记录缺少必需字段: {field}")
                        
        return len(errors) == 0, errors