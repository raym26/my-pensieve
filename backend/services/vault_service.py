"""
vault_service.py
Reads and parses Obsidian markdown notes from the vault directory.
"""
import os
import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional
from models.note import Note


class VaultService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Extract YAML frontmatter and body from a note."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return meta, body
                except yaml.YAMLError:
                    pass
        return {}, content.strip()

    def _extract_tags(self, content: str, meta: dict) -> list[str]:
        """Extract tags from frontmatter and inline #tags."""
        tags = list(meta.get("tags", []) or [])
        inline = re.findall(r"#([a-zA-Z0-9_/-]+)", content)
        return list(set(tags + inline))

    def _extract_links(self, content: str) -> list[str]:
        """Extract [[wikilinks]] from note body."""
        return re.findall(r"\[\[([^\]]+)\]\]", content)

    def read_note(self, filepath: Path) -> Optional[Note]:
        """Parse a single .md file into a Note object."""
        try:
            raw = filepath.read_text(encoding="utf-8")
            meta, body = self._parse_frontmatter(raw)
            stat = filepath.stat()
            return Note(
                id=str(filepath.relative_to(self.vault_path)),
                title=meta.get("title") or filepath.stem,
                body=body,
                tags=self._extract_tags(body, meta),
                links=self._extract_links(body),
                folder=str(filepath.parent.relative_to(self.vault_path)),
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                raw=raw,
            )
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None

    def get_all_notes(self, folder: Optional[str] = None) -> list[Note]:
        """Load all notes from vault (optionally filtered by folder)."""
        root = self.vault_path / folder if folder else self.vault_path
        notes = []
        for md_file in root.rglob("*.md"):
            note = self.read_note(md_file)
            if note:
                notes.append(note)
        return notes

    def get_folders(self) -> list[str]:
        """List top-level folders in the vault."""
        return [
            d.name
            for d in self.vault_path.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]