"""
BatchJob data model for managing batch annotation jobs.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .annotation import Annotation
from .dataset import Dataset
from src.core.exceptions import ValidationError


class JobStatus(Enum):
    """Enumeration of possible job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """
    Represents a batch annotation job with progress tracking and results.
    
    Attributes:
        job_id: Unique identifier for the job
        dataset: Dataset to be processed
        model_name: Name of the model used for annotation
        status: Current job status
        progress: Progress percentage (0.0 to 1.0)
        total_images: Total number of images to process
        processed_images: Number of images processed
        failed_images: Number of images that failed processing
        results: List of annotation results
        error_message: Error message if job failed
        created_at: Timestamp when job was created
        started_at: Timestamp when job started
        completed_at: Timestamp when job completed
    """
    job_id: str
    dataset: Dataset
    model_name: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    total_images: int = 0
    processed_images: int = 0
    failed_images: int = 0
    results: List[Annotation] = field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate job data after initialization."""
        self._validate_progress()
    
    def _validate_progress(self):
        """Validate and clamp progress value."""
        if self.progress < 0.0:
            self.progress = 0.0
        elif self.progress > 1.0:
            self.progress = 1.0
    
    def start(self) -> None:
        """
        Start the batch job.
        Sets status to RUNNING and records start time.
        """
        if self.status != JobStatus.PENDING:
            raise ValidationError(f"Cannot start job in {self.status.value} status")
        
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()
    
    def complete(self) -> None:
        """
        Complete the batch job.
        Sets status to COMPLETED, progress to 1.0, and records completion time.
        """
        if self.status not in [JobStatus.RUNNING, JobStatus.PENDING]:
            raise ValidationError(f"Cannot complete job in {self.status.value} status")
        
        self.status = JobStatus.COMPLETED
        self.progress = 1.0
        self.completed_at = datetime.now()
    
    def fail(self, error_message: str) -> None:
        """
        Mark the batch job as failed.
        
        Args:
            error_message: Description of the failure
        """
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def cancel(self) -> None:
        """
        Cancel the batch job.
        Sets status to CANCELLED and records completion time.
        """
        if self.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            raise ValidationError(f"Cannot cancel job in {self.status.value} status")
        
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def update_progress(self, processed: int, failed: int = 0) -> None:
        """
        Update job progress.
        
        Args:
            processed: Number of images processed
            failed: Number of images that failed processing
        """
        self.processed_images = processed
        self.failed_images = failed
        
        if self.total_images > 0:
            self.progress = min(1.0, processed / self.total_images)
        else:
            self.progress = 0.0
    
    def add_result(self, annotation: Annotation) -> None:
        """
        Add an annotation result to the job.
        
        Args:
            annotation: Annotation result to add
        """
        if not isinstance(annotation, Annotation):
            raise ValidationError("Only Annotation objects can be added as results")
        
        self.results.append(annotation)
    
    def get_duration(self) -> Optional[timedelta]:
        """
        Get the duration of the job.
        
        Returns:
            Duration as timedelta if job has started, None otherwise
        """
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.now()
        return end_time - self.started_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert batch job to dictionary format.
        
        Returns:
            Dictionary representation of the batch job
        """
        return {
            "job_id": self.job_id,
            "dataset": self.dataset.to_dict(),
            "model_name": self.model_name,
            "status": self.status.value,
            "progress": self.progress,
            "total_images": self.total_images,
            "processed_images": self.processed_images,
            "failed_images": self.failed_images,
            "results": [result.to_dict() for result in self.results],
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchJob':
        """
        Create batch job from dictionary data.
        
        Args:
            data: Dictionary containing batch job data
            
        Returns:
            BatchJob instance
        """
        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        
        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        
        # Parse dataset
        dataset = Dataset.from_dict(data["dataset"])
        
        # Parse results
        results = []
        for result_data in data.get("results", []):
            results.append(Annotation.from_dict(result_data))
        
        # Parse status
        status = JobStatus(data["status"])
        
        return cls(
            job_id=data["job_id"],
            dataset=dataset,
            model_name=data["model_name"],
            status=status,
            progress=data.get("progress", 0.0),
            total_images=data.get("total_images", 0),
            processed_images=data.get("processed_images", 0),
            failed_images=data.get("failed_images", 0),
            results=results,
            error_message=data.get("error_message"),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at
        )
    
    def get_success_rate(self) -> float:
        """
        Calculate the success rate of processed images.
        
        Returns:
            Success rate as a percentage (0.0 to 1.0)
        """
        if self.processed_images == 0:
            return 0.0
        
        successful_images = self.processed_images - self.failed_images
        return successful_images / self.processed_images
    
    def is_active(self) -> bool:
        """
        Check if the job is currently active (running).
        
        Returns:
            True if job is running, False otherwise
        """
        return self.status == JobStatus.RUNNING
    
    def is_finished(self) -> bool:
        """
        Check if the job has finished (completed, failed, or cancelled).
        
        Returns:
            True if job is finished, False otherwise
        """
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def __str__(self) -> str:
        """String representation of the batch job."""
        return f"BatchJob(id={self.job_id}, status={self.status.value}, progress={self.progress:.1%})"