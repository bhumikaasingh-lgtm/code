import re
from typing import List, Dict, Any

from .text import tokenize


def _split_sentences(text: str) -> List[str]:
    # Simple sentence splitter; robust enough for our data
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p and not p.isspace()]


def _extractive_answer(question: str, contexts: List[Dict[str, Any]], max_sentences: int = 6) -> str:
    query_terms = set(tokenize(question))
    sentence_scores: List[tuple[float, str]] = []

    for ctx in contexts:
        text = ctx.get("text", "")
        sentences = _split_sentences(text)
        for sentence in sentences:
            terms = set(tokenize(sentence))
            if not terms:
                continue
            overlap = len(query_terms & terms)
            if overlap == 0:
                continue
            score = overlap / (len(terms) ** 0.5)
            sentence_scores.append((score, sentence))

    if not sentence_scores:
        # Fallback: return subjects and statuses
        lines = []
        for ctx in contexts:
            md = ctx.get("metadata", {})
            subject = md.get("subject") or ""
            status = md.get("status") or ""
            issue_id = md.get("id") or ""
            if subject:
                lines.append(f"- [{issue_id}] {subject} ({status})")
        return "\n".join(lines[:max_sentences]) or "No relevant information found."

    sentence_scores.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [s for _, s in sentence_scores[:max_sentences]]
    return " ".join(top_sentences)


 


def generate_answer(question: str, retrieved: List[Dict[str, Any]]) -> str:
    contexts = [r if isinstance(r, dict) else r.doc for r in retrieved]
    return _extractive_answer(question, contexts)
