"""
Tests for Annotation data model.
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from src.models.annotation import Annotation
from src.core.exceptions import ValidationError


class TestAnnotation:
    """Test cases for Annotation class."""
    
    def test_annotation_creation_with_required_fields(self):
        """Test creating annotation with only required fields."""
        annotation = Annotation(
            image_path="test/image.jpg",
            label="cat",
            bbox=[10, 20, 100, 150]
        )
        
        assert annotation.image_path == "test/image.jpg"
        assert annotation.label == "cat"
        assert annotation.bbox == [10, 20, 100, 150]
        assert annotation.confidence is None
        assert annotation.metadata == {}
        assert isinstance(annotation.created_at, datetime)
    
    def test_annotation_creation_with_all_fields(self):
        """Test creating annotation with all fields."""
        metadata = {"source": "manual", "reviewer": "user1"}
        created_time = datetime.now()
        
        annotation = Annotation(
            image_path="test/image.jpg",
            label="dog",
            bbox=[5, 10, 80, 120],
            confidence=0.95,
            metadata=metadata,
            created_at=created_time
        )
        
        assert annotation.image_path == "test/image.jpg"
        assert annotation.label == "dog"
        assert annotation.bbox == [5, 10, 80, 120]
        assert annotation.confidence == 0.95
        assert annotation.metadata == metadata
        assert annotation.created_at == created_time
    
    def test_annotation_validates_bbox_format(self):
        """Test that annotation validates bbox format."""
        # Valid bbox formats
        valid_bboxes = [
            [10, 20, 100, 150],  # [x, y, width, height]
            [0, 0, 50, 50],      # Corner case
        ]
        
        for bbox in valid_bboxes:
            annotation = Annotation(
                image_path="test.jpg",
                label="test",
                bbox=bbox
            )
            assert annotation.bbox == bbox
        
        # Invalid bbox formats
        invalid_bboxes = [
            [10, 20, 100],       # Too few values
            [10, 20, 100, 150, 200],  # Too many values
            [-10, 20, 100, 150], # Negative x
            [10, -20, 100, 150], # Negative y
            [10, 20, -100, 150], # Negative width
            [10, 20, 100, -150], # Negative height
        ]
        
        for bbox in invalid_bboxes:
            with pytest.raises(ValidationError):
                Annotation(
                    image_path="test.jpg",
                    label="test",
                    bbox=bbox
                )
    
    def test_annotation_validates_confidence_range(self):
        """Test that annotation validates confidence range."""
        # Valid confidence values
        valid_confidences = [0.0, 0.5, 1.0, None]
        
        for confidence in valid_confidences:
            annotation = Annotation(
                image_path="test.jpg",
                label="test",
                bbox=[10, 20, 100, 150],
                confidence=confidence
            )
            assert annotation.confidence == confidence
        
        # Invalid confidence values
        invalid_confidences = [-0.1, 1.1, 2.0, -1.0]
        
        for confidence in invalid_confidences:
            with pytest.raises(ValidationError):
                Annotation(
                    image_path="test.jpg",
                    label="test",
                    bbox=[10, 20, 100, 150],
                    confidence=confidence
                )
    
    def test_annotation_to_dict(self):
        """Test converting annotation to dictionary."""
        metadata = {"source": "auto", "model": "yolo"}
        annotation = Annotation(
            image_path="test/image.jpg",
            label="person",
            bbox=[15, 25, 90, 180],
            confidence=0.87,
            metadata=metadata
        )
        
        result = annotation.to_dict()
        
        assert result["image_path"] == "test/image.jpg"
        assert result["label"] == "person"
        assert result["bbox"] == [15, 25, 90, 180]
        assert result["confidence"] == 0.87
        assert result["metadata"] == metadata
        assert "created_at" in result
        assert isinstance(result["created_at"], str)  # Should be ISO format
    
    def test_annotation_from_dict(self):
        """Test creating annotation from dictionary."""
        data = {
            "image_path": "test/image.jpg",
            "label": "car",
            "bbox": [20, 30, 120, 80],
            "confidence": 0.92,
            "metadata": {"source": "manual"},
            "created_at": "2024-01-01T12:00:00"
        }
        
        annotation = Annotation.from_dict(data)
        
        assert annotation.image_path == "test/image.jpg"
        assert annotation.label == "car"
        assert annotation.bbox == [20, 30, 120, 80]
        assert annotation.confidence == 0.92
        assert annotation.metadata == {"source": "manual"}
        assert isinstance(annotation.created_at, datetime)
    
    def test_annotation_to_coco_format(self):
        """Test converting annotation to COCO format."""
        annotation = Annotation(
            image_path="images/test.jpg",
            label="bicycle",
            bbox=[10, 15, 50, 75],
            confidence=0.88
        )
        
        coco_data = annotation.to_coco_format(
            annotation_id=1,
            image_id=100,
            category_id=2
        )
        
        expected = {
            "id": 1,
            "image_id": 100,
            "category_id": 2,
            "bbox": [10, 15, 50, 75],
            "area": 50 * 75,
            "iscrowd": 0,
            "score": 0.88
        }
        
        assert coco_data == expected
    
    def test_annotation_equality(self):
        """Test annotation equality comparison."""
        ann1 = Annotation(
            image_path="test.jpg",
            label="cat",
            bbox=[10, 20, 100, 150]
        )
        
        ann2 = Annotation(
            image_path="test.jpg",
            label="cat",
            bbox=[10, 20, 100, 150]
        )
        
        ann3 = Annotation(
            image_path="test.jpg",
            label="dog",  # Different label
            bbox=[10, 20, 100, 150]
        )
        
        # Same content should be equal (ignoring created_at)
        assert ann1 == ann2
        
        # Different content should not be equal
        assert ann1 != ann3
        
        # Different types should not be equal
        assert ann1 != "not an annotation"