#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

config = ROOT / "src/backend/app/core/config.py"
text = config.read_text(encoding="utf-8")
if "embedding_base_url:" not in text:
    marker = '    cors_origins: str = "http://localhost:5173"\n'
    addition = marker + (
        '    embedding_base_url: str = ""\n'
        '    embedding_api_key: str = ""\n'
        '    embedding_model: str = "text-embedding-3-small"\n'
        '    embedding_dimensions: int = 1536\n'
        '    embedding_send_dimensions: bool = False\n'
        '    embedding_timeout_seconds: float = 20.0\n'
    )
    if marker not in text:
        raise SystemExit("config.py marker not found")
    config.write_text(text.replace(marker, addition, 1), encoding="utf-8")

main = ROOT / "src/backend/app/main.py"
text = main.read_text(encoding="utf-8")
if "retrieval_router" not in text:
    marker = "from app.api.routes import router\n"
    if marker not in text:
        raise SystemExit("main.py routes import not found")
    text = text.replace(
        marker,
        marker
        + "from app.api.retrieval import router as retrieval_router\n"
        + "from app.api.retrieval_admin import router as retrieval_admin_router\n",
        1,
    )
    include_marker = "app.include_router(router)\n"
    if include_marker not in text:
        raise SystemExit("main.py include marker not found")
    text = text.replace(
        include_marker,
        include_marker
        + "app.include_router(retrieval_router)\n"
        + "app.include_router(retrieval_admin_router)\n",
        1,
    )
    main.write_text(text, encoding="utf-8")

requirements = ROOT / "src/backend/requirements.txt"
text = requirements.read_text(encoding="utf-8")
if "pgvector==" not in text:
    requirements.write_text(text.rstrip() + "\npgvector==0.5.0\n", encoding="utf-8")

print("Sprint 2-2 patch applied.")
