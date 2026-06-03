from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from services.vault_service import VaultService
from services.rag_service import RAGService
from services.linking_service import LinkingService
from config import VAULT_PATH, CHROMA_PATH

router = APIRouter()
vault = VaultService(VAULT_PATH)
rag = RAGService(CHROMA_PATH)
linker = LinkingService(rag)


@router.get("/")
def get_connections(
    note_id: str = Query(..., description="Relative path to the note, e.g. folder/note.md"),
    explain: bool = Query(False, description="Ask Claude to explain each connection"),
    limit: int = Query(6, ge=1, le=20),
):
    filepath = Path(VAULT_PATH) / note_id
    note = vault.read_note(filepath)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    connections = linker.find_connections(note, limit=limit)

    if explain and connections:
        connections = linker.explain_connections(note, connections)

    return {
        "note_id": note_id,
        "note_title": note.title,
        "connections": connections,
    }
