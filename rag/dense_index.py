from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from .embeddings import encode_texts, l2_normalize


@dataclass
class DenseResult:
    score: float
    doc_index: int
    doc: Dict[str, Any]


class DenseIndex:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", normalize: bool = True):
        self.model_name = model_name
        self.normalize = normalize
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None

    def build(self, documents: List[Dict[str, Any]], batch_size: int = 128) -> None:
        self.documents = documents
        texts = [d.get("text", "") for d in documents]
        matrix = encode_texts(texts, model_name=self.model_name, batch_size=batch_size)
        if self.normalize:
            matrix = l2_normalize(matrix)
        self.embeddings = matrix

    def search(self, query: str, k: int = 5) -> List[DenseResult]:
        if self.embeddings is None or len(self.documents) == 0:
            return []
        query_vec = encode_texts([query], model_name=self.model_name, batch_size=1)[0]
        if self.normalize:
            query_vec = l2_normalize(query_vec.reshape(1, -1))[0]
        scores = (self.embeddings @ query_vec).astype(float)  # cosine if normalized
        top_idx = np.argsort(-scores)[:k]
        return [DenseResult(score=float(scores[i]), doc_index=int(i), doc=self.documents[int(i)]) for i in top_idx]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "built_at": datetime.utcnow().isoformat() + "Z",
            "model_name": self.model_name,
            "normalize": self.normalize,
            "documents": self.documents,
            "embeddings": self.embeddings.tolist() if self.embeddings is not None else [],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DenseIndex":
        idx = cls(model_name=data.get("model_name", "all-MiniLM-L6-v2"), normalize=bool(data.get("normalize", True)))
        idx.documents = list(data.get("documents", []))
        emb_list = data.get("embeddings", [])
        idx.embeddings = np.array(emb_list, dtype="float32") if emb_list else None
        return idx

    def save(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, input_path: str) -> "DenseIndex":
        path = Path(input_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
