# Engram MCP — Judge's Navigation Guide

**Submission for:** SANS Find Evil Hackathon (findevil.devpost.com)  
**Repository:** https://github.com/Kirtar22/engram-mcp  
**Demo Video:** [Demo Video — YouTube](https://youtu.be/mVMCqGKr64g)  

This document maps every required submission artifact to its exact location so judges do not need to search the repository.

---

## Quick Reference: Required Artifacts

| Artifact | Location |
|---|---|
| Source Code | [mcp_server.py](https://github.com/Kirtar22/engram-mcp/blob/main/mcp_server.py) · [tools/](https://github.com/Kirtar22/engram-mcp/tree/main/tools) |
| Agent System Prompt (Guardrails) | [CLAUDE.md](https://github.com/Kirtar22/engram-mcp/blob/main/CLAUDE.md) |
| Setup Instructions | [README.md](https://github.com/Kirtar22/engram-mcp/blob/main/README.md) |
| Architecture Diagram | [Architecture_Diagram.png](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/Architecture_Diagram.png) · [architecture_diagram.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/architecture_diagram.md) (includes Trust Boundaries + Guardrail Classification) |
| Project Description | [project_description.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/project_description.md) |
| Evidence Dataset Documentation | [evidence_dataset_documentation.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/dataset/evidence_dataset_documentation.md) |
| Baseline Assessment (pre-Engram) | [baseline_assessment.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/baseline_assessment.md) |
| License | [MIT License](https://github.com/Kirtar22/engram-mcp/blob/main/LICENSE) |

---

## Accuracy Reports (per target)

Three targets were investigated. Each has an independent accuracy report with honest self-assessment of false positives, missed artifacts, and hallucinated claims. Evidence integrity (how the architecture prevents data modification) is documented in [evidence_integrity.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/evidence_integrity.md).

| Target | Profile | Accuracy Report |
|---|---|---|
| target-alpha-basewkstn01 | Windows workstation — Mnemosyne.sys DKOM rootkit | [accuracy_report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/target-alpha-basewkstn01_accuracy_report.md) |
| target-beta-basedc | Windows Domain Controller — Ring 0 rootkit (video target) | [accuracy_report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/target-beta-basedc_accuracy_report.md) |
| unknown-dmp-blackenergy | Unknown dump — BlackEnergy malware | [accuracy_report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/accuracy_reports/unknown-dmp-blackenergy_accuracy_report.md) |

---

## Agent Execution Logs (full conversation traces)

Structured logs showing complete agent communication and tool execution with timestamps and token usage. Every finding in the incident reports is traceable to a specific tool call in these logs.

**Machine logs (timestamped tool calls):** [execution_trace.log](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/execution_trace.log) · [token_usage_methodology.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/token_usage_methodology.md) · [dev_notes.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/execution_logs/dev_notes.md)

**Agent reasoning traces (per target):**

| Target | Execution Log |
|---|---|
| target-alpha-basewkstn01 | [execution_trace](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/target_alpha(base-wkstn-01)_execution_trace.md) |
| target-beta-basedc | [conversation_log](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/target-beta(base-dc).md) |
| unknown-dmp (BlackEnergy) | [conversation_log](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/unknown_dmp(BlackEnergy).md) |
| Baseline (pre-Engram, raw terminal) | [vanilla_sift_run](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/vanilla_sift_memoryskill_run.md) |

---

## Final Incident Reports

Machine-generated forensic artifacts written to disk by the agent's `tool_write_report` call — not manually authored.

| Target | Incident Report |
|---|---|
| unknown-dmp (BlackEnergy) | [20260417_Incident_Report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/memory_analysis_reports/20260417_121747_Incident_Report_unknown_dmp.md) |
| target-alpha-basewkstn01 | [20260418_Incident_Report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/memory_analysis_reports/20260418_070623_Incident_Report_target_alpha_2026-04-18.md) |
| target-beta-basedc | [20260423_Incident_Report](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/memory_analysis_reports/20260423_064650_Incident_Report_target-beta-basedc.md) |

---

## Judging Criteria — Where to Look

| Criterion | Where to find evidence |
|---|---|
| Autonomous Execution Quality | Execution logs above — watch for self-correction sequences and Red-Team self-checks |
| IR Accuracy | Accuracy reports + incident reports. Hallucinated claims explicitly flagged |
| Breadth and Depth | Three targets across different OS profiles and malware families |
| Constraint Implementation | [CLAUDE.md](https://github.com/Kirtar22/engram-mcp/blob/main/CLAUDE.md) (prompt layer) + [mcp_server.py](https://github.com/Kirtar22/engram-mcp/blob/main/mcp_server.py) (architectural layer) |
| Audit Trail Quality | Every finding in incident reports has a corresponding tool call in the execution logs with timestamps |
| Usability and Documentation | [README.md](https://github.com/Kirtar22/engram-mcp/blob/main/README.md) — full setup, configuration, and usage instructions |

---

## Baseline Comparison

The [baseline_assessment.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/baseline_assessment.md) documents the pre-Engram raw terminal test: 147k tokens, 20m 31s, $2.07, manually aborted. The full execution log is at [vanilla_sift_memoryskill_run.md](https://github.com/Kirtar22/engram-mcp/blob/main/submission_package/conversation_logs/vanilla_sift_memoryskill_run.md). This establishes the empirical baseline that motivated the architecture.
