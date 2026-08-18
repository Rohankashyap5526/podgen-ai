"""
PodGen AI - Job Manager
Handles concurrent podcast generation jobs with status tracking.
"""

import threading
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_job(self, job_id: str, input_type: str, metadata: dict) -> dict:
        job = {
            "job_id": job_id,
            "input_type": input_type,
            "metadata": metadata,
            "status": JobStatus.QUEUED,
            "stage": "queued",
            "progress": 0,
            "script": None,
            "audio_url": None,
            "title": None,
            "description": None,
            "tags": [],
            "duration_seconds": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "cancelled": False,
        }
        with self._lock:
            self._jobs[job_id] = job
        return job

    def update_job(self, job_id: str, **kwargs):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(kwargs)
                self._jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

    def get_job(self, job_id: str) -> Optional[dict]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list:
        with self._lock:
            return sorted(
                list(self._jobs.values()),
                key=lambda j: j["created_at"],
                reverse=True
            )

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job["status"] in (JobStatus.COMPLETED, JobStatus.FAILED):
                return False
            self._jobs[job_id]["cancelled"] = True
            self._jobs[job_id]["status"] = JobStatus.CANCELLED
            self._jobs[job_id]["stage"] = "cancelled"
            return True

    def update_script(self, job_id: str, script: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id]["script"] = script
            return True

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.get("cancelled", False) if job else False
