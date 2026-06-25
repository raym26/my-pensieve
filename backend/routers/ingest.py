from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from config import VAULT_PATH

router = APIRouter()
client = anthropic.Anthropic()


class IngestRequest(BaseModel):
    url: str
    folder: str = "ALL THINGS AI"  # default to your existing folder


def scrape_url(url: str) -> str:
    """Fetch and extract main text content from a URL.
    Falls back to Jina Reader for JavaScript-heavy pages."""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)

    # If the page requires JS, fall back to Jina Reader which renders it server-side
    js_signals = ["enable javascript", "javascript is required", "javascript is disabled", "please enable js"]
    if len(text) < 500 or any(s in text.lower() for s in js_signals):
        jina_resp = httpx.get(
            f"https://r.jina.ai/{url}",
            headers={"Accept": "text/plain"},
            timeout=30,
            follow_redirects=True,
        )
        text = jina_resp.text

    return text[:6000]


def summarize_article(url: str, text: str) -> dict:
    """Use Claude to extract title, tags, and summary from article text."""
    prompt = f"""You are helping build a personal knowledge base. Given this article content, return ONLY valid JSON with:
- "title": a concise title for the note
- "summary": 3-5 sentence summary of key insights
- "tags": list of 4-6 relevant lowercase tags
- "key_points": list of 3-5 bullet point takeaways

Article URL: {url}
Content:
{text}
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"title": "Untitled", "summary": raw, "tags": [], "key_points": []}


def save_as_note(data: dict, url: str, folder: str) -> str:
    """Write a structured markdown note to the Obsidian vault."""
    vault = Path(VAULT_PATH)
    target_folder = vault / folder
    target_folder.mkdir(parents=True, exist_ok=True)

    safe_title = "".join(c for c in data["title"] if c.isalnum() or c in " -_").strip()
    filename = f"{safe_title[:60]}.md"
    filepath = target_folder / filename

    key_points = "\n".join(f"- {p}" for p in data.get("key_points", []))
    date_str = datetime.now().strftime("%Y-%m-%d")

    import yaml
    frontmatter = yaml.dump({
        "title": data["title"],
        "url": url,
        "tags": data.get("tags", []),
        "date": date_str,
        "source": "ingested",
    }, allow_unicode=True, default_flow_style=False, sort_keys=False)

    note_content = f"""---
{frontmatter}---

## Summary
{data['summary']}

## Key Points
{key_points}

## Source
[{url}]({url})
"""
    filepath.write_text(note_content, encoding="utf-8")
    return str(filepath.relative_to(vault))


@router.post("/url")
def ingest_url(req: IngestRequest):
    """Scrape a URL, summarize it with Claude, and save as an Obsidian note."""
    try:
        text = scrape_url(req.url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {e}")
    try:
        data = summarize_article(req.url, text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize: {e}")
    try:
        note_path = save_as_note(data, req.url, req.folder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save note: {e}")
    return {
        "note_path": note_path,
        "title": data["title"],
        "tags": data.get("tags", []),
        "summary": data.get("summary", ""),
    }