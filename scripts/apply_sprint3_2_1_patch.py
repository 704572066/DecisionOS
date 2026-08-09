#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; p=ROOT/"src/backend/app/main.py"; t=p.read_text(encoding="utf-8")
if "decision_board_router" not in t:
    lines=t.splitlines(); i=max([n for n,l in enumerate(lines) if l.startswith("from app.api.")],default=0)+1
    lines.insert(i,"from app.api.decision_board import router as decision_board_router")
    inc=max([n for n,l in enumerate(lines) if l.startswith("app.include_router(")],default=-1)+1
    lines.insert(inc,"app.include_router(decision_board_router)")
    p.write_text("\n".join(lines)+"\n",encoding="utf-8")
print("Sprint 3-2.1 patch applied")
