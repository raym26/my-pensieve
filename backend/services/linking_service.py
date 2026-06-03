"""
linking_service.py
Surfaces non-obvious connections between notes using semantic similarity.
"""
import json
import anthropic
from models.note import Note
from services.rag_service import RAGService

client = anthropic.Anthropic()

EXPLAIN_PROMPT = """You are analyzing a personal knowledge base to find non-obvious connections between notes.

Source note: "{title}"
{body}

These notes were found to be semantically similar. For each one, write a single sentence explaining
the conceptual connection to the source note. Be specific — name the shared concept, theme, or idea.

Candidates:
{candidates}

Return ONLY valid JSON: [{{"title": "...", "reason": "..."}}]
One object per candidate, in the same order.
"""


class LinkingService:
    def __init__(self, rag: RAGService):
        self.rag = rag

    def find_connections(self, note: Note, limit: int = 6) -> list[dict]:
        query = f"{note.title}\n\n{note.body[:1200]}"
        raw = self.rag.search(query, n_results=limit + 6)

        existing = {l.lower().strip() for l in note.links}

        connections = []
        for r in raw:
            if r["id"] == note.id:
                continue
            title = r["metadata"]["title"]
            if title.lower().strip() in existing:
                continue
            if r["distance"] > 1.4:
                continue
            connections.append({
                "id": r["id"],
                "title": title,
                "folder": r["metadata"]["folder"],
                "tags": r["metadata"].get("tags", ""),
                "distance": round(r["distance"], 4),
                "relevance": max(0, round((1 - r["distance"] / 2) * 100)),
                "reason": None,
            })

        return connections[:limit]

    def explain_connections(self, note: Note, candidates: list[dict]) -> list[dict]:
        if not candidates:
            return candidates

        numbered = "\n".join(
            f"{i+1}. \"{c['title']}\""
            for i, c in enumerate(candidates)
        )
        prompt = EXPLAIN_PROMPT.format(
            title=note.title,
            body=note.body[:600],
            candidates=numbered,
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            explanations = json.loads(response.content[0].text.strip())
            title_to_reason = {e["title"]: e["reason"] for e in explanations}
            for c in candidates:
                c["reason"] = title_to_reason.get(c["title"])
        except (json.JSONDecodeError, KeyError):
            pass

        return candidates
