import os

# ── Obsidian Vault ──────────────────────────────────────────────────────────
VAULT_PATH = os.getenv(
    "VAULT_PATH",
    "/Users/raymundozialcita/Documents/Obsidian Vault"
)

# ── Project root (where second-brain lives) ─────────────────────────────────
PROJECT_ROOT = os.getenv(
    "PROJECT_ROOT",
    "/Users/raymundozialcita/Documents/CODEDAMMIT/AGENTS/second-brain"
)

# ── ChromaDB (local vector store) ──────────────────────────────────────────
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(PROJECT_ROOT, "data", "chroma"))

# ── Anthropic ───────────────────────────────────────────────────────────────
# Set ANTHROPIC_API_KEY in your environment (e.g. in .env or shell profile)
# export ANTHROPIC_API_KEY=sk-ant-...