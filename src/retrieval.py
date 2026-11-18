from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .corpus import ROOT, chunks_for

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Query expansion translates names only, never invents property facts.
ALIASES = {
    "أيدا": "AIDA Muscat Oman", "ايدا": "AIDA Muscat Oman", "أستيرا": "Astera Aston Martin",
    "استيرا": "Astera Aston Martin", "تييرا": "Tierra Viva", "فاغ": "Les Vagues Elie Saab",
    "الرياض": "Riyadh", "جدة": "Jeddah", "مكة": "Makkah", "المدينة": "Madinah",
    "دبي": "Dubai", "مسقط": "Muscat", "عمان": "Oman", "قطر": "Qatar",
}


class Retriever:
    """Multilingual local embeddings + FAISS, combined with lexical retrieval.

    Lexical-only mode is explicit and useful for offline tests, never passed off
    as semantic retrieval. Raw text is not sent to an embedding API.
    """

    def __init__(self, docs: list[dict], mode: str | None = None):
        self.docs = docs
        self.chunks = chunks_for(docs)
        self.mode = mode or os.getenv("RETRIEVAL_MODE", "hybrid")
        if self.mode not in {"hybrid", "lexical"}:
            raise ValueError("RETRIEVAL_MODE must be hybrid or lexical.")
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self.texts = [f"{c['title']} {c.get('location', '')} {c['text']}" for c in self.chunks]
        self.matrix = self.vectorizer.fit_transform(self.texts)
        self.encoder = None
        self.index = None
        if self.mode == "hybrid":
            self._semantic_index()

    def _semantic_index(self):
        import faiss
        from fastembed import TextEmbedding

        model_name = os.getenv("EMBEDDING_MODEL", MODEL)
        model_cache = ROOT / "data" / "model-cache"
        model_cache.mkdir(parents=True, exist_ok=True)
        self.encoder = TextEmbedding(model_name=model_name, cache_dir=str(model_cache), threads=max(1, int(os.getenv("EMBEDDING_THREADS", "1"))))
        index_dir = ROOT / "data" / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        fingerprint = hashlib.sha256(json.dumps([model_name, self.texts], ensure_ascii=False).encode()).hexdigest()[:20]
        index_path = index_dir / f"{fingerprint}.faiss"
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
            if self.index.ntotal == len(self.chunks):
                return
        embeddings = np.asarray(list(self.encoder.embed(self.texts, batch_size=16)), dtype="float32")
        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)
        faiss.write_index(self.index, str(index_path))

    def search(self, query: str, source: str = "All sources", k: int = 6) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        is_arabic = bool(re.search(r"[\u0600-\u06ff]", query))
        expansions = [english for arabic, english in ALIASES.items() if arabic in query]
        expanded_query = query + " " + " ".join(expansions)
        lexical = cosine_similarity(self.vectorizer.transform([expanded_query]), self.matrix).ravel()
        scores = lexical.copy()
        if self.index is not None:
            import faiss
            vector = np.asarray(list(self.encoder.query_embed([expanded_query])), dtype="float32")
            faiss.normalize_L2(vector)
            values, ids = self.index.search(vector, len(self.chunks))
            semantic = np.zeros(len(self.chunks))
            for value, idx in zip(values[0], ids[0]):
                if idx >= 0:
                    semantic[idx] = max(0.0, float(value))
            # Arabic name expansion makes lexical matching more reliable than
            # semantic similarity alone on this small bilingual snapshot.
            lexical_weight = 0.7 if is_arabic else 0.35
            scores = (1 - lexical_weight) * semantic + lexical_weight * lexical
        ranked = np.argsort(-scores)
        results = []
        counts: dict[str, int] = {}
        for idx in ranked:
            chunk = self.chunks[int(idx)]
            if source != "All sources" and chunk["source"] != source:
                continue
            if scores[idx] < (0.16 if self.index is not None else 0.055):
                continue
            if counts.get(chunk["id"], 0) >= 2:
                continue
            counts[chunk["id"]] = counts.get(chunk["id"], 0) + 1
            results.append({**chunk, "score": round(float(scores[idx]), 4)})
            if len(results) >= k:
                break
        return results
