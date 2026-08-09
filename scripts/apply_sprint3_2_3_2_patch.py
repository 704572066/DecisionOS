#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = ROOT / "src/frontend/src/style.css"
text = css.read_text(encoding="utf-8")

addition = r"""

/* Sprint 3-2.3.2
 * Critical fix: previous styles may assign flex-grow to board sections,
 * which makes Risks / Actions / Todos share remaining height equally.
 * Explicitly disable flex growth and let content determine section height.
 */

.decision-board-scroll {
  display: block !important;
  height: auto !important;
}

.decision-board-scroll > .decision-board-overview,
.decision-board-scroll > .board-section,
.decision-board-scroll > .decision-board-links {
  flex: 0 0 auto !important;
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
  flex-basis: auto !important;

  width: auto;
  height: auto !important;
  min-height: 0 !important;
  max-height: none !important;
}

.decision-board-scroll > .board-section {
  display: block !important;
  overflow: visible !important;
}

.board-section > .board-actions,
.board-section > .board-todo,
.board-section > .board-risk {
  flex: 0 0 auto !important;
  height: auto !important;
  min-height: 0 !important;
  max-height: none !important;
}

/* Risks, actions and todos consume only their real content height. */
.board-risk,
.board-actions,
.board-todo {
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
}

/* Only the outer Decision Board body scrolls. */
.decision-board-scroll {
  min-height: 0 !important;
  flex: 1 1 auto !important;
  overflow-y: auto !important;
  overflow-x: hidden;
}
"""

marker = "Sprint 3-2.3.2"
if marker not in text:
    css.write_text(text.rstrip() + addition + "\n", encoding="utf-8")
    print("Sprint 3-2.3.2 flex height hotfix applied:", css)
else:
    print("Sprint 3-2.3.2 already applied:", css)
