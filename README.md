# Company Evaluation Pipeline

An evidence-graded policy specification and validation toolkit for company research. The repository
defines a 17-stage research process, reusable run templates, an executable C9 memo linter and CI.

The Markdown policy is written for an agent such as Claude Code to execute. This repository does not
yet ship an autonomous stage runner, source downloader or the per-company B1/B2/C2 numeric checks.
Those checks are generated and saved during a research run. The distinction matters: only controls
listed as automated in `pipeline_reference.md` are enforced by the supplied Python code.

## What is in the repository

| Path | Purpose |
|---|---|
| `pipeline_core.md` | Canonical always-load rules, objectives, tiers, gates and stop conditions |
| `pipeline_reference.md` | Canonical stage procedures, evidence protocols, checklists and appendices |
| `checks/c9_policy_linter.py` | Read-only validation of status, approvals, artefacts and selected memo policies |
| `templates/` | Copyable C9 status, decision-log and repair-log schemas |
| `tests/` | Executable positive and negative fixtures |
| `build_dist.py` | Deterministic generator for the combined export |
| `dist/` | Generated single-file export; do not edit it directly |
| `docs/implementation_backlog.md` | Explicitly deferred engineering work |
| `legacy/` | Original non-canonical combined file, retained for reference |

Make policy changes only in `pipeline_core.md` and `pipeline_reference.md`, then regenerate the
distribution file.

## Quick start

Requirements:

- Python 3.10 or later for the repository tools
- an agent capable of following the Markdown policy and reading/writing a local project workspace
- a Google account and [`notebooklm-py`](https://github.com/teng-lin/notebooklm-py) only if using the
  NotebookLM workflow

`notebooklm-py` is an unofficial client that depends on undocumented NotebookLM APIs. Authentication
and commands may change upstream. Treat it as an optional integration, review the version you install,
and never commit its cookies or browser-session files.

Run the repository checks:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python build_dist.py --check
```

Regenerate the deterministic combined export after editing either canonical policy file:

```bash
python build_dist.py
```

## Run the research policy

Start the agent in a new company workspace and load `pipeline_core.md`. Its dispatch table identifies
the exact section of `pipeline_reference.md` to read at each stage. Configure:

1. the research objective;
2. the Screen, Standard or Full depth tier;
3. MANUAL or AUTO gate mode;
4. the source locations and, if used, the active NotebookLM notebook.

AUTO mode controls execution continuity only. It never grants human judgement, an investment decision
or position sizing. MANUAL mode pauses at defined human gates.

The canonical objectives are:

| Objective | Mandatory modules and overlay |
|---|---|
| Public equity investment | A1, B1, B2, B6, C0–C9 |
| Private investment / venture / growth | A1, B1–B6, C0–C9; cap table, customer evidence, runway |
| Credit or lending | A1, B1, C3, C7; debt, covenants, cash flow, collateral, downside |
| M&A target diligence | A1, B1–B6, C0–C9; synergies, transaction blockers |
| M&A buyer screening | A1, C1, C4, C5, C7; strategic fit, financing capacity |
| Strategic partnership / JDA | A1, B4, B5, B6; IP, product fit, readiness, governance |
| Supplier or vendor diligence | A1, B1, B4, B5, B6, C7; compliance, references, continuity |
| Customer / competitor intelligence | A1, B3, B4, C1, C7 |
| Distressed / restructuring | A1, B1, B2, C7; security, liquidity, creditors, recovery value |
| Governance / fraud-risk | A1, B1, B6, C7; ownership, related parties, auditor, controls |
| General company profile | A1, B1, B3, B6, C1, C7, C9-lite |

The objective selects applicable modules. The tier changes the depth of those modules. A Screen can
escalate to Standard, and Standard to Full, when the triggers in `pipeline_core.md` are met.

## Validate a C9 memo

Draft the memo at `working/memo_draft.md`, using `templates/c9_status_block.md` near the top. Create the
required project artefacts and run:

```bash
python checks/c9_policy_linter.py \
  path/to/project/working/memo_draft.md \
  --project-root path/to/project \
  --report path/to/project/working/c9_linter_report.md
```

Exit codes are stable for automation:

| Code | Status | Meaning |
|---:|---|---|
| 0 | CLEAN | No automated finding |
| 1 | BLOCKED | A hard policy violation remains |
| 2 | WARNINGS | Only non-blocking, conclusion-capping findings remain |

The linter is intentionally read-only with respect to the memo. An agent or reviewer must make every
repair, record it in `working/c9_repair_log.md`, rerun affected checks, and then rerun the linter. A
memo may be promoted to `final/memo.md` only after the declared and computed statuses agree.

Use `--no-artifact-checks` only for isolated fixtures, never to approve a real research project.

## Evidence and outputs

Every load-bearing claim should be traceable through the facts ledger to a saved source. The base
classification uses five states: fact, observation, inference, assumption and unknown. Standard and
Full runs add finer evidence classes, decision maturity, supersession status and source incentives.

A normal run produces:

```text
company-research-name/
  pipeline.md
  sources/source_register.csv
  sources/raw/
  notebooklm_outputs/raw/
  working/facts_ledger.md
  working/evidence_gaps.md
  working/open_questions.md
  working/claim_audit.md
  working/disconfirming_evidence.md
  working/falsification_triggers.md
  working/c9_repair_log.md
  working/c9_linter_report.md
  working/checks/
  final/decision_log.md
  final/memo.md
```

The linter checks that core artefacts and at least one inspectable source-evidence route exist. It does
not prove that the underlying sources are true, sufficient or independently verified.

## Security

- Keep source workspaces outside this repository when they contain confidential or MNPI-sensitive
  material.
- Never commit `.env` files, keys, tokens, cookies, browser storage or NotebookLM session data.
- Do not upload confidential documents to a third-party service without authorisation.
- This project does not automate trades, filings, emails, data-room uploads or investor communications.

## Limitations

- The process produces research artefacts, not an automatic investment decision.
- Passing the linter means that its implemented checks passed. It is not an audit, source-veracity
  guarantee, complete legal review or endorsement of the conclusion.
- NotebookLM output remains an extraction aid. Load-bearing claims still require direct verification
  against the primary document.
- A fresh context from the same model vendor provides useful context independence, not full model or
  vendor independence.
- Remaining engineering gaps are tracked in `docs/implementation_backlog.md`.

## Licence

[MIT](LICENSE)
