# Process Change Log

| date | version | change | reason | triggering_run | approved_by | scope | rollback_note |
|---|---|---|---|---|---|---|---|
| 2026-06-25 | patch-2026-06-25 | 11-point enforcement patch after Harbour Energy test run | Harbour Energy AUTO run produced a C9 memo with three unresolved C8 must-answer items and investment-action language ("INVEST WITH CONDITIONS", "initiate at 50%"), demonstrating that existing policy rules were not machine-enforced at C9. | Harbour Energy plc (HBR) AUTO run, 2026-06-25, claude-sonnet-4-6 | User (Harbour Energy post-run memo review) | pipeline_core.md, pipeline_reference.md, README.md, checks/c9_policy_linter.py, tests/ | Revert by restoring prior versions of pipeline_core.md and pipeline_reference.md from git; delete checks/c9_policy_linter.py and tests/. |

## Patch detail

### Changes to pipeline_core.md

1. **§8A.10 C8-blocker rule** — Added explicit prohibition on investment-action language when
   `unresolved_must_answer_count > 0`, with required replacement wording (DECISION-NOT-READY /
   THESIS TRACKING). Lists prohibited phrases and required language.

2. **§8A.11 Mandatory YAML status block** — Added `c9_status_block` YAML block with 11 fields
   (`c9_status`, `gate_mode`, `human_review_performed`, `investment_decision_approved`,
   `c0_recommendation_cap`, `unresolved_must_answer_count`, `unresolved_high_risk_count`,
   `unresolved_critical_gap_count`, `allowed_conclusion_language`, `investment_action_allowed`,
   `position_sizing_allowed`) plus mandatory derivation rules:
   - `human_review_performed = no` → `investment_action_allowed = no`, `position_sizing_allowed = no`
   - `unresolved_must_answer_count > 0` → `allowed_conclusion_language = decision-not-ready`,
     `investment_action_allowed = no`, `position_sizing_allowed = no`
   - Linter must refuse CLEAN if any field is blank or any derivation rule is violated.
   The existing 12-row markdown table is retained as the human-readable companion block.

3. **§18 Do-not-proceed** — Added three new bullets:
   - `unresolved_must_answer_count > 0` without human override
   - required C9 artefacts absent
   - c9_status_block YAML absent, incomplete, or violated

4. **§21 C9 artefact-presence check list** — New subsection listing 8 required artefacts
   (hard blockers if absent: facts_ledger.md, evidence_gaps.md, open_questions.md,
   decision_log.md, c9_linter_report.md, c9_repair_log.md, claim_audit.md,
   disconfirming_evidence.md) plus the source evidence alternative rule (source_register.csv
   OR notebooklm_outputs/raw/ non-empty).

### Changes to pipeline_reference.md

5. **C2 valuation output schema** — Added 12-column schema for every valuation table:
   method, value, share_basis, share_count_used, net_debt_basis, hybrid_treatment,
   decommissioning_treatment, capital_need_treatment, scenario_link, evidence_level,
   fact_ids, decision_maturity.

6. **C6 scenario output schema** — Added 10-field schema for each scenario:
   scenario_name, operating_assumption, capital_assumption, dilution_assumption,
   timing_assumption, evidence_for, evidence_against, falsifier, valuation_relevance, risk_link.

7. **C7 hard propagation rule** — Added 5-item checklist per unresolved High/Critical risk.
   Critical risk requires human review; AUTO mode may not silently accept it.

8. **§10A.5 section J — Contradiction linter** — Added four contradiction types:
   - Type 1: human_review = no + investment-action language
   - Type 2: must-answer count > 0 + investment-action language
   - Type 3: c9_status CLEAN + open items without human override
   - Type 4: sourcing claim + absent evidence pack
   Any surviving contradiction after repair → c9_status = BLOCKED.

9. **§10D loopback table** — Added row: C8 unresolved + investment-action language in draft
   C9 → BLOCKED (contradiction type 2); apply C8-blocker rule.

10. **§23 Decision-log override protocol** — Added 10-field YAML override structure
    (reviewer, review_date, review_scope, open_items_reviewed, override_granted, override_reason,
    accepted_risks, position_sizing_approved, approved_action, follow_up_required) with rules:
    - `open_items_reviewed` must name every must-answer item being overridden
    - AUTO mode cannot grant an override
    - Final memo must still disclose open items alongside the override basis

### Changes to README.md

11. **Research objectives** — Section renamed "Common research objectives"; added five more
    objectives (IPO, distressed, competitor benchmarking, ESG, technology deep-dive).
    **C-stage execution order** — Documented correct order (C0→C1→C3→C6→C2→C4→C5→C7→C8→C9)
    with explanation that numerical order ≠ execution order.

### New files

- `checks/c9_policy_linter.py` — Python linter implementing all four contradiction checks
  and YAML field validation. Exit code 0=CLEAN, 1=BLOCKED, 2=AUTO-REPAIRED.
- `tests/fixtures/harbour_memo_unresolved_c8.md` — Negative test fixture demonstrating all
  four contradiction types simultaneously.
- `tests/expected/harbour_memo_unresolved_c8.expected_status.txt` — Expected BLOCKED output
  with correct DECISION-NOT-READY replacement wording.
