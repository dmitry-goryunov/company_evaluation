#!/usr/bin/env python3
"""
build_dist.py — generate the combined single-file export.

Concatenates pipeline_core.md and pipeline_reference.md into
dist/company_research_level3_single_agent_claude.md.

The output file is generated; do not edit it directly.
Edit pipeline_core.md and pipeline_reference.md instead, then re-run this script.

Usage:
    python build_dist.py
    python build_dist.py --check
"""

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CORE = REPO_ROOT / "pipeline_core.md"
REFERENCE = REPO_ROOT / "pipeline_reference.md"
DIST_DIR = REPO_ROOT / "dist"
OUTPUT = DIST_DIR / "company_research_level3_single_agent_claude.md"

HEADER = """> **GENERATED FILE — DO NOT EDIT**
>
> This file is produced by `build_dist.py` by concatenating:
> - `pipeline_core.md` (canonical — always-load core)
> - `pipeline_reference.md` (canonical — reference, read by section on demand)
>
> To update this file, edit the canonical sources and re-run `python build_dist.py`.
---

"""


def build_text():
    core_text = CORE.read_text(encoding="utf-8")
    reference_text = REFERENCE.read_text(encoding="utf-8")
    return (
        HEADER
        + core_text.rstrip()
        + "\n\n---\n\n"
        + reference_text.lstrip()
    )


def build(check=False):
    combined = build_text()
    if check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
        if current != combined:
            print(f"STALE: {OUTPUT}; run python build_dist.py")
            return 1
        print(f"CURRENT: {OUTPUT}")
        return 0

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(combined, encoding="utf-8")
    print(f"Built {OUTPUT}")
    print(f"  pipeline_core.md:      {len(CORE.read_text(encoding='utf-8').splitlines()):>5} lines")
    print(f"  pipeline_reference.md: {len(REFERENCE.read_text(encoding='utf-8').splitlines()):>5} lines")
    print(f"  combined output:       {len(combined.splitlines()):>5} lines")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the deterministic combined pipeline export")
    parser.add_argument("--check", action="store_true", help="Fail if the committed export is stale")
    args = parser.parse_args()
    raise SystemExit(build(check=args.check))
