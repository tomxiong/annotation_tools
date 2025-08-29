"""
Dataset data model for managing collections of annotations.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from models.annotation import Annotation
from core.exceptions import ValidationError


@dataclass
class Dataset:
    """
    Represents a dataset containing multiple image annotations.
    
    Attributes:
        name: Name of the dataset
        root_path: Root path where images are stored
        annotations: List of annotations in the dataset
        metadata: Additional metadata dictionary
        created_at: Timestamp when dataset was created
    """
    name: str
    root_path: str
    annotations: List[Annotation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_annotation(self, annotation: Annotation) -> None:
        """
        Add an annotation to the dataset.
        
        Args:
            annotation: Annotation to add
        """
        if not isinstance(annotation, Annotation):
            raise ValidationError("Only Annotation objects can be added to dataset")
        
        self.annotations.append(annotation)
    
    def remove_annotation(self, annotation: Annotation) -> bool:
        """
        Remove an annotation from the dataset.
        
        Args:
            annotation: Annotation to remove
            
        Returns:
            True if annotation was removed, False if not found
        """
        try:
            self.annotations.remove(annotation)
            return True
        except ValueError:
            return False
    
    def get_annotations_by_label(self, label: str) -> List[Annotation]:
        """
        Get all annotations with a specific label.
        
        Args:
            label: Label to filter by
            
        Returns:
            List of annotations with the specified label
        """
        return [ann for ann in self.annotations if ann.label == label]
    
    def get_unique_labels(self) -> List[str]:
        """
        Get all unique labels in the dataset.
        
        Returns:
            List of unique labels
        """
        labels = set(ann.label for ann in self.annotations)
        return sorted(list(labels))
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get dataset statistics.
        
        Returns:
            Dictionary containing dataset statistics
        """
        unique_labels = self.get_unique_labels()
        label_counts = {}
        unique_images = set()
        
        for annotation in self.annotations:
            # Count labels
            if annotation.label in label_counts:
                label_counts[annotation.label] += 1
            else:
                label_counts[annotation.label] = 1
            
            # Track unique images
            unique_images.add(annotation.image_path)
        
        return {
            "total_annotations": len(self.annotations),
            "unique_labels": len(unique_labels),
            "label_counts": label_counts,
            "unique_images": len(unique_images)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert dataset to dictionary format.
        
        Returns:
            Dictionary representation of the dataset
        """
        return {
            "name": self.name,
            "root_path": self.root_path,
            "annotations": [ann.to_dict() for ann in self.annotations],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dataset':
        """
        Create dataset from dictionary data.
        
        Args:
            data: Dictionary containing dataset data
            
        Returns:
            Dataset instance
        """
        # Parse created_at if it's a string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        # Parse annotations
        annotations = []
        for ann_data in data.get("annotations", []):
            annotations.append(Annotation.from_dict(ann_data))
        
        return cls(
            name=data["name"],
            root_path=data["root_path"],
            annotations=annotations,
            metadata=data.get("metadata", {}),
            created_at=created_at
        )
    
    def save_to_json(self, file_path: str) -> None:
        """
        Save dataset to JSON file.
        
        Args:
            file_path: Path to save the JSON file
        """
        data = self.to_dict()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_json(cls, file_path: str) -> 'Dataset':
        """
        Load dataset from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dataset instance
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def export_to_coco(self) -> Dict[str, Any]:
        """
        Export dataset to COCO format.
        
        Returns:
            Dictionary in COCO format
        """
        # Get unique images and labels
        unique_images = {}
        unique_labels = self.get_unique_labels()
        
        # Create image entries
        image_id = 1
        for annotation in self.annotations:
            if annotation.image_path not in unique_images:
                unique_images[annotation.image_path] = {
                    "id": image_id,
                    "file_name": annotation.image_path,
                    "width": 0,  # Would need actual image dimensions
                    "height": 0  # Would need actual image dimensions
                }
                image_id += 1
        
        # Create category entries
        categories = []
        label_to_id = {}
        for i, label in enumerate(unique_labels, 1):
            categories.append({
                "id": i,
                "name": label,
                "supercategory": ""
            })
            label_to_id[label] = i
        
        # Create annotation entries
        coco_annotations = []
        annotation_id = 1
        
        for annotation in self.annotations:
            image_id = unique_images[annotation.image_path]["id"]
            category_id = label_to_id[annotation.label]
            
            coco_ann = annotation.to_coco_format(
                annotation_id=annotation_id,
                image_id=image_id,
                category_id=category_id
            )
            
            coco_annotations.append(coco_ann)
            annotation_id += 1
        
        return {
            "info": {
                "description": f"Dataset: {self.name}",
                "version": "1.0",
                "year": self.created_at.year,
                "contributor": "Batch Annotation Tool",
                "date_created": self.created_at.isoformat()
            },
            "images": list(unique_images.values()),
            "annotations": coco_annotations,
            "categories": categories
        }
    
    def __len__(self) -> int:
        """Return number of annotations in dataset."""
        return len(self.annotations)
    
    def __iter__(self):
        """Make dataset iterable over annotations."""
        return iter(self.annotations)