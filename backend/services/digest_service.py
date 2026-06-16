"""
digest_service.py
Generates a daily/weekly digest from recent vault activity.
"""
import json
from datetime import datetime, timedelta
from models.note import Note
from services.vault_service import VaultService
import anthropic

client = anthropic.Anthropic()

JOURNAL_KEYWORDS = ["journal", "daily", "diary", "log", "entries", "notes/personal"]

DIGEST_PROMPT = """You are a personal assistant helping someone reflect on their recent thinking and activity.

Today's date: {today}
Period: last {days} day(s)

JOURNAL ENTRIES ({journal_count} entries):
{journal_block}

OTHER RECENTLY MODIFIED NOTES ({other_count} notes):
{other_block}

Important context: this person's journal entries freely mix professional work (building software, learning about AI, running a business) and personal life — these are intentionally woven together, not separate. Don't try to compartmentalize them. Surface the themes and tensions that run through both.

Write a digest in JSON with these exact keys:
- "greeting": one warm, specific opening sentence that names something concrete from their entries (not generic).
- "journal_summary": 2-4 sentences capturing what they were working through — ideas, questions, energy, momentum. Treat professional and personal as one life, not two. Skip if no journal entries.
- "themes": list of 3-6 short topic tags (lowercase) that cut across both personal and professional, e.g. "building in public", "money mindset", "ai tools"
- "note_highlights": list of objects for other modified notes, each with "title" and "one_liner" (max 12 words). Max 6 items. Omit if no other notes.
- "closing": one honest, specific sentence — an observation, a question worth sitting with, or a thread worth pulling.

Respond ONLY with valid JSON, no markdown fences.
"""


class DigestService:
    def __init__(self, vault: VaultService):
        self.vault = vault

    def _is_journal(self, note: Note) -> bool:
        folder = note.folder.lower()
        return any(kw in folder for kw in JOURNAL_KEYWORDS)

    def get_recent_notes(self, days: int) -> tuple[list[Note], list[Note]]:
        cutoff = datetime.now() - timedelta(days=days)
        all_notes = self.vault.get_all_notes()
        journal, other = [], []
        for note in all_notes:
            if note.modified_at < cutoff:
                continue
            (journal if self._is_journal(note) else other).append(note)
        journal.sort(key=lambda n: n.modified_at, reverse=True)
        other.sort(key=lambda n: n.modified_at, reverse=True)
        return journal, other

    def generate(self, days: int = 1) -> dict:
        journal_notes, other_notes = self.get_recent_notes(days)

        if not journal_notes and not other_notes:
            return {
                "period_days": days,
                "journal_count": 0,
                "other_count": 0,
                "empty": True,
            }

        def fmt(notes, body_limit=800):
            if not notes:
                return "(none)"
            return "\n\n---\n\n".join(
                f"[{n.title}]\n{n.body[:body_limit]}" for n in notes[:10]
            )

        prompt = DIGEST_PROMPT.format(
            today=datetime.now().strftime("%A, %B %d %Y"),
            days=days,
            journal_count=len(journal_notes),
            journal_block=fmt(journal_notes),
            other_count=len(other_notes),
            other_block=fmt(other_notes[:6], body_limit=300),
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {"greeting": raw, "themes": [], "note_highlights": []}

        result["period_days"] = days
        result["journal_count"] = len(journal_notes)
        result["other_count"] = len(other_notes)
        result["empty"] = False
        result["generated_at"] = datetime.now().isoformat()
        return result
