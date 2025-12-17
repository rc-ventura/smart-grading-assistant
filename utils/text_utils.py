import re
import unicodedata
from typing import Optional


def slugify(text: Optional[str]) -> str:
    """Normalize arbitrary text into a safe identifier."""
    if not text:
        return "criterion"
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text)
    slug = slug.strip("_").lower()
    return slug or "criterion"
