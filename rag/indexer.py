import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Any

from .text import tokenize


@dataclass
class SearchResult:
    score: float
    doc_index: int
    doc: Dict[str, Any]


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.num_documents: int = 0
        self.average_document_length: float = 0.0
        self.document_lengths: List[int] = []
        self.inverted_index: Dict[str, Dict[int, int]] = defaultdict(dict)
        self.documents: List[Dict[str, Any]] = []

    @staticmethod
    def _compute_idf(num_documents: int, document_frequency: int) -> float:
        # Okapi BM25 idf with +1 variant for stability
        return math.log(1.0 + (num_documents - document_frequency + 0.5) / (document_frequency + 0.5))

    @staticmethod
    def _term_frequency(term: str, doc_index: int, inverted_index: Dict[str, Dict[int, int]]) -> int:
        postings = inverted_index.get(term)
        if not postings:
            return 0
        return postings.get(doc_index, 0)

    def build(self, documents: List[Dict[str, Any]]) -> None:
        self.documents = documents
        self.num_documents = len(documents)
        if self.num_documents == 0:
            # Nothing to index
            self.average_document_length = 0.0
            self.document_lengths = []
            self.inverted_index = defaultdict(dict)
            return

        tokenized_documents: List[List[str]] = []
        document_lengths: List[int] = []

        for idx, doc in enumerate(documents):
            tokens = tokenize(doc.get("text", ""))
            tokenized_documents.append(tokens)
            document_lengths.append(len(tokens))

            term_counts = Counter(tokens)
            for term, count in term_counts.items():
                self.inverted_index[term][idx] = count

        self.document_lengths = document_lengths
        self.average_document_length = sum(document_lengths) / float(self.num_documents)

    def _score(self, query_terms: List[str], doc_index: int) -> float:
        score = 0.0
        doc_length = self.document_lengths[doc_index]
        for term in query_terms:
            postings = self.inverted_index.get(term)
            if not postings:
                continue
            df = len(postings)
            idf = self._compute_idf(self.num_documents, df)
            tf = postings.get(doc_index, 0)
            if tf == 0:
                continue
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_length / self.average_document_length))
            score += idf * (numerator / denominator)
        return score

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        query_terms = tokenize(query)
        if not query_terms or self.num_documents == 0:
            return []

        candidate_doc_indices = set()
        for term in set(query_terms):
            postings = self.inverted_index.get(term)
            if postings:
                candidate_doc_indices.update(postings.keys())

        scored: List[Tuple[float, int]] = []
        for doc_index in candidate_doc_indices:
            score = self._score(query_terms, doc_index)
            if score > 0:
                scored.append((score, doc_index))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:k]
        return [SearchResult(score=s, doc_index=i, doc=self.documents[i]) for s, i in top]

    def to_dict(self) -> Dict[str, Any]:
        # Convert dict keys to strings for JSON compatibility
        inverted_index_serializable: Dict[str, Dict[str, int]] = {}
        for term, postings in self.inverted_index.items():
            inverted_index_serializable[term] = {str(idx): tf for idx, tf in postings.items()}

        return {
            "version": 1,
            "built_at": datetime.utcnow().isoformat() + "Z",
            "k1": self.k1,
            "b": self.b,
            "num_documents": self.num_documents,
            "average_document_length": self.average_document_length,
            "document_lengths": self.document_lengths,
            "inverted_index": inverted_index_serializable,
            "documents": self.documents,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BM25Index":
        idx = cls(k1=float(data.get("k1", 1.5)), b=float(data.get("b", 0.75)))
        idx.num_documents = int(data.get("num_documents", 0))
        idx.average_document_length = float(data.get("average_document_length", 0.0))
        idx.document_lengths = list(map(int, data.get("document_lengths", [])))
        idx.documents = list(data.get("documents", []))

        inverted_index_serializable: Dict[str, Dict[str, int]] = data.get("inverted_index", {})
        inverted_index: Dict[str, Dict[int, int]] = defaultdict(dict)
        for term, postings in inverted_index_serializable.items():
            for idx_str, tf in postings.items():
                inverted_index[term][int(idx_str)] = int(tf)
        idx.inverted_index = inverted_index
        return idx

    def save(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False)

    @classmethod
    def load(cls, input_path: str) -> "BM25Index":
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {input_path}")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
