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

---

| 2026-06-25 | patch-2026-06-25b | Five generic depth controls | Research memos can pass the C9 linter without answering (1) what the market already prices in, (2) the strongest opposing thesis, (3) what would falsify the conclusion, (4) whether valuation is scenario-first, or (5) whether the per-share bridge is complete. These omissions allow a thesis-tracking memo to omit material uncertainty in a way that is policy-compliant but epistemically weak. | Harbour Energy plc (HBR) AUTO run, 2026-06-25, post-patch review | User (Five Generic Depth Controls memo, 2026-06-25) | pipeline_core.md, pipeline_reference.md, checks/c9_policy_linter.py | Revert by reverting pipeline_core.md and pipeline_reference.md to commit 6b410c9; remove K-check functions from c9_policy_linter.py. |

## Patch detail (patch-2026-06-25b)

### Changes to pipeline_core.md

1. **§8A.0 proportionality table** — Added rows for 8A.14 (market-implied expectations +
   opposing thesis) and 8A.15 (full economic share-basis and liability bridge).

2. **§8A.14 Market-implied expectations and opposing thesis** (new section) — Two required
   outputs for Standard and Full tier valuation-mandate runs:
   - `working/market_implied_expectations.md` (7 fields) — required when memo uses mispricing
     language; `alternative_rational_explanation` must be completed.
   - `working/opposing_thesis.md` (6 fields) — required for Standard and Full tier; if
     `resolution_status = unresolved`, conclusion caps to thesis-tracking or decision-not-ready.

3. **§8A.15 Full economic share-basis and liability bridge** (new section) — 12-row bridge
   from EV to per-share output must be completed before headlining a per-share figure; share
   denominator must be inherited from B2. Unknown material rows cause `bridge-incomplete` label.

4. **§18 Do-not-proceed** — Four new bullets:
   - `market_implied_expectations.md` absent but mispricing language present
   - `opposing_thesis.md` absent for Standard/Full run without opposing-thesis section
   - No "Evidence that would change the conclusion" section with specific falsifiers
   - C2 per-share figure without completed liability bridge

5. **§21 C9 artefact-presence check list** — Added three conditionally required artefacts:
   `working/market_implied_expectations.md`, `working/opposing_thesis.md`,
   `working/falsification_triggers.md`.

6. **§22 Directory structure** — Added `working/market_implied_expectations.md`,
   `working/opposing_thesis.md`, `working/falsification_triggers.md`,
   `working/capital_structure.md`.

### Changes to pipeline_reference.md

7. **A1 stage** — Added market-implied expectations output requirement: must output
   `working/market_implied_expectations.md` at A1 close for valuation-mandate runs.

8. **C0 stage** — Added opposing thesis requirement: as part of claim audit, document
   `working/opposing_thesis.md`; unresolved opposing thesis caps C9.

9. **C2 stage** — Added full economic liability bridge table (12 rows: EV → per-share
   output); gate rule that per-share figure without complete bridge carries `bridge-incomplete`
   label and is not decision-ready. Added required scenario-first wording for C2.

10. **C6 stage** — Added falsification triggers section: `working/falsification_triggers.md`
    required output (7-field schema); thesis-level falsifiers must appear in C9 "Evidence that
    would change the conclusion" section verbatim.

11. **C7 stage** — Extended hard propagation checklist: HIGH/Critical risks that would destroy
    the central thesis must also appear in `working/falsification_triggers.md`.

12. **§10 C9 memo structure** — Added "decision-depth checks (§8A.14–§8A.15)" section to memo
    structure; added "Evidence that would change the conclusion" note (must list specific
    falsification triggers); added Decision-depth checks template (5 subsections).

13. **§10A.5 section K** — Five new linter checks (K1–K5):
    - K1 BLOCKED: mispricing language without market_implied_expectations.md
    - K2 ADVISORY: no opposing thesis artefact or section (caps conclusion)
    - K3 BLOCKED: no "Evidence that would change the conclusion" section with specific falsifier
    - K4 BLOCKED: base case is arithmetic midpoint of bull and bear
    - K4 ADVISORY: per-share valuation without scenario_link reference
    - K5 ADVISORY: per-share figure without completed liability bridge

