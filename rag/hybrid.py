from __future__ import annotations

from typing import List, Dict, Any

from .indexer import BM25Index, SearchResult as BM25Result
from .dense_index import DenseIndex, DenseResult


def hybrid_search(bm25_index: BM25Index, dense_index: DenseIndex, query: str, k: int = 5, alpha: float = 0.5):
    bm25_results = bm25_index.search(query, k=k)
    dense_results = dense_index.search(query, k=k)

    # Normalize scores per retriever to [0,1] for simple interpolation
    def normalize(results):
        if not results:
            return []
        scores = [r.score for r in results]
        mn, mx = min(scores), max(scores)
        rng = (mx - mn) or 1.0
        return [(r, (r.score - mn) / rng) for r in results]

    bm25_norm = normalize(bm25_results)
    dense_norm = normalize(dense_results)

    # Merge by doc identity (fallback to index) with weighted sum
    combined: Dict[int, float] = {}
    ref_docs: Dict[int, Dict[str, Any]] = {}

    for r, s in bm25_norm:
        combined[r.doc_index] = combined.get(r.doc_index, 0.0) + alpha * s
        ref_docs[r.doc_index] = r.doc
    for r, s in dense_norm:
        combined[r.doc_index] = combined.get(r.doc_index, 0.0) + (1 - alpha) * s
        ref_docs[r.doc_index] = r.doc

    ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:k]
    return [(score, ref_docs[idx]) for idx, score in ranked]
