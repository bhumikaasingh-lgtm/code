import csv
from pathlib import Path
from typing import Dict, List

from .text import chunk_text_by_sentences


def load_csv_documents(csv_path: str, sentences_per_chunk: int | None = None, overlap: int = 1) -> List[Dict]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    documents: List[Dict] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Required columns
            issue_id = (row.get("id") or "").strip()
            subject = (row.get("subject") or "").strip()
            author = (row.get("author") or "").strip()
            status = (row.get("status") or "").strip()
            related = (row.get("related issues") or "").strip()
            description = (row.get("description") or "").strip()

            text_parts: List[str] = []
            if subject:
                text_parts.append(f"Subject: {subject}")
            if description:
                text_parts.append(f"Description: {description}")
            if related:
                text_parts.append(f"Related: {related}")
            if status:
                text_parts.append(f"Status: {status}")
            if author:
                text_parts.append(f"Author: {author}")

            full_text = "\n".join(text_parts)

            if sentences_per_chunk and sentences_per_chunk > 0:
                chunks = chunk_text_by_sentences(full_text, sentences_per_chunk=sentences_per_chunk, overlap=overlap)
                for ci, chunk in enumerate(chunks):
                    doc = {
                        "doc_id": f"{issue_id}#c{ci}" if issue_id else None,
                        "text": chunk,
                        "metadata": {
                            "id": issue_id,
                            "subject": subject,
                            "author": author,
                            "status": status,
                            "related_issues": related,
                            "source": str(path),
                            "chunk_index": ci,
                        },
                    }
                    documents.append(doc)
            else:
                doc = {
                    "doc_id": issue_id or None,
                    "text": full_text,
                    "metadata": {
                        "id": issue_id,
                        "subject": subject,
                        "author": author,
                        "status": status,
                        "related_issues": related,
                        "source": str(path),
                    },
                }
                documents.append(doc)

    return documents
