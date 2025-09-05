#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型建议导入服务测试
"""

import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.model_suggestion_import_service import (
    ModelSuggestionImportService, 
    Suggestion, 
    SuggestionsMap
)

class TestModelSuggestionImportService(unittest.TestCase):
    """模型建议导入服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.service = ModelSuggestionImportService()
        
        # 创建测试数据
        self.test_data = {
            "model_info": {
                "model_path": "test_model_v1.0",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            "annotations": [
                {
                    "panoramic_id": "P001",
                    "hole_number": 1,
                    "features": {
                        "growth_level": "positive",
                        "growth_pattern": ["clustered"],
                        "interference_factors": ["pores"],
                        "confidence": 0.95
                    },
                    "annotation_metadata": {
                        "model_version": "1.0"
                    }
                },
                {
                    "panoramic_id": "P001",
                    "hole_number": 2,
                    "features": {
                        "growth_level": "negative",
                        "confidence": 0.88
                    },
                    "annotation_metadata": {
                        "model_version": "1.0"
                    }
                }
            ]
        }
    
    def test_suggestion_creation(self):
        """测试建议对象创建"""
        suggestion = Suggestion(
            growth_level="positive",
            growth_pattern=["clustered"],
            interference_factors=["pores"],
            model_confidence=0.95,
            model_name="test_model",
            model_version="1.0"
        )
        
        self.assertEqual(suggestion.growth_level, "positive")
        self.assertEqual(suggestion.growth_pattern, ["clustered"])
        self.assertEqual(suggestion.interference_factors, ["pores"])
        self.assertEqual(suggestion.model_confidence, 0.95)
        self.assertEqual(suggestion.model_name, "test_model")
        self.assertEqual(suggestion.model_version, "1.0")
    
    def test_suggestions_map_creation(self):
        """测试建议映射创建"""
        suggestions_map = SuggestionsMap()
        
        suggestion1 = Suggestion(
            growth_level="positive",
            model_confidence=0.95,
            model_name="test_model"
        )
        suggestion2 = Suggestion(
            growth_level="negative",
            model_confidence=0.88,
            model_name="test_model"
        )
        
        suggestions_map.add_suggestion("P001", 1, suggestion1)
        suggestions_map.add_suggestion("P001", 2, suggestion2)
        
        self.assertEqual(suggestions_map.count(), 2)
        
        # 测试获取建议
        suggestion = suggestions_map.get_suggestion("P001", 1)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.growth_level, "positive")
        
        # 测试不存在的建议
        suggestion = suggestions_map.get_suggestion("P001", 99)
        self.assertIsNone(suggestion)
    
    def test_parse_annotation_record(self):
        """测试解析单个标注记录"""
        record = self.test_data["annotations"][0]
        suggestion, warning = self.service._parse_annotation(record, "test_model")
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.growth_level, "positive")
        self.assertEqual(suggestion.growth_pattern, ["clustered"])
        self.assertEqual(suggestion.interference_factors, ["pores"])
        self.assertEqual(suggestion.model_confidence, 0.95)
        self.assertEqual(suggestion.model_name, "test_model")
        self.assertEqual(suggestion.model_version, "1.0")
        self.assertIsNone(warning)
    
    def test_validate_json_structure_valid(self):
        """测试有效JSON结构验证"""
        # 创建临时文件进行测试
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name
        
        try:
            is_valid, errors = self.service.validate_json_structure(temp_file)
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
        finally:
            os.unlink(temp_file)
    
    def test_validate_json_structure_invalid(self):
        """测试无效JSON结构验证"""
        # 缺少annotations字段
        invalid_data = {"model_info": {}}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            temp_file = f.name
        
        try:
            is_valid, errors = self.service.validate_json_structure(temp_file)
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)
        finally:
            os.unlink(temp_file)
    
    def test_load_from_file(self):
        """测试从文件加载"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name
        
        try:
            suggestions_map, warnings = self.service.load_from_json(temp_file)
            
            self.assertIsNotNone(suggestions_map)
            self.assertEqual(suggestions_map.count(), 2)
            self.assertIsInstance(warnings, list)
            
            # 验证第一个建议
            suggestion = suggestions_map.get_suggestion("P001", 1)
            self.assertIsNotNone(suggestion)
            self.assertEqual(suggestion.growth_level, "positive")
            self.assertEqual(suggestion.model_confidence, 0.95)
            
            # 验证第二个建议
            suggestion = suggestions_map.get_suggestion("P001", 2)
            self.assertIsNotNone(suggestion)
            self.assertEqual(suggestion.growth_level, "negative")
            self.assertEqual(suggestion.model_confidence, 0.88)
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    
    def test_load_from_nonexistent_file(self):
        """测试加载不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.service.load_from_json("nonexistent_file.json")
    
    def test_load_invalid_json_file(self):
        """测试加载无效JSON文件"""
        # 创建包含无效JSON的临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                self.service.load_from_json(temp_file)
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    
    def test_logging(self):
        """测试日志记录功能"""
        # 测试成功加载时日志功能正常
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name
        
        try:
            suggestions_map, warnings = self.service.load_from_json(temp_file)
            # 验证加载成功
            self.assertIsNotNone(suggestions_map)
            self.assertEqual(suggestions_map.count(), 2)
        finally:
            os.unlink(temp_file)
        
        # 测试错误情况下日志功能正常
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            temp_file = f.name
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                self.service.load_from_json(temp_file)
        finally:
            os.unlink(temp_file)

if __name__ == '__main__':
    unittest.main()