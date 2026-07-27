#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p docs/product docs/architecture docs/specs docs/adr docs/diagrams docs/templates schemas examples src/backend src/frontend src/ai
move_if_exists() { src="$1"; dst="$2"; if [ -f "$src" ]; then mkdir -p "$(dirname "$dst")"; git mv "$src" "$dst" 2>/dev/null || mv "$src" "$dst"; echo "Moved $src -> $dst"; fi; }
move_if_exists docs/000_Product_Constitution.md docs/product/000_Product_Constitution.md
move_if_exists docs/001_Product_Vision.md docs/product/001_Product_Vision.md
move_if_exists docs/002_MVP_Definition.md docs/product/002_MVP_Definition.md
move_if_exists docs/003_Context_Engine.md docs/architecture/003_Context_Engine.md
move_if_exists docs/specs/Spec-001_ContextObject.md docs/specs/Spec-001_ContextObject.md
move_if_exists docs/specs/Spec-002_Knowledge_Object_Model.md docs/specs/Spec-002_Knowledge_Object_Model.md
# Remove .gitkeep where actual files now exist
find docs schemas examples src -name .gitkeep -type f | while read -r f; do d="$(dirname "$f")"; [ "$(find "$d" -mindepth 1 -maxdepth 1 ! -name .gitkeep | wc -l)" -gt 0 ] && rm -f "$f" || true; done
echo "Repository v1.0 migration completed. Review with: git status"
