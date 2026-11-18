from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_HOSTS = {"darglobal.co.uk", "www.darglobal.co.uk", "wasalt.com", "www.wasalt.com", "wasalt.sa", "www.wasalt.sa"}


def allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS and not parsed.username and not parsed.password and parsed.port in (None, 443)


def clean_text(text: str) -> str:
    text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    return "\n".join(re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()).strip()


def document_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def load_documents(path: Path | None = None) -> list[dict]:
    path = path or ROOT / "data" / "documents.json"
    docs = json.loads(path.read_text(encoding="utf-8"))
    seen = set()
    valid = []
    for doc in docs:
        if not allowed_url(doc.get("url", "")):
            raise ValueError("The dataset contains a source outside the permitted websites.")
        if doc["url"] in seen:
            continue
        seen.add(doc["url"])
        doc = dict(doc)
        doc["id"] = document_id(doc["url"])
        doc["text"] = clean_text(doc["text"])
        if len(doc["text"]) >= 60:
            valid.append(doc)
    if not valid:
        raise ValueError("No usable source documents. Run the scraper or import authorized HTML exports.")
    return valid


def chunks_for(docs: list[dict], size: int = 650, overlap: int = 100) -> list[dict]:
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed overlap.")
    chunks = []
    for doc in docs:
        text = doc["text"]
        start = 0
        part = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + size // 2, end)
                if boundary > start:
                    end = boundary
            chunks.append({**doc, "chunk_id": f"{doc['id']}-{part}", "text": text[start:end]})
            if end == len(text):
                break
            start = end - overlap
            part += 1
    return chunks
