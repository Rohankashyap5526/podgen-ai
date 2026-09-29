# 🎙️ PodGen AI

> AI-powered podcast generation from topics, URLs and documents.

## 🚀 Overview

PodGen AI turns research material into a structured multi-speaker podcast. It combines retrieval, LLM-based script generation and text-to-speech into an end-to-end pipeline.

## ✨ Features

- Topic, URL and document input
- RAG-based research and context enrichment
- Multi-speaker podcast scripts
- Groq-powered LLM inference
- FAISS vector retrieval
- Sentence-transformer embeddings
- gTTS / ElevenLabs voice generation
- Audio merging and metadata generation
- React frontend with FastAPI backend
- Docker-ready deployment

## 🏗️ Architecture

~~~text
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
Research / Document Processing
  ↓
Embeddings → FAISS
  ↓
Planner / Context Enrichment
  ↓
Groq LLM
  ↓
Podcast Script
  ↓
TTS Engine
  ↓
Audio Output
~~~

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq |
| RAG | FAISS + sentence-transformers |
| Backend | FastAPI + Uvicorn |
| Frontend | React + Vite |
| Documents | PyMuPDF + python-docx |
| TTS | gTTS + ElevenLabs |
| Audio | pydub |
| Infrastructure | Docker + Nginx |

## ⚙️ Setup

~~~bash
git clone https://github.com/Rohankashyap5526/podgen-ai.git
cd podgen-ai
~~~

Create your environment file from the provided example.

~~~env
GROQ_API_KEY=your_key
TTS_ENGINE=gtts
ELEVENLABS_API_KEY=optional
~~~

Never commit API keys.

## 🐳 Deployment

The project includes Docker/deployment configuration and can be deployed using container-based infrastructure or a frontend/backend split deployment.

## 🔐 Security

- Secrets are loaded through environment variables.
- Uploaded files should be validated before processing.
- Production deployments should use HTTPS and appropriate rate limiting.

## 📌 Future Improvements

- Persistent job queue
- Better observability and logging
- Automated test coverage
- More TTS providers
- Production vector database support

## 📄 License

MIT
