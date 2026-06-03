from pydantic import BaseModel
from datetime import datetime


class Note(BaseModel):
    id: str
    title: str
    body: str
    tags: list[str] = []
    links: list[str] = []
    folder: str = ""
    created_at: datetime
    modified_at: datetime
    raw: str = ""


class NoteOut(BaseModel):
    id: str
    title: str
    summary: str = ""
    tags: list[str] = []
    folder: str
    modified_at: datetime