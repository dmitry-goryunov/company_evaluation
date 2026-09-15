# Oman LNG evaluation run

This directory contains the Standard-tier, public-source Oman LNG evaluation completed on 15 September 2026.

## Decision status

- Research objective: general company profile
- C9 status: WARNINGS
- Conclusion cap: decision-not-ready
- Human review: not performed
- Investment action: not authorised

The warning is substantive: public information is insufficient to evaluate capital-allocation discipline. The absence of audited balance-sheet and cash-flow disclosure separately blocks credit, investment and counterparty-exposure sizing.

## Main output

- `final/Oman_LNG_Company_Evaluation_2026-09-15.md`

## Reproduce the policy check

From the repository root:

```bash
python checks/c9_policy_linter.py \
  runs/oman_lng_2026-09-15/final/Oman_LNG_Company_Evaluation_2026-09-15.md \
  --project-root runs/oman_lng_2026-09-15 \
  --report runs/oman_lng_2026-09-15/working/c9_linter_report.md
```

Expected exit code: `2` (`WARNINGS`). The report contains one `DEPTH_CONTROL_K9` warning.

## Scope limitation

The supplied NotebookLM notebook required a separate Google sign-in that was not completed. No NotebookLM-only output is treated as evidence. The run relies on the supplied Drive documents and independently checked public sources recorded in `sources/source_register.csv`.
