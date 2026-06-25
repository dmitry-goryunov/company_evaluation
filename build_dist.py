#!/usr/bin/env python3
"""
build_dist.py — generate the combined single-file export.

Concatenates pipeline_core.md and pipeline_reference.md into
dist/company_research_level3_single_agent_claude.md.

The output file is generated; do not edit it directly.
Edit pipeline_core.md and pipeline_reference.md instead, then re-run this script.

Usage:
    python build_dist.py
"""

import os
import datetime

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(REPO_ROOT, "pipeline_core.md")
REFERENCE = os.path.join(REPO_ROOT, "pipeline_reference.md")
DIST_DIR = os.path.join(REPO_ROOT, "dist")
OUTPUT = os.path.join(DIST_DIR, "company_research_level3_single_agent_claude.md")

HEADER = """> **GENERATED FILE — DO NOT EDIT**
>
> This file is produced by `build_dist.py` by concatenating:
> - `pipeline_core.md` (canonical — always-load core)
> - `pipeline_reference.md` (canonical — reference, read by section on demand)
>
> To update this file, edit the canonical sources and re-run `python build_dist.py`.
> Generated: {timestamp}

---

"""


def build():
    os.makedirs(DIST_DIR, exist_ok=True)

    with open(CORE, encoding="utf-8") as f:
        core_text = f.read()

    with open(REFERENCE, encoding="utf-8") as f:
        reference_text = f.read()

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = HEADER.format(timestamp=timestamp)

    combined = (
        header
        + core_text.rstrip()
        + "\n\n---\n\n"
        + reference_text.lstrip()
    )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(combined)

    core_lines = core_text.count("\n")
    ref_lines = reference_text.count("\n")
    total_lines = combined.count("\n")
    print(f"Built {OUTPUT}")
    print(f"  pipeline_core.md:      {core_lines:>5} lines")
    print(f"  pipeline_reference.md: {ref_lines:>5} lines")
    print(f"  combined output:       {total_lines:>5} lines")


if __name__ == "__main__":
    build()
