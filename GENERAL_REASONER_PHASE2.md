# General Reasoner v1 — Phase 2.0 Shared Reasoning Integration

This patch integrates General Reasoner into the existing shared Reasoning pipeline.

## Pipeline

RuntimeState
-> Enterprise Policy Reasoning
-> General Reasoner (receives active policy findings)
-> SharedFindingMerger
-> RecommendationSetEvaluator
-> ReasoningResult
-> shared snapshot
-> DecisionBoard / Dialogue

## Important boundaries

- General Reasoner failure does not fail enterprise-policy reasoning.
- Enterprise findings have deterministic merge priority.
- General findings do not yet have their own persisted Finding lifecycle in Phase 2.0.
  They are current-cycle findings; Recommendation lifecycle still handles obsolete recommendations.
- Active voice interruption/TTS is not included.

## Added/changed

- NEW `backend/app/reasoning/shared_finding_merger.py`
- MOD `backend/app/reasoning/service.py`
- MOD `backend/app/reasoning/models.py`
- MOD `backend/app/reasoning/recommendation_generator.py`
- MOD `backend/app/decision_board/service.py`
- MOD `backend/app/reasoning/__init__.py`

## Tests

```bash
python tests/test_shared_finding_merger.py
python tests/test_general_recommendation_adapter.py
python tests/test_general_reasoner_phase2_integration.py
```
