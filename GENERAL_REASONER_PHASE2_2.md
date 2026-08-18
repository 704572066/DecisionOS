# General Reasoner Phase 2.2 — State-grounded Reasoning

## Scope

Phase 2.2 does not add new reasoning types. It strengthens the grounding boundary between runtime state, conversation history, enterprise policy findings, and General Reasoner output.

## Changes

### 1. State Evolution replay
`RuntimeStateService` now replays every unprocessed final transcript segment in ascending sequence order instead of processing only the latest segment. This prevents intermediate proposals/rejections from being skipped when multiple transcript segments arrive between DecisionBoard refreshes.

Expected example:
- 18% proposed
- 15% rejected
- 10% confirmed

The reducer can now receive the complete event sequence and resolve the latest participant position instead of remaining stale at an earlier segment.

### 2. State Authority Enforcement
`FindingGate` rejects a General candidate when it tries to use `conversation_text` to make a current-state claim for a subject that already has structured current-state authority, unless the candidate also grounds itself in that authoritative structured source.

Rejection reason:
`conversation_cannot_override_current_state`

### 3. Semantic Compatibility Guard
A General `contradiction` that directly compares discount percentage with gross-margin percentage is rejected unless a future explicit calculation/conversion layer establishes such a relationship.

Rejection reason:
`incompatible_metric_comparison`

### 4. Robust Enterprise Coverage
Enterprise dependency operand coverage is now subject-centric rather than requiring the LLM-generated General domain to match the enterprise domain.

Therefore:
- Enterprise: `commercial / discountPercent > 10 -> paymentTermAssessment exists`
- General: `general / paymentTermAssessment / missing_information`

is suppressed as the same underlying issue.

Rejection/suppression reason:
`enterprise_dependency_operand_already_covered`

## Verification

Run:

```bash
python tests/test_general_reasoner_phase2_2_guards.py
python tests/test_general_reasoner_phase2_1_grounding.py
python tests/test_general_reasoner_phase2_1_source_authority.py
```

The package was syntax-checked with `python -m compileall backend/app`.
