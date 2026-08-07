#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

cleaner = ROOT / "src/backend/app/context/cleaner.py"
text = cleaner.read_text(encoding="utf-8")

if "from app.context.canonicalizer import canonicalize_business_statements" not in text:
    text = text.replace(
        "from difflib import SequenceMatcher\n",
        "from difflib import SequenceMatcher\n\nfrom app.context.canonicalizer import canonicalize_business_statements\n",
        1,
    )

old = "    consolidated, consolidated_count = _consolidate_business_sentences(deduplicated)\n"
new = old + "    canonical = canonicalize_business_statements(consolidated)\n"
if new not in text:
    if old not in text:
        raise SystemExit("cleaner.py: consolidation hook not found")
    text = text.replace(old, new, 1)

text = text.replace('        clean_text="\\n".join(consolidated).strip(),', '        clean_text="\\n".join(canonical.statements).strip(),', 1)
text = text.replace("        clean_segments=len(consolidated),", "        clean_segments=len(canonical.statements),", 1)

if "    covered_sentences: int\n" not in text:
    text = text.replace(
        "    incomplete_segments: int\n",
        "    incomplete_segments: int\n    covered_sentences: int\n    canonical_statements: int\n",
        1,
    )

if '"coveredSentences"' not in text:
    text = text.replace(
        '            "incompleteSegments": self.incomplete_segments,\n',
        '            "incompleteSegments": self.incomplete_segments,\n            "coveredSentences": self.covered_sentences,\n            "canonicalStatements": self.canonical_statements,\n',
        1,
    )

if "        covered_sentences=canonical.covered_sentences,\n" not in text:
    text = text.replace(
        "        incomplete_segments=incomplete,\n",
        "        incomplete_segments=incomplete,\n        covered_sentences=canonical.covered_sentences,\n        canonical_statements=canonical.canonical_statements,\n",
        1,
    )

cleaner.write_text(text, encoding="utf-8")

models = ROOT / "src/backend/app/context/models.py"
text = models.read_text(encoding="utf-8")
text = text.replace('    builderVersion: str = "context-builder-v0.1.2"', '    builderVersion: str = "context-builder-v0.1.3"')
if "    coveredSentences: int = 0\n" not in text:
    text = text.replace(
        "    incompleteSegments: int = 0\n",
        "    incompleteSegments: int = 0\n    coveredSentences: int = 0\n    canonicalStatements: int = 0\n",
        1,
    )
models.write_text(text, encoding="utf-8")
print("Sprint 2-1.3 patch applied.")
