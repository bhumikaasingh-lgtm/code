from __future__ import annotations

from typing import List

import numpy as np


_model_cache = {}


def _get_model(model_name: str):
    if model_name in _model_cache:
        return _model_cache[model_name]
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "sentence-transformers is required. Install via: pip install sentence-transformers"
        ) from exc
    model = SentenceTransformer(model_name)
    _model_cache[model_name] = model
    return model


def encode_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64) -> np.ndarray:
    model = _get_model(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    return embeddings.astype("float32", copy=False)


def l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
    return matrix / norms
