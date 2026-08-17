# General Reasoner v1 — Phase 2.2.2 Normative Boundary Guard

## Principle

Once enterprise policy has been compiled into `EvaluationConstraint`, the
Constraint Engine is authoritative for normative applicability.

General Reasoner may explain or supplement policy context, but it must not:

- turn `>` into `>=`;
- require an operand when the primary trigger is false;
- emit a duplicate General warning for an active Enterprise Finding;
- claim a missing normative requirement when that requirement is already
  satisfied.

## Deterministic suppression reasons

- `normative_precondition_not_satisfied`
- `normative_issue_already_covered`
- `normative_requirement_already_satisfied`

## Canonical boundary test

Policy:

`discountPercent > 10 -> paymentTermAssessment exists`

Current state:

`discountPercent = 10`

Expected:

- Enterprise dependency: inactive/resolved
- General payment-term compliance warning: suppressed
- diagnostic reason: `normative_precondition_not_satisfied`
