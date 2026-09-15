# Run templates

Copy these templates into the corresponding path in a company research workspace. Replace every
bracketed value. Blank values are invalid.

| Template | Destination |
|---|---|
| `c9_status_block.md` | Near the top of `final/memo.md` |
| `decision_log.md` | `final/decision_log.md` |
| `decision_approval.md` | Append to `final/decision_log.md` after an actual human decision |
| `decision_log_override.md` | Append to `final/decision_log.md` after explicit human acceptance of open items |
| `c9_repair_log.md` | `working/c9_repair_log.md` |

The approval and override templates are intentionally separate so unused placeholder blocks cannot be
mistaken for decisions. `decision_log_override` is exceptional and does not erase the underlying risk
or evidence gap.
