# Company Evaluation Pipeline

A structured, evidence-graded company research framework for [Claude Code](https://claude.ai/code). It runs a 17-stage pipeline (16 core stages + C0 claim-audit gate) — financial spine, capital structure, business model, management track record, market position, valuation, scenarios — and produces a final investment memo with a fully traceable facts ledger.

The pipeline integrates with **Google NotebookLM** as its document Q&A backend, so all answers are grounded in the source documents you upload rather than Claude's training data.

---

## What it produces

Running the full pipeline on a public equity target gives you:

| Output | Description |
|---|---|
| `pipeline.md` | Stage-by-stage tracker with gate decisions and decision log |
| `sources/source_register.csv` | All sources registered with IDs and local paths |
| `working/facts_ledger.md` | Append-only ledger of every fact, classified as fact / observation / inference / assumption |
| `working/checks/B1_cash_rollforward.py` | Deterministic cash roll-forward verification |
| `working/checks/B2_capital_structure.py` | 4-step cap table check: bridge → instruments → FD → valuation |
| `working/checks/C2_valuation.py` | Valuation multiples locked to fully-diluted share count |
| `notebooklm_outputs/raw/` | Raw NotebookLM responses for every stage (immutable) |
| `C9_final_memo.md` | Final investment research memo with scenario analysis |

---

## Prerequisites

| Requirement | Notes |
|---|---|
| [Claude Code](https://claude.ai/code) | Anthropic's official CLI — runs the pipeline |
| Python 3.9+ | For deterministic numeric checks (cash roll-forward, cap table, valuation) |
| Google account | For NotebookLM authentication |
| `notebooklm-py` | CLI for programmatic NotebookLM access — see installation below |

---

## Step 1 — Install `notebooklm-py`

[`notebooklm-py`](https://github.com/teng-lin/notebooklm-py) gives Claude Code programmatic access to Google NotebookLM: creating notebooks, adding document sources, and querying them.

### Install from PyPI (recommended)

```bash
pip install notebooklm-py
```

### Authenticate with your Google account

```bash
notebooklm login
```

This opens a browser window for Google OAuth. Sign in with the Google account that has your NotebookLM notebooks.

### Verify authentication

```bash
notebooklm list
```

You should see a list of your existing notebooks (or an empty list if you have none yet). If this command fails, re-run `notebooklm login`.

### Quick reference

```bash
notebooklm status                        # Show authenticated account
notebooklm create "Company: Acme Corp"   # Create a new notebook
notebooklm use <notebook_id>             # Set the active notebook
notebooklm source add ./report.pdf       # Upload a PDF as a source
notebooklm source add "https://..."      # Add a URL as a source
notebooklm ask "What is the revenue?"    # Query the notebook
```

> **Windows note:** If you see `UnicodeEncodeError` when running Python scripts that contain special characters, set `$env:PYTHONIOENCODING = "utf-8"` before running.

---

## Step 2 — Install Claude Code

Follow the [Claude Code quickstart](https://docs.anthropic.com/en/docs/claude-code/quickstart). The CLI is available on macOS, Windows, and Linux.

```bash
npm install -g @anthropic-ai/claude-code
claude
```

Or use the [Claude Code desktop app](https://claude.ai/code) for Windows and macOS.

---

## Step 3 — Run the pipeline

### 3a. Create a NotebookLM notebook for your target company

```bash
notebooklm create "Company: [Target Name]"
# Note the notebook ID returned — you'll need it
notebooklm use <notebook_id>
```

### 3b. Open Claude Code and load the framework file

Start a Claude Code session and attach the core file:

```
@pipeline_core.md read the file. do not action anything
```

The core file (~500 lines) contains everything needed for every stage. As you run each stage, Claude
will read the relevant section from `pipeline_reference.md` on demand (the dispatch table at the end
of `pipeline_core.md` tells it when). This two-file structure cuts the mandatory context load by
roughly two-thirds compared to loading the full combined file.

Alternatively, load the full combined file if you prefer everything in one place:

```
@company_research_level3_single_agent_claude.md read the file. do not action anything
```

Claude will read the pipeline specification. It will then ask you:
- What company you want to research
- What research objective (public equity, M&A, credit, etc.)
- Whether to run in **MANUAL** or **AUTO** gate mode

### 3c. Choose a gate mode

| Mode | Description | When to use |
|---|---|---|
| **MANUAL** | Claude pauses at each of the 5 human gates and waits for your explicit approval before proceeding | Default — use when actively reviewing |
| **AUTO** | Claude runs stages without human pauses, records checkpoint packets, runs the self-repair loop, and marks each stage as `AUTO-RUN COMPLETE`, `AUTO-RUN COMPLETE WITH CAVEATS`, `AUTO-REPAIRED`, or `AUTO-BLOCKED`. AUTO mode is an execution setting, not an approval setting. | Use when you want continuous execution — the final output requires human review before any investment decision. |

### 3d. Collect and upload source documents

The pipeline includes a **Step 0 — Deep Internet Search** that Claude Code runs automatically. It will:

1. Search for annual reports, investor presentations, regulatory filings, and news for your target company
2. Download relevant PDFs to `sources/raw/`
3. Upload them to your NotebookLM notebook as **file sources** (not URL sources, so the content is indexed locally)
4. Register each source in `sources/source_register.csv`

You can also add documents manually:

```bash
notebooklm source add ./annual_report_2025.pdf
notebooklm source add "https://example.com/investor-presentation"
notebooklm source wait   # Wait for NotebookLM to index all sources
```

### 3e. Run the pipeline stages

Tell Claude to proceed:

```
follow the process
```

Claude Code will run each stage sequentially:

| Phase | Stages | What happens |
|---|---|---|
| **A — Scope & source integrity** | A1 | Checks if the research mandate is answerable from your sources. Halts if not. |
| **B — Evidence spine** | B1–B6 | Financial spine → cap table → business model → asset evidence → management track record. Python scripts verify every key number. |
| **C — Judgement** | C0–C9 | Claim audit & confidence caps (C0) → market/competition → valuation → capital requirements → scenarios → final memo |

At each human gate (MANUAL mode), Claude will present a structured checkpoint packet and wait for one of:
- `approve` — proceed to next stage
- `approve with caveats: [your notes]` — proceed, caveat recorded
- `request revision: [what to redo]` — Claude redoes the stage
- `add sources: [what's missing]` — pause to add more documents
- `halt` — stop the pipeline

---

## Evidence classification

Every fact in the ledger carries one of four classifications:

| Label | Meaning |
|---|---|
| **fact** | Directly stated in a primary source (audited accounts, regulatory filing, signed contract) |
| **observation** | Stated by the company or a credible source but not independently verified or audited |
| **inference** | Derived from facts/observations by the analyst; not directly stated anywhere |
| **assumption** | Required for the analysis but not grounded in a primary source |

The pipeline automatically applies **qualitative downgrade rules**: if a claim lacks a primary source, its classification is downgraded and the wording in the output is softened accordingly.

For Standard and Full diligence, §8A refines these four classes into eight evidence classes (e.g.
*filed fact*, *reported estimate*, *company-reported test result*, *analyst observation*) and adds a
separate **decision-maturity** axis (decision-ready → not-usable-for-decision), a **valuation evidence
ladder** (Level 0–6), and **recommendation caps** so a memo cannot state a conclusion stronger than its
weakest load-bearing evidence supports.

---

## Directory structure

The pipeline creates the following structure in your working directory:

```
[Company Name]/
├── pipeline.md                          # Stage tracker + decision log
├── C9_final_memo.md                     # Final investment memo
├── sources/
│   ├── source_register.csv              # All sources with IDs and paths
│   └── raw/                             # Downloaded PDFs and documents
├── working/
│   ├── facts_ledger.md                  # Append-only evidence ledger
│   ├── evidence_gaps.md                 # Open evidence gaps
│   ├── open_questions.md                # Unresolved questions
│   ├── [Stage]_approval.md              # Gate approval records
│   └── checks/
│       ├── B1_cash_rollforward.py       # Cash flow verification
│       ├── B2_capital_structure.py      # Cap table 4-step check
│       └── C2_valuation.py              # Valuation multiples
└── notebooklm_outputs/
    └── raw/                             # Immutable NotebookLM responses per stage
```

---

## Research objectives

The pipeline adapts to different research objectives. At the start of a run, select one:

| Objective | Key mandatory stages |
|---|---|
| Public equity investment | A1, B1, B2, B6, C0–C9 |
| Private investment / VC / growth | A1, B1–B6, C0–C9 |
| Credit / lending | A1, B1, C3, C7 |
| M&A target diligence | A1, B1–B6, C0–C9 |
| Supplier / vendor diligence | A1, B1, B4, B5, B6, C7 |
| General company profile | A1, B1, B3, B6, C0, C1, C9-lite |

---

## Depth tiers

| Tier | When | Human gates |
|---|---|---|
| **Screen** | Quick read, watchlist, first pass | 2 |
| **Standard** | Active position, real money at stake | 4 |
| **Full diligence** | Large position, deal, or contested view | 5 |

A Screen automatically escalates to Standard if it finds: pre-revenue company, going-concern warning, complex cap table, milestone-dependent valuation, or repeated missed guidance.

---

## Limitations

- This pipeline produces a research memo and an evidence record. **It does not produce an automatic investment decision.**
- AUTO mode is an execution setting, not an approval setting. The output is a research artefact that requires human review before any investment decision. Running AUTO removes live human challenge at the gates; the final output must state that human judgement was not performed.
- The reliability of the output depends on the quality and completeness of the source documents you upload to NotebookLM.
- The deterministic Python checks verify internal consistency; they do not substitute for a full audit.

---

## Files in this repository

| File | Description |
|---|---|
| `pipeline_core.md` | **Load this at session start.** ~500 lines. Design principles, stage loop, cross-cutting rules (§8A core controls, do-not-proceed conditions, core principles). Stays in context for the entire run. |
| `pipeline_reference.md` | **Read specific sections on demand.** ~1,300 lines. Source-acquisition checklists, stage procedures, verification protocols, linter checklists, appendix templates, post-run learning. The dispatch table in `pipeline_core.md` says when to read which section. |
| `company_research_level3_single_agent_claude.md` | Full combined file (legacy). Equivalent to core + reference in one document. Use if you prefer a single-file load; accept the higher context cost. |
| `README.md` | This file |

---

## License

MIT
