# Engram MCP: Deterministic AI Orchestration for Memory Forensics
**A Model Context Protocol (MCP) Approach to Autonomous Digital Forensics and Incident Response (DFIR)**

## 1. Problem Statement & Baseline Empirical Observations
The integration of Large Language Models (LLMs) into autonomous DFIR workflows has historically relied on piping agent outputs directly into interactive Unix/Linux bash shells (e.g., SANS SIFT). To establish a baseline for this project, we subjected an unconstrained LLM agent to a standard memory forensics CTF (MemLabs Lab 5: "Black Tuesday") via raw terminal I/O. 

While the agent successfully completed initial triage, the architecture suffered a cascading failure at the 20-minute mark, consuming over 147,000 tokens before manual abortion. This baseline assessment revealed four critical, inherent flaws in the "LLM-to-Terminal" paradigm:

1. **Context Window Flooding via Unstructured Data**
   * *The Flaw:* Forensics tools output high-volume, unstructured tabular data. When attempting to locate a password, the agent dumped 176+ lines of raw hexadecimal and virtual allocations directly into `stdout`. Forcing an LLM to parse raw graphical hex dumps exhausted its active context window, causing a severe degradation in reasoning.
   * *The MCP Solution:* Force Volatility to output in JSON. Python MCP tools ingest the JSON, filter out noise, and return tightly formatted intelligence summaries to the Orchestrator.
2. **Unhandled Interactive Prompts (The Execution Hang)**
   * *The Flaw:* Standard CLI tools block execution when expecting `[y/N]` or password prompts. When the agent executed `unrar`, the process halted awaiting a password. Lacking an asynchronous mechanism to inject `STDIN`, the agent entered a token-burning loop.
   * *The MCP Solution:* Python wrappers monitor `stderr/stdout` for hanging prompts and gracefully kill/timeout the process, returning a clean error state to the Orchestrator.
3. **Inefficient Threat Hunting**
   * *The Flaw:* The agent utilized standard bash `grep` to hunt for signatures across a multi-gigabyte memory dump, which is highly computationally inefficient.
   * *The MCP Solution:* Abstract complex sweeps into strict functions (e.g., `tool_yara_scan`) utilizing optimized C-bindings (YARA) under the hood.
4. **Syntax Hallucinations Under Pressure**
   * *The Flaw:* As context decayed, the agent began hallucinating Volatility command syntax, resulting in repeated `Exit code 2` failures and complete methodology breakdown.
   * *The MCP Solution:* MCP abstracts command creation. The Orchestrator calls a strict Python function (e.g., `extract_file(pid=2724)`), guaranteeing 100% deterministic Volatility API syntax.

---

## 2. Architectural Methodology
To resolve the baseline failures, we engineered **Engram MCP**. The architecture decouples the reasoning engine from the execution layer. 
* **The Evidence Layer:** Raw memory dumps (`.img`, `.raw`, `.vmem`).
* **Telemetry Extraction:** Volatility 3 Framework (Symbol tables, memory carving).
* **Control & Safety Layer:** FastMCP Python Server (Tool routing, timeout handling, JSON serialization).
* **Orchestration Layer:** LLM Agent governed by a strict system prompt (`CLAUDE.md`).

---

## 3. The 6-Phase OODA Loop Methodology
The crux of Engram MCP is its rigidly enforced state machine. The agent is strictly forbidden from wandering or executing plugins out of order. It must progress through a deterministic 6-Phase OODA Loop:

