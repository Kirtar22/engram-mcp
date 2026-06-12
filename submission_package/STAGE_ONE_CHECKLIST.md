# Engram MCP — Stage One Qualification Checklist

This document maps every Stage One check to its direct evidence in this repository. Structured for the qualification reviewer to verify each check without searching the repo.

**Repository:** https://github.com/Kirtar22/engram-mcp  
**Devpost:** https://findevil.devpost.com  
**Demo Video:** https://youtu.be/mVMCqGKr64g  

---

## Quick Reference Table

| # | Check | Status | Primary Evidence |
|---|---|---|---|
| 1 | Repository is Public | **PASS** | [github.com/Kirtar22/engram-mcp](https://github.com/Kirtar22/engram-mcp) |
| 2 | Open Source License | **PASS** | [LICENSE](https://github.com/Kirtar22/engram-mcp/blob/main/LICENSE) — MIT |
| 3 | README with Setup Instructions | **PASS** | [README.md](https://github.com/Kirtar22/engram-mcp/blob/main/README.md) — "Installation & Setup Instructions" |
| 4 | Demo Video (≤5 min) | **NEEDS MANUAL REVIEW** | [youtu.be/mVMCqGKr64g](https://youtu.be/mVMCqGKr64g) — confirm duration, live terminal, narration, self-correction |
| 5 | Architecture Diagram | **PASS** | [Architecture_Diagram.png](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/Architecture_Diagram.png) · [architecture_diagram.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/architecture_diagram.md) |
| 6 | Written Project Description | **PASS** | [project_description.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/project_description.md) — all 5 sections present |
| 7 | Dataset Documentation | **PASS** | [evidence_dataset_documentation.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/dataset/evidence_dataset_documentation.md) |
| 8 | Accuracy Report | **PASS** | [accuracy_reports/](https://github.com/Kirtar22/engram-mcp/tree/main/submission_package/accuracy_reports) · [evidence_integrity.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/evidence_integrity.md) |
| 9 | Try-It-Out Instructions | **PASS** | [README.md](https://github.com/Kirtar22/engram-mcp/blob/main/README.md) — full local setup steps |
| 10 | Agent Execution Logs | **PASS** | [execution_trace.log](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/execution_trace.log) · [token_usage_methodology.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/token_usage_methodology.md) |
| 11 | Disqualification Screen | **PASS** | No flags — see detail below |

---

## Check 1: Repository is Public

**Status: PASS**  
**Evidence:** https://github.com/Kirtar22/engram-mcp loads without authentication. Root contains: `CLAUDE.md`, `LICENSE`, `README.md`, `mcp_server.py`, `requirements.txt`, `tools/`, `submission_package/`.

---

## Check 2: Open Source License (MIT or Apache 2.0)

**Status: PASS**  
**Evidence:** [LICENSE](https://github.com/Kirtar22/engram-mcp/blob/main/LICENSE) — MIT License. GitHub About section detects and displays the MIT license badge.

---

## Check 3: README with Setup Instructions

**Status: PASS**  
**Evidence:** [README.md](https://github.com/Kirtar22/engram-mcp/blob/main/README.md) contains sections:
- **"Installation & Setup Instructions"** — prerequisites (Python 3.10+, Volatility 3, Claude Code), git clone, venv, pip install, `VOLATILITY_PATH` env var, CLAUDE.md image path configuration, MCP server registration via `claude mcp add`
- **"Usage: Running an Investigation"** — run command (`claude`) and initial prompt

---

## Check 4: Demo Video (5 minutes max)

**Status: NEEDS MANUAL REVIEW**  
**Evidence:** https://youtu.be/mVMCqGKr64g — Title: *"Engram MCP: Autonomous AI Memory Forensics — Detects Ring 0 Rootkit | SANS Find Evil 2026"*  
**Manual reviewer must confirm:** (1) duration ≤5 minutes, (2) live terminal execution visible, (3) audio narration present, (4) at least one on-screen self-correction sequence shown.

---

## Check 5: Architecture Diagram

**Status: PASS**  
**Evidence:**
- [Architecture_Diagram.png](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/Architecture_Diagram.png) — visual pipeline diagram
- [architecture_diagram.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/architecture_diagram.md) — Mermaid diagram with:
  - Architectural pattern explicitly named: *"Custom MCP Server — as defined by the Find Evil! hackathon classification framework"*
  - Trust Boundaries table (4 rows: Evidence→Forensic Engine, Forensic Engine→MCP Server, MCP Server→LLM, LLM→Filesystem)
  - Guardrail Classification table distinguishing 3 architectural guardrails from 3 prompt-based guardrails

---

## Check 6: Written Project Description

**Status: PASS**  
**Evidence:** [project_description.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/project_description.md) — mirrors the full Devpost story. All five required sections present:
- **What it does** — OODA loop, MCP architecture, Domain Controller rootkit finding
- **How we built it** — Volatility 3, FastMCP, CLAUDE.md, Claude Sonnet 4.6, three real images
- **Challenges** — Empty Data Protocol, context decay, zero-knowledge analysis
- **What we learned** — data pipeline integrity, honesty as architectural decision, guardrail anchoring
- **What's next** — disk images, Linux support, YARA generation, multi-host orchestration

*Note: Devpost project page may require authentication for automated reviewers. Full story is available at the GitHub link above.*

---

## Check 7: Dataset Documentation

**Status: PASS**  
**Evidence:** [evidence_dataset_documentation.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/dataset/evidence_dataset_documentation.md) — documents all three test images:

| Image | Source | Download URL |
|---|---|---|
| `unknown_dmp.raw` (BlackEnergy) | CyberDefenders CTF | https://cyberdefenders.org/blueteam-ctf-challenges/blackenergy/ |
| `target_alpha.img` (Workstation) | SANS SRL-2018 | [Egnyte — base-wkstn-01-memory](https://sansorg.egnyte.com/fl/HhH7crTYT4JK#folder-link/HACKATHON-2026/Compromised%20APT%20Attack%20Scenarios/SRL-2018-Compromised%20Enterprise%20Network/SRL-2018?p=ebd34b81-dcdd-4086-8147-140079d93db9) |
| `target-beta-basedc.img` (DC) | SANS SRL-2018 | [Egnyte — base-dc-memory](https://sansorg.egnyte.com/fl/HhH7crTYT4JK#folder-link/HACKATHON-2026/Compromised%20APT%20Attack%20Scenarios/SRL-2018-Compromised%20Enterprise%20Network/SRL-2018?p=75d28978-a43f-4eff-abd9-a9ff4c98f45b) |

Each section includes: OS profile, findings table, attack chain reconstruction, false positives discarded, and forensic blind spots.

---

## Check 8: Accuracy Report

**Status: PASS**  
**Evidence — per-target accuracy reports** (false positives, missed artifacts, hallucinated claims):

| Target | Accuracy Report |
|---|---|
| target-alpha-basewkstn01 | [accuracy_report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/target-alpha-basewkstn01_accuracy_report.md) |
| target-beta-basedc | [accuracy_report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/target-beta-basedc_accuracy_report.md) |
| unknown-dmp-blackenergy | [accuracy_report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/unknown-dmp-blackenergy_accuracy_report.md) |

**Evidence — evidence integrity** (how the architecture prevents data modification):  
[evidence_integrity.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/evidence_integrity.md) — covers: Volatility 3 read-only memory mapping, MCP server exposes no write-path tools targeting evidence, subprocess read-only flags, chain of custody statement across all three investigations.

*Note: Engram uses both architectural and prompt-based guardrails. Evidence integrity is enforced architecturally (Volatility read-only + MCP API design) independent of model behavior.*

---

## Check 9: Try-It-Out Instructions

**Status: PASS**  
**Evidence:** [README.md — Installation & Setup Instructions](https://github.com/Kirtar22/engram-mcp/blob/main/README.md)

Full local setup steps:
1. `git clone https://github.com/Kirtar22/engram-mcp.git`
2. Create venv, `pip install -r requirements.txt`
3. Install Volatility 3 separately
4. Set `VOLATILITY_PATH` env var
5. Update `CLAUDE.md` with evidence image path
6. `claude mcp add engram python /path/to/mcp_server.py`
7. Run: `claude` → issue investigation prompt

---

## Check 10: Agent Execution Logs

**Status: PASS**  
**Evidence — machine logs (timestamped tool calls + token usage):**
- [execution_trace.log](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/execution_trace.log) — ISO 8601 timestamps, TOOL_CALL/TOOL_SUCCESS/TOOL_EXCEPTION entries for all four investigation sessions
- [token_usage_methodology.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/token_usage_methodology.md) — per-session token counts
- [dev_notes.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/dev_notes.md) — session metadata

**Spot-check:** Devpost story states *"the agent autonomously detected a Ring 0 rootkit (Mnemosyne.sys) responsible for hiding 124 processes via DKOM on the Domain Controller."* Filter `execution_trace.log` for `2026-04-23` and `target-beta-basedc` to find the Phase 1 `tool_phase1_surface_triage` TOOL_CALL and TOOL_SUCCESS entries that produced this finding.

**Evidence — agent reasoning traces (per target):**

| Target | Reasoning Trace |
|---|---|
| target-alpha-basewkstn01 | [execution_trace.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/target_alpha(base-wkstn-01)_execution_trace.md) |
| target-beta-basedc | [conversation_log](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/target-beta(base-dc).md) |
| unknown-dmp (BlackEnergy) | [conversation_log](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/unknown_dmp(BlackEnergy).md) |

---

## Check 11: Disqualification Screen

**Status: PASS — no flags**

**(a) Thin wrapper with no agentic behavior?**  
No. The FastMCP Python server exposes 6 typed endpoints. The agent executes a deterministic 6-phase OODA loop with state tracking, self-correction, and structured JSON output. Conversation logs show multi-step reasoning, false positive rejection, and Red Team self-checks. This is not pass-through to an LLM.

**(b) No real case data analyzed?**  
No. Three real memory images investigated across different OS profiles and malware families. Full findings, incident reports, and traceable execution logs are present for each.

**(c) Dependent on proprietary tools judges cannot access?**  
No. Volatility 3 is open source. Claude Code is publicly available. SANS SRL-2018 images are accessible via the Egnyte links in Check 7. BlackEnergy image is freely available via CyberDefenders.
