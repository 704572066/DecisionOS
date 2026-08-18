# Phase 2.3.1 — Proactive Intervention Policy

This phase adds deterministic attention governance after reasoning.

Pipeline:

Reasoning Findings + Recommendations + RuntimeState
→ InterventionPolicy
→ silent | surface | interrupt

## Invariants

- Severity is not urgency.
- High severity alone never implies interruption.
- Interrupt requires high/critical severity, explicit high/critical urgency,
  sufficient confidence, decision relevance, actionability and score.
- Resolved findings are always silent.
- Repeated interrupt-worthy findings are downgraded during cooldown.
- Intervention failure must not break ReasoningResult.
- No LLM decides whether to interrupt in Phase 2.3.1.

DecisionBoard exposes decisions under `reasoning.interventions` only.
No websocket / TTS / frontend interruption is implemented in this phase.
