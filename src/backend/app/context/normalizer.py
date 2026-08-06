import re
from app.context.cleaner import CleanTranscriptResult, clean_transcript

WS = re.compile(r"[ \t]+")

def normalize(text: str) -> str:
    return "\n".join(
        WS.sub(" ", line).strip()
        for line in (text or "").replace("\r\n","\n").split("\n")
        if line.strip()
    )

def clean_and_normalize(text: str) -> CleanTranscriptResult:
    return clean_transcript(normalize(text))

def recent_window(text: str, max_chars: int) -> str:
    value = normalize(text)
    if len(value) <= max_chars:
        return value
    suffix = value[-max_chars:]
    positions = [suffix.find(x) for x in ("。","！","？","\n") if suffix.find(x) >= 0]
    return suffix[min(positions)+1:].strip() if positions else suffix
