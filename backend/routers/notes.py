from fastapi import APIRouter, Query
from services.vault_service import VaultService
from services.tagging_service import TaggingService
from services.rag_service import RAGService
from config import VAULT_PATH, CHROMA_PATH

router = APIRouter()
vault = VaultService(VAULT_PATH)
tagger = TaggingService()
rag = RAGService(CHROMA_PATH)


@router.get("/")
def list_notes(folder: str = Query(None)):
    notes = vault.get_all_notes(folder=folder)
    return [{"id": n.id, "title": n.title, "folder": n.folder,
             "tags": n.tags, "modified_at": n.modified_at} for n in notes]


@router.get("/folders")
def list_folders():
    return vault.get_folders()


@router.get("/search")
def search_notes(q: str = Query(...)):
    return rag.search(q)


@router.post("/index")
def index_all():
    """Embed all notes into ChromaDB."""
    notes = vault.get_all_notes()
    count = rag.index_notes(notes)
    return {"indexed": count}


@router.post("/autotag")
def autotag_notes(folder: str = Query(None), limit: int = Query(10)):
    """Auto-tag a batch of notes using Claude."""
    notes = vault.get_all_notes(folder=folder)[:limit]
    results = tagger.batch_tag(notes)
    return results


@router.get("/{note_id:path}")
def get_note(note_id: str):
    from pathlib import Path
    from config import VAULT_PATH
    filepath = Path(VAULT_PATH) / note_id
    note = vault.read_note(filepath)
    if not note:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Note not found")
    return note