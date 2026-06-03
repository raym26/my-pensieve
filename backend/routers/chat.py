from fastapi import APIRouter
from pydantic import BaseModel
import anthropic
from services.rag_service import RAGService
from services.vault_service import VaultService
from config import CHROMA_PATH, VAULT_PATH

router = APIRouter()
rag = RAGService(CHROMA_PATH)
vault = VaultService(VAULT_PATH)
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a personal memory assistant — a Pensieve for the user's thoughts.
You have access to excerpts from the user's private Obsidian notes (journal entries, research, ideas).
Answer questions by drawing directly from these notes. 
- Cite which note a memory comes from (use the title).
- If the notes don't contain relevant info, say so honestly.
- Be warm and personal — you're helping someone remember their own thoughts.
- When relevant, surface connections between ideas the user may not have noticed.
"""


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


def find_notes_by_title(query: str) -> list[dict]:
    """Search vault notes whose title appears in the query."""
    all_notes = vault.get_all_notes()
    query_lower = query.lower()
    matches = []
    for note in all_notes:
        if note.title.lower() in query_lower:
            matches.append({
                "id": note.id,
                "content": f"{note.title}\n\n{note.body}"[:2000],
                "metadata": {
                    "title": note.title,
                    "folder": note.folder,
                }
            })
    return matches


@router.post("/")
def chat(req: ChatRequest):
    # 1. Title match first (catches "May 2026", "March 2026", etc.)
    title_matches = find_notes_by_title(req.message)

    # 2. Semantic search for broader context
    semantic_matches = rag.search(req.message, n_results=10)

    # 3. Merge — title matches take priority, dedupe by id
    seen = set()
    context_notes = []
    for note in title_matches + semantic_matches:
        if note["id"] not in seen:
            seen.add(note["id"])
            context_notes.append(note)

    context_notes = context_notes[:12]  # cap total

    # 4. Build context block
    context_block = "\n\n---\n\n".join([
        f"[Note: {n['metadata']['title']} | Folder: {n['metadata']['folder']}]\n{n['content'][:1500]}"
        for n in context_notes
    ])

    # 5. Build messages
    messages = req.history + [
        {
            "role": "user",
            "content": f"Here are relevant excerpts from my notes:\n\n{context_block}\n\n---\n\nMy question: {req.message}"
        }
    ]

    # 6. Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    return {
        "reply": response.content[0].text,
        "sources": [{"title": n["metadata"]["title"], "folder": n["metadata"]["folder"]} for n in context_notes[:10]],
    }