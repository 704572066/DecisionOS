#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "src/frontend/src/main.tsx"
text = path.read_text(encoding="utf-8")

old_type = '''type Reminder = {
  title: string;
  summary: string;
  source: {type: string; id: string};
  relevanceScore: number;
};'''
new_type = '''type Reminder = {
  type?: string;
  title: string;
  summary: string;
  suggestion?: string;
  reason?: string;
  sources?: Array<{type: string; id: string; title?: string; score?: number}>;
  source: {type: string; id: string};
  relevanceScore: number;
  confidence?: number;
};'''
if new_type not in text and old_type in text:
    text = text.replace(old_type, new_type, 1)

old_card = '''              <p>{reminder.summary}</p>
              <small>'''
new_card = '''              <p>{reminder.summary}</p>
              {reminder.suggestion && (
                <p className="reminder-suggestion">
                  <strong>建议：</strong>{reminder.suggestion}
                </p>
              )}
              {reminder.reason && (
                <p className="reminder-reason">
                  <strong>依据：</strong>{reminder.reason}
                </p>
              )}
              <small>'''
if "reminder-suggestion" not in text and old_card in text:
    text = text.replace(old_card, new_card, 1)

path.write_text(text, encoding="utf-8")
print("Sprint 2-3 frontend patch applied.")
