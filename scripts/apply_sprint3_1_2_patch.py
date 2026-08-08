#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
front = ROOT / "src/frontend/src/main.tsx"
text = front.read_text(encoding="utf-8")

# Keep only the latest 5 completed reminders.
text = text.replace(
    "[...payload.reminders, ...current].slice(0, 10)",
    "[...payload.reminders, ...current].slice(0, 5)",
)

# Add refs.
if "transcriptScrollRef" not in text:
    marker = "  const [reminders, setReminders] = useState<Reminder[]>([]);\n"
    if marker not in text:
        raise SystemExit("reminders state marker not found")
    text = text.replace(
        marker,
        marker
        + "  const transcriptScrollRef = useRef<HTMLDivElement | null>(null);\n"
        + "  const reminderScrollRef = useRef<HTMLDivElement | null>(null);\n",
        1,
    )

# Ensure useRef is imported from React.
lines = text.splitlines()
for i, line in enumerate(lines):
    if "from 'react'" in line or 'from "react"' in line:
        if "useRef" not in line:
            if "{" in line:
                line = line.replace("{", "{ useRef,", 1)
                line = line.replace("  ", " ", 1)
            else:
                raise SystemExit("React import format unsupported")
            lines[i] = line
        break
text = "\n".join(lines) + "\n"

# Auto-scroll transcript to latest content.
if "transcriptScrollRef.current" not in text:
    marker = "  useEffect(() => {\n"
    idx = text.find(marker)
    if idx == -1:
        raise SystemExit("useEffect marker not found")
    effect = """  useEffect(() => {
    const node = transcriptScrollRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [transcript]);

"""
    text = text[:idx] + effect + text[idx:]

# Wrap transcript <pre> if present.
if 'className="transcript-scroll"' not in text:
    marker = "          <pre>{transcript}</pre>\n"
    if marker in text:
        text = text.replace(
            marker,
            """          <div className="transcript-scroll" ref={transcriptScrollRef}>
            <pre>{transcript}</pre>
          </div>
""",
            1,
        )

# Add refs/classes to known panels.
text = text.replace(
    'className="transcript-panel"',
    'className="transcript-panel realtime-column"',
)
text = text.replace(
    'className="reminder-panel"',
    'className="reminder-panel realtime-column"',
)

# Wrap completed reminder list only once.
if 'className="reminder-scroll"' not in text:
    start_marker = "          {reminders.map((reminder, index) => (\n"
    if start_marker not in text:
        raise SystemExit("reminders.map marker not found")
    text = text.replace(
        start_marker,
        """          <div className="reminder-scroll" ref={reminderScrollRef}>
            {reminders.map((reminder, index) => (
""",
        1,
    )
    start = text.find('className="reminder-scroll"')
    close = text.find("          ))}\n", start)
    if close == -1:
        raise SystemExit("reminders.map close marker not found")
    close += len("          ))}\n")
    text = text[:close] + "          </div>\n" + text[close:]

front.write_text(text, encoding="utf-8")
print("Sprint 3-1.2 patch applied:", front)
