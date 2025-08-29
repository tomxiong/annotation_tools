"""
Tests for ImageProcessor service.
"""
import pytest
from pathlib import Path
import tempfile
import numpy as np
from PIL import Image
import cv2

from src.services.image_processor import ImageProcessor
from src.core.exceptions import ValidationError


class TestImageProcessor:
    """Test cases for ImageProcessor service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ImageProcessor()
        
        # Create temporary test images
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create a test image
        self.test_image = np.zeros((100, 150, 3), dtype=np.uint8)
        self.test_image[20:80, 30:120] = [255, 0, 0]  # Red rectangle
        
        self.test_image_path = self.temp_path / "test_image.jpg"
        cv2.imwrite(str(self.test_image_path), self.test_image)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_image_processor_initialization(self):
        """Test ImageProcessor initialization."""
        processor = ImageProcessor()
        assert processor.supported_formats == {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        # Test with custom formats
        custom_formats = {'.jpg', '.png'}
        processor = ImageProcessor(supported_formats=custom_formats)
        assert processor.supported_formats == custom_formats
    
    def test_is_supported_format(self):
        """Test checking if image format is supported."""
        processor = ImageProcessor()
        
        # Supported formats
        assert processor.is_supported_format("image.jpg") is True
        assert processor.is_supported_format("image.jpeg") is True
        assert processor.is_supported_format("image.png") is True
        assert processor.is_supported_format("image.bmp") is True
        assert processor.is_supported_format("IMAGE.JPG") is True  # Case insensitive
        
        # Unsupported formats
        assert processor.is_supported_format("image.gif") is False
        assert processor.is_supported_format("image.webp") is False
        assert processor.is_supported_format("document.pdf") is False
        assert processor.is_supported_format("no_extension") is False
    
    def test_load_image_success(self):
        """Test successful image loading."""
        image = self.processor.load_image(str(self.test_image_path))
        
        assert isinstance(image, np.ndarray)
        assert image.shape == (100, 150, 3)
        assert image.dtype == np.uint8
    
    def test_load_image_file_not_found(self):
        """Test loading non-existent image."""
        with pytest.raises(ValidationError, match="Image file not found"):
            self.processor.load_image("non_existent.jpg")
    
    def test_load_image_unsupported_format(self):
        """Test loading unsupported image format."""
        # Create a text file with image extension
        fake_image = self.temp_path / "fake.jpg"
        fake_image.write_text("not an image")
        
        with pytest.raises(ValidationError, match="Failed to load image"):
            self.processor.load_image(str(fake_image))
    
    def test_get_image_info(self):
        """Test getting image information."""
        info = self.processor.get_image_info(str(self.test_image_path))
        
        assert info["width"] == 150
        assert info["height"] == 100
        assert info["channels"] == 3
        assert info["format"] == ".jpg"
        assert info["size_bytes"] > 0
        assert "file_name" in info
    
    def test_resize_image(self):
        """Test image resizing."""
        image = self.processor.load_image(str(self.test_image_path))
        
        # Resize to specific dimensions
        resized = self.processor.resize_image(image, target_size=(200, 300))
        assert resized.shape == (300, 200, 3)
        
        # Resize with max dimension
        resized = self.processor.resize_image(image, max_dimension=50)
        assert max(resized.shape[:2]) == 50
        
        # Resize with scale factor
        resized = self.processor.resize_image(image, scale_factor=0.5)
        assert resized.shape == (50, 75, 3)
    
    def test_resize_image_invalid_params(self):
        """Test image resizing with invalid parameters."""
        image = self.processor.load_image(str(self.test_image_path))
        
        # No resize parameters
        with pytest.raises(ValidationError, match="Must specify one of"):
            self.processor.resize_image(image)
        
        # Multiple parameters
        with pytest.raises(ValidationError, match="Cannot specify multiple"):
            self.processor.resize_image(image, target_size=(100, 100), scale_factor=0.5)
    
    def test_normalize_image(self):
        """Test image normalization."""
        image = self.processor.load_image(str(self.test_image_path))
        
        # Default normalization (0-1)
        normalized = self.processor.normalize_image(image)
        assert normalized.dtype == np.float32
        assert 0.0 <= normalized.min() <= normalized.max() <= 1.0
        
        # Custom range normalization
        normalized = self.processor.normalize_image(image, target_range=(-1, 1))
        assert -1.0 <= normalized.min() <= normalized.max() <= 1.0
        
        # ImageNet normalization
        normalized = self.processor.normalize_image(
            image, 
            mean=[0.485, 0.456, 0.406], 
            std=[0.229, 0.224, 0.225]
        )
        assert normalized.dtype == np.float32
    
    def test_crop_image(self):
        """Test image cropping."""
        image = self.processor.load_image(str(self.test_image_path))
        
        # Crop with bbox [x, y, width, height]
        cropped = self.processor.crop_image(image, bbox=[30, 20, 90, 60])
        assert cropped.shape == (60, 90, 3)
        
        # Crop with coordinates [x1, y1, x2, y2]
        cropped = self.processor.crop_image(image, coordinates=[30, 20, 120, 80])
        assert cropped.shape == (60, 90, 3)
    
    def test_crop_image_invalid_params(self):
        """Test image cropping with invalid parameters."""
        image = self.processor.load_image(str(self.test_image_path))
        
        # No crop parameters
        with pytest.raises(ValidationError, match="Must specify either bbox or coordinates"):
            self.processor.crop_image(image)
        
        # Both parameters
        with pytest.raises(ValidationError, match="Cannot specify both"):
            self.processor.crop_image(image, bbox=[0, 0, 50, 50], coordinates=[0, 0, 50, 50])
        
        # Invalid bbox
        with pytest.raises(ValidationError, match="Bounding box extends beyond image"):
            self.processor.crop_image(image, bbox=[0, 0, 200, 200])
    
    def test_apply_augmentation(self):
        """Test image augmentation."""
        image = self.processor.load_image(str(self.test_image_path))
        
        # Horizontal flip
        flipped = self.processor.apply_augmentation(image, "horizontal_flip")
        assert flipped.shape == image.shape
        
        # Rotation
        rotated = self.processor.apply_augmentation(image, "rotate", angle=90)
        assert rotated.shape[:2] == (150, 100)  # Dimensions swapped
        
        # Brightness adjustment
        bright = self.processor.apply_augmentation(image, "brightness", factor=1.2)
        assert bright.shape == image.shape
        
        # Gaussian blur
        blurred = self.processor.apply_augmentation(image, "blur", kernel_size=5)
        assert blurred.shape == image.shape
    
    def test_apply_augmentation_invalid(self):
        """Test invalid augmentation."""
        image = self.processor.load_image(str(self.test_image_path))
        
        with pytest.raises(ValidationError, match="Unknown augmentation"):
            self.processor.apply_augmentation(image, "invalid_augmentation")
    
    def test_save_image(self):
        """Test saving image."""
        image = self.processor.load_image(str(self.test_image_path))
        
        # Save as different format
        output_path = self.temp_path / "output.png"
        self.processor.save_image(image, str(output_path))
        
        assert output_path.exists()
        
        # Verify saved image
        loaded = self.processor.load_image(str(output_path))
        assert loaded.shape == image.shape
    
    def test_batch_process_images(self):
        """Test batch processing of images."""
        # Create multiple test images
        image_paths = []
        for i in range(3):
            path = self.temp_path / f"test_{i}.jpg"
            cv2.imwrite(str(path), self.test_image)
            image_paths.append(str(path))
        
        # Define processing function
        def resize_func(img_path):
            image = self.processor.load_image(img_path)
            return self.processor.resize_image(image, target_size=(50, 50))
        
        # Batch process
        results = self.processor.batch_process(image_paths, resize_func)
        
        assert len(results) == 3
        for result in results:
            assert result["success"] is True
            assert result["processed_image"].shape == (50, 50, 3)
    
    def test_batch_process_with_errors(self):
        """Test batch processing with some errors."""
        # Mix of valid and invalid paths
        image_paths = [
            str(self.test_image_path),
            "non_existent.jpg",
            str(self.test_image_path)
        ]
        
        def load_func(img_path):
            return self.processor.load_image(img_path)
        
        results = self.processor.batch_process(image_paths, load_func)
        
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "error" in results[1]
        assert results[2]["success"] is True
    
    def test_get_batch_statistics(self):
        """Test getting batch processing statistics."""
        results = [
            {"success": True, "processing_time": 0.1},
            {"success": False, "error": "File not found"},
            {"success": True, "processing_time": 0.2},
            {"success": True, "processing_time": 0.15}
        ]
        
        stats = self.processor.get_batch_statistics(results)
        
        assert stats["total_images"] == 4
        assert stats["successful"] == 3
        assert stats["failed"] == 1
        assert stats["success_rate"] == 0.75
        assert abs(stats["average_processing_time"] - 0.15) < 1e-10  # (0.1 + 0.2 + 0.15) / 3