14. **§10D loopback** — Five new loopback rows for K1–K5 triggers.

### Changes to checks/c9_policy_linter.py

15. Added five new check functions (`check_mispricing_language`, `check_opposing_thesis`,
    `check_falsification_section`, `check_scenario_midpoint`, `check_liability_bridge`) and
    integrated into `lint()`. K1/K3/K4(midpoint) produce BLOCKED; K2/K5 produce ADVISORY
    (AUTO-REPAIRED if otherwise CLEAN).

---

| 2026-06-25 | patch-2026-06-25c | Five second-layer depth controls | Research memos can satisfy all K-check controls yet still (1) assume the company is exceptional without testing base rates, (2) capitalise adjusted EBITDA without testing recurring cash quality, (3) ignore incentive/control conflicts between stakeholders, (4) assume good future capital allocation without checking the historical record, and (5) produce static research with no expiry or monitoring plan. These are research-quality failures, not decision-discipline failures. | Harbour Energy plc (HBR) AUTO run, 2026-06-25, second-layer review | User (Second-Layer Depth Controls memo, 2026-06-25) | pipeline_core.md, pipeline_reference.md, checks/c9_policy_linter.py | Revert by reverting pipeline_core.md and pipeline_reference.md to commit 0a35d17; remove L-check functions from c9_policy_linter.py. |

## Patch detail (patch-2026-06-25c)

### Changes to pipeline_core.md

1. **§8A.0 proportionality table** — Added rows for 8A.16–8A.20.

2. **§8A.16 Reference-class and base-rate check** (new section) — Required output
   `working/reference_class_base_rate.md` (7 fields). Gate: C9 must not imply exceptional
   outcomes without this artefact. Cap wording if missing.

3. **§8A.17 Quality of earnings and cash conversion** (new section) — Required output
   `working/quality_of_earnings_cash_conversion.md` (10 fields). Gate: C2 may not capitalise
   adjusted EBITDA or guided FCF without `sustainable_cash_flow` field completed.

4. **§8A.18 Incentive and control map** (new section) — Required output
   `working/incentive_control_map.md` (stakeholder table). Gate: C9 must not describe
   governance as favourable without this artefact where triggering conditions exist.

5. **§8A.19 Capital allocation record** (new section) — Required output
   `working/capital_allocation_record.md` (10 categories). Gate: C2/C9 must not assume
   value-accretive future capital allocation without historical record support.

6. **§8A.20 Re-underwriting and monitoring protocol** (new section) — Required output
   `working/monitoring_plan.md` (monitoring table). Gate: C9 without monitoring section
   cannot be decision-ready except by human override.

7. **§18 Do-not-proceed** — Six new bullets (exceptional language without reference class;
   adjusted EBITDA capitalised without quality-of-earnings check; governance/alignment
   conclusions without incentive map; capital allocation assumptions without record;
   no monitoring section).

8. **§21 C9 artefact-presence check list** — Added 5 new conditionally required artefacts.

9. **§22 Directory structure** — Added 5 new working/ files.

### Changes to pipeline_reference.md

10. **B1 stage** — Added quality of earnings (§8A.17) and capital allocation record (§8A.19)
    initiation requirement.

11. **B2 stage** — Added incentive and control map (§8A.18) population requirement.

12. **B6 stage** — Added capital allocation record completion and incentive/control map
    confirmation requirement.

13. **C1 stage** — Added reference-class check (§8A.16) population requirement; reference
    class must inform C6 and C9.

14. **C2 stage** — Added quality-of-earnings gate and capital-allocation gate: C2 may not
    capitalise adjusted EBITDA/FCF without quality-of-earnings artefact; must not assume
    value-accretive allocation without historical record.

15. **C8 stage** — Added monitoring links: unanswered C8 questions tagged with monitoring-plan
    rows; thesis falsifiers linked to monitoring plan.

16. **§10 C9 memo structure** — Updated to include monitoring and re-underwriting plan;
    decision-depth checks extended to §8A.14–§8A.20; Decision-depth checks block template
    extended from 5 to 10 subsections.

