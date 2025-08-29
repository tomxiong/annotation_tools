"""
Tests for BatchJob data model.
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
from enum import Enum

from src.models.batch_job import BatchJob, JobStatus
from src.models.dataset import Dataset
from src.models.annotation import Annotation
from src.core.exceptions import ValidationError


class TestBatchJob:
    """Test cases for BatchJob class."""
    
    def test_batch_job_creation_with_required_fields(self):
        """Test creating batch job with only required fields."""
        dataset = Dataset("test_dataset", "/data/images")
        
        job = BatchJob(
            job_id="job_001",
            dataset=dataset,
            model_name="yolo_v8"
        )
        
        assert job.job_id == "job_001"
        assert job.dataset == dataset
        assert job.model_name == "yolo_v8"
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0
        assert job.total_images == 0
        assert job.processed_images == 0
        assert job.failed_images == 0
        assert job.results == []
        assert job.error_message is None
        assert isinstance(job.created_at, datetime)
        assert job.started_at is None
        assert job.completed_at is None
    
    def test_batch_job_creation_with_all_fields(self):
        """Test creating batch job with all fields."""
        dataset = Dataset("test_dataset", "/data/images")
        created_time = datetime.now()
        
        job = BatchJob(
            job_id="job_002",
            dataset=dataset,
            model_name="yolo_v8",
            status=JobStatus.RUNNING,
            progress=0.5,
            total_images=100,
            processed_images=50,
            failed_images=2,
            results=[],
            error_message=None,
            created_at=created_time,
            started_at=created_time,
            completed_at=None
        )
        
        assert job.job_id == "job_002"
        assert job.status == JobStatus.RUNNING
        assert job.progress == 0.5
        assert job.total_images == 100
        assert job.processed_images == 50
        assert job.failed_images == 2
        assert job.created_at == created_time
        assert job.started_at == created_time
    
    def test_job_status_enum(self):
        """Test JobStatus enum values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
    
    def test_batch_job_start(self):
        """Test starting a batch job."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8")
        
        assert job.status == JobStatus.PENDING
        assert job.started_at is None
        
        job.start()
        
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        assert isinstance(job.started_at, datetime)
    
    def test_batch_job_complete(self):
        """Test completing a batch job."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8")
        job.start()
        
        assert job.status == JobStatus.RUNNING
        assert job.completed_at is None
        
        job.complete()
        
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert isinstance(job.completed_at, datetime)
        assert job.progress == 1.0
    
    def test_batch_job_fail(self):
        """Test failing a batch job."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8")
        job.start()
        
        error_msg = "Model loading failed"
        job.fail(error_msg)
        
        assert job.status == JobStatus.FAILED
        assert job.error_message == error_msg
        assert job.completed_at is not None
    
    def test_batch_job_cancel(self):
        """Test cancelling a batch job."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8")
        job.start()
        
        job.cancel()
        
        assert job.status == JobStatus.CANCELLED
        assert job.completed_at is not None
    
    def test_batch_job_update_progress(self):
        """Test updating job progress."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8", total_images=100)
        
        job.update_progress(processed=25, failed=2)
        
        assert job.processed_images == 25
        assert job.failed_images == 2
        assert job.progress == 0.25  # 25/100
        
        job.update_progress(processed=50, failed=3)
        
        assert job.processed_images == 50
        assert job.failed_images == 3
        assert job.progress == 0.5  # 50/100
    
    def test_batch_job_add_result(self):
        """Test adding annotation results to job."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8")
        
        annotation1 = Annotation("img1.jpg", "cat", [10, 20, 100, 150])
        annotation2 = Annotation("img2.jpg", "dog", [5, 15, 80, 120])
        
        job.add_result(annotation1)
        assert len(job.results) == 1
        assert job.results[0] == annotation1
        
        job.add_result(annotation2)
        assert len(job.results) == 2
        assert job.results[1] == annotation2
    
    def test_batch_job_get_duration(self):
        """Test calculating job duration."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8")
        
        # Job not started
        assert job.get_duration() is None
        
        # Job started but not completed
        job.start()
        duration = job.get_duration()
        assert duration is not None
        assert duration.total_seconds() >= 0
        
        # Job completed
        job.complete()
        duration = job.get_duration()
        assert duration is not None
        assert duration.total_seconds() >= 0
    
    def test_batch_job_to_dict(self):
        """Test converting batch job to dictionary."""
        dataset = Dataset("test_dataset", "/data/images")
        job = BatchJob("job_001", dataset, "yolo_v8")
        job.start()
        job.add_result(Annotation("img1.jpg", "cat", [10, 20, 100, 150]))
        
        result = job.to_dict()
        
        assert result["job_id"] == "job_001"
        assert result["model_name"] == "yolo_v8"
        assert result["status"] == "running"
        assert result["progress"] == 0.0
        assert result["total_images"] == 0
        assert result["processed_images"] == 0
        assert result["failed_images"] == 0
        assert len(result["results"]) == 1
        assert "dataset" in result
        assert "created_at" in result
        assert "started_at" in result
    
    def test_batch_job_from_dict(self):
        """Test creating batch job from dictionary."""
        dataset_data = {
            "name": "test_dataset",
            "root_path": "/data/images",
            "annotations": [],
            "metadata": {},
            "created_at": "2024-01-01T10:00:00"
        }
        
        data = {
            "job_id": "job_001",
            "dataset": dataset_data,
            "model_name": "yolo_v8",
            "status": "running",
            "progress": 0.5,
            "total_images": 100,
            "processed_images": 50,
            "failed_images": 2,
            "results": [
                {
                    "image_path": "img1.jpg",
                    "label": "cat",
                    "bbox": [10, 20, 100, 150],
                    "confidence": 0.9,
                    "metadata": {},
                    "created_at": "2024-01-01T12:00:00"
                }
            ],
            "error_message": None,
            "created_at": "2024-01-01T10:00:00",
            "started_at": "2024-01-01T10:05:00",
            "completed_at": None
        }
        
        job = BatchJob.from_dict(data)
        
        assert job.job_id == "job_001"
        assert job.model_name == "yolo_v8"
        assert job.status == JobStatus.RUNNING
        assert job.progress == 0.5
        assert job.total_images == 100
        assert job.processed_images == 50
        assert job.failed_images == 2
        assert len(job.results) == 1
        assert job.results[0].label == "cat"
        assert isinstance(job.dataset, Dataset)
        assert job.dataset.name == "test_dataset"
    
    def test_batch_job_validates_progress_range(self):
        """Test that batch job validates progress range."""
        dataset = Dataset("test_dataset", "/data/images")
        
        # Valid progress values
        valid_progress = [0.0, 0.5, 1.0]
        for progress in valid_progress:
            job = BatchJob("job_001", dataset, "yolo_v8", progress=progress)
            assert job.progress == progress
        
        # Invalid progress values should be clamped
        job = BatchJob("job_001", dataset, "yolo_v8", progress=-0.1)
        assert job.progress == 0.0
        
        job = BatchJob("job_001", dataset, "yolo_v8", progress=1.5)
        assert job.progress == 1.0