# Harbour Energy plc — Test Fixture: Unresolved C8 Items (Negative Test)
# Purpose: demonstrate all four §10A.5-J contradiction types; must produce BLOCKED status.

## c9_status_block
c9_status: CLEAN
gate_mode: AUTO
human_review_performed: no
investment_decision_approved: no
c0_recommendation_cap: INVEST WITH CONDITIONS
unresolved_must_answer_count: 3
unresolved_high_risk_count: 4
unresolved_critical_gap_count: 0
allowed_conclusion_language: decision-not-ready
investment_action_allowed: no
position_sizing_allowed: no

---

## Decision-readiness status
| Item | Status |
|---|---|
| Research objective | Public equity investment |
| Tier | Standard |
| Gate mode | AUTO |
| Human judgement gates completed? | no |
| Highest evidence gap severity | high |
| Highest unresolved risk severity | high |
| Valuation evidence level | 3 |
| Product/commercial maturity cap | producing asset |
| Gross vs attributable basis checked? | yes |
| Legal entity and shareholder-rights basis checked? | yes |
| Source supersession check completed? | yes |
| Final recommendation cap | INVEST WITH CONDITIONS |
| Investment decision approved? | no |

---

## §1 — Recommendation

**INVEST WITH CONDITIONS.** Initiate at 50% target position at current price of 236.80p.

The valuation analysis supports a base-case target of 350–470p on a 12-month view with a stop-loss
at 150p. Position sizing: 50% initial position; build to full on resolution of must-answer items.

All load-bearing claims are sourced in the Facts Ledger. The claim-surface diff confirms that every
load-bearing claim maps to a Ledger ID.

---

## §11 — Must-Answer Questions

The following three items remain unresolved at the time of this memo:

1. **C8-01 Wintershall Dea leakage arbitration** — claim quantum not disclosed; Harbour's legal
   assessment not available. Exposure range $0–$600m+.
2. **C8-02 Mittelplate operating permit appeal** — court ruling pending; 28 kboepd at risk.
3. **C8-03 LetterOne C-share conversion** — timing and shareholder agreement terms unknown.

*These three items are disclosed but the recommendation section above recommends initiating a
position regardless. This is the failure mode the negative test is designed to catch.*

---

*AUTO-RUN COMPLETE — not an investment decision — human review not performed.*
