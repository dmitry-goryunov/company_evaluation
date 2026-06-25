"""
c9_policy_linter.py — C9 policy linter for the company evaluation pipeline.

Checks a final memo file for the four contradiction types defined in §10A.5 section J
of pipeline_reference.md and validates the c9_status_block YAML fields.

Usage:
    python checks/c9_policy_linter.py final/memo.md [--decision-log final/decision_log.md]

Exit codes:
    0 — CLEAN (no policy violations found)
    1 — BLOCKED (hard violation; memo cannot be presented as final)
    2 — AUTO-REPAIRED (fixable issues found; see linter report)
"""

import re
import sys
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Investment-action phrases that are prohibited when must-answer count > 0
# or when human_review_performed = no.
# ---------------------------------------------------------------------------
INVESTMENT_ACTION_PHRASES = [
    r"\bINVEST WITH CONDITIONS\b",
    r"\bINVEST\b",
    r"\bBUY\b",
    r"\bADD\b",
    r"\bconviction\b",
    r"\binitiate position\b",
    r"\bbuild position\b",
    r"\bfull position\b",
    r"\btarget position\b",
    r"\b\d+%\s+(?:initial\s+)?(?:target\s+)?position\b",
    r"\bposition sizing\b",
    r"\bposition-sizing\b",
    r"\brecommended allocation\b",
    r"\binvestment recommendation\b",
    r"\bentry at\b",
    r"\binitiate at\b",
    r"\bopen a position\b",
]

SOURCING_CLAIM_PHRASES = [
    r"all load-bearing claims are sourced",
    r"all claims are sourced",
    r"all facts are sourced",
    r"fully sourced",
    r"claim.surface.diff.*all.*sourced",
]


def parse_yaml_block(text):
    """Extract c9_status_block YAML fields from memo text."""
    block_match = re.search(
        r"##\s*c9_status_block\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if not block_match:
        return None

    fields = {}
    for line in block_match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def check_investment_action_phrases(text):
    """Return list of matched prohibited phrases."""
    hits = []
    for pattern in INVESTMENT_ACTION_PHRASES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            hits.extend(matches)
    return hits


def check_sourcing_claim(text, memo_dir):
    """Check if sourcing claim is made but evidence pack is absent."""
    has_claim = any(
        re.search(p, text, re.IGNORECASE) for p in SOURCING_CLAIM_PHRASES
    )
    if not has_claim:
        return False

    source_register = memo_dir / "sources" / "source_register.csv"
    notebooklm_raw = memo_dir / "notebooklm_outputs" / "raw"
    register_ok = source_register.exists() and source_register.stat().st_size > 0
    notebooklm_ok = notebooklm_raw.exists() and any(notebooklm_raw.iterdir())
    return not (register_ok or notebooklm_ok)


def lint(memo_path, decision_log_path=None):
    memo_path = Path(memo_path)
    text = memo_path.read_text(encoding="utf-8")

    # Determine project root (two levels up from final/ or working/)
    memo_dir = memo_path.parent.parent

    findings = []
    status = "CLEAN"

    # --- Parse YAML status block ---
    yaml_fields = parse_yaml_block(text)
    if yaml_fields is None:
        findings.append({
            "type": "MISSING_STATUS_BLOCK",
            "severity": "BLOCKED",
            "detail": "c9_status_block YAML not found in memo. Required near top of document.",
        })
        status = "BLOCKED"
    else:
        required_fields = [
            "c9_status", "gate_mode", "human_review_performed",
            "investment_decision_approved", "c0_recommendation_cap",
            "unresolved_must_answer_count", "unresolved_high_risk_count",
            "unresolved_critical_gap_count", "allowed_conclusion_language",
            "investment_action_allowed", "position_sizing_allowed",
        ]
        for f in required_fields:
            if f not in yaml_fields or not yaml_fields[f]:
                findings.append({
                    "type": "MISSING_YAML_FIELD",
                    "severity": "BLOCKED",
                    "detail": f"Required c9_status_block field missing or empty: {f}",
                })
                status = "BLOCKED"

    # --- Check for human override in decision log ---
    has_human_override = False
    if decision_log_path and Path(decision_log_path).exists():
        dl_text = Path(decision_log_path).read_text(encoding="utf-8")
        if re.search(r"override_granted\s*:\s*yes", dl_text, re.IGNORECASE):
            has_human_override = True

    # --- Contradiction type 1: human_review = no + investment-action language ---
    human_review = (yaml_fields or {}).get("human_review_performed", "no")
    if human_review.lower() == "no":
        hits = check_investment_action_phrases(text)
        if hits and not has_human_override:
            findings.append({
                "type": "CONTRADICTION_TYPE_1",
                "severity": "BLOCKED",
                "detail": (
                    f"human_review_performed = no but memo contains investment-action language: "
                    f"{hits[:5]}. Replace with DECISION-NOT-READY wording."
                ),
            })
            status = "BLOCKED"

    # --- Contradiction type 2: must-answer count > 0 + investment-action language ---
    must_answer_raw = (yaml_fields or {}).get("unresolved_must_answer_count", "0")
    try:
        must_answer_count = int(must_answer_raw)
    except (ValueError, TypeError):
        must_answer_count = 0

    if must_answer_count > 0:
        hits = check_investment_action_phrases(text)
        if hits and not has_human_override:
            findings.append({
                "type": "CONTRADICTION_TYPE_2",
                "severity": "BLOCKED",
                "detail": (
                    f"unresolved_must_answer_count = {must_answer_count} but memo contains "
                    f"investment-action language: {hits[:5]}. C8-blocker rule violated."
                ),
            })
            status = "BLOCKED"

    # --- Contradiction type 3: c9_status CLEAN + open items without override ---
    c9_status_field = (yaml_fields or {}).get("c9_status", "")
    high_risk_raw = (yaml_fields or {}).get("unresolved_high_risk_count", "0")
    try:
        high_risk_count = int(high_risk_raw)
    except (ValueError, TypeError):
        high_risk_count = 0

    if c9_status_field.upper() == "CLEAN":
        if (must_answer_count > 0 or high_risk_count > 0) and not has_human_override:
            findings.append({
                "type": "CONTRADICTION_TYPE_3",
                "severity": "BLOCKED",
                "detail": (
                    f"c9_status = CLEAN but open items remain "
                    f"(must_answer={must_answer_count}, high_risk={high_risk_count}). "
                    f"Downgrade to AUTO-REPAIRED or BLOCKED."
                ),
            })
            status = "BLOCKED"

    # --- Contradiction type 4: sourcing claim without artefacts ---
    if check_sourcing_claim(text, memo_dir):
        findings.append({
            "type": "CONTRADICTION_TYPE_4",
            "severity": "BLOCKED",
            "detail": (
                "Memo claims all load-bearing claims are sourced, but neither "
                "sources/source_register.csv nor notebooklm_outputs/raw/ is inspectable."
            ),
        })
        status = "BLOCKED"

    return status, findings


def main():
    parser = argparse.ArgumentParser(description="C9 policy linter")
    parser.add_argument("memo", help="Path to final/memo.md")
    parser.add_argument("--decision-log", help="Path to final/decision_log.md", default=None)
    args = parser.parse_args()

    status, findings = lint(args.memo, args.decision_log)

    print(f"c9_linter_status: {status}")
    print(f"findings_count: {len(findings)}")
    print()
    for i, f in enumerate(findings, 1):
        print(f"[{i}] {f['type']} ({f['severity']})")
        print(f"    {f['detail']}")
        print()

    if status == "BLOCKED":
        sys.exit(1)
    elif status == "AUTO-REPAIRED":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
