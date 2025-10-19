import re
import unicodedata
from typing import List


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    return text


def tokenize(text: str) -> List[str]:
    normalized = normalize_text(text)
    return re.findall(r"\w+", normalized)


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    # Split on sentence boundaries or newlines; keep it robust/simple
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p and not p.isspace()]


def chunk_text_by_sentences(text: str, sentences_per_chunk: int = 6, overlap: int = 1) -> List[str]:
    if sentences_per_chunk <= 0:
        return [text]
    if overlap < 0:
        overlap = 0
    sentences = split_sentences(text)
    if not sentences:
        return [text]
    chunks: List[str] = []
    step = max(1, sentences_per_chunk - overlap)
    for start in range(0, len(sentences), step):
        window = sentences[start : start + sentences_per_chunk]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + sentences_per_chunk >= len(sentences):
            break
    return chunks
