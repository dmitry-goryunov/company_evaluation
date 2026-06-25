## c9_status_block
c9_status: CLEAN
gate_mode: AUTO
human_review_performed: no
investment_decision_approved: no
c0_recommendation_cap: THESIS-TRACKING
unresolved_must_answer_count: 0
unresolved_high_risk_count: 0
unresolved_critical_gap_count: 0
allowed_conclusion_language: thesis-tracking
investment_action_allowed: no
position_sizing_allowed: no

---

## Decision-readiness status
| Item | Status |
|---|---|
| Gate mode | AUTO |
| Human judgement gates completed? | no |
| Investment decision approved? | no |

---

## §1 RESEARCH CONCLUSION

THESIS-TRACKING. The company trades at 3.2x EV/EBITDA versus a sector median of 5.5x. The FCF yield
of 18% at current price implies material undervaluation relative to peers on a free cash flow yield basis.
The EV/EBITDAX multiple of 2.5x is a 55% discount to the nearest comparable.

## §2 EVIDENCE THAT WOULD CHANGE THE CONCLUSION

1. EBITDA margin compression below 20% for two consecutive quarters.
2. FCF yield falls below 10% due to capex overruns.
3. Multiple re-expansion in sector narrows gap versus this name.

## §3 MONITORING AND RE-UNDERWRITING PLAN

| Variable | Source | Frequency | Trigger | Stage to re-run | Action |
|---|---|---|---|---|---|
| EV/EBITDA | quarterly results | quarterly | above 4.5x | C2 | reassess valuation |
| FCF yield | interim results | semi-annual | below 10% | C2, C7 | review thesis |

---

Note: `working/quality_of_earnings_cash_conversion.md` is intentionally absent.
This fixture must trigger K7 (ADVISORY) and produce AUTO-REPAIRED status.
