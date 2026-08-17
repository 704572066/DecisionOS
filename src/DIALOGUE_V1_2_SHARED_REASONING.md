# Dialogue v1.2 — Shared Reasoning Context

## Goal

DecisionBoard and Dialogue must consume one `ReasoningResult` for one
`RuntimeState` revision. Lifecycle-aware reasoning must not execute once per
interaction surface.

## Flow

```text
RuntimeState revision
        ↓
ReasoningService.get_or_reason()
        ↓
ReasoningSnapshotStore
   ┌────┴────┐
   ↓         ↓
Board     Dialogue
```

A snapshot key currently consists of `contextId`,
`lastProcessedSegmentSequence`, and `updatedAt`. A new runtime revision misses
the snapshot and computes/publishes a new `ReasoningResult`.

The store also uses a meeting-scoped `asyncio.Lock`, preventing concurrent
Board/Dialogue requests from both running reasoning for the same state.

## Dialogue grounding additions

- `customer + requirement + confirmed` means the customer's requirement is
  established. It does **not** mean mutual acceptance/final agreement.
- Historical evidence must not be inserted into the current meeting timeline.
- An 8% historical case must be described as historical/reference evidence
  unless current meeting state/events explicitly show that 8% was proposed.
