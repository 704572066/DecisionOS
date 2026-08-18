from pathlib import Path

from app.core.config import settings


def storage_root() -> Path:
    root = Path(settings.knowledge_storage_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def source_path(workspace_id: str, source_id: str, suffix: str) -> Path:
    safe_suffix = suffix.lower() if suffix.lower() in {".pdf", ".docx", ".txt", ".md", ".markdown"} else ""
    directory = storage_root() / workspace_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{source_id}{safe_suffix}"


def remove_file(path: str) -> None:
    candidate = Path(path).resolve()
    root = storage_root()
    if candidate == root or root not in candidate.parents:
        return
    candidate.unlink(missing_ok=True)

