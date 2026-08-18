"""
PodGen AI - API Routes
"""

import asyncio
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl

from services.pipeline import PodcastPipeline
from services.job_manager import JobManager, JobStatus

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Request / Response Models ───────────────────────────────────────────────

class TopicRequest(BaseModel):
    topic: str
    style: str = "educational"          # educational | debate | storytelling
    audience: str = "general"           # general | technical | kids | experts
    tone: str = "conversational"        # conversational | formal | casual | excited
    language: str = "en"
    duration_minutes: int = 10          # target length
    host_name: str = "Alex"
    guest_name: str = "Jordan"
    host_personality: str = "curious and engaging"
    guest_personality: str = "knowledgeable and enthusiastic"

class UrlRequest(BaseModel):
    url: str
    style: str = "educational"
    audience: str = "general"
    tone: str = "conversational"
    language: str = "en"
    duration_minutes: int = 10
    host_name: str = "Alex"
    guest_name: str = "Jordan"
    host_personality: str = "curious and engaging"
    guest_personality: str = "knowledgeable and enthusiastic"

class PodcastResponse(BaseModel):
    job_id: str
    status: str
    message: str

class ScriptUpdateRequest(BaseModel):
    job_id: str
    script: str


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_job_manager(request: Request) -> JobManager:
    return request.app.state.job_manager


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/generate/topic", response_model=PodcastResponse)
async def generate_from_topic(
    req: TopicRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Generate podcast from a topic."""
    job_manager = get_job_manager(request)
    job_id = str(uuid.uuid4())
    job_manager.create_job(job_id, "topic", {"topic": req.topic})

    pipeline = PodcastPipeline(job_manager)
    background_tasks.add_task(
        pipeline.run,
        job_id=job_id,
        input_type="topic",
        content=req.topic,
        config=req.dict()
    )

    return PodcastResponse(job_id=job_id, status="queued", message="Podcast generation started")


@router.post("/generate/url", response_model=PodcastResponse)
async def generate_from_url(
    req: UrlRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Generate podcast from a URL."""
    job_manager = get_job_manager(request)
    job_id = str(uuid.uuid4())
    job_manager.create_job(job_id, "url", {"url": req.url})

    pipeline = PodcastPipeline(job_manager)
    background_tasks.add_task(
        pipeline.run,
        job_id=job_id,
        input_type="url",
        content=req.url,
        config=req.dict()
    )

    return PodcastResponse(job_id=job_id, status="queued", message="URL processing started")


@router.post("/generate/document", response_model=PodcastResponse)
async def generate_from_document(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    style: str = Form("educational"),
    audience: str = Form("general"),
    tone: str = Form("conversational"),
    language: str = Form("en"),
    duration_minutes: int = Form(10),
    host_name: str = Form("Alex"),
    guest_name: str = Form("Jordan"),
    host_personality: str = Form("curious and engaging"),
    guest_personality: str = Form("knowledgeable and enthusiastic"),
):
    """Generate podcast from an uploaded document."""
    allowed_types = {
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    job_manager = get_job_manager(request)
    job_id = str(uuid.uuid4())

    file_bytes = await file.read()
    job_manager.create_job(job_id, "document", {"filename": file.filename})

    config = dict(
        style=style, audience=audience, tone=tone, language=language,
        duration_minutes=duration_minutes, host_name=host_name,
        guest_name=guest_name, host_personality=host_personality,
        guest_personality=guest_personality
    )

    pipeline = PodcastPipeline(job_manager)
    background_tasks.add_task(
        pipeline.run,
        job_id=job_id,
        input_type="document",
        content=file_bytes,
        config=config,
        filename=file.filename
    )

    return PodcastResponse(job_id=job_id, status="queued", message="Document processing started")


@router.get("/job/{job_id}")
async def get_job_status(job_id: str, request: Request):
    """Get the status and result of a podcast generation job."""
    job_manager = get_job_manager(request)
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs")
async def list_jobs(request: Request):
    """List all podcast generation jobs."""
    job_manager = get_job_manager(request)
    return {"jobs": job_manager.list_jobs()}


@router.delete("/job/{job_id}")
async def cancel_job(job_id: str, request: Request):
    """Cancel a running job."""
    job_manager = get_job_manager(request)
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already completed")
    return {"message": "Job cancelled"}


@router.put("/job/script")
async def update_script(req: ScriptUpdateRequest, request: Request):
    """Update the script for a job (before audio generation)."""
    job_manager = get_job_manager(request)
    success = job_manager.update_script(req.job_id, req.script)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Script updated"}


@router.get("/stream/{job_id}")
async def stream_progress(job_id: str, request: Request):
    """SSE endpoint for real-time progress streaming."""
    job_manager = get_job_manager(request)

    async def event_generator():
        last_stage = None
        while True:
            job = job_manager.get_job(job_id)
            if not job:
                yield f"data: {{\"error\": \"Job not found\"}}\n\n"
                break

            if job["stage"] != last_stage:
                last_stage = job["stage"]
                import json
                yield f"data: {json.dumps(job)}\n\n"

            if job["status"] in ("completed", "failed", "cancelled"):
                break

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
