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

THESIS-TRACKING. This company represents a successful turnaround with durable outperformance
potential versus peers. The structural re-rating thesis is supported by improving unit economics.

## §2 EVIDENCE THAT WOULD CHANGE THE CONCLUSION

1. Unit economics deteriorate below breakeven for two consecutive quarters.
2. Key management departure without replacement within 90 days.
3. Refinancing at materially higher spreads signals credit stress.

## §3 MONITORING AND RE-UNDERWRITING PLAN

| Variable | Source | Frequency | Trigger | Stage to re-run | Action |
|---|---|---|---|---|---|
| Unit economics | quarterly results | quarterly | below breakeven | C2, C7 | reassess thesis |
| Management changes | regulatory filings | event-driven | CEO/CFO departure | B6, C8 | escalate to human |

---

Note: `working/reference_class_base_rate.md` is intentionally absent.
This fixture must trigger K6 (ADVISORY) and produce AUTO-REPAIRED status.
