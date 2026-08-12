# Sprint 3-3.3.1 Semantic Runtime Stabilization

本阶段只稳定 Semantic Runtime，不扩展 Decision Board UI，也不加入 Semantic Active Risk Reasoning。

## Changes

1. **Meeting-date anchored date normalization**
   - Semantic Extractor receives the authoritative meeting date.
   - Dates without a year (for example `10月1日`) are normalized relative to the meeting date.
   - Past dates are rejected/adjusted unless the utterance explicitly refers to the past.

2. **semanticHistory / semanticState separation**
   - `decisionFacts.semanticHistory` is append-only semantic history.
   - `decisionFacts.semanticState` contains only current effective semantic objects.
   - New values replace the previous value in the same semantic slot.
   - `withdrawn` / `rejected` objects are removed from current state but remain in history.

3. **Approval / Contract domain governance**
   - Contract clauses remain in `contract`.
   - Approval/review/authorization dependencies required before signing/proceeding are normalized to `approval`.

4. **Actor normalization**
   - Runtime actor values are limited to `customer | us | third_party | unknown`.
   - Unknown speaker/party is never guessed.
   - Explicit third-party text can be retained in `metadata.actorText`.

## Verification

```bash
DATABASE_URL='sqlite+pysqlite:///:memory:' \
PYTHONPATH=src/backend \
python -m pytest -q \
  tests/test_semantic_event_validator.py \
  tests/test_semantic_runtime_reducer.py \
  tests/test_hybrid_event_extractor.py \
  tests/test_event_extractor.py
```

Expected: `15 passed`.
