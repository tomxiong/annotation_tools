"""
Tests for Dataset data model.
"""
import pytest
from pathlib import Path
import tempfile
import json
from datetime import datetime

from src.models.dataset import Dataset
from src.models.annotation import Annotation
from src.core.exceptions import ValidationError


class TestDataset:
    """Test cases for Dataset class."""
    
    def test_dataset_creation_with_required_fields(self):
        """Test creating dataset with only required fields."""
        dataset = Dataset(
            name="test_dataset",
            root_path="/path/to/images"
        )
        
        assert dataset.name == "test_dataset"
        assert dataset.root_path == "/path/to/images"
        assert dataset.annotations == []
        assert dataset.metadata == {}
        assert isinstance(dataset.created_at, datetime)
    
    def test_dataset_creation_with_all_fields(self):
        """Test creating dataset with all fields."""
        annotations = [
            Annotation("img1.jpg", "cat", [10, 20, 100, 150]),
            Annotation("img2.jpg", "dog", [5, 15, 80, 120])
        ]
        metadata = {"source": "manual", "version": "1.0"}
        created_time = datetime.now()
        
        dataset = Dataset(
            name="full_dataset",
            root_path="/data/images",
            annotations=annotations,
            metadata=metadata,
            created_at=created_time
        )
        
        assert dataset.name == "full_dataset"
        assert dataset.root_path == "/data/images"
        assert len(dataset.annotations) == 2
        assert dataset.metadata == metadata
        assert dataset.created_at == created_time
    
    def test_dataset_add_annotation(self):
        """Test adding annotations to dataset."""
        dataset = Dataset("test", "/path")
        
        annotation1 = Annotation("img1.jpg", "cat", [10, 20, 100, 150])
        annotation2 = Annotation("img2.jpg", "dog", [5, 15, 80, 120])
        
        dataset.add_annotation(annotation1)
        assert len(dataset.annotations) == 1
        assert dataset.annotations[0] == annotation1
        
        dataset.add_annotation(annotation2)
        assert len(dataset.annotations) == 2
        assert dataset.annotations[1] == annotation2
    
    def test_dataset_remove_annotation(self):
        """Test removing annotations from dataset."""
        annotation1 = Annotation("img1.jpg", "cat", [10, 20, 100, 150])
        annotation2 = Annotation("img2.jpg", "dog", [5, 15, 80, 120])
        
        dataset = Dataset("test", "/path", annotations=[annotation1, annotation2])
        
        # Remove existing annotation
        result = dataset.remove_annotation(annotation1)
        assert result is True
        assert len(dataset.annotations) == 1
        assert annotation1 not in dataset.annotations
        
        # Try to remove non-existing annotation
        result = dataset.remove_annotation(annotation1)
        assert result is False
        assert len(dataset.annotations) == 1
    
    def test_dataset_get_annotations_by_label(self):
        """Test filtering annotations by label."""
        annotations = [
            Annotation("img1.jpg", "cat", [10, 20, 100, 150]),
            Annotation("img2.jpg", "dog", [5, 15, 80, 120]),
            Annotation("img3.jpg", "cat", [15, 25, 90, 140]),
            Annotation("img4.jpg", "bird", [20, 30, 60, 80])
        ]
        
        dataset = Dataset("test", "/path", annotations=annotations)
        
        cat_annotations = dataset.get_annotations_by_label("cat")
        assert len(cat_annotations) == 2
        assert all(ann.label == "cat" for ann in cat_annotations)
        
        dog_annotations = dataset.get_annotations_by_label("dog")
        assert len(dog_annotations) == 1
        assert dog_annotations[0].label == "dog"
        
        # Non-existing label
        fish_annotations = dataset.get_annotations_by_label("fish")
        assert len(fish_annotations) == 0
    
    def test_dataset_get_unique_labels(self):
        """Test getting unique labels from dataset."""
        annotations = [
            Annotation("img1.jpg", "cat", [10, 20, 100, 150]),
            Annotation("img2.jpg", "dog", [5, 15, 80, 120]),
            Annotation("img3.jpg", "cat", [15, 25, 90, 140]),
            Annotation("img4.jpg", "bird", [20, 30, 60, 80]),
            Annotation("img5.jpg", "dog", [25, 35, 70, 90])
        ]
        
        dataset = Dataset("test", "/path", annotations=annotations)
        
        unique_labels = dataset.get_unique_labels()
        assert len(unique_labels) == 3
        assert set(unique_labels) == {"cat", "dog", "bird"}
    
    def test_dataset_get_statistics(self):
        """Test getting dataset statistics."""
        annotations = [
            Annotation("img1.jpg", "cat", [10, 20, 100, 150]),
            Annotation("img2.jpg", "dog", [5, 15, 80, 120]),
            Annotation("img3.jpg", "cat", [15, 25, 90, 140]),
            Annotation("img4.jpg", "bird", [20, 30, 60, 80])
        ]
        
        dataset = Dataset("test", "/path", annotations=annotations)
        
        stats = dataset.get_statistics()
        
        assert stats["total_annotations"] == 4
        assert stats["unique_labels"] == 3
        assert stats["label_counts"]["cat"] == 2
        assert stats["label_counts"]["dog"] == 1
        assert stats["label_counts"]["bird"] == 1
        assert stats["unique_images"] == 4  # All different images
    
    def test_dataset_to_dict(self):
        """Test converting dataset to dictionary."""
        annotations = [
            Annotation("img1.jpg", "cat", [10, 20, 100, 150]),
            Annotation("img2.jpg", "dog", [5, 15, 80, 120])
        ]
        metadata = {"source": "test", "version": "1.0"}
        
        dataset = Dataset("test_dataset", "/data", annotations, metadata)
        
        result = dataset.to_dict()
        
        assert result["name"] == "test_dataset"
        assert result["root_path"] == "/data"
        assert len(result["annotations"]) == 2
        assert result["metadata"] == metadata
        assert "created_at" in result
        assert isinstance(result["created_at"], str)
    
    def test_dataset_from_dict(self):
        """Test creating dataset from dictionary."""
        data = {
            "name": "test_dataset",
            "root_path": "/data/images",
            "annotations": [
                {
                    "image_path": "img1.jpg",
                    "label": "cat",
                    "bbox": [10, 20, 100, 150],
                    "confidence": 0.9,
                    "metadata": {},
                    "created_at": "2024-01-01T12:00:00"
                }
            ],
            "metadata": {"source": "manual"},
            "created_at": "2024-01-01T10:00:00"
        }
        
        dataset = Dataset.from_dict(data)
        
        assert dataset.name == "test_dataset"
        assert dataset.root_path == "/data/images"
        assert len(dataset.annotations) == 1
        assert dataset.annotations[0].label == "cat"
        assert dataset.metadata == {"source": "manual"}
        assert isinstance(dataset.created_at, datetime)
    
    def test_dataset_save_and_load_json(self):
        """Test saving and loading dataset to/from JSON file."""
        annotations = [
            Annotation("img1.jpg", "cat", [10, 20, 100, 150]),
            Annotation("img2.jpg", "dog", [5, 15, 80, 120])
        ]
        
        dataset = Dataset("test_dataset", "/data", annotations)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save to JSON
            dataset.save_to_json(temp_path)
            
            # Load from JSON
            loaded_dataset = Dataset.load_from_json(temp_path)
            
            assert loaded_dataset.name == dataset.name
            assert loaded_dataset.root_path == dataset.root_path
            assert len(loaded_dataset.annotations) == len(dataset.annotations)
            assert loaded_dataset.annotations[0].label == "cat"
            assert loaded_dataset.annotations[1].label == "dog"
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_dataset_export_to_coco(self):
        """Test exporting dataset to COCO format."""
        annotations = [
            Annotation("img1.jpg", "cat", [10, 20, 100, 150]),
            Annotation("img2.jpg", "dog", [5, 15, 80, 120]),
            Annotation("img1.jpg", "bird", [50, 60, 30, 40])  # Same image, different object
        ]
        
        dataset = Dataset("test_dataset", "/data", annotations)
        
        coco_data = dataset.export_to_coco()
        
        # Check basic structure
        assert "images" in coco_data
        assert "annotations" in coco_data
        assert "categories" in coco_data
        
        # Check images (should be 2 unique images)
        assert len(coco_data["images"]) == 2
        
        # Check annotations (should be 3)
        assert len(coco_data["annotations"]) == 3
        
        # Check categories (should be 3 unique labels)
        assert len(coco_data["categories"]) == 3
        category_names = [cat["name"] for cat in coco_data["categories"]]
        assert set(category_names) == {"cat", "dog", "bird"}