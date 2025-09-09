"""
Annotation data model for storing image annotation information.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from src.core.exceptions import ValidationError


@dataclass
class Annotation:
    """
    Represents a single image annotation with bounding box and metadata.
    
    Attributes:
        image_path: Path to the annotated image
        label: Classification label for the annotation
        bbox: Bounding box coordinates [x, y, width, height]
        confidence: Confidence score (0.0-1.0) if available
        metadata: Additional metadata dictionary
        created_at: Timestamp when annotation was created
    """
    image_path: str
    label: str
    bbox: List[int]
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate annotation data after initialization."""
        self._validate_bbox()
        self._validate_confidence()
    
    def _validate_bbox(self):
        """Validate bounding box format and values."""
        if not isinstance(self.bbox, list) or len(self.bbox) != 4:
            raise ValidationError("Bounding box must be a list of 4 integers [x, y, width, height]")
        
        x, y, width, height = self.bbox
        
        if not all(isinstance(coord, (int, float)) for coord in self.bbox):
            raise ValidationError("Bounding box coordinates must be numeric")
        
        if x < 0 or y < 0:
            raise ValidationError("Bounding box x and y coordinates must be non-negative")
        
        if width <= 0 or height <= 0:
            raise ValidationError("Bounding box width and height must be positive")
    
    def _validate_confidence(self):
        """Validate confidence score range."""
        if self.confidence is not None:
            if not isinstance(self.confidence, (int, float)):
                raise ValidationError("Confidence must be a number")
            
            if not (0.0 <= self.confidence <= 1.0):
                raise ValidationError("Confidence must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert annotation to dictionary format.
        
        Returns:
            Dictionary representation of the annotation
        """
        return {
            "image_path": self.image_path,
            "label": self.label,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Annotation':
        """
        Create annotation from dictionary data.
        
        Args:
            data: Dictionary containing annotation data
            
        Returns:
            Annotation instance
        """
        # Parse created_at if it's a string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            image_path=data["image_path"],
            label=data["label"],
            bbox=data["bbox"],
            confidence=data.get("confidence"),
            metadata=data.get("metadata", {}),
            created_at=created_at
        )
    
    def to_coco_format(self, annotation_id: int, image_id: int, category_id: int) -> Dict[str, Any]:
        """
        Convert annotation to COCO format.
        
        Args:
            annotation_id: Unique annotation ID
            image_id: ID of the associated image
            category_id: ID of the annotation category
            
        Returns:
            Dictionary in COCO annotation format
        """
        x, y, width, height = self.bbox
        
        coco_annotation = {
            "id": annotation_id,
            "image_id": image_id,
            "category_id": category_id,
            "bbox": self.bbox,
            "area": width * height,
            "iscrowd": 0
        }
        
        # Add confidence score if available
        if self.confidence is not None:
            coco_annotation["score"] = self.confidence
        
        return coco_annotation
    
    def __eq__(self, other) -> bool:
        """
        Compare annotations for equality (excluding created_at).
        
        Args:
            other: Another annotation to compare with
            
        Returns:
            True if annotations are equal (ignoring timestamps)
        """
        if not isinstance(other, Annotation):
            return False
        
        return (
            self.image_path == other.image_path and
            self.label == other.label and
            self.bbox == other.bbox and
            self.confidence == other.confidence and
            self.metadata == other.metadata
        )
    
    def __hash__(self) -> int:
        """Make annotation hashable (excluding mutable metadata and created_at)."""
        return hash((
            self.image_path,
            self.label,
            tuple(self.bbox),
            self.confidence
        ))