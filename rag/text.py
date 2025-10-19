import re
import unicodedata
from typing import List


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    return text


def tokenize(text: str) -> List[str]:
    normalized = normalize_text(text)
    return re.findall(r"\w+", normalized)
