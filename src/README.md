# DecisionOS Sprint 3-4.6-B Authority Switch

This patch switches DecisionBoard authority to the new generic Reasoning pipeline.

Key changes:
- `DecisionBoardService` no longer calls legacy `decision_board_engine`.
- New `DecisionBoardBuilder` is a pure projection layer.
- `Finding -> BoardRisk`
- `Recommendation -> BoardAction`
- `rerankedEvidence -> BoardEvidence`
- Runtime state -> currentConditions/recentEvents
- No business thresholds or field-specific decision logic in the new builder.

Files:
- backend/app/decision_board/builder.py (new)
- backend/app/decision_board/reasoning_adapter.py (included if missing)
- backend/app/decision_board/service.py (replace)
- tests/test_decision_board_authority_switch.py
