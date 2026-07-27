# Contributing to DecisionOS

## 1. Contribution flow

1. Create an Issue or reference an existing Issue.
2. Create a focused branch.
3. Update documents, contracts, examples and tests together when applicable.
4. Submit a Pull Request using the repository template.
5. Obtain review before changing an `Approved` specification.

## 2. Document status

- `Draft`: work in progress.
- `Review`: ready for architecture or product review.
- `Approved`: frozen development baseline.
- `Deprecated`: retained for traceability and linked to its replacement.

## 3. Naming

- Product documents: existing numeric names are preserved.
- Specifications: `Spec-NNN_Title.md`.
- Architecture decisions: `ADR-NNNN-short-title.md`.
- Fields and JSON properties: `lowerCamelCase`.
- Object IDs: lowercase type prefix plus stable identifier, such as `meeting-000001`.

## 4. Change rules

- Do not silently redefine terms owned by another approved document.
- Reference `SPEC-001 ContextObject` rather than redefining ContextObject.
- Reference `SPEC-002 Knowledge Object Model` for domain-object boundaries.
- Breaking changes require an ADR and explicit migration notes.
- Do not commit secrets, credentials, private customer data or model keys.
