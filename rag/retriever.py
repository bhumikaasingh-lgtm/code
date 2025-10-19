from typing import List, Dict, Any

from .indexer import BM25Index, SearchResult


def retrieve(index_path: str, query: str, k: int = 5) -> List[SearchResult]:
    index = BM25Index.load(index_path)
    return index.search(query=query, k=k)