17. **§10A.5 section L** — Five new linter checks (L1–L5):
    - L1 BLOCKED: exceptional-outcome language without reference class artefact
    - L2 BLOCKED: EBITDA/FCF multiples without quality-of-earnings artefact
    - L3 ADVISORY: control-structure triggers without incentive map
    - L4 ADVISORY: capital allocation assumptions without record
    - L5 BLOCKED: no monitoring section and no monitoring_plan.md

18. **§10D loopback** — Six new loopback rows for L1–L5 triggers.

### Changes to checks/c9_policy_linter.py

19. Added five new check functions (`check_exceptional_language`, `check_ebitda_quality`,
    `check_incentive_map`, `check_capital_allocation`, `check_monitoring_plan`) and
    integrated into `lint()`. L1/L2/L5 produce BLOCKED; L3/L4 produce ADVISORY
    (AUTO-REPAIRED if otherwise CLEAN).

---

| 2026-06-25 | patch-2026-06-25c-addendum | Rename L1–L5 to K6–K10; downgrade K6/K7/K10 severity to ADVISORY | L1–L5 naming was inconsistent with the K1–K5 naming convention established in patch-2026-06-25b. Severity of K6 (reference class), K7 (quality of earnings), and K10 (monitoring plan) was set to BLOCKED in the initial implementation but the approving memo specified these as ADVISORY (CAPPED). Fix aligns implementation with intent. | patch-2026-06-25c post-implementation review | User (Remaining Process and Implementation Updates memo, 2026-06-25) | pipeline_reference.md, checks/c9_policy_linter.py, tests/ | Revert by reverting pipeline_reference.md and c9_policy_linter.py to commit 68369bd; delete five new fixture and expected-output files. |

## Patch detail (patch-2026-06-25c-addendum)

### Changes to pipeline_reference.md

1. **§10A.5 section header** — Renamed "#### L. Five second-layer depth controls" to
   "#### K6–K10. Five second-layer depth controls".

2. **§10A.5 check labels** — Renamed L1→K6, L2→K7, L3→K8, L4→K9, L5→K10 in all
   check descriptions and explanatory text.

3. **Severity corrections** — K6 (was BLOCKED) → ADVISORY (CAPPED); K7 (was BLOCKED) →
   ADVISORY (CAPPED); K10 (was BLOCKED) → ADVISORY (CAPPED). K8 and K9 remain ADVISORY.
   Severity guide table updated accordingly.

4. **§10D loopback table** — Updated L1–L5 column labels to K6–K10.

### Changes to checks/c9_policy_linter.py

5. **Finding codes** — Renamed DEPTH_CONTROL_L1→K6, L2→K7, L3→K8, L4→K9, L5→K10
   throughout `lint()` and all check functions.

6. **Severity downgrade** — K6 (`check_exceptional_language`): changed from BLOCKED to
   ADVISORY; K7 (`check_ebitda_quality`): changed from BLOCKED to ADVISORY; K10
   (`check_monitoring_plan`): changed from BLOCKED to ADVISORY. Exit code for these
   checks changes from 1 to 2 (AUTO-REPAIRED if otherwise CLEAN).

### New files

7. **Five test fixtures** (tests/fixtures/):
   - `k6_missing_reference_class.md` — triggers K6 + K2; must produce AUTO-REPAIRED
   - `k7_missing_quality_of_earnings.md` — triggers K7 + K2; must produce AUTO-REPAIRED
   - `k8_missing_incentive_control_map.md` — triggers K8 + K2; must produce AUTO-REPAIRED
   - `k9_missing_capital_allocation_record.md` — triggers K9 + K2; must produce AUTO-REPAIRED
   - `k10_missing_monitoring_plan.md` — triggers K10 + K2; must produce AUTO-REPAIRED

8. **Five expected output files** (tests/expected/):
   - `k6_missing_reference_class.expected_status.txt`
   - `k7_missing_quality_of_earnings.expected_status.txt`
   - `k8_missing_incentive_control_map.expected_status.txt`
   - `k9_missing_capital_allocation_record.expected_status.txt`
   - `k10_missing_monitoring_plan.expected_status.txt`
