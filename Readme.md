# CodeRush 2.0 | Team Sahayya

---

## Project Information

- **Team Name**: Team Sahayya
- **Project Title**: AURA - Autonomous Unified Research Agent
- **Track/Theme**: Agentic Ecosystem

---

## Project Description

**AURA (Autonomous Unified Research Agent)** is a self-evolving multi-agent research ecosystem designed to solve hallucinations, slow document retrieval, and untrusted code execution in automated AI research workflows.

### Key Capabilities & Solution:
1. **Multi-Agent Pipeline & Live Status Stream**:
   Dispatches specialized sub-agents working sequentially:
   - 🤖 **Controller Agent**: Task planning, query decomposition, and DAG execution.
   - 🧠 **Embedding Agent**: Dual vector embedding generation (OpenAI `text-embedding-3-small` primary with automatic Gemini `text-embedding-004` fallback).
   - 🔍 **Hybrid Retrieval Agent**: BM25 keyword frequency combined with Supabase `pgvector` HNSW cosine similarity search via Reciprocal Rank Fusion (RRF $k=60$) and Time-Aware Decay ranking.
   - 🛡️ **Claim Verification Agent**: Fact triangulation, evidence entailment verification, and claim confidence scoring.
   - 🔒 **Sandbox Execution Agent**: Resource-constrained Docker container sandbox management (`mem_limit=512m`, 1 CPU core, `network_mode=none`, non-root user `1000`).
   - ✍️ **Synthesis Agent**: Generates comprehensive, factual AI research summaries with expandable citations.

2. **Human-in-the-Loop Governance**:
   Interactive permission modals prompt user authorization (`Grant Permission` / `Deny Action`) before agents execute sandbox code or external web actions.

3. **ChatGPT & Gemini Minimalist Interface**:
   Clean dark-mode single-page UI with real-time active agent badges, live thinking stream logs, citation cards, and a slide-over governance drawer.

---

## Technical Stack

- **Frontend**: HTML5, Modern CSS3 (ChatGPT/Gemini Dark Aesthetic), Vanilla JavaScript (Zero NPM / build step dependencies).
- **Backend**: Python 3.11+, FastAPI, Uvicorn, AsyncIO, Pydantic v2, HTTPX.
- **Database & Vector Store**: PostgreSQL, Supabase, `pgvector` (1536-dimensional HNSW cosine search), SQLAlchemy 2.0 (AsyncSession), PgBouncer transaction mode (`statement_cache_size=0`).
- **AI & RAG Engine**: OpenAI API (`text-embedding-3-small`), Gemini API (`text-embedding-004`), Reciprocal Rank Fusion (RRF), BM25 tokenization, Time-Aware Decay.
- **Sandbox & Containerization**: Docker (`aura-agent-runner:latest` / `python:3.11-slim`), Playwright, PyMuPDF, Pandas, Requests, non-root `sandboxuser`.

---

## Setup and Installation

Follow these instructions to run AURA locally:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PiyushTheProgrammer/CodeRush2.0-Team_Sahayya.git
   cd CodeRush2.0-Team_Sahayya
   ```

2. **Install backend dependencies**:
   ```bash
   python -m pip install -r backend/requirements.txt
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

4. **Start the FastAPI & Frontend server**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend
   ```

5. **Access the application**:
   - **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
   - **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
