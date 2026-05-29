# Multi-Source RAG Research Assistant

A production-grade AI research tool that lets you upload URLs, PDFs, and Notion pages, then chat with all of them simultaneously — with source citations streamed in real time.

---

## What it does

You paste a mix of sources — a research paper PDF, a few URLs, a Notion doc — and the system ingests, chunks, and embeds them all into a shared vector store. You then open a chat session scoped to those sources and ask questions in plain language. The assistant retrieves the most relevant chunks across all your documents, synthesises a grounded answer, and streams it back token-by-token with inline citations pointing to the exact source and page.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API gateway | FastAPI (async) |
| Background processing | Celery + Redis |
| Vector store | Qdrant |
| Relational store | PostgreSQL (async SQLAlchemy) |
| Embeddings | OpenAI `text-embedding-3-small` (swappable) |
| LLM synthesis | Claude / GPT-4o (streaming) |
| Real-time delivery | WebSockets |
| Frontend | React + Tailwind CSS |
| Containerisation | Docker Compose |

---

## Architecture — data flow

```
[Ingest] → [Parse] → [Chunk] → [Embed] → [Store] → [Stream]
```

1. **Ingest** — user submits a URL/PDF/Notion page via REST; FastAPI dispatches a Celery task and returns a `source_id`.
2. **Parse** — worker extracts raw text (httpx + BeautifulSoup, PyMuPDF, or Notion API).
3. **Chunk** — text split into 512-token chunks with 64-token overlap.
4. **Embed** — all chunks embedded in one batched API call.
5. **Store** — vectors → Qdrant (with `source_id` in payload); metadata → Postgres; status → `ready`.
6. **Stream** — query embedded, Qdrant returns top-8 chunks (filtered to session sources), LLM streams a grounded answer over WebSocket, final `done` frame carries citations.

---

## Build Progress

Backend-first build. Each module covered over 1–3 days.

### Day 1–2 · FastAPI foundations + models
- [x] Project folder structure
- [x] Concepts: FastAPI / ASGI / Starlette / Uvicorn vs Gunicorn
- [x] Concepts: SQLAlchemy vs Pydantic, `Base` + metadata
- [x] `app/models/db.py` — 4 models (`User`, `Source`, `Session`, `Message`)
- [x] Design decision: chunks stored exclusively in Qdrant, not Postgres
- [ ] `app/core/config.py` — Pydantic Settings
- [ ] `app/main.py` — FastAPI app factory

### Day 3–4 · Async programming
- [ ] async/await, event loop fundamentals
- [ ] `app/core/database.py` — async session factory

### Day 5–6 · PostgreSQL + SQLAlchemy + Alembic
- [ ] Alembic setup + first migration
- [ ] `alembic/` migrations wired to `Base.metadata`

### Day 7–8 · Data ingestion
- [ ] `app/ingestion/parsers.py`
- [ ] `app/ingestion/chunker.py`
- [ ] `app/ingestion/embedder.py`
- [ ] `app/ingestion/tasks.py`

### Day 9 · Celery + Redis
- [ ] `celery_app.py` — broker config + worker

### Day 10–11 · Qdrant
- [ ] `app/core/vector_store.py` — client + collection bootstrap
- [ ] `app/retrieval/search.py` — filtered similarity search

### Day 12 · WebSockets
- [ ] `app/api/ws.py` — streaming query handler
- [ ] `app/retrieval/synthesiser.py` — context build + LLM stream

### Day 13 · RAG → Advanced RAG
- [ ] Hybrid search (dense + BM25)
- [ ] Re-ranking (cross-encoder)

### Day 14–15 · Docker + integration
- [ ] `Dockerfile` (backend)
- [ ] `docker-compose.yml` — all services wired
- [ ] End-to-end integration test

---

## Database Schema

```
users
 ├── owns → sources   (documents uploaded by the user)
 └── owns → sessions  (conversations scoped to specific sources)

sessions
 ├── source_ids[]     (UUID array — which sources this session can search)
 └── contains → messages (conversation turns with citations)
```

Chunks are **not** stored in Postgres. They live exclusively in Qdrant as vectors with a `source_id` payload field. On source deletion, Qdrant points are removed by filtering on `source_id`.

See `backend/app/models/db.py` for the full SQLAlchemy definitions.

---

## Project Structure

```
rag-research-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/         # sources, sessions, ws routes
│   │   ├── ingestion/   # tasks, parsers, chunker, embedder
│   │   ├── retrieval/   # search, synthesiser
│   │   ├── models/      # db.py — SQLAlchemy models
│   │   └── core/        # config, database, vector_store
│   ├── celery_app.py
│   ├── alembic/
│   └── requirements.txt
├── frontend/
├── docker-compose.yml
└── .env.example
```

---

*Built with FastAPI · Qdrant · Celery · PostgreSQL · SQLAlchemy · React*