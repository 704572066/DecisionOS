#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = ROOT / "src/frontend/src/style.css"

text = css.read_text(encoding="utf-8")

addition = r"""

/* Sprint 3-2.3.1: Decision Board sections use natural content height. */
.decision-board-scroll {
  display: block;
}

.decision-board-overview,
.board-section {
  flex: none;
  height: auto;
  min-height: 0;
  max-height: none;
}

.board-section {
  overflow: visible;
}

.board-actions {
  height: auto;
  max-height: none;
  overflow: visible;
}

.board-todo {
  height: auto;
  min-height: 0;
}

.board-risk {
  height: auto;
  min-height: 0;
}

/* Keep text concise, but let the section itself grow naturally. */
.board-risk p {
  -webkit-line-clamp: unset;
  display: block;
  overflow: visible;
}

.decision-board-links {
  flex: none;
}
"""

if "Sprint 3-2.3.1: Decision Board sections use natural content height." not in text:
    css.write_text(text.rstrip() + addition + "\n", encoding="utf-8")
    print("Sprint 3-2.3.1 CSS patch applied:", css)
else:
    print("Sprint 3-2.3.1 already applied:", css)
