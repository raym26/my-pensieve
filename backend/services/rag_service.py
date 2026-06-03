"""
rag_service.py
Embeds notes into ChromaDB for semantic search + RAG chat.
"""
import chromadb
from chromadb.utils import embedding_functions
from models.note import Note

COLLECTION_NAME = "second_brain"


class RAGService:
    def __init__(self, db_path: str = "../data/chroma"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.ef,
        )

    def index_notes(self, notes: list[Note]):
        """Embed and store notes in ChromaDB."""
        ids, docs, metas = [], [], []
        for note in notes:
            ids.append(note.id)
            docs.append(f"{note.title}\n\n{note.body}"[:8000])
            metas.append({
                "title": note.title,
                "folder": note.folder,
                "tags": ", ".join(note.tags),
                "modified_at": note.modified_at.isoformat(),
            })
        if ids:
            self.collection.upsert(ids=ids, documents=docs, metadatas=metas)
        return len(ids)

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Semantic search over indexed notes."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        notes = []
        for i, doc_id in enumerate(results["ids"][0]):
            notes.append({
                "id": doc_id,
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return notes

    def get_count(self) -> int:
        return self.collection.count()