# Pensieve — AI Second Brain for Obsidian

A local AI assistant that knows your Obsidian vault. Ask questions about your notes, auto-tag them, and clip articles from the web — all powered by Claude and a local vector store.

---

## What It Does

| Feature | Description |
|---|---|
| **Chat** | Ask anything. Pensieve retrieves relevant notes and answers with citations. |
| **Auto-tag** | Claude reads a note and suggests tags + a one-line summary. |
| **Ingest URL** | Paste a link. Pensieve scrapes it, summarizes it with Claude, and saves a structured `.md` file to your vault. |
| **Index Vault** | Embeds all your notes into a local ChromaDB vector store for semantic search. |
| **Connections** | Select a note and surface semantically related notes you haven't explicitly linked. Optionally ask Claude to explain why they're connected. |
| **Daily Digest** | Generate a journal summary + highlights of notes modified in the last 1, 3, or 7 days. |

Everything runs locally — your notes never leave your machine except for the Claude API call.

---

## How the RAG Works

When you send a chat message, Pensieve runs a two-pass retrieval:

1. **Title match** — scans all note filenames for exact/partial matches (catches journal entries like "May 2026", named topics, etc.)
2. **Semantic search** — queries ChromaDB with sentence embeddings to find conceptually related notes

Results are merged, deduplicated, and capped at 12 notes. The top context is injected into the Claude prompt along with your conversation history.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| LLM | Anthropic Claude (`claude-sonnet-4-6`) |
| Vector store | ChromaDB (local, persistent) |
| Embeddings | `all-MiniLM-L6-v2` via `chromadb` default EF |
| Web scraping | `httpx` + `BeautifulSoup4` |
| Frontend | Plain HTML/JS (no build step) |
| Notes format | Obsidian Markdown with YAML frontmatter |

---

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- An Obsidian vault on your local machine

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/raym26/my-pensieve.git
cd my-pensieve
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
cd backend
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example and fill in your values:

```bash
cp backend/.env.example backend/.env
```

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
VAULT_PATH=/path/to/your/Obsidian Vault
```

`backend/.env` is loaded automatically on startup via `python-dotenv`. `VAULT_PATH` falls back to the default in `config.py` if not set.

### 4. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 5. Open the frontend

Open `frontend/index.html` directly in your browser. No build step, no Node.

---

## First Run

1. Go to **Index Vault** → click "Index All Notes"
   - Embeds every `.md` file in your vault into ChromaDB (~1–2 min for large vaults)
   - Only needs to run once; re-run after adding many new notes
2. Go to **Chat** and ask a question
3. Use **Ingest URL** to clip an article — it lands in your vault as a formatted `.md` note

---

## API Reference

All endpoints are prefixed with `/api`.

### Notes

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/notes` | List all notes in the vault |
| `GET` | `/api/notes/search?q=<query>` | Full-text search over notes |
| `POST` | `/api/notes/{id}/tag` | Auto-tag a note with Claude |

### Connections

| Method | Path | Body / Params | Description |
|---|---|---|---|
| `GET` | `/api/connections/` | `note_id`, `explain?`, `limit?` | Find semantically related notes not already linked |

### Chat

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/api/chat/` | `{ message, history[] }` | RAG chat with your vault |

### Ingest

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/api/ingest/url` | `{ url, folder? }` | Scrape URL, summarize, save to vault |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |

---

## Configuration Reference

All config lives in `backend/config.py` and can be overridden with environment variables:

| Variable | Default | Description |
|---|---|---|
| `VAULT_PATH` | `~/Documents/Obsidian Vault` | Path to your Obsidian vault |
| `PROJECT_ROOT` | Path to repo | Used to locate `data/chroma/` |
| `CHROMA_PATH` | `{PROJECT_ROOT}/data/chroma` | Where ChromaDB persists its index |
| `ANTHROPIC_API_KEY` | _(required)_ | Your Anthropic API key |

---

## Project Structure

```
my-pensieve/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, router mounts
│   ├── config.py                # Env-driven configuration
│   ├── requirements.txt
│   ├── reindex.py               # CLI script to rebuild the vector index
│   ├── routers/
│   │   ├── notes.py             # List, search, tag notes
│   │   ├── chat.py              # Hybrid RAG chat endpoint
│   │   ├── ingest.py            # URL scrape → Claude summary → .md file
│   │   ├── connections.py       # Semantic connection discovery
│   │   └── digest.py            # Daily/weekly digest endpoint
│   ├── services/
│   │   ├── vault_service.py     # Read Obsidian markdown files
│   │   ├── rag_service.py       # ChromaDB index + semantic search
│   │   ├── tagging_service.py   # Claude-powered auto-tagger
│   │   ├── linking_service.py   # Surface connections between notes
│   │   └── digest_service.py    # Journal summary + recent activity digest
│   └── models/
│       └── note.py              # Pydantic Note model
├── frontend/
│   └── index.html               # Local web UI (no build needed)
├── data/
│   └── chroma/                  # Vector DB (auto-created, gitignored)
└── STARTUP.txt                  # Quick-start reference
```

---

## Roadmap

- [x] Phase 1: Vault reading + auto-tagging
- [x] Phase 2: RAG chat with hybrid retrieval
- [x] Phase 3: URL ingestion → structured Obsidian notes
- [x] Phase 4: Auto-linking — surface connections between notes
- [x] Phase 5: Daily digest / journal summary
- [ ] Phase 6: Deploy as a product
