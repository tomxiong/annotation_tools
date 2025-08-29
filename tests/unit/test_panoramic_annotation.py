"""
Tests for PanoramicAnnotation data model.
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from src.models.panoramic_annotation import PanoramicAnnotation
from src.models.enhanced_annotation import EnhancedPanoramicAnnotation, FeatureCombination, GrowthLevel, GrowthPattern, InterferenceType
from src.core.exceptions import ValidationError


class TestPanoramicAnnotation:
    """Test cases for PanoramicAnnotation class."""
    
    def test_panoramic_annotation_creation_with_required_fields(self):
        """Test creating panoramic annotation with required fields."""
        annotation = PanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            label="negative",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11,
            microbe_type="bacteria",
            growth_level="negative"
        )
        
        assert annotation.image_path == "test/EB10000026_hole_108.png"
        assert annotation.label == "negative"
        assert annotation.bbox == [0, 0, 70, 70]
        assert annotation.panoramic_image_id == "EB10000026"
        assert annotation.hole_number == 108
        assert annotation.hole_row == 8
        assert annotation.hole_col == 11
        assert annotation.microbe_type == "bacteria"
        assert annotation.growth_level == "negative"
        assert annotation.interference_factors == []
    
    def test_panoramic_annotation_creation_with_all_fields(self):
        """Test creating panoramic annotation with all fields."""
        interference_factors = ["pores", "artifacts"]
        gradient_context = {"adjacent_holes": [107, 109, 96, 120]}
        created_time = datetime.now()
        
        annotation = PanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            label="positive",
            bbox=[0, 0, 70, 70],
            confidence=0.95,
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11,
            microbe_type="fungi",
            growth_level="positive",
            interference_factors=interference_factors,
            gradient_context=gradient_context,
            annotation_source="manual",
            is_confirmed=True,
            created_at=created_time
        )
        
        assert annotation.image_path == "test/EB10000026_hole_108.png"
        assert annotation.label == "positive"
        assert annotation.bbox == [0, 0, 70, 70]
        assert annotation.confidence == 0.95
        assert annotation.panoramic_image_id == "EB10000026"
        assert annotation.hole_number == 108
        assert annotation.hole_row == 8
        assert annotation.hole_col == 11
        assert annotation.microbe_type == "fungi"
        assert annotation.growth_level == "positive"
        assert annotation.interference_factors == interference_factors
        assert annotation.gradient_context == gradient_context
        assert annotation.annotation_source == "manual"
        assert annotation.is_confirmed == True
        assert annotation.created_at == created_time
    
    def test_panoramic_annotation_validates_hole_number(self):
        """Test that panoramic annotation validates hole number range."""
        # Valid hole numbers
        valid_hole_numbers = [1, 60, 120]
        
        for hole_number in valid_hole_numbers:
            row = (hole_number - 1) // 12
            col = (hole_number - 1) % 12
            annotation = PanoramicAnnotation(
                image_path=f"test/EB10000026_hole_{hole_number}.png",
                label="negative",
                bbox=[0, 0, 70, 70],
                panoramic_image_id="EB10000026",
                hole_number=hole_number,
                hole_row=row,
                hole_col=col
            )
            assert annotation.hole_number == hole_number
        
        # Invalid hole numbers
        invalid_hole_numbers = [0, -1, 121, 200]
        
        for hole_number in invalid_hole_numbers:
            with pytest.raises(ValueError):
                PanoramicAnnotation(
                    image_path=f"test/EB10000026_hole_{hole_number}.png",
                    label="negative",
                    bbox=[0, 0, 70, 70],
                    panoramic_image_id="EB10000026",
                    hole_number=hole_number,
                    hole_row=0,
                    hole_col=0
                )
    
    def test_panoramic_annotation_validates_microbe_type(self):
        """Test that panoramic annotation validates microbe type."""
        # Valid microbe types
        valid_microbe_types = ["bacteria", "fungi"]
        
        for microbe_type in valid_microbe_types:
            annotation = PanoramicAnnotation(
                image_path="test/EB10000026_hole_108.png",
                label="negative",
                bbox=[0, 0, 70, 70],
                panoramic_image_id="EB10000026",
                hole_number=108,
                hole_row=8,
                hole_col=11,
                microbe_type=microbe_type
            )
            assert annotation.microbe_type == microbe_type
        
        # Invalid microbe types
        invalid_microbe_types = ["virus", "parasite", ""]
        
        for microbe_type in invalid_microbe_types:
            # This should not raise an error in the constructor, but will be validated in the setter
            annotation = PanoramicAnnotation(
                image_path="test/EB10000026_hole_108.png",
                label="negative",
                bbox=[0, 0, 70, 70],
                panoramic_image_id="EB10000026",
                hole_number=108,
                hole_row=8,
                hole_col=11,
                microbe_type="bacteria"  # Valid initial value
            )
            # Setting invalid value should raise error
            with pytest.raises(ValueError):
                annotation.panoramic_id = microbe_type  # This triggers validation
    
    def test_panoramic_annotation_validates_growth_level(self):
        """Test that panoramic annotation validates growth level."""
        # Valid growth levels
        valid_growth_levels = ["negative", "weak_growth", "positive"]
        
        for growth_level in valid_growth_levels:
            annotation = PanoramicAnnotation(
                image_path="test/EB10000026_hole_108.png",
                label=growth_level,
                bbox=[0, 0, 70, 70],
                panoramic_image_id="EB10000026",
                hole_number=108,
                hole_row=8,
                hole_col=11,
                growth_level=growth_level
            )
            assert annotation.growth_level == growth_level
        
        # Invalid growth levels
        invalid_growth_levels = ["none", "medium", "strong", ""]
        
        for growth_level in invalid_growth_levels:
            # This should not raise an error in the constructor, but will be validated in the setter
            annotation = PanoramicAnnotation(
                image_path="test/EB10000026_hole_108.png",
                label="negative",
                bbox=[0, 0, 70, 70],
                panoramic_image_id="EB10000026",
                hole_number=108,
                hole_row=8,
                hole_col=11,
                growth_level="negative"  # Valid initial value
            )
            # Setting invalid value should raise error
            with pytest.raises(ValueError):
                annotation.panoramic_id = growth_level  # This triggers validation
    
    def test_panoramic_annotation_from_filename_independent_mode(self):
        """Test creating panoramic annotation from filename in independent mode."""
        # Independent path mode: EB10000026_hole_108.png
        annotation = PanoramicAnnotation.from_filename(
            "EB10000026_hole_108.png",
            label="negative",
            microbe_type="bacteria",
            growth_level="negative"
        )
        
        assert annotation.image_path == "EB10000026_hole_108.png"
        assert annotation.panoramic_image_id == "EB10000026"
        assert annotation.hole_number == 108
        assert annotation.hole_row == 8  # (108-1)//12 = 8
        assert annotation.hole_col == 11  # (108-1)%12 = 11
        assert annotation.microbe_type == "bacteria"
        assert annotation.growth_level == "negative"
        assert annotation.bbox == [0, 0, 70, 70]
    
    def test_panoramic_annotation_from_filename_subdirectory_mode(self):
        """Test creating panoramic annotation from filename in subdirectory mode."""
        # Subdirectory mode: hole_108.png with panoramic_id provided
        annotation = PanoramicAnnotation.from_filename(
            "hole_108.png",
            label="positive",
            microbe_type="fungi",
            growth_level="positive",
            panoramic_id="EB20000045"
        )
        
        assert annotation.image_path == "hole_108.png"
        assert annotation.panoramic_image_id == "EB20000045"
        assert annotation.hole_number == 108
        assert annotation.hole_row == 8  # (108-1)//12 = 8
        assert annotation.hole_col == 11  # (108-1)%12 = 11
        assert annotation.microbe_type == "fungi"
        assert annotation.growth_level == "positive"
        assert annotation.bbox == [0, 0, 70, 70]
    
    def test_panoramic_annotation_from_filename_invalid_formats(self):
        """Test creating panoramic annotation from invalid filename formats."""
        # Invalid formats
        invalid_filenames = [
            "invalid_format.png",
            "EB10000026_hole_invalid.png",
            "hole_notanumber.png",
            "EB10000026_hole_0.png",  # Invalid hole number
            "EB10000026_hole_121.png"  # Invalid hole number
        ]
        
        for filename in invalid_filenames:
            with pytest.raises(ValueError):
                if "hole_" in filename and not filename.startswith("hole_"):
                    # Independent mode
                    PanoramicAnnotation.from_filename(filename, label="negative")
                else:
                    # Subdirectory mode
                    PanoramicAnnotation.from_filename(filename, label="negative", panoramic_id="EB10000026")
    
    def test_panoramic_annotation_subdirectory_mode_without_id(self):
        """Test subdirectory mode without providing panoramic_id."""
        with pytest.raises(ValueError, match="子目录模式需要提供panoramic_id参数"):
            PanoramicAnnotation.from_filename("hole_108.png", label="negative")
    
    def test_panoramic_annotation_get_hole_position(self):
        """Test getting hole position."""
        annotation = PanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            label="negative",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11
        )
        
        position = annotation.get_hole_position()
        assert position == (8, 11)
    
    def test_panoramic_annotation_get_adjacent_holes(self):
        """Test getting adjacent hole numbers."""
        # Test middle hole (hole 60 = row 4, col 11)
        annotation = PanoramicAnnotation(
            image_path="test/EB10000026_hole_60.png",
            label="negative",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=60,
            hole_row=4,
            hole_col=11
        )
        
        adjacent = annotation.get_adjacent_holes()
        # Should have left (59), top (48), bottom (72) neighbors but not right (no right neighbor)
        assert set(adjacent) == {48, 59, 72}
        
        # Test corner hole (hole 1 = row 0, col 0)
        annotation = PanoramicAnnotation(
            image_path="test/EB10000026_hole_1.png",
            label="negative",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=1,
            hole_row=0,
            hole_col=0
        )
        
        adjacent = annotation.get_adjacent_holes()
        # Should have right (2) and bottom (13) neighbors but not left or top
        assert set(adjacent) == {2, 13}
    
    def test_panoramic_annotation_to_dict(self):
        """Test converting panoramic annotation to dictionary."""
        interference_factors = ["pores", "artifacts"]
        gradient_context = {"adjacent_holes": [107, 109, 96, 120]}
        
        annotation = PanoramicAnnotation(
            image_path="test/EB10000026_hole_108.png",
            label="positive",
            bbox=[10, 20, 70, 70],
            confidence=0.92,
            panoramic_image_id="EB10000026",
            hole_number=108,
            hole_row=8,
            hole_col=11,
            microbe_type="fungi",
            growth_level="positive",
            interference_factors=interference_factors,
            gradient_context=gradient_context,
            annotation_source="manual",
            is_confirmed=True
        )
        
        result = annotation.to_dict()
        
        assert result["image_path"] == "test/EB10000026_hole_108.png"
        assert result["label"] == "positive"
        assert result["bbox"] == [10, 20, 70, 70]
        assert result["confidence"] == 0.92
        assert result["panoramic_image_id"] == "EB10000026"
        assert result["hole_number"] == 108
        assert result["hole_row"] == 8
        assert result["hole_col"] == 11
        assert result["microbe_type"] == "fungi"
        assert result["growth_level"] == "positive"
        assert result["interference_factors"] == interference_factors
        assert result["gradient_context"] == gradient_context
        assert result["annotation_source"] == "manual"
        assert result["is_confirmed"] == True
        assert "created_at" in result
        assert isinstance(result["created_at"], str)
    
    def test_panoramic_annotation_from_dict(self):
        """Test creating panoramic annotation from dictionary."""
        data = {
            "image_path": "test/EB10000026_hole_108.png",
            "label": "weak_growth",
            "bbox": [5, 15, 70, 70],
            "confidence": 0.78,
            "panoramic_image_id": "EB10000026",
            "hole_number": 108,
            "hole_row": 8,
            "hole_col": 11,
            "microbe_type": "bacteria",
            "growth_level": "weak_growth",
            "interference_factors": ["pores"],
            "gradient_context": {"adjacent_holes": [107, 109, 96, 120]},
            "annotation_source": "config_import",
            "is_confirmed": False,
            "created_at": "2024-01-01T12:00:00"
        }
        
        annotation = PanoramicAnnotation.from_dict(data)
        
        assert annotation.image_path == "test/EB10000026_hole_108.png"
        assert annotation.label == "weak_growth"
        assert annotation.bbox == [5, 15, 70, 70]
        assert annotation.confidence == 0.78
        assert annotation.panoramic_image_id == "EB10000026"
        assert annotation.hole_number == 108
        assert annotation.hole_row == 8
        assert annotation.hole_col == 11
        assert annotation.microbe_type == "bacteria"
        assert annotation.growth_level == "weak_growth"
        assert annotation.interference_factors == ["pores"]
        assert annotation.gradient_context == {"adjacent_holes": [107, 109, 96, 120]}
        assert annotation.annotation_source == "config_import"
        assert annotation.is_confirmed == False
        assert isinstance(annotation.created_at, datetime)