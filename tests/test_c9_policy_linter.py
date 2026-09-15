from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checks.c9_policy_linter import (
    PER_SHARE_PATTERN,
    check_investment_action_phrases,
    check_liability_bridge,
    check_scenario_midpoint,
    format_report,
    lint,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
EXPECTED = ROOT / "tests" / "expected"


def read_expectation(path: Path) -> tuple[str, set[str]]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip()
    codes = {code.strip() for code in values.get("required_codes", "").split(",") if code.strip()}
    return values["status"], codes


def clean_screen_memo(**replacements: str) -> str:
    text = (FIXTURES / "clean_screen_memo.md").read_text(encoding="utf-8")
    for field, value in replacements.items():
        text = text.replace(f"{field}: " + next(
            line.split(": ", 1)[1]
            for line in text.splitlines()
            if line.startswith(f"{field}: ")
        ), f"{field}: {value}", 1)
    return text


class FixtureTests(unittest.TestCase):
    def test_fixture_expectations_are_executable(self) -> None:
        for expectation in sorted(EXPECTED.glob("*.expected_status.txt")):
            fixture = FIXTURES / expectation.name.replace(".expected_status.txt", ".md")
            with self.subTest(fixture=fixture.name):
                expected_status, expected_codes = read_expectation(expectation)
                status, findings = lint(fixture, check_artefacts=False)
                codes = {finding["code"] for finding in findings}
                self.assertEqual(status, expected_status)
                self.assertTrue(expected_codes.issubset(codes), expected_codes - codes)


class StatusValidationTests(unittest.TestCase):
    def lint_text(self, text: str, decision_log: str | None = None) -> tuple[str, set[str]]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            memo = root / "memo.md"
            memo.write_text(text, encoding="utf-8")
            decision = None
            if decision_log is not None:
                decision = root / "decision_log.md"
                decision.write_text(decision_log, encoding="utf-8")
            status, findings = lint(memo, decision_log_path=decision, check_artefacts=False)
            return status, {finding["code"] for finding in findings}

    def test_invalid_enums_counts_and_critical_gap_cannot_be_clean(self) -> None:
        memo = clean_screen_memo(
            gate_mode="BANANA",
            human_review_performed="maybe",
            investment_decision_approved="yes",
            unresolved_must_answer_count="banana",
            unresolved_critical_gap_count="9",
            allowed_conclusion_language="decision-approved",
            investment_action_allowed="yes",
            position_sizing_allowed="yes",
        )
        status, codes = self.lint_text(memo)
        self.assertEqual(status, "BLOCKED")
        self.assertIn("INVALID_STATUS_VALUE", codes)
        self.assertIn("STATUS_DERIVATION_ERROR", codes)

    def test_duplicate_status_key_is_blocked(self) -> None:
        memo = clean_screen_memo().replace("gate_mode: AUTO", "gate_mode: AUTO\ngate_mode: MANUAL")
        status, codes = self.lint_text(memo)
        self.assertEqual(status, "BLOCKED")
        self.assertIn("INVALID_STATUS_BLOCK", codes)

    def test_one_line_override_is_invalid(self) -> None:
        status, codes = self.lint_text(clean_screen_memo(), "## decision_log_override\noverride_granted: yes\n")
        self.assertEqual(status, "BLOCKED")
        self.assertIn("INVALID_OVERRIDE", codes)

    def test_complete_human_override_is_scoped_to_run_and_open_items(self) -> None:
        memo = clean_screen_memo(
            run_id="fixture-valid-override",
            human_review_performed="yes",
            c0_recommendation_cap="decision-not-ready",
            unresolved_must_answer_count="1",
            unresolved_high_risk_count="1",
            allowed_conclusion_language="decision-approved",
            investment_action_allowed="yes",
            position_sizing_allowed="yes",
        ).replace("THESIS-TRACKING. The evidence supports monitoring only.", "BUY.")
        decision_log = """## decision_log_override
run_id: fixture-valid-override
reviewer: Portfolio manager
review_date: 2026-09-15
review_scope: C8-01 and RISK-01
open_items_reviewed: [C8-01, RISK-01]
override_granted: yes
override_reason: Explicit human judgement after reviewing both items
accepted_risks: [RISK-01]
position_sizing_approved: yes
approved_action: Initiate a 1% position
follow_up_required: Reassess both items monthly
"""
        status, codes = self.lint_text(memo, decision_log)
        self.assertEqual(status, "CLEAN")
        self.assertEqual(codes, set())

    def test_approved_decision_must_match_status_and_run(self) -> None:
        memo = clean_screen_memo(
            run_id="fixture-approved-decision",
            human_review_performed="yes",
            investment_decision_approved="yes",
            c0_recommendation_cap="unrestricted",
            allowed_conclusion_language="decision-approved",
            investment_action_allowed="yes",
        )
        decision_log = """## decision_approval
run_id: fixture-approved-decision
reviewer: Investment committee chair
review_date: 2026-09-15
decision: approved-with-caveats
approved_action: Proceed subject to stated conditions
position_sizing_approved: no
follow_up_required: Review in 30 days
"""
        status, codes = self.lint_text(memo, decision_log)
        self.assertEqual(status, "CLEAN")
        self.assertEqual(codes, set())

    def test_approval_cannot_be_hidden_by_negative_status(self) -> None:
        memo = clean_screen_memo(run_id="fixture-approval-mismatch", human_review_performed="yes")
        decision_log = """## decision_approval
run_id: fixture-approval-mismatch
reviewer: Investment committee chair
review_date: 2026-09-15
decision: approved
approved_action: Proceed
position_sizing_approved: no
follow_up_required: none
"""
        status, codes = self.lint_text(memo, decision_log)
        self.assertEqual(status, "BLOCKED")
        self.assertIn("STATUS_DERIVATION_ERROR", codes)

    def test_report_carries_run_id(self) -> None:
        report = format_report("CLEAN", [], "fixture-report-001")
        self.assertIn("run_id: fixture-report-001", report)


class ProseControlTests(unittest.TestCase):
    def test_required_midpoint_wording_is_not_a_violation(self) -> None:
        text = "The base case is the most evidence-supported case, not the midpoint between bull and bear."
        self.assertFalse(check_scenario_midpoint(text))

    def test_affirmative_midpoint_wording_is_a_violation(self) -> None:
        text = "The base case is calculated as the midpoint between bull and bear."
        self.assertTrue(check_scenario_midpoint(text))

    def test_corporate_operating_verbs_are_not_investment_actions(self) -> None:
        text = "Management will invest £100m, add £10m of debt and buy an asset."
        self.assertEqual(check_investment_action_phrases(text), [])

    def test_recommendation_words_and_sentence_boundaries_are_detected(self) -> None:
        text = "The refinancing is not expected to fail.\nBUY.\nRecommended allocation: 2%."
        hits = check_investment_action_phrases(text)
        self.assertTrue(any("BUY" in hit for hit in hits))
        self.assertTrue(any("allocation" in hit.lower() for hit in hits))

    def test_common_per_share_currencies_are_detected(self) -> None:
        for value in ("$5 per share", "£5/share", "EUR 4.20 per share", "350–470p"):
            with self.subTest(value=value):
                self.assertIsNotNone(PER_SHARE_PATTERN.search(value))

    def test_liability_bridge_requires_all_twelve_rows(self) -> None:
        rows = (
            "Enterprise value\nNet debt\nLeases\nHybrids\nDecommissioning\nPension\n"
            "Tax liabilities\nMinority interests\nOff-balance-sheet\nEquity value\n"
            "Share denominator\nPer-share output\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            working = root / "working"
            working.mkdir()
            bridge = working / "capital_structure.md"
            bridge.write_text("Share denominator\nPer-share output\n", encoding="utf-8")
            self.assertTrue(check_liability_bridge(root, "$5 per share in the base scenario"))
            bridge.write_text(rows, encoding="utf-8")
            self.assertFalse(check_liability_bridge(root, "$5 per share in the base scenario"))


class ArtefactTests(unittest.TestCase):
    def test_project_memo_without_required_artefacts_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            working = root / "working"
            working.mkdir()
            memo = working / "memo_draft.md"
            memo.write_text(clean_screen_memo(), encoding="utf-8")
            status, findings = lint(memo)
            codes = {finding["code"] for finding in findings}
            self.assertEqual(status, "BLOCKED")
            self.assertIn("MISSING_REQUIRED_ARTEFACT", codes)
            self.assertIn("MISSING_SOURCE_EVIDENCE", codes)


if __name__ == "__main__":
    unittest.main()
