# Pensieve — Second Brain

A local AI-powered second brain built on your Obsidian vault.

## Features
- **Chat** — Ask questions, get answers grounded in your notes (RAG)
- **Auto-tag** — Claude suggests tags and summaries for your notes
- **Ingest** — Paste a URL, get a structured Obsidian note saved automatically
- **Index** — Embed all notes into a local vector store (ChromaDB)

## Setup

### 1. Clone and install backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```
Or add it to a `.env` file in `/backend`.

### 3. Verify your vault path
Open `backend/config.py` and confirm `VAULT_PATH` points to your Obsidian vault.

### 4. Start the backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Open the frontend
Just open `frontend/index.html` in your browser. No build step needed.

## First Run Workflow
1. Open the app → go to **Index Vault** → click "Index All Notes"
   - This embeds all your notes into ChromaDB (one-time, ~1-2 min)
2. Go to **Chat** and start asking questions
3. Use **Ingest URL** to save articles into your vault

## Project Structure
```
second-brain/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Vault path, settings
│   ├── requirements.txt
│   ├── routers/
│   │   ├── notes.py         # List, search, tag notes
│   │   ├── chat.py          # RAG chat endpoint
│   │   └── ingest.py        # URL scraping + saving
│   ├── services/
│   │   ├── vault_service.py # Read Obsidian markdown files
│   │   ├── tagging_service.py # Auto-tag with Claude
│   │   └── rag_service.py   # ChromaDB vector store
│   └── models/
│       └── note.py          # Pydantic models
├── frontend/
│   └── index.html           # Local web UI
└── data/
    └── chroma/              # Vector DB (auto-created)
```

## Roadmap
- [x] Phase 1: Organization (auto-tagging, vault reading)
- [x] Phase 2: RAG chat
- [x] Phase 3: URL ingestion
- [ ] Phase 4: Auto-linking (surface connections between notes)
- [ ] Phase 5: Daily digest / journal summary
- [ ] Phase 6: Deploy as product
- 