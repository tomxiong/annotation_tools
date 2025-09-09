"""
Image processing service for loading, transforming, and saving images.
"""
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import numpy as np
import cv2
from PIL import Image

from src.core.exceptions import ValidationError


class ImageProcessor:
    """
    Service for processing images with various transformations and utilities.
    
    Supports loading, resizing, normalization, cropping, augmentation, and batch processing.
    """
    
    def __init__(self, supported_formats: Optional[set] = None):
        """
        Initialize ImageProcessor.
        
        Args:
            supported_formats: Set of supported image file extensions
        """
        self.supported_formats = supported_formats or {
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'
        }
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if image format is supported.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            True if format is supported, False otherwise
        """
        path = Path(file_path)
        return path.suffix.lower() in self.supported_formats
    
    def load_image(self, file_path: str) -> np.ndarray:
        """
        Load image from file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Image as numpy array in BGR format
            
        Raises:
            ValidationError: If file not found or cannot be loaded
        """
        path = Path(file_path)
        
        if not path.exists():
            raise ValidationError(f"Image file not found: {file_path}")
        
        try:
            # Use OpenCV to load image
            image = cv2.imread(str(path))
            
            if image is None:
                raise ValidationError(f"Failed to load image: {file_path}")
            
            return image
            
        except Exception as e:
            raise ValidationError(f"Failed to load image {file_path}: {str(e)}")
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary containing image information
        """
        path = Path(file_path)
        image = self.load_image(file_path)
        
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        
        return {
            "file_name": path.name,
            "width": width,
            "height": height,
            "channels": channels,
            "format": path.suffix.lower(),
            "size_bytes": path.stat().st_size
        }
    
    def resize_image(
        self, 
        image: np.ndarray, 
        target_size: Optional[Tuple[int, int]] = None,
        max_dimension: Optional[int] = None,
        scale_factor: Optional[float] = None
    ) -> np.ndarray:
        """
        Resize image using different methods.
        
        Args:
            image: Input image
            target_size: Target size as (width, height)
            max_dimension: Maximum dimension (maintains aspect ratio)
            scale_factor: Scale factor for resizing
            
        Returns:
            Resized image
            
        Raises:
            ValidationError: If invalid parameters provided
        """
        params_count = sum(x is not None for x in [target_size, max_dimension, scale_factor])
        
        if params_count == 0:
            raise ValidationError("Must specify one of: target_size, max_dimension, or scale_factor")
        
        if params_count > 1:
            raise ValidationError("Cannot specify multiple resize parameters")
        
        height, width = image.shape[:2]
        
        if target_size is not None:
            new_width, new_height = target_size
            
        elif max_dimension is not None:
            if width > height:
                new_width = max_dimension
                new_height = int(height * max_dimension / width)
            else:
                new_height = max_dimension
                new_width = int(width * max_dimension / height)
                
        elif scale_factor is not None:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
        
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    
    def normalize_image(
        self, 
        image: np.ndarray,
        target_range: Tuple[float, float] = (0.0, 1.0),
        mean: Optional[List[float]] = None,
        std: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        Normalize image pixel values.
        
        Args:
            image: Input image
            target_range: Target range for normalization
            mean: Mean values for each channel (for ImageNet-style normalization)
            std: Standard deviation values for each channel
            
        Returns:
            Normalized image as float32
        """
        # Convert to float32
        normalized = image.astype(np.float32)
        
        if mean is not None and std is not None:
            # ImageNet-style normalization
            normalized = normalized / 255.0  # Scale to 0-1 first
            
            mean = np.array(mean, dtype=np.float32)
            std = np.array(std, dtype=np.float32)
            
            normalized = (normalized - mean) / std
            
        else:
            # Simple range normalization
            min_val, max_val = target_range
            normalized = normalized / 255.0  # Scale to 0-1
            normalized = normalized * (max_val - min_val) + min_val
        
        return normalized
    
    def crop_image(
        self, 
        image: np.ndarray,
        bbox: Optional[List[int]] = None,
        coordinates: Optional[List[int]] = None
    ) -> np.ndarray:
        """
        Crop image using bounding box or coordinates.
        
        Args:
            image: Input image
            bbox: Bounding box as [x, y, width, height]
            coordinates: Coordinates as [x1, y1, x2, y2]
            
        Returns:
            Cropped image
            
        Raises:
            ValidationError: If invalid parameters provided
        """
        if bbox is None and coordinates is None:
            raise ValidationError("Must specify either bbox or coordinates")
        
        if bbox is not None and coordinates is not None:
            raise ValidationError("Cannot specify both bbox and coordinates")
        
        height, width = image.shape[:2]
        
        if bbox is not None:
            x, y, w, h = bbox
            x2, y2 = x + w, y + h
        else:
            x, y, x2, y2 = coordinates
        
        # Validate bounds
        if x < 0 or y < 0 or x2 > width or y2 > height or x >= x2 or y >= y2:
            raise ValidationError("Bounding box extends beyond image boundaries")
        
        return image[y:y2, x:x2]
    
    def apply_augmentation(
        self, 
        image: np.ndarray, 
        augmentation_type: str, 
        **kwargs
    ) -> np.ndarray:
        """
        Apply augmentation to image.
        
        Args:
            image: Input image
            augmentation_type: Type of augmentation
            **kwargs: Additional parameters for augmentation
            
        Returns:
            Augmented image
            
        Raises:
            ValidationError: If unknown augmentation type
        """
        if augmentation_type == "horizontal_flip":
            return cv2.flip(image, 1)
        
        elif augmentation_type == "vertical_flip":
            return cv2.flip(image, 0)
        
        elif augmentation_type == "rotate":
            angle = kwargs.get("angle", 0)
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Calculate new dimensions
            cos_val = abs(rotation_matrix[0, 0])
            sin_val = abs(rotation_matrix[0, 1])
            new_width = int(height * sin_val + width * cos_val)
            new_height = int(height * cos_val + width * sin_val)
            
            # Adjust translation
            rotation_matrix[0, 2] += (new_width - width) / 2
            rotation_matrix[1, 2] += (new_height - height) / 2
            
            return cv2.warpAffine(image, rotation_matrix, (new_width, new_height))
        
        elif augmentation_type == "brightness":
            factor = kwargs.get("factor", 1.0)
            return cv2.convertScaleAbs(image, alpha=factor, beta=0)
        
        elif augmentation_type == "contrast":
            factor = kwargs.get("factor", 1.0)
            return cv2.convertScaleAbs(image, alpha=factor, beta=0)
        
        elif augmentation_type == "blur":
            kernel_size = kwargs.get("kernel_size", 5)
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        
        else:
            raise ValidationError(f"Unknown augmentation type: {augmentation_type}")
    
    def save_image(self, image: np.ndarray, file_path: str, quality: int = 95) -> None:
        """
        Save image to file.
        
        Args:
            image: Image to save
            file_path: Output file path
            quality: JPEG quality (0-100)
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set compression parameters
        if path.suffix.lower() in ['.jpg', '.jpeg']:
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        elif path.suffix.lower() == '.png':
            params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
        else:
            params = []
        
        success = cv2.imwrite(str(path), image, params)
        
        if not success:
            raise ValidationError(f"Failed to save image: {file_path}")
    
    def batch_process(
        self, 
        image_paths: List[str], 
        processing_func: Callable[[str], np.ndarray]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            processing_func: Function to apply to each image
            
        Returns:
            List of processing results
        """
        results = []
        
        for image_path in image_paths:
            start_time = time.time()
            
            try:
                processed_image = processing_func(image_path)
                processing_time = time.time() - start_time
                
                results.append({
                    "image_path": image_path,
                    "success": True,
                    "processed_image": processed_image,
                    "processing_time": processing_time
                })
                
            except Exception as e:
                processing_time = time.time() - start_time
                
                results.append({
                    "image_path": image_path,
                    "success": False,
                    "error": str(e),
                    "processing_time": processing_time
                })
        
        return results
    
    def get_batch_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics from batch processing results.
        
        Args:
            results: List of processing results
            
        Returns:
            Dictionary containing batch statistics
        """
        total_images = len(results)
        successful = sum(1 for r in results if r["success"])
        failed = total_images - successful
        
        success_rate = successful / total_images if total_images > 0 else 0.0
        
        # Calculate average processing time for successful images
        successful_times = [r["processing_time"] for r in results if r["success"]]
        avg_processing_time = sum(successful_times) / len(successful_times) if successful_times else 0.0
        
        return {
            "total_images": total_images,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time
        }