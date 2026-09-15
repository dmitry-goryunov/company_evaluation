# Implementation backlog

This repository now provides an executable C9 policy linter, tests and CI. It does not yet provide a
complete autonomous pipeline runner. The following improvements are deliberately tracked rather than
claimed as implemented.

## Priority 1

- Add a `company-evaluation init/run/resume` CLI with a versioned run manifest and stage state machine.
- Move policy constants and schemas into one machine-readable source, then generate prose tables and
  validation rules from it to prevent core/reference drift.
- Add source-file hashes, retrieval timestamps, legal-entity identifiers and claim-to-source links to
  a structured provenance store.
- Enforce claim-audit coverage and risk propagation from C7 to C0, C2 and C9 in code.

## Priority 2

- Extract reusable, unit-tested libraries for cash roll-forward, fully diluted share count and
  enterprise-value-to-equity bridges instead of generating one-off scripts in each run.
- Add a synthetic end-to-end company corpus covering filings, cap-table changes, contradictory
  disclosures, stale data and NotebookLM failure modes.
- Make tier escalation and objective overlays executable policy rather than agent-reviewed guidance.
- Model valuation depth on separate axes for evidence maturity, scenario quality, denominator quality
  and liability-bridge completeness.

## Priority 3

- Add proportional source acquisition with stop conditions, duplicate detection and source-quality
  budgets so “deep search” has a bounded cost.
- Support independent-model or human reconstruction for the highest-risk valuation and recommendation
  stages. A fresh context from the same vendor provides context independence, not full independence.
- Publish a migration guide and policy changelog for schema evolution.
