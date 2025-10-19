import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .ingest_csv import load_csv_documents
from .indexer import BM25Index
from .retriever import retrieve
from .generator import generate_answer
from .dense_index import DenseIndex
from .hybrid import hybrid_search


def build_index(args: argparse.Namespace) -> None:
    csv_path = args.csv
    index_path = args.index
    sentences_per_chunk = int(args.sentences_per_chunk) if args.sentences_per_chunk is not None else None
    overlap = int(args.overlap)

    documents = load_csv_documents(csv_path, sentences_per_chunk=sentences_per_chunk, overlap=overlap)

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

    results = retrieve(index_path=index_path, query=question, k=top_k)

    answer = generate_answer(question, results)

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
    p_build.add_argument("--sentences-per-chunk", type=int, default=None, help="Sentences per chunk (enable chunking)")
    p_build.add_argument("--overlap", type=int, default=1, help="Sentence overlap between chunks")
    p_build.set_defaults(func=build_index)

    p_query = sub.add_parser("query", help="Query the index")
    p_query.add_argument("--index", default="data/index.json", help="Path to index JSON")
    p_query.add_argument("--question", required=True, help="User question")
    p_query.add_argument("--k", default=5, help="Top-K documents to consider")
    p_query.set_defaults(func=query_index)

    # Dense index build
    def build_dense(args: argparse.Namespace) -> None:
        csv_path = args.csv
        index_path = args.index
        model_name = args.model
        sentences_per_chunk = int(args.sentences_per_chunk) if args.sentences_per_chunk is not None else 8
        overlap = int(args.overlap)

        documents = load_csv_documents(csv_path, sentences_per_chunk=sentences_per_chunk, overlap=overlap)
        dindex = DenseIndex(model_name=model_name, normalize=True)
        dindex.build(documents)
        dindex.save(index_path)
        print(json.dumps({
            "indexed_documents": len(documents),
            "index_path": index_path,
            "model": model_name,
        }, indent=2))

    p_dense = sub.add_parser("build-dense", help="Build dense embeddings index from CSV")
    p_dense.add_argument("--csv", required=True, help="Path to CSV file")
    p_dense.add_argument("--index", default="data/index_dense.json", help="Path to output dense index JSON")
    p_dense.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    p_dense.add_argument("--sentences-per-chunk", type=int, default=8, help="Sentences per chunk for dense index")
    p_dense.add_argument("--overlap", type=int, default=1, help="Sentence overlap between chunks")
    p_dense.set_defaults(func=build_dense)

    # Query dense index
    def query_dense(args: argparse.Namespace) -> None:
        index_path = args.index
        question = args.question
        top_k = int(args.k)
        dindex = DenseIndex.load(index_path)
        results = dindex.search(question, k=top_k)
        answer = generate_answer(question, results)
        print("Answer:\n" + answer + "\n")
        print("Top results:")
        for rank, r in enumerate(results, start=1):
            md: Dict[str, Any] = r.doc.get("metadata", {})
            print(f"{rank:>2}. score={r.score:.3f} id={md.get('id','')} subject={md.get('subject','')} status={md.get('status','')}")

    p_qd = sub.add_parser("query-dense", help="Query dense embeddings index")
    p_qd.add_argument("--index", default="data/index_dense.json", help="Path to dense index JSON")
    p_qd.add_argument("--question", required=True, help="User question")
    p_qd.add_argument("--k", default=5, help="Top-K documents to consider")
    p_qd.set_defaults(func=query_dense)

    # Hybrid query using both BM25 and Dense
    def query_hybrid(args: argparse.Namespace) -> None:
        bm25_path = args.bm25
        dense_path = args.dense
        question = args.question
        top_k = int(args.k)
        alpha = float(args.alpha)

        bm25 = BM25Index.load(bm25_path)
        dense = DenseIndex.load(dense_path)
        results = hybrid_search(bm25, dense, question, k=top_k, alpha=alpha)
        # Convert to simple printout
        print("Top hybrid results:")
        for rank, (score, doc) in enumerate(results, start=1):
            md: Dict[str, Any] = doc.get("metadata", {})
            print(f"{rank:>2}. score={score:.3f} id={md.get('id','')} subject={md.get('subject','')} status={md.get('status','')}")
        # Build answer using docs only
        docs = [doc for _, doc in results]
        answer = generate_answer(question, docs)
        print("\nAnswer:\n" + answer + "\n")

    p_h = sub.add_parser("query-hybrid", help="Query with hybrid (BM25 + Dense)")
    p_h.add_argument("--bm25", default="data/index.json", help="Path to BM25 index JSON")
    p_h.add_argument("--dense", default="data/index_dense.json", help="Path to Dense index JSON")
    p_h.add_argument("--question", required=True, help="User question")
    p_h.add_argument("--k", default=5, help="Top-K documents to consider")
    p_h.add_argument("--alpha", default=0.5, help="Weight for BM25 vs Dense [0..1]")
    p_h.set_defaults(func=query_hybrid)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
