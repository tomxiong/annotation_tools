"""
Core annotation engine for processing images with AI models.
"""
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

from src.models.annotation import Annotation
from src.models.batch_job import BatchJob, JobStatus
from src.core.config import Config
from src.core.logger import get_logger
from src.core.exceptions import ValidationError
from .image_processor import ImageProcessor


class ModelType(Enum):
    """Enumeration of supported model types."""
    YOLO_V8 = "yolo_v8"
    DETECTRON2 = "detectron2"
    CUSTOM = "custom"


class AnnotationEngine:
    """
    Core engine for running AI models on images to generate annotations.
    
    Supports multiple model types and batch processing with progress tracking.
    """
    
    def __init__(self, config: Config, logger_name: str = None):
        """
        Initialize AnnotationEngine.

        Args:
            config: Configuration object
            logger_name: Logger name (optional)
        """
        self.config = config
        self.logger = get_logger(logger_name or __name__)
        self.image_processor = ImageProcessor()
        self.models: Dict[str, Any] = {}
        self.current_job: Optional[BatchJob] = None
        
        # Statistics tracking
        self._stats = {
            "total_jobs_processed": 0,
            "total_images_processed": 0,
            "total_processing_time": 0.0,
            "successful_images": 0
        }
    
    def load_model(self, model_name: str, model_type: ModelType) -> bool:
        """
        Load an AI model for annotation.
        
        Args:
            model_name: Name of the model to load
            model_type: Type of the model
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if isinstance(model_type, str):
                model_type = ModelType(model_type)
            
            self.logger.info(f"Loading model: {model_name} (type: {model_type.value})")
            
            if model_type == ModelType.YOLO_V8:
                model = self._load_yolo_model(model_name)
            elif model_type == ModelType.DETECTRON2:
                model = self._load_detectron2_model(model_name)
            elif model_type == ModelType.CUSTOM:
                model = self._load_custom_model(model_name)
            else:
                raise ValidationError(f"Unsupported model type: {model_type}")
            
            self.models[model_name] = model
            self.logger.info(f"Model {model_name} loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {str(e)}")
            return False
    
    def _load_yolo_model(self, model_name: str) -> Any:
        """Load YOLO v8 model."""
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ValidationError("ultralytics package not installed. Install with: pip install ultralytics")
        
        model_config = self.config.models.get(model_name, {})
        model_path = model_config.get("path", f"{model_name}.pt")
        
        return YOLO(model_path)
    
    def _load_detectron2_model(self, model_name: str) -> Any:
        """Load Detectron2 model."""
        raise ValidationError("Detectron2 support not implemented yet")
    
    def _load_custom_model(self, model_name: str) -> Any:
        """Load custom model."""
        raise ValidationError("Custom model support not implemented yet")
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            True if model unloaded successfully, False if model not found
        """
        if model_name in self.models:
            del self.models[model_name]
            self.logger.info(f"Model {model_name} unloaded")
            return True
        else:
            self.logger.warning(f"Model {model_name} not found for unloading")
            return False
    
    def predict_single_image(self, image_path: str, model_name: str) -> List[Annotation]:
        """
        Run prediction on a single image.
        
        Args:
            image_path: Path to the image file
            model_name: Name of the model to use
            
        Returns:
            List of annotations for the image
            
        Raises:
            ValidationError: If model not loaded or image not found
        """
        if model_name not in self.models:
            raise ValidationError(f"Model {model_name} not loaded")
        
        if not Path(image_path).exists():
            raise ValidationError(f"Image file not found: {image_path}")
        
        try:
            model = self.models[model_name]
            model_config = self.config.models.get(model_name, {})
            confidence_threshold = model_config.get("confidence_threshold", 0.5)
            
            # Run prediction
            results = model(image_path)
            
            # Convert results to annotations
            annotations = []
            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes
                    
                    # Extract detection data
                    if len(boxes.xyxy) > 0:
                        xyxy = boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
                        confidences = boxes.conf.cpu().numpy()
                        class_ids = boxes.cls.cpu().numpy().astype(int)
                        
                        for i in range(len(xyxy)):
                            confidence = float(confidences[i])
                            
                            # Filter by confidence threshold
                            if confidence < confidence_threshold:
                                continue
                            
                            # Convert xyxy to xywh format
                            x1, y1, x2, y2 = xyxy[i]
                            x, y = int(x1), int(y1)
                            width, height = int(x2 - x1), int(y2 - y1)
                            
                            # Get class name
                            class_id = class_ids[i]
                            label = result.names.get(class_id, f"class_{class_id}")
                            
                            annotation = Annotation(
                                image_path=image_path,
                                label=label,
                                bbox=[x, y, width, height],
                                confidence=confidence,
                                metadata={"model": model_name}
                            )
                            
                            annotations.append(annotation)
            
            return annotations
            
        except Exception as e:
            self.logger.error(f"Prediction failed for {image_path}: {str(e)}")
            raise ValidationError(f"Prediction failed: {str(e)}")
    
    def process_batch_job(self, job: BatchJob, image_paths: List[str]) -> bool:
        """
        Process a batch job with multiple images.
        
        Args:
            job: BatchJob instance to process
            image_paths: List of image file paths
            
        Returns:
            True if job completed successfully, False otherwise
        """
        try:
            # Validate model is loaded
            if job.model_name not in self.models:
                error_msg = f"Model {job.model_name} not loaded"
                job.fail(error_msg)
                self.logger.error(error_msg)
                return False
            
            # Start the job
            job.start()
            self.current_job = job
            
            self.logger.info(f"Starting batch job {job.job_id} with {len(image_paths)} images")
            
            processed_count = 0
            failed_count = 0
            start_time = time.time()
            
            for i, image_path in enumerate(image_paths):
                try:
                    # Check if job was cancelled
                    if job.status == JobStatus.CANCELLED:
                        self.logger.info(f"Job {job.job_id} was cancelled")
                        break
                    
                    # Process single image
                    annotations = self.predict_single_image(image_path, job.model_name)
                    
                    # Add results to job
                    for annotation in annotations:
                        job.add_result(annotation)
                    
                    processed_count += 1
                    self._stats["successful_images"] += 1
                    
                    self.logger.debug(f"Processed {image_path}: {len(annotations)} annotations")
                    
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Failed to process {image_path}: {str(e)}")
                
                # Update progress
                job.update_progress(processed=processed_count + failed_count, failed=failed_count)
                
                # Log progress every 10% or every 10 images
                if (i + 1) % max(1, len(image_paths) // 10) == 0 or (i + 1) % 10 == 0:
                    self.logger.info(f"Progress: {job.progress:.1%} ({processed_count + failed_count}/{len(image_paths)})")
            
            # Complete the job
            processing_time = time.time() - start_time
            
            if job.status != JobStatus.CANCELLED:
                job.complete()
                self.logger.info(f"Job {job.job_id} completed in {processing_time:.2f}s")
            
            # Update statistics
            self._stats["total_jobs_processed"] += 1
            self._stats["total_images_processed"] += processed_count + failed_count
            self._stats["total_processing_time"] += processing_time
            
            self.current_job = None
            return True
            
        except Exception as e:
            error_msg = f"Batch job failed: {str(e)}"
            job.fail(error_msg)
            self.logger.error(error_msg)
            self.current_job = None
            return False
    
    def cancel_current_job(self) -> bool:
        """
        Cancel the currently running job.
        
        Returns:
            True if job was cancelled, False if no job running
        """
        if self.current_job is not None and self.current_job.is_active():
            self.current_job.cancel()
            self.logger.info(f"Job {self.current_job.job_id} cancelled")
            self.current_job = None
            return True
        else:
            self.logger.warning("No active job to cancel")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded and available models.
        
        Returns:
            Dictionary containing model information
        """
        available_models = list(self.config.models.keys()) if hasattr(self.config, 'models') else []
        
        return {
            "loaded_models": list(self.models.keys()),
            "available_models": available_models,
            "model_configs": getattr(self.config, 'models', {})
        }
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        total_images = self._stats["total_images_processed"]
        successful_images = self._stats["successful_images"]
        
        success_rate = successful_images / total_images if total_images > 0 else 0.0
        avg_processing_time = (
            self._stats["total_processing_time"] / self._stats["total_jobs_processed"]
            if self._stats["total_jobs_processed"] > 0 else 0.0
        )
        
        return {
            "total_jobs_processed": self._stats["total_jobs_processed"],
            "total_images_processed": total_images,
            "successful_images": successful_images,
            "failed_images": total_images - successful_images,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time
        }
    
    def cleanup(self) -> None:
        """Clean up resources and unload all models."""
        self.logger.info("Cleaning up annotation engine")
        
        # Cancel current job if running
        if self.current_job is not None:
            self.cancel_current_job()
        
        # Unload all models
        for model_name in list(self.models.keys()):
            self.unload_model(model_name)
        
        self.logger.info("Annotation engine cleanup completed")