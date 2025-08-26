"""
Tests for AnnotationEngine service.
"""
import pytest
from pathlib import Path
import tempfile
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock

from src.services.annotation_engine import AnnotationEngine, ModelType
from src.models.annotation import Annotation
from src.models.dataset import Dataset
from src.models.batch_job import BatchJob, JobStatus
from src.services.image_processor import ImageProcessor
from src.core.config import Config
from src.core.logger import Logger
from src.core.exceptions import ValidationError


class TestAnnotationEngine:
    """Test cases for AnnotationEngine service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test config
        config_data = {
            "models": {
                "yolo_v8": {
                    "path": "yolov8n.pt",
                    "confidence_threshold": 0.5,
                    "device": "cpu"
                }
            },
            "processing": {
                "batch_size": 32,
                "max_workers": 4
            }
        }
        
        self.config = Config()
        for key, value in config_data.items():
            setattr(self.config, key, value)
        
        # Create test logger
        with patch('src.core.logger.Logger.__enter__'), \
             patch('src.core.logger.Logger.__exit__'):
            self.logger = Logger("test", str(self.temp_path))
        
        # Create test images
        self.test_image = np.zeros((100, 150, 3), dtype=np.uint8)
        self.test_image[20:80, 30:120] = [255, 0, 0]  # Red rectangle
        
        self.test_image_path = self.temp_path / "test_image.jpg"
        cv2.imwrite(str(self.test_image_path), self.test_image)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_annotation_engine_initialization(self):
        """Test AnnotationEngine initialization."""
        engine = AnnotationEngine(self.config, self.logger)
        
        assert engine.config == self.config
        assert engine.logger == self.logger
        assert isinstance(engine.image_processor, ImageProcessor)
        assert engine.models == {}
        assert engine.current_job is None
    
    def test_model_type_enum(self):
        """Test ModelType enum values."""
        assert ModelType.YOLO_V8.value == "yolo_v8"
        assert ModelType.DETECTRON2.value == "detectron2"
        assert ModelType.CUSTOM.value == "custom"
    
    @patch('ultralytics.YOLO')
    def test_load_model_yolo_success(self, mock_yolo_class):
        """Test successful YOLO model loading."""
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model
        
        engine = AnnotationEngine(self.config, self.logger)
        
        result = engine.load_model("yolo_v8", ModelType.YOLO_V8)
        
        assert result is True
        assert "yolo_v8" in engine.models
        assert engine.models["yolo_v8"] == mock_model
        mock_yolo_class.assert_called_once_with("yolov8n.pt")
    
    @patch('ultralytics.YOLO')
    def test_load_model_yolo_failure(self, mock_yolo_class):
        """Test YOLO model loading failure."""
        mock_yolo_class.side_effect = Exception("Model not found")
        
        engine = AnnotationEngine(self.config, self.logger)
        
        result = engine.load_model("yolo_v8", ModelType.YOLO_V8)
        
        assert result is False
        assert "yolo_v8" not in engine.models
    
    def test_load_model_unsupported_type(self):
        """Test loading unsupported model type."""
        engine = AnnotationEngine(self.config, self.logger)
        
        result = engine.load_model("test", "unsupported_type")
        assert result is False
    
    @patch('ultralytics.YOLO')
    def test_predict_single_image_success(self, mock_yolo_class):
        """Test successful single image prediction."""
        # Mock YOLO model and results
        mock_result = Mock()
        mock_result.boxes.xyxy = np.array([[10, 20, 110, 120]])  # x1, y1, x2, y2
        mock_result.boxes.conf = np.array([0.85])
        mock_result.boxes.cls = np.array([0])
        mock_result.names = {0: "person"}
        
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model
        
        engine = AnnotationEngine(self.config, self.logger)
        engine.load_model("yolo_v8", ModelType.YOLO_V8)
        
        annotations = engine.predict_single_image(
            str(self.test_image_path), 
            "yolo_v8"
        )
        
        assert len(annotations) == 1
        annotation = annotations[0]
        assert annotation.image_path == str(self.test_image_path)
        assert annotation.label == "person"
        assert annotation.bbox == [10, 20, 100, 100]  # [x, y, width, height]
        assert annotation.confidence == 0.85
    
    def test_predict_single_image_model_not_loaded(self):
        """Test prediction with unloaded model."""
        engine = AnnotationEngine(self.config, self.logger)
        
        with pytest.raises(ValidationError, match="Model .* not loaded"):
            engine.predict_single_image(str(self.test_image_path), "yolo_v8")
    
    def test_predict_single_image_file_not_found(self):
        """Test prediction with non-existent image."""
        engine = AnnotationEngine(self.config, self.logger)
        
        with pytest.raises(ValidationError, match="Image file not found"):
            engine.predict_single_image("non_existent.jpg", "yolo_v8")
    
    @patch('ultralytics.YOLO')
    def test_process_batch_job_success(self, mock_yolo_class):
        """Test successful batch job processing."""
        # Create test dataset
        dataset = Dataset("test_dataset", str(self.temp_path))
        
        # Create additional test images
        for i in range(3):
            img_path = self.temp_path / f"test_{i}.jpg"
            cv2.imwrite(str(img_path), self.test_image)
        
        # Create batch job
        job = BatchJob("job_001", dataset, "yolo_v8")
        job.total_images = 3
        
        # Mock YOLO model
        mock_result = Mock()
        mock_result.boxes.xyxy = np.array([[10, 20, 110, 120]])
        mock_result.boxes.conf = np.array([0.85])
        mock_result.boxes.cls = np.array([0])
        mock_result.names = {0: "person"}
        
        mock_model = Mock()
        mock_model.return_value = [mock_result]
        mock_yolo_class.return_value = mock_model
        
        engine = AnnotationEngine(self.config, self.logger)
        engine.load_model("yolo_v8", ModelType.YOLO_V8)
        
        # Process batch job
        image_paths = [str(self.temp_path / f"test_{i}.jpg") for i in range(3)]
        result = engine.process_batch_job(job, image_paths)
        
        assert result is True
        assert job.status == JobStatus.COMPLETED
        assert job.progress == 1.0
        assert job.processed_images == 3
        assert job.failed_images == 0
        assert len(job.results) == 3
    
    @patch('ultralytics.YOLO')
    def test_process_batch_job_with_failures(self, mock_yolo_class):
        """Test batch job processing with some failures."""
        # Create test dataset
        dataset = Dataset("test_dataset", str(self.temp_path))
        job = BatchJob("job_001", dataset, "yolo_v8")
        job.total_images = 3
        
        # Mock YOLO model that fails on second image
        def mock_predict(image_path):
            if "test_1" in str(image_path):
                raise Exception("Processing failed")
            
            mock_result = Mock()
            mock_result.boxes.xyxy = np.array([[10, 20, 110, 120]])
            mock_result.boxes.conf = np.array([0.85])
            mock_result.boxes.cls = np.array([0])
            mock_result.names = {0: "person"}
            return [mock_result]
        
        mock_model = Mock()
        mock_model.side_effect = mock_predict
        mock_yolo_class.return_value = mock_model
        
        engine = AnnotationEngine(self.config, self.logger)
        engine.load_model("yolo_v8", ModelType.YOLO_V8)
        
        # Process batch job
        image_paths = [
            str(self.test_image_path),
            str(self.temp_path / "test_1.jpg"),  # This will fail
            str(self.test_image_path)
        ]
        
        result = engine.process_batch_job(job, image_paths)
        
        assert result is True
        assert job.status == JobStatus.COMPLETED
        assert job.processed_images == 3
        assert job.failed_images == 1
        assert len(job.results) == 2  # Only successful predictions
    
    def test_process_batch_job_model_not_loaded(self):
        """Test batch job processing with unloaded model."""
        dataset = Dataset("test_dataset", str(self.temp_path))
        job = BatchJob("job_001", dataset, "yolo_v8")
        
        engine = AnnotationEngine(self.config, self.logger)
        
        result = engine.process_batch_job(job, [str(self.test_image_path)])
        
        assert result is False
        assert job.status == JobStatus.FAILED
        assert "Model yolo_v8 not loaded" in job.error_message
    
    def test_get_model_info(self):
        """Test getting model information."""
        engine = AnnotationEngine(self.config, self.logger)
        
        info = engine.get_model_info()
        
        assert "loaded_models" in info
        assert "available_models" in info
        assert info["loaded_models"] == []
        assert "yolo_v8" in info["available_models"]
    
    @patch('ultralytics.YOLO')
    def test_get_model_info_with_loaded_model(self, mock_yolo_class):
        """Test getting model information with loaded models."""
        mock_model = Mock()
        mock_yolo_class.return_value = mock_model
        
        engine = AnnotationEngine(self.config, self.logger)
        engine.load_model("yolo_v8", ModelType.YOLO_V8)
        
        info = engine.get_model_info()
        
        assert "yolo_v8" in info["loaded_models"]
    
    def test_unload_model(self):
        """Test unloading a model."""
        engine = AnnotationEngine(self.config, self.logger)
        engine.models["test_model"] = Mock()
        
        result = engine.unload_model("test_model")
        
        assert result is True
        assert "test_model" not in engine.models
        
        # Test unloading non-existent model
        result = engine.unload_model("non_existent")
        assert result is False
    
    def test_cancel_current_job(self):
        """Test cancelling current job."""
        dataset = Dataset("test_dataset", str(self.temp_path))
        job = BatchJob("job_001", dataset, "yolo_v8")
        job.start()
        
        engine = AnnotationEngine(self.config, self.logger)
        engine.current_job = job
        
        result = engine.cancel_current_job()
        
        assert result is True
        assert job.status == JobStatus.CANCELLED
        assert engine.current_job is None
        
        # Test cancelling when no job is running
        result = engine.cancel_current_job()
        assert result is False
    
    def test_get_processing_statistics(self):
        """Test getting processing statistics."""
        engine = AnnotationEngine(self.config, self.logger)
        
        stats = engine.get_processing_statistics()
        
        assert "total_jobs_processed" in stats
        assert "total_images_processed" in stats
        assert "average_processing_time" in stats
        assert "success_rate" in stats
        
        # All should be 0 initially
        assert stats["total_jobs_processed"] == 0
        assert stats["total_images_processed"] == 0
        assert stats["average_processing_time"] == 0.0
        assert stats["success_rate"] == 0.0