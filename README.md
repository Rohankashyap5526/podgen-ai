# 🎙️ PodGen AI

> **AI-powered podcast generation** from topics, URLs, and documents — using Groq (LLaMA 3.3 70B) for ultra-fast inference, RAG for context-aware scripts, and multi-speaker TTS for realistic audio.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **3 input modes** | Topic, Website URL, PDF / DOCX / TXT |
| **Groq LLM** | LLaMA 3.3 70B via Groq — sub-second tokens |
| **RAG pipeline** | FAISS vector search + sentence-transformers |
| **Multi-speaker audio** | Host vs Guest voices (gTTS free / ElevenLabs premium) |
| **Podcast styles** | Educational · Debate · Storytelling |
| **Script editor** | Edit script before or after audio generation |
| **Quality scoring** | Coherence, engagement, naturalness scores |
| **Job management** | Concurrent jobs, cancel mid-generation, real-time SSE |
| **Agent architecture** | PlannerAgent → ScriptAgent → VoiceAgent |

---

## 🗂️ Project Structure

```
podgen/
├── backend/
│   ├── main.py                 # FastAPI app + lifespan
│   ├── api/
│   │   └── routes.py           # All REST endpoints + SSE
│   ├── services/
│   │   ├── pipeline.py         # Orchestration + 3 agents
│   │   ├── groq_service.py     # LLM: research, script, metadata, scoring
│   │   ├── rag_service.py      # Chunking, FAISS indexing, retrieval
│   │   ├── content_extractor.py# URL scraping, PDF/DOCX/TXT parsing
│   │   ├── tts_service.py      # gTTS / ElevenLabs + pydub merge
│   │   └── job_manager.py      # Thread-safe concurrent job tracking
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Complete React UI (single-file)
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── notebooks/
│   └── pipeline_test.ipynb     # Test each stage independently
├── audio_output/               # Generated MP3 files
├── vector_store/               # FAISS index files
├── data/                       # Uploaded documents
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Groq API key](https://console.groq.com) (free tier available)
- `ffmpeg` for audio merging (`brew install ffmpeg` / `apt install ffmpeg`)

---

### 1. Clone & Configure

```bash
git clone https://github.com/yourname/podgen-ai.git
cd podgen-ai

cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

---

### 2. Backend Setup

```bash
cd backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # Add GROQ_API_KEY here too

uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

---

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

### 4. Docker (Full Stack)

```bash
# From project root
cp .env.example .env            # set GROQ_API_KEY

docker-compose up --build
```

- Frontend → http://localhost:3000
- Backend  → http://localhost:8000
- API Docs → http://localhost:8000/docs

---

## 🔑 API Reference

### Generate Podcast

```bash
# From a topic
curl -X POST http://localhost:8000/api/v1/generate/topic \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The rise of AI agents",
    "style": "educational",
    "audience": "general",
    "tone": "conversational",
    "duration_minutes": 10,
    "host_name": "Alex",
    "guest_name": "Jordan"
  }'

# From a URL
curl -X POST http://localhost:8000/api/v1/generate/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "style": "debate"}'

# From a document
curl -X POST http://localhost:8000/api/v1/generate/document \
  -F "file=@paper.pdf" \
  -F "style=storytelling" \
  -F "duration_minutes=15"
```

### Track Progress

```bash
# Poll status
curl http://localhost:8000/api/v1/job/{job_id}

# Stream real-time SSE events
curl -N http://localhost:8000/api/v1/stream/{job_id}
```

### Edit Script & Cancel

```bash
# Update script before audio generation
curl -X PUT http://localhost:8000/api/v1/job/script \
  -H "Content-Type: application/json" \
  -d '{"job_id": "...", "script": "HOST: Updated line...\nGUEST: ..."}'

# Cancel a running job
curl -X DELETE http://localhost:8000/api/v1/job/{job_id}
```

---

## 🧠 Pipeline Architecture

```
Input (topic/url/doc)
       │
       ▼
┌─────────────────┐
│  ContentExtractor│  ← BeautifulSoup, PyMuPDF, python-docx
│  (or Groq research│
└────────┬────────┘
         │ raw text
         ▼
┌─────────────────┐
│   RAGService    │  ← chunk → embed (sentence-transformers)
│   FAISS Index   │          → FAISS IndexFlatIP
└────────┬────────┘
         │ relevant chunks
         ▼
┌─────────────────┐
│  PlannerAgent   │  ← multi-query retrieval, context enrichment
└────────┬────────┘
         │ enriched context
         ▼
┌─────────────────┐
│  ScriptAgent    │  ← Groq LLaMA 3.3 70B, style/tone/persona prompts
│  (Groq LLM)    │
└────────┬────────┘
         │ HOST/GUEST script
         ▼
┌─────────────────┐
│   VoiceAgent    │  ← parse segments → gTTS/ElevenLabs → pydub merge
│   TTSService    │
└────────┬────────┘
         │ .mp3 file
         ▼
     Audio Output + Metadata + Quality Score
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | **required** | Get free at console.groq.com |
| `TTS_ENGINE` | `gtts` | `gtts` (free) or `elevenlabs` |
| `ELEVENLABS_API_KEY` | — | Required if `TTS_ENGINE=elevenlabs` |
| `ELEVENLABS_HOST_VOICE` | Rachel | ElevenLabs voice ID for host |
| `ELEVENLABS_GUEST_VOICE` | Domi | ElevenLabs voice ID for guest |

---

## 🎙️ Podcast Styles

| Style | Description |
|---|---|
| `educational` | Host asks questions, guest explains concepts with examples |
| `debate` | Host and guest take opposing views, challenge each other |
| `storytelling` | Narrative-driven, anecdotes, human stories |

---

## 🔐 Security Notes

- API keys are read from environment variables only — never hardcoded
- File uploads are validated by MIME type before processing
- Job manager uses thread locks for safe concurrent access
- Rate limiting can be added via `slowapi` middleware (see `main.py`)

---

## 🚀 Deployment

### Backend → Render / Railway

```bash
# render.yaml (already included)
# Set env vars in dashboard: GROQ_API_KEY, TTS_ENGINE
```

### Frontend → Vercel

```bash
cd frontend
npm run build
vercel --prod
# Set VITE_API_BASE=https://your-backend.onrender.com/api/v1
```

### Backend → AWS ECS

```bash
docker build -t podgen-backend ./backend
docker tag podgen-backend:latest <aws-account>.dkr.ecr.<region>.amazonaws.com/podgen-backend
docker push <aws-account>.dkr.ecr.<region>.amazonaws.com/podgen-backend
```

---

## 🧪 Testing the Pipeline

```bash
cd notebooks
jupyter notebook pipeline_test.ipynb
```

Or run a quick smoke test:

```bash
cd backend
python -c "
from services.groq_service import GroqService
g = GroqService()
print(g.research_topic('quantum computing', 'general')[:200])
"
```

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq API · LLaMA 3.3 70B · Mixtral 8x7B |
| RAG | FAISS · sentence-transformers (all-MiniLM-L6-v2) |
| Backend | FastAPI · Uvicorn · Python 3.11 |
| Content | BeautifulSoup4 · PyMuPDF · python-docx |
| TTS | gTTS · ElevenLabs · pydub |
| Frontend | React 18 · Vite · SSE streaming |
| Infra | Docker · docker-compose · Nginx |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit: `git commit -m 'feat: add my feature'`
4. Push and open a PR

---

## 📄 License

MIT © 2025 PodGen AI
