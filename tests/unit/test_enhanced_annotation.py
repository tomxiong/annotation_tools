"""
Tests for EnhancedPanoramicAnnotation data model.
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from src.models.enhanced_annotation import EnhancedPanoramicAnnotation, FeatureCombination, GrowthLevel, GrowthPattern, InterferenceType
from src.core.exceptions import ValidationError


class TestEnhancedPanoramicAnnotation:
    """Test cases for EnhancedPanoramicAnnotation class."""
    
    def test_enhanced_annotation_creation_with_defaults(self):
        """Test creating enhanced annotation with default feature combination."""
        annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11,
            microbe_type="bacteria"
        )
        
        assert annotation.image_path == "test/EB10000026_hole_108.png"
        assert annotation.bbox == [0, 0, 70, 70]
        assert annotation.panoramic_image_id == "EB10000026"
        assert annotation.hole_number == 108
        assert annotation.hole_row == 8
        assert annotation.hole_col == 11
        assert annotation.microbe_type == "bacteria"
        assert annotation.annotation_source == "manual"
        assert annotation.is_confirmed == True
        assert annotation.metadata == {}
        assert isinstance(annotation.feature_combination, FeatureCombination)
        assert annotation.feature_combination.growth_level == GrowthLevel.NEGATIVE
        # Test both method and property access for to_label
        if hasattr(annotation.feature_combination.to_label, '__call__'):
            assert annotation.label == annotation.feature_combination.to_label()
        else:
            assert annotation.label == annotation.feature_combination.to_label
        assert annotation.confidence == 1.0
        assert annotation.growth_level == "negative"
        assert annotation.interference_factors == []
    
    def test_enhanced_annotation_creation_with_custom_feature_combination(self):
        """Test creating enhanced annotation with custom feature combination."""
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.CLUSTERED,
            interference_factors={InterferenceType.PORES, InterferenceType.ARTIFACTS},
            confidence=0.85
        )
        
        annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11,
            microbe_type="fungi",
            feature_combination=feature_combination,
            annotation_source="manual",
            is_confirmed=True
        )
        
        assert annotation.image_path == "test/EB10000026_hole_108.png"
        assert annotation.bbox == [0, 0, 70, 70]
        assert annotation.panoramic_image_id == "EB10000026"
        assert annotation.hole_number == 108
        assert annotation.hole_row == 8
        assert annotation.hole_col == 11
        assert annotation.microbe_type == "fungi"
        assert annotation.annotation_source == "manual"
        assert annotation.is_confirmed == True
        assert annotation.feature_combination == feature_combination
        # Test both method and property access for to_label
        if hasattr(feature_combination.to_label, '__call__'):
            assert annotation.label == feature_combination.to_label()
        else:
            assert annotation.label == feature_combination.to_label
        assert annotation.confidence == 0.85
        assert annotation.growth_level == "positive"
        assert set(annotation.interference_factors) == {"pores", "artifacts"}
    
    def test_enhanced_annotation_update_feature_combination(self):
        """Test updating feature combination in enhanced annotation."""
        # Start with default (negative)
        annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11
        )
        
        assert annotation.growth_level == "negative"
        assert annotation.interference_factors == []
        
        # Update to positive with pattern and interference
        new_feature_combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.SCATTERED,
            interference_factors={InterferenceType.EDGE_BLUR},
            confidence=0.92
        )
        
        annotation.update_feature_combination(new_feature_combination)
        
        assert annotation.feature_combination == new_feature_combination
        # Test both method and property access for to_label
        if hasattr(new_feature_combination.to_label, '__call__'):
            assert annotation.label == new_feature_combination.to_label()
        else:
            assert annotation.label == new_feature_combination.to_label
        assert annotation.confidence == 0.92
        assert annotation.growth_level == "positive"
        assert annotation.interference_factors == ["edge_blur"]
    
    def test_enhanced_annotation_add_remove_interference_factor(self):
        """Test adding and removing interference factors."""
        annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11
        )
        
        assert annotation.interference_factors == []
        
        # Add interference factors
        annotation.add_interference_factor(InterferenceType.PORES)
        assert set(annotation.interference_factors) == {"pores"}
        
        annotation.add_interference_factor(InterferenceType.ARTIFACTS)
        assert set(annotation.interference_factors) == {"pores", "artifacts"}
        
        # Remove interference factor
        annotation.remove_interference_factor(InterferenceType.PORES)
        assert set(annotation.interference_factors) == {"artifacts"}
        
        # Try to remove non-existent factor (should not raise error)
        annotation.remove_interference_factor(InterferenceType.PORES)
        assert set(annotation.interference_factors) == {"artifacts"}
    
    def test_enhanced_annotation_set_growth_pattern(self):
        """Test setting growth pattern."""
        annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11
        )
        
        # Initially no growth pattern
        assert annotation.feature_combination.growth_pattern is None
        
        # Set growth pattern
        annotation.set_growth_pattern(GrowthPattern.HEAVY_GROWTH)
        assert annotation.feature_combination.growth_pattern == GrowthPattern.HEAVY_GROWTH
    
    def test_enhanced_annotation_get_training_label(self):
        """Test getting training label."""
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.WEAK_GROWTH,
            growth_pattern=GrowthPattern.LIGHT_GRAY,
            interference_factors={InterferenceType.PORES},
            confidence=0.75
        )
        
        annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11,
            feature_combination=feature_combination
        )
        
        # Test both method and property access for to_label
        expected_label = "weak_growth_light_gray_with_pores"
        if hasattr(feature_combination.to_label, '__call__'):
            assert annotation.get_training_label() == feature_combination.to_label()
        else:
            assert annotation.get_training_label() == feature_combination.to_label
        assert annotation.get_training_label() == expected_label
    
    def test_enhanced_annotation_get_simple_label(self):
        """Test getting simple label."""
        # Test negative
        annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11
        )
        assert annotation.get_simple_label() == "negative"
        
        # Test positive
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.CLUSTERED
        )
        annotation.update_feature_combination(feature_combination)
        assert annotation.get_simple_label() == "positive"
        
        # Test weak growth
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.WEAK_GROWTH,
            growth_pattern=GrowthPattern.SMALL_DOTS
        )
        annotation.update_feature_combination(feature_combination)
        assert annotation.get_simple_label() == "weak_growth"


class TestFeatureCombination:
    """Test cases for FeatureCombination class."""
    
    def test_feature_combination_creation(self):
        """Test creating feature combination."""
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.CLUSTERED,
            interference_factors={InterferenceType.PORES, InterferenceType.ARTIFACTS},
            confidence=0.85
        )
        
        assert feature_combination.growth_level == GrowthLevel.POSITIVE
        assert feature_combination.growth_pattern == GrowthPattern.CLUSTERED
        assert feature_combination.interference_factors == {InterferenceType.PORES, InterferenceType.ARTIFACTS}
        assert feature_combination.confidence == 0.85
    
    def test_feature_combination_to_label(self):
        """Test generating label from feature combination."""
        # Test negative with no pattern or interference
        feature_combination = FeatureCombination(GrowthLevel.NEGATIVE)
        expected_label = "negative"
        if hasattr(feature_combination.to_label, '__call__'):
            assert feature_combination.to_label() == expected_label
        else:
            assert feature_combination.to_label == expected_label
        
        # Test positive with pattern and interference
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.SCATTERED,
            interference_factors={InterferenceType.PORES, InterferenceType.ARTIFACTS},
            confidence=0.92
        )
        expected_label = "positive_scattered_with_artifacts_pores"
        if hasattr(feature_combination.to_label, '__call__'):
            assert feature_combination.to_label() == expected_label
        else:
            assert feature_combination.to_label == expected_label
    
    def test_feature_combination_to_dict(self):
        """Test converting feature combination to dictionary."""
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.WEAK_GROWTH,
            growth_pattern=GrowthPattern.LIGHT_GRAY,
            interference_factors={InterferenceType.EDGE_BLUR},
            confidence=0.78
        )
        
        result = feature_combination.to_dict()
        
        assert result["growth_level"] == "weak_growth"
        assert result["growth_pattern"] == "light_gray"
        assert set(result["interference_factors"]) == {"edge_blur"}
        assert result["confidence"] == 0.78
        assert result["label"] == "weak_growth_light_gray_with_edge_blur"
    
    def test_feature_combination_from_dict(self):
        """Test creating feature combination from dictionary."""
        data = {
            "growth_level": "positive",
            "growth_pattern": "heavy_growth",
            "interference_factors": ["pores", "contamination"],
            "confidence": 0.88
        }
        
        feature_combination = FeatureCombination.from_dict(data)
        
        assert feature_combination.growth_level == GrowthLevel.POSITIVE
        assert feature_combination.growth_pattern == GrowthPattern.HEAVY_GROWTH
        assert feature_combination.interference_factors == {InterferenceType.PORES, InterferenceType.CONTAMINATION}
        assert feature_combination.confidence == 0.88