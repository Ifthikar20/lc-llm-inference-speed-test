import io

from pypdf import PdfReader


def extract_text(data: bytes) -> str:
    """Extract plain text from a PDF byte stream."""
    reader = PdfReader(io.BytesIO(data))
    parts = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(p.strip() for p in parts if p.strip())
