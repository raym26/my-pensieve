from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import notes, chat, ingest, connections, digest

app = FastAPI(title="Second Brain API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
app.include_router(digest.router, prefix="/api/digest", tags=["digest"])

@app.get("/health")
def health():
    return {"status": "ok"}