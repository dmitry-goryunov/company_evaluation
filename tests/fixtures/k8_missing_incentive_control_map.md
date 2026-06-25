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

THESIS-TRACKING. The company is majority-owned by a controlling shareholder holding 62% of voting
rights via dual-class shares. The minority free float of 38% trades at a 30% discount to estimated
NAV. Related-party transactions represent approximately 15% of revenue and have not been independently
verified. The sponsor has held its stake since a 2019 leveraged buyout and may face exit pressure.

## §2 EVIDENCE THAT WOULD CHANGE THE CONCLUSION

1. Controlling shareholder commences a formal sale process at a material discount to NAV.
2. Related-party transactions exceed 25% of revenue without independent oversight.
3. Sponsor exit through a secondary placement dilutes free float liquidity.

## §3 MONITORING AND RE-UNDERWRITING PLAN

| Variable | Source | Frequency | Trigger | Stage to re-run | Action |
|---|---|---|---|---|---|
| Controlling shareholder filings | regulatory | event-driven | sale announcement | C7, C8 | escalate |
| Related-party transaction disclosures | annual report | annual | above 20% revenue | B6, C7 | review governance |

---

Note: `working/incentive_control_map.md` is intentionally absent.
This fixture must trigger K8 (ADVISORY) and produce AUTO-REPAIRED status.
