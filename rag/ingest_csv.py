import csv
from pathlib import Path
from typing import Dict, List


def load_csv_documents(csv_path: str) -> List[Dict]:
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
