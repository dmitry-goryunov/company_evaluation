#!/usr/bin/env python3
"""Validate the decision controls on a C9 company-research memo.

The linter is read-only with respect to the memo. It may write a report, but it
never edits or "repairs" research. Exit codes are 0 CLEAN, 1 BLOCKED, and
2 WARNINGS.

Machine-readable blocks use a constrained ``key: value`` format. The parser
rejects duplicate keys, invalid enums, malformed counts, and incomplete
overrides without requiring a third-party YAML parser.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable


STATUS_HEADING = "c9_status_block"
OVERRIDE_HEADING = "decision_log_override"
APPROVAL_HEADING = "decision_approval"

REQUIRED_STATUS_FIELDS = (
    "schema_version",
    "run_id",
    "research_objective",
    "tier",
    "c9_status",
    "gate_mode",
    "human_review_performed",
    "investment_decision_approved",
    "c0_recommendation_cap",
    "unresolved_must_answer_count",
    "unresolved_high_risk_count",
    "unresolved_critical_gap_count",
    "allowed_conclusion_language",
    "investment_action_allowed",
    "position_sizing_allowed",
)

RESEARCH_OBJECTIVES = {
    "public-equity",
    "private-investment",
    "credit-lending",
    "m-and-a-target",
    "m-and-a-buyer",
    "strategic-partnership",
    "supplier-vendor",
    "customer-competitor",
    "distressed-restructuring",
    "governance-fraud-risk",
    "general-company-profile",
}

VALUATION_OBJECTIVES = {
    "public-equity",
    "private-investment",
    "credit-lending",
    "m-and-a-target",
    "m-and-a-buyer",
    "distressed-restructuring",
}

C9_STATUSES = {"CLEAN", "WARNINGS", "BLOCKED"}
TIERS = {"SCREEN", "STANDARD", "FULL"}
GATE_MODES = {"AUTO", "MANUAL"}
CONCLUSION_LANGUAGES = {
    "decision-not-ready",
    "watchlist",
    "thesis-tracking",
    "speculative-only",
    "human-decision-candidate",
    "decision-approved",
    "reject-avoid",
}
RECOMMENDATION_CAPS = {
    "decision-not-ready",
    "watchlist-only",
    "thesis-tracking",
    "speculative-only",
    "human-decision-candidate",
    "unrestricted",
    "reject-avoid",
}
CONCLUSION_RANK = {
    "decision-not-ready": 0,
    "watchlist": 1,
    "thesis-tracking": 2,
    "speculative-only": 3,
    "human-decision-candidate": 4,
    "decision-approved": 5,
    "reject-avoid": 0,
}
CAP_RANK = {
    "decision-not-ready": 0,
    "watchlist-only": 1,
    "thesis-tracking": 2,
    "speculative-only": 3,
    "human-decision-candidate": 4,
    "unrestricted": 5,
    "reject-avoid": 0,
}

BOOL_FIELDS = (
    "human_review_performed",
    "investment_decision_approved",
    "investment_action_allowed",
    "position_sizing_allowed",
)
COUNT_FIELDS = (
    "unresolved_must_answer_count",
    "unresolved_high_risk_count",
    "unresolved_critical_gap_count",
)

INVESTMENT_ACTION_PATTERNS = (
    r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*)?"
    r"(?:BUY|SELL|HOLD|ADD|ACCUMULATE|INVEST WITH CONDITIONS)"
    r"(?:\*\*)?(?=\s|[.:;!]|$)",
    r"\b(?:we|the memo|the recommendation|investment action)\s+"
    r"(?:recommend(?:s|ed)?|is|=|:)\s+(?:buy|sell|hold|add|accumulate|invest)\b",
    r"\brecommend(?:s|ed|ation)?\s+(?:to\s+)?(?:buy|sell|hold|add|accumulate|invest)\b",
    r"\b(?:initiate|build|open|increase|reduce|exit)\s+(?:a\s+|the\s+)?position\b",
    r"\b(?:full|target|initial)\s+position\b",
    r"\b\d+(?:\.\d+)?%\s+(?:initial\s+|target\s+)?position\b",
    r"\bposition[ -]sizing\b",
    r"\brecommended allocation\b",
    r"\bentry at\b",
    r"\b(?:high|strong|full)\s+conviction\b",
)

SOURCING_CLAIM_PHRASES = (
    r"all load-bearing claims are sourced",
    r"all claims are sourced",
    r"all facts are sourced",
    r"fully sourced",
    r"claim.surface.diff.*all.*sourced",
)

MISPRICING_PHRASES = (
    r"\bmispriced\b",
    r"\bundervalued\b",
    r"\bovervalued\b",
    r"\bcheap\b",
    r"\bexpensive\b",
    r"\birrational discount\b",
    r"\bmarket is wrong\b",
    r"\bmarket is pricing in\b",
)

EXCEPTIONAL_OUTCOME_PHRASES = (
    r"\bexceptional\s+(?:outcome|return|performance|result|case)\b",
    r"\bdurable\s+outperformance\b",
    r"\bsuccessful\s+turnaround\b",
    r"\bproven\s+turnaround\b",
    r"\b(?:structural\s+)?re-?rating\b",
    r"\bde-risking\b",
    r"\bsustained\s+recovery\b",
    r"\brecovery\s+(?:thesis|play|story|case)\b",
)

EBITDA_FCF_PHRASES = (
    r"\bEV/EBITDA[X]?\b",
    r"\bEBITDA[X]?\s+multiple\b",
    r"\bFCF\s+yield\b",
    r"\bfree\s+cash\s+flow\s+yield\b",
    r"\bcapitalis(?:ed|ing)\s+(?:adjusted\s+)?(?:earnings|EBITDA|FCF)\b",
    r"\bguided\s+(?:free\s+cash\s+flow|FCF)\b",
    r"\badjusted\s+FCF\b",
)

CONTROL_STRUCTURE_PHRASES = (
    r"\bcontrolling\s+shareholder\b",
    r"\bdual[ -]class\b",
    r"\bnon[ -]voting\s+shares?\b",
    r"\bpreferred\s+equity\b",
    r"\bsponsor\s+(?:exit|ownership|control|pressure)\b",
    r"\bearn[ -]?out\b",
    r"\brelated[ -]party\b",
    r"\bmanagement\s+earnout\b",
    r"\bcovenant\s+control\b",
)

CAPITAL_ALLOCATION_PHRASES = (
    r"\bdeleverage\b|\bdeleveraging\b",
    r"\bshare\s+buy[ -]?back\b|\bbuy[ -]?back\b",
    r"\bdividend\s+growth\b",
    r"\bM&A\s+integration\b",
    r"\bcapex\s+discipline\b",
    r"\bvalue[ -]accretive\s+(?:acquisition|reinvestment|capital)\b",
    r"\breinvestment\s+success\b",
)

PER_SHARE_PATTERN = re.compile(
    r"(?:"
    r"(?:US\$|A\$|C\$|HK\$|S\$|£|\$|€|¥|₹|GBP|USD|EUR|NOK|SEK|DKK|CHF|CAD|AUD|JPY)"
    r"\s*\d+(?:[.,]\d+)?(?:\s*[–-]\s*\d+(?:[.,]\d+)?)?\s*(?:per\s+share|/share)"
    r"|\d+(?:[.,]\d+)?(?:\s*[–-]\s*\d+(?:[.,]\d+)?)?\s*(?:pence|cents|p|¢)\b"
    r")",
    re.IGNORECASE,
)

HEADING_NUMBER = r"(?:(?:§\s*)?\d+(?:[.)]|\s*[–—-])?\s*)?"
FALSIFICATION_HEADING = re.compile(
    rf"^#{{2,6}}\s+{HEADING_NUMBER}(?:evidence that would change the conclusion|falsification triggers)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
OPPOSING_HEADING = re.compile(
    rf"^#{{2,6}}\s+{HEADING_NUMBER}(?:strongest\s+)?opposing thesis\s*$",
    re.IGNORECASE | re.MULTILINE,
)
MONITORING_HEADING = re.compile(
    rf"^#{{2,6}}\s+{HEADING_NUMBER}(?:monitoring(?:\s+and\s+re-underwriting)?|re-underwriting)(?:\s+(?:plan|section|protocol))?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

NEGATION_PATTERN = re.compile(
    r"\b(?:cannot|can't|do\s+not|does\s+not|did\s+not|no|not|without|"
    r"prohibited|declin(?:e|es|ed)|withhold)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    detail: str


def normalise_token(value: str) -> str:
    return re.sub(r"[-_\s]+", "-", value.strip().lower()).strip("-")


def parse_key_value_block(text: str, heading: str) -> tuple[dict[str, str] | None, list[str]]:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None, []

    fields: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(match.group(1).splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("```") or stripped == "---":
            continue
        if stripped.startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"line {line_number} is not key: value")
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            errors.append(f"invalid key {key!r}")
            continue
        if key in fields:
            errors.append(f"duplicate key {key!r}")
            continue
        fields[key] = value
    return fields, errors


def parse_yes_no(value: str) -> bool | None:
    token = normalise_token(value)
    if token == "yes":
        return True
    if token == "no":
        return False
    return None


def parse_non_negative_int(value: str) -> int | None:
    if not re.fullmatch(r"0|[1-9]\d*", value.strip()):
        return None
    return int(value)


def parse_inline_list(value: str, *, allow_none: bool = False) -> list[str] | None:
    stripped = value.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        stripped = stripped[1:-1]
    items = [item.strip().strip("'\"") for item in re.split(r"[,;]", stripped) if item.strip()]
    lowered = {normalise_token(item) for item in items}
    if not items or lowered & {"all", "all-open-items", "tbd", "unknown"}:
        return None
    if lowered == {"none"}:
        return [] if allow_none else None
    return items


def valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value.strip())
    except ValueError:
        return False
    return True


def substantive_file(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return False
    non_template = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
        and not re.fullmatch(r"\|?\s*[-:| ]+\|?", line)
    ]
    return bool(non_template)


def csv_has_data_row(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    return len(rows) >= 2 and any(cell.strip() for cell in rows[1])


def directory_has_file(path: Path) -> bool:
    return path.is_dir() and any(item.is_file() and item.stat().st_size > 0 for item in path.rglob("*"))


def field_has_value(path: Path, field: str) -> bool:
    if not substantive_file(path):
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf"(?im)^\s*{re.escape(field)}\s*:\s*(.+?)\s*$", text)
    if not match:
        return False
    return normalise_token(match.group(1)) not in {"", "none", "unknown", "tbd", "not-tested", "n-a"}


def extract_section(text: str, heading_match: re.Match[str]) -> str:
    start = heading_match.end()
    next_heading = re.search(r"^#{1,6}\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def section_has_items(section: str, minimum: int = 1) -> bool:
    items = re.findall(r"(?m)^\s*(?:[-*]|\d+[.)])\s+\S", section)
    table_rows = [
        line
        for line in section.splitlines()
        if line.strip().startswith("|")
        and not re.fullmatch(r"\|?\s*[-:| ]+\|?", line.strip())
    ]
    return max(len(items), max(0, len(table_rows) - 1)) >= minimum


def get_body_text(text: str) -> str:
    """Return memo content after the status metadata blocks."""
    status = re.search(r"^##\s+c9_status_block\s*$", text, re.IGNORECASE | re.MULTILINE)
    search_from = status.end() if status else 0
    readiness = re.search(
        r"^##\s+Decision-readiness status\s*$",
        text[search_from:],
        re.IGNORECASE | re.MULTILINE,
    )
    if readiness:
        after_readiness = search_from + readiness.end()
        next_heading = re.search(r"^##\s+(?!Decision-readiness status)", text[after_readiness:], re.MULTILINE)
        if next_heading:
            return text[after_readiness + next_heading.start():]
    section = re.search(r"^##\s*§", text[search_from:], re.MULTILINE)
    if section:
        return text[search_from + section.start():]
    separators = list(re.finditer(r"^---\s*$", text[:4000], re.MULTILINE))
    return text[separators[-1].end():] if separators else text


def sentence_prefix(text: str, position: int) -> str:
    start = max(
        text.rfind(".", 0, position),
        text.rfind("!", 0, position),
        text.rfind("?", 0, position),
        text.rfind("\n", 0, position),
    )
    return text[start + 1:position]


def check_investment_action_phrases(body_text: str) -> list[str]:
    hits: list[str] = []
    for pattern in INVESTMENT_ACTION_PATTERNS:
        for match in re.finditer(pattern, body_text, re.IGNORECASE):
            if NEGATION_PATTERN.search(sentence_prefix(body_text, match.start())):
                continue
            value = match.group().strip()
            if value and value.lower() not in {item.lower() for item in hits}:
                hits.append(value)
    return hits


def check_scenario_midpoint(body_text: str) -> bool:
    """Detect an affirmative claim that base case is derived as a midpoint."""
    for sentence in re.split(r"(?<=[.!?])\s+|\n", body_text):
        lower = sentence.lower()
        if not all(term in lower for term in ("base", "midpoint")):
            continue
        if not ("bull" in lower or "bear" in lower):
            continue
        midpoint_index = lower.index("midpoint")
        if NEGATION_PATTERN.search(sentence_prefix(sentence, midpoint_index)):
            continue
        if re.search(
            r"\bbase(?:[ -]case)?\b.{0,120}\b(?:is|equals|uses|set at|derived|calculated)\b.{0,80}\bmidpoint\b",
            sentence,
            re.IGNORECASE,
        ):
            return True
    return False


def check_falsification_section(body_text: str, tier: str) -> bool:
    match = FALSIFICATION_HEADING.search(body_text)
    if not match:
        return True
    minimum = 1 if tier == "SCREEN" else 3
    return not section_has_items(extract_section(body_text, match), minimum)


def check_opposing_thesis(project_root: Path | None, body_text: str, tier: str) -> bool:
    if tier == "SCREEN":
        return False
    if project_root:
        artefact = project_root / "working" / "opposing_thesis.md"
        if substantive_file(artefact) and all(
            field_has_value(artefact, field)
            for field in ("opposing_claim", "evidence_for_opposing", "resolution_status")
        ):
            return False
    match = OPPOSING_HEADING.search(body_text)
    return not (match and section_has_items(extract_section(body_text, match)))


def check_monitoring_plan(project_root: Path | None, body_text: str, tier: str) -> bool:
    if tier == "SCREEN":
        return False
    match = MONITORING_HEADING.search(body_text)
    if match and section_has_items(extract_section(body_text, match)):
        return False
    return not (project_root and substantive_file(project_root / "working" / "monitoring_plan.md"))


def check_mispricing_language(project_root: Path | None, body_text: str) -> bool:
    if not any(re.search(pattern, body_text, re.IGNORECASE) for pattern in MISPRICING_PHRASES):
        return False
    return not (
        project_root
        and field_has_value(
            project_root / "working" / "market_implied_expectations.md",
            "alternative_rational_explanation",
        )
    )


def check_exceptional_language(project_root: Path | None, body_text: str, tier: str, objective: str) -> bool:
    if tier == "SCREEN" or objective not in VALUATION_OBJECTIVES:
        return False
    if not any(re.search(pattern, body_text, re.IGNORECASE) for pattern in EXCEPTIONAL_OUTCOME_PHRASES):
        return False
    return not (
        project_root
        and field_has_value(project_root / "working" / "reference_class_base_rate.md", "why_may_differ")
    )


def check_ebitda_quality(project_root: Path | None, body_text: str, tier: str) -> bool:
    if tier == "SCREEN":
        return False
    if not any(re.search(pattern, body_text, re.IGNORECASE) for pattern in EBITDA_FCF_PHRASES):
        return False
    return not (
        project_root
        and field_has_value(
            project_root / "working" / "quality_of_earnings_cash_conversion.md",
            "sustainable_cash_flow",
        )
    )


def check_triggered_artefact(
    project_root: Path | None,
    body_text: str,
    patterns: Iterable[str],
    relative_path: str,
) -> bool:
    if not any(re.search(pattern, body_text, re.IGNORECASE) for pattern in patterns):
        return False
    return not (project_root and substantive_file(project_root / relative_path))


def check_liability_bridge(project_root: Path | None, body_text: str) -> bool:
    if not PER_SHARE_PATTERN.search(body_text):
        return False
    if re.search(r"bridge[ -]incomplete", body_text, re.IGNORECASE):
        return False
    if not project_root:
        return True
    bridge = project_root / "working" / "capital_structure.md"
    if not substantive_file(bridge):
        return True
    content = bridge.read_text(encoding="utf-8", errors="replace")
    required_rows = (
        "enterprise value",
        "net debt",
        "leases",
        "hybrids",
        "decommissioning",
        "pension",
        "tax liabilities",
        "minority interests",
        "off-balance-sheet",
        "equity value",
        "share denominator",
        "per-share output",
    )
    return not all(re.search(re.escape(row), content, re.IGNORECASE) for row in required_rows)


def source_evidence_available(project_root: Path) -> bool:
    return csv_has_data_row(project_root / "sources" / "source_register.csv") or directory_has_file(
        project_root / "notebooklm_outputs" / "raw"
    )


def validate_project_artefacts(project_root: Path, add: Callable[[str, str, str], None]) -> None:
    required = (
        "working/facts_ledger.md",
        "working/evidence_gaps.md",
        "working/open_questions.md",
        "working/claim_audit.md",
        "working/disconfirming_evidence.md",
        "working/falsification_triggers.md",
        "working/c9_repair_log.md",
        "final/decision_log.md",
    )
    for relative in required:
        if not substantive_file(project_root / relative):
            add(
                "MISSING_REQUIRED_ARTEFACT",
                "BLOCKED",
                f"Required artefact is absent, empty, or template-only: {relative}",
            )
    if not source_evidence_available(project_root):
        add(
            "MISSING_SOURCE_EVIDENCE",
            "BLOCKED",
            "A populated sources/source_register.csv or a non-empty notebooklm_outputs/raw/ directory is required.",
        )


def validate_status_block(
    fields: dict[str, str] | None,
    parse_errors: list[str],
    add: Callable[[str, str, str], None],
) -> dict[str, object]:
    typed: dict[str, object] = {}
    if fields is None:
        add("MISSING_STATUS_BLOCK", "BLOCKED", "The c9_status_block is absent.")
        return typed
    for error in parse_errors:
        add("INVALID_STATUS_BLOCK", "BLOCKED", error)
    for field in REQUIRED_STATUS_FIELDS:
        if not fields.get(field, "").strip():
            add("MISSING_STATUS_FIELD", "BLOCKED", f"Required c9_status_block field missing or empty: {field}")

    if fields.get("schema_version") != "1":
        add("INVALID_STATUS_VALUE", "BLOCKED", "schema_version must be 1.")
    run_id = fields.get("run_id", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,79}", run_id):
        add(
            "INVALID_STATUS_VALUE",
            "BLOCKED",
            "run_id must be 3-80 characters using letters, numbers, dots, underscores, or hyphens.",
        )
    typed["run_id"] = run_id

    objective = normalise_token(fields.get("research_objective", ""))
    if objective not in RESEARCH_OBJECTIVES:
        add("INVALID_STATUS_VALUE", "BLOCKED", f"Unknown research_objective: {fields.get('research_objective', '')!r}")
    typed["research_objective"] = objective

    tier = fields.get("tier", "").strip().upper()
    if tier not in TIERS:
        add("INVALID_STATUS_VALUE", "BLOCKED", f"tier must be one of {sorted(TIERS)}.")
    typed["tier"] = tier

    c9_status = fields.get("c9_status", "").strip().upper()
    if c9_status not in C9_STATUSES:
        add("INVALID_STATUS_VALUE", "BLOCKED", f"c9_status must be one of {sorted(C9_STATUSES)}.")
    typed["c9_status"] = c9_status

    gate_mode = fields.get("gate_mode", "").strip().upper()
    if gate_mode not in GATE_MODES:
        add("INVALID_STATUS_VALUE", "BLOCKED", f"gate_mode must be one of {sorted(GATE_MODES)}.")
    typed["gate_mode"] = gate_mode

    for field in BOOL_FIELDS:
        value = parse_yes_no(fields.get(field, ""))
        if value is None:
            add("INVALID_STATUS_VALUE", "BLOCKED", f"{field} must be yes or no.")
        typed[field] = value

    for field in COUNT_FIELDS:
        value = parse_non_negative_int(fields.get(field, ""))
        if value is None:
            add("INVALID_STATUS_VALUE", "BLOCKED", f"{field} must be a non-negative integer.")
        typed[field] = value

    cap = normalise_token(fields.get("c0_recommendation_cap", ""))
    if cap not in RECOMMENDATION_CAPS:
        add("INVALID_STATUS_VALUE", "BLOCKED", f"Unknown c0_recommendation_cap: {fields.get('c0_recommendation_cap', '')!r}")
    typed["c0_recommendation_cap"] = cap

    conclusion = normalise_token(fields.get("allowed_conclusion_language", ""))
    if conclusion not in CONCLUSION_LANGUAGES:
        add(
            "INVALID_STATUS_VALUE",
            "BLOCKED",
            f"Unknown allowed_conclusion_language: {fields.get('allowed_conclusion_language', '')!r}",
        )
    typed["allowed_conclusion_language"] = conclusion
    return typed


def validate_override(
    decision_log_text: str,
    status: dict[str, object],
    add: Callable[[str, str, str], None],
) -> tuple[bool, bool]:
    fields, errors = parse_key_value_block(decision_log_text, OVERRIDE_HEADING)
    if fields is None:
        return False, False
    required = (
        "run_id",
        "reviewer",
        "review_date",
        "review_scope",
        "open_items_reviewed",
        "override_granted",
        "override_reason",
        "accepted_risks",
        "position_sizing_approved",
        "approved_action",
        "follow_up_required",
    )
    valid = True
    for error in errors:
        add("INVALID_OVERRIDE", "BLOCKED", error)
        valid = False
    for field in required:
        if not fields.get(field, "").strip():
            add("INVALID_OVERRIDE", "BLOCKED", f"Required override field missing or empty: {field}")
            valid = False
    if fields.get("run_id") != status.get("run_id"):
        add("INVALID_OVERRIDE", "BLOCKED", "Override run_id does not match the memo run_id.")
        valid = False
    reviewer = normalise_token(fields.get("reviewer", ""))
    if reviewer in {"", "agent", "auto", "claude", "codex", "ai"}:
        add("INVALID_OVERRIDE", "BLOCKED", "Override reviewer must identify a human name or role.")
        valid = False
    if not valid_iso_date(fields.get("review_date", "")):
        add("INVALID_OVERRIDE", "BLOCKED", "Override review_date must be an ISO 8601 date.")
        valid = False
    granted = parse_yes_no(fields.get("override_granted", ""))
    sizing = parse_yes_no(fields.get("position_sizing_approved", ""))
    if granted is None or sizing is None:
        add("INVALID_OVERRIDE", "BLOCKED", "Override boolean fields must be yes or no.")
        valid = False

    open_items = parse_inline_list(fields.get("open_items_reviewed", ""), allow_none=True)
    accepted_risks = parse_inline_list(fields.get("accepted_risks", ""), allow_none=True)
    if open_items is None:
        add("INVALID_OVERRIDE", "BLOCKED", "open_items_reviewed must list explicit item IDs; blanket values are invalid.")
        valid = False
        open_items = []
    if accepted_risks is None:
        add("INVALID_OVERRIDE", "BLOCKED", "accepted_risks must list explicit risk IDs or [none].")
        valid = False
        accepted_risks = []

    expected_open = sum(
        int(status.get(field) or 0)
        for field in (
            "unresolved_must_answer_count",
            "unresolved_high_risk_count",
            "unresolved_critical_gap_count",
        )
    )
    expected_risks = int(status.get("unresolved_high_risk_count") or 0) + int(
        status.get("unresolved_critical_gap_count") or 0
    )
    if len(open_items) < expected_open:
        add("INVALID_OVERRIDE", "BLOCKED", f"Override lists {len(open_items)} open items but the memo declares {expected_open}.")
        valid = False
    if len(accepted_risks) < expected_risks:
        add("INVALID_OVERRIDE", "BLOCKED", f"Override accepts {len(accepted_risks)} risks/gaps but the memo declares {expected_risks}.")
        valid = False
    if granted and status.get("human_review_performed") is not True:
        add("INVALID_OVERRIDE", "BLOCKED", "A granted override requires human_review_performed: yes.")
        valid = False
    return bool(valid and granted), bool(valid and sizing)


def validate_decision_approval(
    decision_log_text: str,
    status: dict[str, object],
    add: Callable[[str, str, str], None],
) -> tuple[bool, bool]:
    fields, errors = parse_key_value_block(decision_log_text, APPROVAL_HEADING)
    if fields is None:
        return False, False
    required = (
        "run_id",
        "reviewer",
        "review_date",
        "decision",
        "approved_action",
        "position_sizing_approved",
        "follow_up_required",
    )
    valid = True
    for error in errors:
        add("INVALID_DECISION_APPROVAL", "BLOCKED", error)
        valid = False
    for field in required:
        if not fields.get(field, "").strip():
            add("INVALID_DECISION_APPROVAL", "BLOCKED", f"Required decision approval field missing or empty: {field}")
            valid = False
    if fields.get("run_id") != status.get("run_id"):
        add("INVALID_DECISION_APPROVAL", "BLOCKED", "Decision approval run_id does not match the memo run_id.")
        valid = False
    if normalise_token(fields.get("reviewer", "")) in {"", "agent", "auto", "claude", "codex", "ai"}:
        add("INVALID_DECISION_APPROVAL", "BLOCKED", "Decision approval must identify a human reviewer.")
        valid = False
    if not valid_iso_date(fields.get("review_date", "")):
        add("INVALID_DECISION_APPROVAL", "BLOCKED", "Decision approval review_date must be an ISO 8601 date.")
        valid = False
    decision = normalise_token(fields.get("decision", ""))
    approved = decision in {"approved", "approved-with-caveats"}
    if decision not in {"approved", "approved-with-caveats", "rejected"}:
        add(
            "INVALID_DECISION_APPROVAL",
            "BLOCKED",
            "decision must be approved, approved-with-caveats, or rejected.",
        )
        valid = False
    sizing = parse_yes_no(fields.get("position_sizing_approved", ""))
    if sizing is None:
        add("INVALID_DECISION_APPROVAL", "BLOCKED", "position_sizing_approved must be yes or no.")
        valid = False
    return bool(valid and approved), bool(valid and approved and sizing)


def status_from_findings(findings: list[Finding]) -> str:
    if any(finding.severity == "BLOCKED" for finding in findings):
        return "BLOCKED"
    if findings:
        return "WARNINGS"
    return "CLEAN"


def lint(
    memo_path: str | Path,
    decision_log_path: str | Path | None = None,
    project_root: str | Path | None = None,
    check_artefacts: bool | None = None,
) -> tuple[str, list[dict[str, str]]]:
    memo_path = Path(memo_path)
    text = memo_path.read_text(encoding="utf-8")
    body = get_body_text(text)

    if project_root is not None:
        root = Path(project_root)
    elif memo_path.parent.name in {"final", "working"}:
        root = memo_path.parent.parent
    else:
        root = None
    if check_artefacts is None:
        check_artefacts = root is not None

    findings: list[Finding] = []

    def add(code: str, severity: str, detail: str) -> None:
        findings.append(Finding(code, severity, detail))

    fields, parse_errors = parse_key_value_block(text, STATUS_HEADING)
    status = validate_status_block(fields, parse_errors, add)
    tier = str(status.get("tier") or "STANDARD")
    objective = str(status.get("research_objective") or "public-equity")

    if check_artefacts:
        if root is None:
            add("PROJECT_ROOT_REQUIRED", "BLOCKED", "Artefact checks require --project-root or a memo under final/ or working/.")
        else:
            validate_project_artefacts(root, add)

    if decision_log_path is not None:
        decision_log = Path(decision_log_path)
    elif root is not None:
        decision_log = root / "final" / "decision_log.md"
    else:
        decision_log = None
    decision_log_text = ""
    if decision_log and decision_log.is_file():
        decision_log_text = decision_log.read_text(encoding="utf-8", errors="replace")

    has_override, override_allows_sizing = validate_override(decision_log_text, status, add)
    has_approval, approval_allows_sizing = validate_decision_approval(decision_log_text, status, add)
    human_review = status.get("human_review_performed")
    action_allowed = status.get("investment_action_allowed")
    sizing_allowed = status.get("position_sizing_allowed")
    decision_approved = status.get("investment_decision_approved")
    must_answer_count = int(status.get("unresolved_must_answer_count") or 0)
    high_risk_count = int(status.get("unresolved_high_risk_count") or 0)
    critical_gap_count = int(status.get("unresolved_critical_gap_count") or 0)
    conclusion = str(status.get("allowed_conclusion_language") or "")
    cap = str(status.get("c0_recommendation_cap") or "")

    if human_review is False:
        for field, value in (
            ("investment_decision_approved", decision_approved),
            ("investment_action_allowed", action_allowed),
            ("position_sizing_allowed", sizing_allowed),
        ):
            if value is True:
                add("STATUS_DERIVATION_ERROR", "BLOCKED", f"human_review_performed: no requires {field}: no.")

    if decision_approved is True and not has_approval:
        add(
            "STATUS_DERIVATION_ERROR",
            "BLOCKED",
            "investment_decision_approved: yes requires a valid decision_approval block for this run.",
        )
    if has_approval and decision_approved is not True:
        add(
            "STATUS_DERIVATION_ERROR",
            "BLOCKED",
            "An approved decision_approval block requires investment_decision_approved: yes.",
        )
    if action_allowed is True and not (has_approval or has_override):
        add(
            "STATUS_DERIVATION_ERROR",
            "BLOCKED",
            "investment_action_allowed: yes requires a valid decision approval or override.",
        )
    if sizing_allowed is True and not (approval_allows_sizing or override_allows_sizing):
        add(
            "STATUS_DERIVATION_ERROR",
            "BLOCKED",
            "position_sizing_allowed: yes requires explicit position-sizing approval.",
        )

    if must_answer_count > 0 and not has_override:
        if conclusion != "decision-not-ready":
            add(
                "STATUS_DERIVATION_ERROR",
                "BLOCKED",
                "Open must-answer items require allowed_conclusion_language: decision-not-ready.",
            )
        if action_allowed is True or sizing_allowed is True:
            add(
                "STATUS_DERIVATION_ERROR",
                "BLOCKED",
                "Open must-answer items prohibit investment action and position sizing without a valid override.",
            )

    if critical_gap_count > 0 and not has_override:
        if conclusion != "decision-not-ready":
            add(
                "STATUS_DERIVATION_ERROR",
                "BLOCKED",
                "Open critical gaps require allowed_conclusion_language: decision-not-ready.",
            )
        if action_allowed is True or sizing_allowed is True:
            add(
                "STATUS_DERIVATION_ERROR",
                "BLOCKED",
                "Open critical gaps prohibit investment action and position sizing without a valid override.",
            )

    if (
        cap in CAP_RANK
        and conclusion in CONCLUSION_RANK
        and CONCLUSION_RANK[conclusion] > CAP_RANK[cap]
        and not has_override
    ):
        add("C0_CAP_EXCEEDED", "BLOCKED", f"Conclusion {conclusion!r} exceeds the C0 cap {cap!r}.")

    action_hits = check_investment_action_phrases(body)
    if human_review is False and action_hits and not has_override:
        add(
            "CONTRADICTION_TYPE_1",
            "BLOCKED",
            f"No human review, but memo body contains investment-action language: {action_hits[:5]}.",
        )
    if must_answer_count > 0 and action_hits and not has_override:
        add(
            "CONTRADICTION_TYPE_2",
            "BLOCKED",
            f"{must_answer_count} must-answer items remain, but memo body contains investment-action language: {action_hits[:5]}.",
        )

    declared_c9_status = str(status.get("c9_status") or "")
    if (
        declared_c9_status == "CLEAN"
        and (must_answer_count > 0 or high_risk_count > 0 or critical_gap_count > 0)
        and not has_override
    ):
        add(
            "CONTRADICTION_TYPE_3",
            "BLOCKED",
            "c9_status is CLEAN while unresolved must-answer, High-risk, or Critical-gap items remain without a valid override.",
        )

    if any(re.search(pattern, text, re.IGNORECASE) for pattern in SOURCING_CLAIM_PHRASES):
        if not root or not source_evidence_available(root):
            add(
                "CONTRADICTION_TYPE_4",
                "BLOCKED",
                "The memo claims complete sourcing, but no populated source register or saved raw extraction is inspectable.",
            )

    if re.search(
        r"\b(?:AUTO-APPROVED|gate approved|final memo approved|zero-open closure passed)\b",
        body,
        re.IGNORECASE,
    ):
        add("PROHIBITED_APPROVAL_LANGUAGE", "BLOCKED", "Memo body contains prohibited approval wording.")

    if check_mispricing_language(root, body):
        add(
            "DEPTH_CONTROL_K1",
            "BLOCKED",
            "Mispricing language requires market_implied_expectations.md with a substantive alternative_rational_explanation.",
        )
    if check_opposing_thesis(root, body, tier):
        add(
            "DEPTH_CONTROL_K2",
            "WARNING",
            "Standard and Full runs require a substantive opposing thesis artefact or section; conclusion is capped.",
        )
    if check_falsification_section(body, tier):
        required = "one" if tier == "SCREEN" else "three"
        add(
            "DEPTH_CONTROL_K3",
            "BLOCKED",
            f"The falsification section is absent or contains fewer than {required} specific trigger(s).",
        )
    if check_scenario_midpoint(body):
        add(
            "DEPTH_CONTROL_K4",
            "BLOCKED",
            "The base case is affirmatively described as a midpoint of bull and bear; use an independently evidenced base case.",
        )
    if PER_SHARE_PATTERN.search(body) and not re.search(
        r"\bscenario[_ -]link\b|\b(?:bull|base|bear)\s+scenario\b",
        body,
        re.IGNORECASE,
    ):
        add(
            "DEPTH_CONTROL_K4_SCENARIO_LINK",
            "WARNING",
            "Per-share valuation is not linked to a named scenario; label it directional until linked.",
        )
    if check_liability_bridge(root, body):
        add(
            "DEPTH_CONTROL_K5",
            "WARNING",
            "A per-share figure lacks a complete twelve-row liability bridge or an explicit bridge-incomplete label.",
        )
    if check_exceptional_language(root, body, tier, objective):
        add(
            "DEPTH_CONTROL_K6",
            "WARNING",
            "Exceptional-outcome language lacks a completed reference-class and base-rate artefact; cap the conclusion.",
        )
    if check_ebitda_quality(root, body, tier):
        add(
            "DEPTH_CONTROL_K7",
            "WARNING",
            "EBITDA/FCF valuation lacks a substantive sustainable_cash_flow field; label it directional only.",
        )
    if check_triggered_artefact(
        root,
        body,
        CONTROL_STRUCTURE_PHRASES,
        "working/incentive_control_map.md",
    ):
        add(
            "DEPTH_CONTROL_K8",
            "WARNING",
            "Control-structure language requires a substantive incentive and control map; cap governance conclusions.",
        )
    if check_triggered_artefact(
        root,
        body,
        CAPITAL_ALLOCATION_PHRASES,
        "working/capital_allocation_record.md",
    ):
        add(
            "DEPTH_CONTROL_K9",
            "WARNING",
            "Capital-allocation assumptions require a substantive historical record; label them untested.",
        )
    if check_monitoring_plan(root, body, tier):
        add(
            "DEPTH_CONTROL_K10",
            "WARNING",
            "Standard and Full runs require a substantive monitoring plan; conclusion is point-in-time research only.",
        )

    preliminary = status_from_findings(findings)
    if declared_c9_status in C9_STATUSES and declared_c9_status != preliminary:
        severity = "BLOCKED" if preliminary == "BLOCKED" else "WARNING"
        add(
            "DECLARED_STATUS_MISMATCH",
            severity,
            f"Memo declares {declared_c9_status}, but current findings imply {preliminary}. Update the block and rerun.",
        )

    final_status = status_from_findings(findings)
    return final_status, [finding.__dict__ for finding in findings]


def format_report(status: str, findings: list[dict[str, str]], run_id: str = "unknown") -> str:
    lines = [
        "# C9 Policy Linter Report",
        "",
        f"run_id: {run_id}",
        f"c9_linter_status: {status}",
        f"findings_count: {len(findings)}",
        "",
    ]
    if not findings:
        lines.extend(["No policy violations or warnings found.", ""])
    for index, finding in enumerate(findings, start=1):
        lines.extend(
            [
                f"## {index}. {finding['code']} ({finding['severity']})",
                "",
                finding["detail"],
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="C9 company-research policy linter")
    parser.add_argument("memo", help="Path to working/memo_draft.md or final/memo.md")
    parser.add_argument(
        "--decision-log",
        default=None,
        help="Decision log path; defaults to <project>/final/decision_log.md",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root; inferred for memos under working/ or final/",
    )
    parser.add_argument(
        "--no-artifact-checks",
        action="store_true",
        help="Skip project artefact checks; intended only for isolated unit fixtures",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Report output path; defaults to <project>/working/c9_linter_report.md",
    )
    args = parser.parse_args()

    status, findings = lint(
        args.memo,
        decision_log_path=args.decision_log,
        project_root=args.project_root,
        check_artefacts=False if args.no_artifact_checks else None,
    )
    status_fields, _ = parse_key_value_block(Path(args.memo).read_text(encoding="utf-8"), STATUS_HEADING)
    report = format_report(status, findings, (status_fields or {}).get("run_id", "unknown"))
    print(report)

    memo = Path(args.memo)
    root = (
        Path(args.project_root)
        if args.project_root
        else (memo.parent.parent if memo.parent.name in {"working", "final"} else None)
    )
    report_path = (
        Path(args.report)
        if args.report
        else (root / "working" / "c9_linter_report.md" if root else None)
    )
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

    if status == "BLOCKED":
        raise SystemExit(1)
    if status == "WARNINGS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
