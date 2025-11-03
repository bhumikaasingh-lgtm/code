"""Run LLM-backed Ragas retrieval evaluation for the Weaviate `Chunks` collection.

This script mirrors `ragas_retrieval_eval.py` but scores retrieval quality using
LLM-based metrics (`ContextPrecision`, `ContextRecall`). Set the
`OPENAI_API_KEY` environment variable (and optionally `RAGAS_LLM_MODEL`) before
running.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

import pandas as pd
from datasets import Dataset
import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.config import AdditionalConfig
from sentence_transformers import SentenceTransformer
from ragas import evaluate
from ragas.llms import OpenAI
from ragas.metrics import ContextPrecision, ContextRecall


WEAVIATE_URL = "https://s4g1odnruqfcsvvsmlg.c0.europe-west3.gcp.weaviate.cloud"
WEAVIATE_API_KEY = os.environ.get(
    "WEAVIATE_API_KEY",
    "MDM2ZlpPVHRETVhiSUtYVF91N0hsZFE3QlhpWTBKR1ppYzdVN3lUaC9tWjZlNkQ5UUNSamZjUVVmN0FFPV92MjAw",
)
EMBED_MODEL = "intfloat/e5-large-v2"
DEFAULT_LLM_MODEL = os.environ.get("RAGAS_LLM_MODEL", "gpt-4o-mini")


@dataclass
class EvaluationConfig:
    csv_path: str = "all_issues_for_test.csv"
    sample_size: int = 20
    top_k: int = 5
    alpha: float = 0.4
    output_csv: str = "ragas_retrieval_per_sample_llm.csv"


def require_env(var_name: str) -> str:
    value = os.environ.get(var_name)
    if not value:
        raise RuntimeError(f"Environment variable '{var_name}' must be set for LLM evaluation")
    return value


def embed_queries(model: SentenceTransformer, texts: List[str]) -> List[List[float]]:
    return model.encode(
        ["query: " + t for t in texts],
        batch_size=16,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).tolist()


def hybrid_filtered(
    collection: weaviate.collections.Collection,
    embeddings_model: SentenceTransformer,
    query_text: str,
    *,
    author: str | None = None,
    status: str | None = None,
    limit: int,
    alpha: float,
) -> List[weaviate.collections.classes.grpc.ReferencesResult]:
    query_vector = embed_queries(embeddings_model, [query_text])[0]

    filters = None
    if author:
        filters = Filter.by_property("author").equal(author)
    if status:
        status_filter = Filter.by_property("status").equal(status)
        filters = Filter.all_of([filters, status_filter]) if filters else status_filter

    response = collection.query.hybrid(
        query=query_text,
        vector=query_vector,
        alpha=alpha,
        limit=limit,
        filters=filters,
        return_metadata=MetadataQuery(score=True),
        return_properties=["id_str", "author", "status", "chunk_idx", "text"],
    )

    return response.objects


def build_dataset(
    collection: weaviate.collections.Collection,
    model: SentenceTransformer,
    issues: pd.DataFrame,
    *,
    sample_size: int,
    top_k: int,
    alpha: float,
) -> Dataset:
    sample = issues.sample(n=min(sample_size, len(issues)), random_state=42)
    rows = []

    for _, row in sample.iterrows():
        question = str(row["subject"]).strip()
        reference = str(row["description"]).strip()
        if not question or not reference:
            continue

        hits = hybrid_filtered(
            collection,
            model,
            question,
            limit=top_k,
            alpha=alpha,
        )

        contexts = [hit.properties.get("text", "") for hit in hits]
        contexts = [context for context in contexts if context]

        if not contexts:
            continue

        rows.append(
            {
                "user_input": question,
                "retrieved_contexts": contexts,
                "reference": reference,
            }
        )

    return Dataset.from_list(rows)


def main(config: EvaluationConfig) -> None:
    openai_key = require_env("OPENAI_API_KEY")

    model = SentenceTransformer(EMBED_MODEL)
    model.max_seq_length = 512

    issues = pd.read_csv(config.csv_path)
    issues = issues.dropna(subset=["subject", "description"])

    with weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=AuthApiKey(WEAVIATE_API_KEY),
        additional_config=AdditionalConfig(grpc_enabled=False),
    ) as client:
        collection = client.collections.get("Chunks")
        dataset = build_dataset(
            collection,
            model,
            issues,
            sample_size=config.sample_size,
            top_k=config.top_k,
            alpha=config.alpha,
        )

    if len(dataset) == 0:
        raise RuntimeError("No evaluation samples were prepared. Check query results or adjust sample size/top_k.")

    print(f"Prepared dataset with {len(dataset)} samples")

    llm = OpenAI(api_key=openai_key, model=DEFAULT_LLM_MODEL)

    metrics = [
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
    ]

    evaluation = evaluate(
        dataset=dataset,
        metrics=metrics,
        column_map={
            "user_input": "user_input",
            "retrieved_contexts": "retrieved_contexts",
            "reference": "reference",
        },
    )

    averaged = {
        metric: sum(scores) / len(scores) if scores else float("nan")
        for metric, scores in evaluation._scores_dict.items()
    }

    print("RAGAS LLM Retrieval Evaluation Results (averaged):")
    for metric, score in averaged.items():
        print(f"  {metric}: {score:.4f}")

    per_sample = evaluation.to_pandas()
    per_sample.insert(0, "question", dataset["user_input"])
    per_sample.to_csv(config.output_csv, index=False)
    print(f"Saved per-sample scores to {config.output_csv}")


if __name__ == "__main__":
    main(EvaluationConfig())

