# General Reasoner v1 — Phase 2.1 Situation Grounding

## Goals

1. Structured current state outranks conversation text.
2. General Reasoner must not resurrect stale/rejected positions from the
   transcript window.
3. General Reasoner must not infer hidden negotiation intent.
4. Active enterprise dependency findings suppress equivalent General
   missing-information findings through operand coverage.
5. Policy sources are marked normative; historical decisions/documents/CRM
   are marked historical.
6. Dialogue explicitly distinguishes enterprise-specific reasoning from
   general decision reasoning.

## Authority order

1. semanticState / decisionState
2. recentEvents
3. conversationText
4. retrieved references

## Regression scenarios

### A. Enterprise negotiation

If policy says:

`discountPercent > 10 requires paymentTermAssessment`

and the enterprise finding is already active, a General finding:

`missing_information / paymentTermAssessment`

must be suppressed.

### B. No-enterprise investment conversation

Claims such as industry growth, gross margin, customer count, competition
barrier and time pressure should still be detected by General Reasoner.
