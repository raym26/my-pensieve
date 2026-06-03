"""
reindex.py — Run this anytime you add new notes to your vault.
Usage: python reindex.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.vault_service import VaultService
from services.rag_service import RAGService
from config import VAULT_PATH, CHROMA_PATH

vault = VaultService(VAULT_PATH)
rag = RAGService(CHROMA_PATH)

print(f"Vault: {VAULT_PATH}")
print(f"ChromaDB: {CHROMA_PATH}")
print("Reading notes...")

notes = vault.get_all_notes()
print(f"Found {len(notes)} notes:")
for n in notes:
    print(f"  [{n.folder}] {n.title}")

print("\nIndexing...")
count = rag.index_notes(notes)
print(f"\n✓ Done. {count} notes indexed.")