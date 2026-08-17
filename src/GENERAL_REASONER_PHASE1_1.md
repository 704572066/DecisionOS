# General Reasoner v1 / Phase 1.1 — Signal Discipline

This patch tightens the standalone General Reasoner. It still does **not** connect to production `ReasoningService`.

## Changes

- General candidates may only use severity `low|medium|high`; LLM cannot emit `critical`.
- Candidate adds:
  - `specificity`
  - `evidenceDirectness`
  - `directlyObserved`
  - `directlyNeeded`
- Prompt explicitly prohibits due-diligence/domain checklists.
- `missing_information` must be an immediate prerequisite for the concrete decision being discussed.
- Non-missing signals must be directly observed and directly grounded.
- Deterministic Gate rejects generic/weak signals.
- Intervention budget limits accepted General Findings to at most 5 per cycle.

## Expected investment LLM test behavior

The previous 10/10 result should shrink substantially. Strong candidates should be dominated by directly observed signals such as:

- industry growth 50% claim
- gross margin 40% claim
- 20 large customers claim
- competitive barrier claim
- artificial urgency / "decide this week"

Generic checklist candidates such as generic team background, board seat, fund-use plan, or generic exit-mechanism requirements should either not be generated or be rejected.

## Tests

```bash
python tests/test_general_reasoner_phase1.py
python tests/test_general_reasoner_llm.py
```
