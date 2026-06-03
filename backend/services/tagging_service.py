"""
tagging_service.py
Uses Claude to auto-generate tags and summaries for notes.
"""
import anthropic
from models.note import Note

client = anthropic.Anthropic()

TAGGING_PROMPT = """You are organizing a personal knowledge base (a "second brain").
Given the following note, return a JSON object with:
- "tags": list of 3-7 concise lowercase tags (topics, themes, concepts)
- "summary": 1-2 sentence summary of the note's key idea
- "connections": list of 2-3 concepts or topics this note likely connects to

Respond ONLY with valid JSON, no markdown, no preamble.

Note title: {title}
Note content:
{body}
"""


class TaggingService:
    def suggest_tags(self, note: Note) -> dict:
        """Ask Claude to suggest tags and a summary for a note."""
        prompt = TAGGING_PROMPT.format(
            title=note.title,
            body=note.body[:3000],  # cap to avoid token overrun
        )
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = response.content[0].text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"tags": [], "summary": raw, "connections": []}

    def batch_tag(self, notes: list[Note]) -> list[dict]:
        """Tag a list of notes, returning enriched metadata."""
        results = []
        for note in notes:
            enriched = self.suggest_tags(note)
            enriched["note_id"] = note.id
            enriched["title"] = note.title
            results.append(enriched)
        return results