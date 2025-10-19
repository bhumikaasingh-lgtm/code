import os
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


def _maybe_openai_answer(question: str, contexts: List[Dict[str, Any]]) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI()
        context_blocks = []
        for i, ctx in enumerate(contexts, start=1):
            md = ctx.get("metadata", {})
            header = f"[Doc {i}] id={md.get('id','')}, subject={md.get('subject','')}"
            context_blocks.append(header + "\n" + ctx.get("text", ""))
        prompt = (
            "You are a helpful assistant. Answer the user's question using ONLY the provided context blocks. "
            "If the answer is not in the context, say you don't know. "
            "Cite doc numbers inline like [Doc 2] when relevant.\n\n"
            + "\n\n".join(context_blocks)
        )
        messages = [
            {"role": "system", "content": "Answer concisely and cite sources as [Doc N]."},
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{prompt}"},
        ]
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


def generate_answer(question: str, retrieved: List[Dict[str, Any]], prefer_openai: bool = False) -> str:
    contexts = [r if isinstance(r, dict) else r.doc for r in retrieved]  # tolerate SearchResult or raw dict
    if prefer_openai:
        answer = _maybe_openai_answer(question, contexts)
        if isinstance(answer, str) and answer.strip():
            return answer
    return _extractive_answer(question, contexts)
