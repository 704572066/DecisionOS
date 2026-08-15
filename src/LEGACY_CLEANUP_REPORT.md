# Sprint 3-4.6-C Legacy DecisionBoard Cleanup

## Scan conclusion

The uploaded `src(4).zip` had already switched `DecisionBoardService` to the new Reasoning authority,
but the repository still contained the complete legacy DecisionBoard implementation and two temporary
Board-level metrics.

### Removed legacy DecisionBoard modules

- `backend/app/decision_board/engine.py`
- `backend/app/decision_board/claim_guard.py`
- `backend/app/decision_board/signal.py`
- `backend/app/decision_board/signal_engine.py`
- `backend/app/decision_board/event_analyzer.py`
- `backend/app/decision_board/priority.py`

These modules were either referenced only by the legacy engine family or had no live references from
the current Reasoning -> DecisionBoard projection path.

### Removed Board contract fields

- `status`
- `decisionReadiness`
- `DecisionStatus`

Also removed:
- `DecisionBoardBuilder._status`
- `DecisionBoardBuilder._decision_readiness`
- frontend status label mapping
- frontend decision maturity display/progress bar
- associated CSS

## Retained current architecture

`RuntimeState -> ReasoningService -> DecisionBoardBuilder`

DecisionBoard remains a projection surface:
- `Finding -> risks`
- `Recommendation -> actions`
- `rerankedEvidence -> evidence`
- Runtime state -> `currentConditions` / `recentEvents`

## Post-cleanup exact legacy scan

Backend/repository legacy identifiers:
```
/mnt/data/decisionos_3_4_6_C_legacy_cleanup/tests/test_decision_board_authority_switch.py:103:assert "decisionReadiness" not in payload
/mnt/data/decisionos_3_4_6_C_legacy_cleanup/README.md:6:- `DecisionBoardService` no longer calls legacy `decision_board_engine`.
```

Frontend removed-metric UI references:
```
(none)
```