| Phase | Objective | Volatility 3 Plugins Used | What We Are Hunting For (The AI's Logic) |
| :--- | :--- | :--- | :--- |
| **Phase 1: Surface Triage** | Baseline context, obvious anomalies, and privilege checks. | `pslist`, `psscan`, `pstree`, `netscan`, `getsids` | **DKOM/ADD Spoofing:** Are processes hidden or thread-starved?<br>**Anomalous Topology:** Typosquatting or orphaned parents?<br>**Network C2:** Active external connections?<br>**PrivEsc:** Is a user-space app running as SYSTEM? |
| **Phase 2: Deep User-Space** | Hollowing, Reflective Injection, and PEB manipulation. | `malfind`, `ldrmodules`, `dlllist` | **PEB Diffing:** Compare `dlllist` against `ldrmodules` to catch VAD-mapped DLLs hiding from the OS.<br>**Memory Carving:** Locate unbacked RWX (Read/Write/Execute) memory regions. |
| **Phase 3: The Kernel Abyss** | Ring 0 Rootkits and Subversion. | `modules`, `modscan`, `ssdt`, `callbacks`, `driverirp` | **Hidden Drivers:** Diff `modules` vs `modscan`.<br>**PatchGuard Evasion:** Rogue thread/process callbacks.<br>**SSDT/IRP Hooking:** Catch drivers intercepting file/network I/O before it reaches the OS. |
| **Phase 4: Advanced Evasion** | Memory evasion counters and transient execution tracking. | `threads`, `windows.registry`, `vadyarascan` | **Gargoyle/RX Evasion:** Sweep threads and APC queues for execution pointers in RX memory.<br>**Execution Tracking:** Parse Shimcache/Amcache to prove transient malware ran and died. |
| **Phase 5: Substantiation** | IOC Extraction and Proof. (Triggered by phase anomalies). | `cmdline`, `handles`, `dumpfiles`, `memmap` | **The Sniper Rifle:** Extract base64 arguments, malicious Mutexes, and safely dump the binary/memory segment to disk for the final report. |
| **Phase 6: Incident Reporting** | Synthesize the OODA loop into an immutable artifact. | N/A (`tool_write_report`) | **Final Synthesis:** Compile forensic blind spots, verified IOCs, and the OODA timeline into a structured Markdown report for the SOC team, decoupling report generation from standard output. |

---

## 4. Key Innovations & Features

* **Mitigating LLM Training Data Bias (Zero-Knowledge Analysis):** Because standard datasets (e.g., SANS 2018 APT) are heavily documented online, LLMs risk triggering "Semantic Anchors"—hallucinating findings from CTF write-ups rather than analyzing actual tool output. We enforce *Zero-Knowledge Analysis* by anonymizing evidence files (e.g., `target_alpha.img`) and stripping metadata, forcing the agent to evaluate the threat strictly through our MCP data pipeline.
* **Autonomous DKOM Correlation:** During testing, the OS API layer (`pslist`) returned 0 active processes. Rather than halting, the agent cross-referenced this with physical memory carving (`psscan`), finding 131 processes. The agent successfully correlated this discrepancy to autonomously prove the `PsActiveProcessHead` had been unlinked by a Ring-0 rootkit.
* **Audit Trail & Linear Execution Tracking:** We enforce strict linear execution. The agent is required to print a Markdown Checkbox State Tracker (`[x]`) after every tool call. This forbids parallel tool execution, ensuring human judges and SOC analysts can trace exactly which tool yielded which hypothesis.
* **Dependency Stability (The PDF Decision):** Early iterations attempted to generate automated PDFs via Python (`weasyprint`), which introduced severe system-level dependency crashes on headless Linux VMs. Optimizing for hackathon stability, we engineered the MCP server to output clean, highly structured Markdown (`tool_write_report`), bypassing external OS-level render dependencies entirely.

---

## 5. Empirical Learnings, Constraints & Self-Corrections
Throughout development, the agent’s reasoning parameters were refined based on encountered False Positives (FPs) and legacy OS limitations. We prioritized "Honesty over Perfection."

### 5.1 Constraint Implementation: The Empty Data Protocol
* **The Problem:** On legacy systems (Windows XP), modern Volatility plugins (like `ssdt` and `netscan`) silently fail and return empty arrays `[]`. Initially, the LLM hallucinated that empty arrays meant the system was "Clean."
* **The Architectural Fix:** We built a Deterministic Data Guardrail at the Python MCP layer. If a tool fails, the server intercepts it and explicitly injects the string: `"UNVERIFIED: Tool returned no data. DO NOT declare clean."`
* **The Prompt Fix:** We added a Universal Guardrail to `CLAUDE.md` explicitly forbidding the agent from using words like "clean" or "intact" if it encounters the "UNVERIFIED" tag, forcing it to generate a "Forensic Blind Spots" table instead.

### 5.2 Context Decay & Final Report Hallucinations
* **The Problem:** During the Windows XP test, Phase 3 tools returned empty. The agent noted this mid-investigation. However, by Phase 5, the agent had consumed so many tokens that it "forgot" the Phase 3 failure and hallucinated "Kernel is clean" in the Final Report.
* **The Fix:** We engineered an Anti-Hallucination Guardrail at the *very bottom* of `CLAUDE.md`. Anchoring the rule at the end of the prompt forces the agent to read it immediately before generating the summary, completely eliminating context decay.

### 5.3 Red Team Self-Correction (FPs)
* **The Windows XP `FFEEFFEE` Artifact:** `malfind` flagged 11 memory regions in `winlogon.exe` and `csrss.exe`. The agent autonomously analyzed the hex, recognized `ff ee ff ee` as a benign Windows GDI heap artifact, and successfully self-corrected, downgrading them to "False Positives" without human intervention.
* **OS Font Mapping:** The agent noticed unlinked modules in `csrss.exe`, but autonomously referenced OS architecture knowledge to determine this was a normal Windows console subsystem font-mapping behavior, discarding the alert.
* **Stale EPROCESS Resolution:** The agent discovered suspicious shells (`cmd.exe`) via pool-tag scanning. However, Phase 5 substantiation failed. Instead of hallucinating command lines, the agent correctly diagnosed these as terminated processes whose EPROCESS structures were just stale artifacts left in physical memory.

---

## 6. Conclusion
Engram MCP proves that the barrier to autonomous AI forensics is not the LLM’s reasoning capacity, but the structural integrity of its data pipeline. By utilizing MCP to enforce deterministic guardrails, gracefully degrade during legacy tool failures, and enforce zero-knowledge analysis, we have created an OS-agnostic, research-grade orchestration engine capable of dissecting DEFCON-level APTs without hallucination.