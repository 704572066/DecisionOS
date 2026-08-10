from pathlib import Path


def patch_file(path, marker, insert):
    p = Path(path)
    if not p.exists():
        raise RuntimeError(f"file not found: {path}")

    text = p.read_text(encoding="utf-8")

    if insert.strip() in text:
        print(f"[SKIP] already patched: {path}")
        return

    if marker not in text:
        raise RuntimeError(f"marker not found: {path}\n{marker}")

    text = text.replace(marker, insert + "\n" + marker, 1)
    p.write_text(text, encoding="utf-8")
    print(f"[OK] patched: {path}")


# Add DecisionSignal into existing type DecisionBoard block area
patch_file(
    "src/frontend/src/main.tsx",
    "type DecisionBoard = {",
    """
type DecisionSignal = {
  level: "NOW" | "NEXT" | "LATER";
  type: string;
  title: string;
  message: string;
};
"""
)

# Insert UI before existing NOW section
patch_file(
    "src/frontend/src/main.tsx",
    "🔴 NOW 当前关注",
    """
                <section className="board-section signal-layer">
                  <div className="board-section-title">
                    <strong>🤖 AI Decision Signal</strong>
                  </div>
                  {(decisionBoard.signals || []).map((signal) => (
                    <article
                      key={`${signal.level}-${signal.title}`}
                      className={`signal-card signal-${signal.level}`}
                    >
                      <strong>{signal.title}</strong>
                      <p>{signal.message}</p>
                    </article>
                  ))}
                </section>

"""
)

css = Path("src/frontend/src/style.css")
if not css.exists():
    raise RuntimeError("file not found: src/frontend/src/style.css")

css_insert = """
.signal-card {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
}

.signal-NOW {
  border-left: 4px solid red;
}

.signal-NEXT {
  border-left: 4px solid orange;
}

.signal-LATER {
  border-left: 4px solid gray;
}
"""

css_text = css.read_text(encoding="utf-8")
if css_insert.strip() not in css_text:
    css.write_text(css_text + "\n" + css_insert, encoding="utf-8")
    print("[OK] patched: src/frontend/src/style.css")
else:
    print("[SKIP] css already patched")

print("Sprint 3-3.1.1 frontend patch completed")
