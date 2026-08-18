"""
PodGen AI - FastAPI Backend
Production-ready AI podcast generation system
"""

import asyncio
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
import uvicorn

from api.routes import router as api_router
from services.job_manager import JobManager
from utils.security import SecurityMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

job_manager = JobManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎙️ PodGen AI starting up...")
    app.state.job_manager = job_manager
    yield
    logger.info("PodGen AI shutting down...")

app = FastAPI(
    title="PodGen AI",
    description="AI-powered podcast generation from topics, URLs, and documents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Serve generated audio files
import os
os.makedirs("audio_output", exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio_output"), name="audio")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "PodGen AI", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
