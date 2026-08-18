from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def parse_file(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported knowledge file type: {suffix or 'unknown'}")
    if suffix == ".pdf":
        text = "\n\n".join((page.extract_text() or "").strip() for page in PdfReader(path).pages)
    elif suffix == ".docx":
        text = "\n".join(paragraph.text.strip() for paragraph in Document(path).paragraphs)
    else:
        raw = file_path.read_bytes()
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Unable to decode text file")
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not normalized:
        raise ValueError("No readable text was found in the file")
    return normalized


def chunk_text(text: str, limit: int = 1800, overlap: int = 180) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        pieces = [paragraph[i:i + limit] for i in range(0, len(paragraph), limit)] or [paragraph]
        for piece in pieces:
            candidate = f"{current}\n{piece}".strip() if current else piece
            if current and len(candidate) > limit:
                chunks.append(current)
                current = f"{current[-overlap:]}\n{piece}".strip()
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks

