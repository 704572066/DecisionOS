# Sprint 3-3.3 — Decision Semantic Runtime

## Goal

Expand DecisionOS from hard-coded price/payment phrase matching into a schema-guided semantic decision runtime while preserving the deterministic Runtime reducer.

## Architecture

```text
Final Transcript Segment
        ↓
Fast Rule Extractor
        +
Semantic Event Extractor (LLM)
        ↓
Semantic Event Validator
        ↓
Hybrid Decision Events
        ↓
Runtime State Reducer
        ↓
Current Decision State
```

LLM responsibilities are limited to semantic interpretation. The LLM never mutates `RuntimeState` directly.

## Semantic domains

- commercial
- delivery
- scope
- resource
- contract
- commitment
- approval
- decision
- unknown / other

## Runtime behavior

Existing price/payment rule events remain authoritative. Semantic extraction supplements broader business meaning such as delivery deadlines, scope changes, staffing limits, contract liabilities, commitments and approval dependencies.

Semantic objects are stored under:

```json
{
  "decisionFacts": {
    "semanticState": {
      "delivery": [],
      "scope": [],
      "resource": [],
      "contract": [],
      "commitment": [],
      "approval": []
    }
  }
}
```

Replaceable state-like semantic slots overwrite their previous value. Commitments/dependencies/decisions accumulate as history-relevant objects.

## Configuration

```env
SEMANTIC_EVENT_ENABLED=true
SEMANTIC_EVENT_MIN_CONFIDENCE=0.72
```

If the LLM is not configured or semantic extraction fails, DecisionOS falls back to the existing deterministic rule path.
