# General Reasoner v1 — Phase 1

This phase is intentionally isolated from the production reasoning chain.

## Added

`backend/app/reasoning/general/`

- `models.py` — Candidate/result contracts
- `context.py` — RuntimeState -> GeneralReasoningContext
- `prompts.py` — signal-detection prompt
- `backend.py` — LLM/Null backend boundary
- `finding_gate.py` — deterministic candidate -> Finding authority gate
- `reasoner.py` — standalone orchestration
- `__init__.py`

Test:

- `tests/test_general_reasoner_phase1.py`

## Not changed

- `ReasoningService`
- `FindingRepository` / `FindingLifecycleManager`
- `RecommendationGenerator`
- `DecisionBoard`
- `Dialogue`

Therefore this phase cannot affect current production findings or reminders.

## Principle

The LLM can only propose `GeneralFindingCandidate` objects.
It cannot create an active `Finding` directly.

Pipeline:

`RuntimeState -> GeneralReasoningContext -> Backend -> Candidate[] -> FindingGate -> Finding[]`

General taxonomy is stored in `Finding.attributes.generalFindingType` while the existing Finding taxonomy remains stable:

- claim -> risk
- contradiction -> conflict
- missing_information -> gap
- uncertainty -> risk
- decision_risk -> risk
