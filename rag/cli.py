import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .ingest_csv import load_csv_documents
from .indexer import BM25Index
from .retriever import retrieve
from .generator import generate_answer


def build_index(args: argparse.Namespace) -> None:
    csv_path = args.csv
    index_path = args.index

    documents = load_csv_documents(csv_path)

    index = BM25Index()
    index.build(documents)
    index.save(index_path)

    print(json.dumps({
        "indexed_documents": len(documents),
        "index_path": index_path,
        "average_document_length": index.average_document_length,
    }, indent=2))


def query_index(args: argparse.Namespace) -> None:
    index_path = args.index
    question = args.question
    top_k = int(args.k)
    prefer_openai = bool(args.openai)

    results = retrieve(index_path=index_path, query=question, k=top_k)

    answer = generate_answer(question, results, prefer_openai=prefer_openai)

    print("Answer:\n" + answer + "\n")

    print("Top results:")
    for rank, r in enumerate(results, start=1):
        md: Dict[str, Any] = r.doc.get("metadata", {})
        print(f"{rank:>2}. score={r.score:.3f} id={md.get('id','')} subject={md.get('subject','')} status={md.get('status','')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG pipeline CLI for CSV issues")
    sub = parser.add_subparsers(required=True)

    p_build = sub.add_parser("build", help="Build index from CSV")
    p_build.add_argument("--csv", required=True, help="Path to CSV file")
    p_build.add_argument("--index", default="data/index.json", help="Path to output index JSON")
    p_build.set_defaults(func=build_index)

    p_query = sub.add_parser("query", help="Query the index")
    p_query.add_argument("--index", default="data/index.json", help="Path to index JSON")
    p_query.add_argument("--question", required=True, help="User question")
    p_query.add_argument("--k", default=5, help="Top-K documents to consider")
    p_query.add_argument("--openai", action="store_true", help="Prefer OpenAI generation if available")
    p_query.set_defaults(func=query_index)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
