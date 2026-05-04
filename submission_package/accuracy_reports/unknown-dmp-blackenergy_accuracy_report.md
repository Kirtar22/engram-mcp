> **Evidence Integrity:** See [evidence_integrity.md](evidence_integrity.md) for the architectural approach to read-only chain of custody across all investigations.

# Engram Engine: Accuracy & Self-Assessment Report
**Target:** `unknown_dmp.raw` (Windows XP SP3 — VirtualBox Guest, CyberDefenders challenge — BlackEnergy)
**MCP Engine:** Engram (`mcp__engram__tool_phase1_surface_triage` through `tool_write_report`)
**Investigator:** Principal DFIR Orchestrator (claude-sonnet-4-6)
**Investigation Date:** 2026-04-17 (UTC)
**Incident Report Reference:** `submission_package/20260417_121747_Incident_Report_unknown_dmp.md`
**Conversation Log Reference:** `submission_package/conversation_logs/unknonwn_dmp(BlackEnergy).html`

---

## 1. Verified Successes & Accurate Findings

### 1.1 rootkit.exe Identification — Unambiguous Malware Naming
`rootkit.exe` (PID 964, PPID 1484/explorer.exe) was correctly identified as the primary IOC in Phase 1. The identification required no inferential leap — no legitimate Windows system process is named `rootkit.exe`. The investigation performed an explicit red-team self-check: *"Is rootkit.exe a legitimate system binary? No — there is no Windows system process by this name."* The finding is fully grounded in raw Phase 1 psscan output.

### 1.2 cmd.exe as Child of rootkit.exe — Correct Parent-Child Interpretation
`cmd.exe` (PID 1960, PPID 964) was correctly identified as a command shell spawned directly by the dropper. This is accurately assessed as HIGH confidence: a shell parented to an explicitly malicious binary is itself a confirmed component of the attack chain regardless of its own behavior. The Phase 5 empty result (zombie process) did not alter the confidence level — correct reasoning.

### 1.3 PE Injection in svchost.exe PID 880 — Triple-Corroborated Confirmation
The injection into `svchost.exe -k DcomLaunch` (PID 880) was confirmed via three independent evidence chains:
1. Phase 2 `ldrmodules` diff: anonymous unlinked module at base `0x00980000` with `path=None` (no backing file on disk)
2. Phase 2 `malfind`: RWX hit in PID 880 at VPN `9,961,472` (0x00980000) — exact address match to the unlinked module
3. Phase 5 hex dump: bytes `4D 5A 90 00 03 00 00 00...` — valid MZ PE header at that address

The cross-phase address correlation (`ldrmodules` base address == `malfind` VPN == Phase 5 hex confirmation) is the strongest possible form of injection evidence available from memory forensics. This is a high-quality analytical outcome.

### 1.4 Mutex 746bbf3569adEncrypt — Correctly Isolated from Benign Handles
The malicious mutex was correctly identified by contrasting it against all other handles in PID 880. The investigation noted that every other mutex was a legitimate WinInet handle (`ZonesLockedCacheCounterMutex`, `WininetProxyRegistryMutex`, etc.) — making `746bbf3569adEncrypt` the sole anomaly. The contrast-against-baseline approach is sound and prevents false positive escalation of normal OS handles.

### 1.5 winlogon.exe 11 Malfind Hits — Correct False Positive Self-Correction
Phase 2 initially flagged `winlogon.exe` (PID 616) with 11 RWX regions as "HIGH SEVERITY — 11 RWX anomalies in authentication process is extreme." Phase 5 substantiation was correctly triggered. The hex analysis produced the key correction:
- 10 of 11 regions: zero-filled pages (`00 00 00 00...`) — malfind triggered on RWX permission bits, not actual code content
- Regions at 0x580000 and 0x7F6B0000: `FF EE FF EE` pattern — correctly identified as the Windows GDI object header sentinel / shared heap structure, not injected code
- No malicious mutexes in winlogon.exe

The downgrade from HIGH SEVERITY to False Positive based on raw hex analysis is a strong demonstration of the anti-hallucination discipline. This is this investigation's most significant self-correction.

### 1.6 csrss.exe Font .fon Unlinking — Correct XP OS Behavior Recognition
`csrss.exe` (Windows Client/Server Runtime) appeared in the `ldrmodules` diff with multiple `.fon` console font files unlinked from the PEB. The investigation correctly identified this as standard Windows XP behavior: csrss.exe maps console fonts via VAD directly without PEB-registering them, because they are not DLLs and the mapping is a resource-only operation. Not flagging this requires specific XP internals knowledge.

### 1.7 csrss.exe @ 0x7F6B0000 Malfind — Correct XP Shared Memory Recognition
A malfind hit in `csrss.exe` at address `0x7F6B0000` was correctly assessed as low confidence — this address falls in the upper user-space region near `KUSER_SHARED_DATA` (a read-only kernel-mapped page that all processes share on XP at fixed VA). Flagging this as an OS artifact rather than injected code is XP-specific knowledge applied correctly.

### 1.8 explorer.exe shellstyle.dll / msxml3r.dll — Correct Low-Confidence Disposition
`explorer.exe` showed two unlinked modules (`shellstyle.dll` — Luna theme skin, `msxml3r.dll` — XML resource DLL). These were correctly assessed as "Low confidence — theme/resource DLLs, likely legitimate." Resource-only DLLs containing no executable code sections are routinely mapped without PEB registration in Windows XP's shell. Not escalating these was the correct call.

### 1.9 Stale Zombie EPROCESS Handling — Phase 5 Correctly Applied and Interpreted
Phase 5 (Round 1) for rootkit.exe (PID 964) and cmd.exe (PID 1960) returned empty results. The investigation correctly diagnosed this as zombie/terminated processes with reclaimed working set pages, not exoneration. The explicit statement: *"The absence of malfind data is a telemetry limitation (terminated process), not evidence of benignity"* — is precisely correct and prevents false-negative conclusions.

### 1.10 XP-Specific Tool Limitations — Correctly Diagnosed for Phase 3 and Phase 4
Both Phase 3 (kernel) and Phase 4 (advanced evasion) returned empty arrays. The investigation correctly attributed these to:
- Phase 3: Windows XP KPCR/KDDEBUGGER_DATA64 parsing limitations in Volatility 3 (optimized for Vista+)
- Phase 4: AppCompatCache binary format differs between XP and Vista/7+ (shimcache plugin incompatibility); KTHREAD structure differences for Gargoyle scan

Both empty results were correctly handled via the Empty Data Protocol. Notably, the Phase 3 empty result was interpreted with additional caution: *"A well-implemented kernel rootkit would by definition hide from modules/modscan enumeration. Empty results are consistent with both 'no kernel payload' and 'successful kernel-level evasion.'"* This dual-hypothesis handling is correct.

### 1.11 Phase 5 Triggered Correctly Twice (OODA Compliance)
Round 1: triggered after Phase 1 (PIDs 964/rootkit.exe, 1960/cmd.exe — highest-confidence Phase 1 anomalies).
Round 2: triggered after Phase 2 (PID 880/svchost.exe — confirmed injection; PID 616/winlogon.exe — 11 RWX hits requiring hex verification).
Both triggers are correct per OODA mandate. The Round 2 trigger on winlogon.exe (which turned out to be a FP) shows the process working as designed — substantiating before labeling.

### 1.12 DumpIt.exe (PID 276) Not Flagged as Threat
`DumpIt.exe` (PID 276) appeared in the process list as it was the memory acquisition tool that created the dump. The investigation did not flag this as suspicious. This is correct — forensic acquisition tools present in a memory dump are expected artifacts, not IOCs.

---

## 2. Handled False Positives (Self-Correction During Investigation)

| Potential False Positive | Phase Detected | Resolution | Correct? |
|--------------------------|---------------|------------|----------|
| winlogon.exe — 11 malfind RWX regions | Phase 2 (initially HIGH SEVERITY) | Phase 5 hex analysis: zero-filled pages + `FF EE FF EE` GDI sentinel → All 11 downgraded to FP | Yes — definitive raw hex evidence |
| csrss.exe — `.fon` font file unlinked modules | Phase 2 | Recognized as XP console font VAD mapping (not PEB-registered by design) → FP | Yes — correct XP OS behavior |
| csrss.exe malfind @ 0x7F6B0000 | Phase 2 | Recognized as upper user-space near KUSER_SHARED_DATA shared mapping → FP | Yes — correct XP architecture knowledge |
| explorer.exe — shellstyle.dll, msxml3r.dll unlinked | Phase 2 | Recognized as Luna theme skin / XML resource DLL (no executable sections) → Low confidence FP | Yes — resource-only DLL behavior |

---

## 3. Accuracy Limitations — Unverifiable or Overstated Claims (Honest Assessment)

### 3.1 wscntfy.exe Parent Claim — Factually Incorrect
**Claim:** Phase 1 flagged `wscntfy.exe` (PID 480, PPID 1060/svchost.exe) with the note: *"Windows Security Center Notifier should parent from winlogon, not svchost."*
**Limitation:** This is factually incorrect on Windows XP SP2/SP3. `wscntfy.exe` is the client notification helper spawned by the Windows Security Center service (`wscsvc`), which runs inside `svchost.exe`. Its correct parent IS a svchost.exe instance hosting wscsvc — not winlogon.exe. winlogon on XP spawns userinit.exe → explorer.exe; it does not spawn Security Center utilities. The investigation flagged a legitimate process parent relationship as anomalous.
**Impact:** Low — this process was not escalated to an IOC in the final incident report, so the error did not pollute the conclusions. However, a junior analyst reading the Phase 1 table might have been misled.
**Honest Rating:** **Minor factual error in Phase 1 analysis** — correct parent for wscntfy.exe on XP SP2+ is svchost.exe (Security Center service host).

### 3.2 cmd.exe Labeled "C2 Pivot Point" — Unsupported Role Assignment
**Claim:** cmd.exe (PID 1960) described as: *"Shell spawned directly by rootkit.exe — C2 pivot point."* The attack narrative further states the dropper *"spawned cmd.exe for a command shell pivot."*
**Limitation:** Phase 5 returned empty for cmd.exe (zombie process). No command-line arguments, handles, or executed commands are recoverable. Calling it a "C2 pivot point" or "staging/injection invocation or reconnaissance" are reasonable hypotheses but entirely unconfirmed by tool output. cmd.exe as a child of rootkit.exe could equally have been used for a one-line command that immediately returned (e.g., `cmd.exe /c sc.exe create...` for service installation), not a persistent shell.
**Honest Rating:** Correct to flag as HIGH confidence IOC based on parent-child; "C2 pivot" and "staging/injection invocation" are **narrative inferences unsupported by tool data**.

### 3.3 rootkit.exe → svchost.exe Injection — Causal Chain Not Proven
**Claim:** Attack narrative: *"rootkit.exe...injected a PE into a privileged svchost, created a crypto/C2 mutex, and terminated."*
**Limitation:** The injection into svchost.exe PID 880 is confirmed. But who performed the injection is not confirmed by tool output. The causal chain — rootkit.exe as the injector — is the most parsimonious explanation but is not evidenced. rootkit.exe may have dropped a second binary that performed the injection, or used cmd.exe as an intermediary. Phase 5 returned empty for rootkit.exe (zombie), so no injection API calls, no injected handles, no memory maps are available to confirm rootkit.exe as the injector.
**Honest Rating:** The "drop-inject-exit" attack pattern is a **plausible and well-reasoned narrative** but is technically an inference from circumstantial evidence (proximity of rootkit.exe execution and presence of injection).

### 3.4 Mutex Naming Convention — Stated as Confirmed Fact
**Claim:** *"The format [hex_hash]Encrypt is a textbook malware C2/crypto mutex pattern. All other mutexes are legitimate WinInet handles."*
**Limitation:** The observation that `746bbf3569adEncrypt` is anomalous among WinInet handles is correct and evidence-based. However, calling it a *"textbook malware C2/crypto mutex pattern"* and describing it as one that *"malware families use...to create unique C2 channel markers"* presents analyst threat-intel knowledge as if it were verified from tool output. `746bbf3569adEncrypt` is a known BlackEnergy 2 indicator, but the investigation never attributed the malware to BlackEnergy — the mutex analysis reads as generic threat-intel commentary not tied to a specific confirmed family.
**Honest Rating:** The anomaly detection is correct; the mutex naming convention commentary is **analyst inference presented as confirmed threat intelligence**. Better stated as: "format is consistent with known malware mutex patterns."

### 3.5 notepad.exe x3 — "Process Hollowing Candidates" Without Phase 5 Substantiation
**Claim:** Three `notepad.exe` instances (PIDs 528, 1444, 1432) listed as IOC-005 with MEDIUM confidence: *"Possible process hollowing attempts."*
**Limitation:** Phase 5 was not run against these PIDs. All three are zombie processes (0 threads), so Phase 5 would have returned empty (consistent with Rounds 1 and 2 results for other zombies). The incident report correctly labels them MEDIUM confidence and states *"Memory freed — unverifiable."* However, three zombie notepad.exe processes parented from explorer.exe with 0 threads is more consistent with a user who simply opened and closed Notepad three times before the memory dump, not necessarily hollowing attempts. The hollowing hypothesis requires a living process with RWX memory — a zombie notepad entry proves only that notepad ran and exited.
**Honest Rating:** MEDIUM confidence label with explicit "unconfirmed" caveat is appropriate. The "process hollowing" framing is **plausible but unsupported** and could be misleading — "zombie notepad instances, possible hollowing targets, more likely benign terminated user sessions" would be more accurate.

### 3.6 BlackEnergy Family Not Explicitly Attributed
**Observation:** The image is from the CyberDefenders "BlackEnergy" challenge. `746bbf3569adEncrypt` is a documented BlackEnergy 2 mutex. The investigation never identified the malware family by name in the incident report, describing it only as "malware" with a "C2/crypto mutex."
**Assessment:** This is not an error — the Engram tool output contains no threat-intel enrichment. The investigation correctly confined itself to what the tools produced. Claiming BlackEnergy attribution without OSINT/hash verification would itself have been a hallucination risk. The omission of explicit family attribution is the **correct and disciplined approach** under the anti-hallucination guardrail. Noted here for context only.

---

## 4. Missed Artifacts / Investigation Gaps

### 4.1 msmsgs.exe (PID 636) Malfind Hit — Not Explicitly Closed
`msmsgs.exe` (Windows Messenger) appeared in the Phase 2 malfind table as "Medium — investigate after priority targets." The investigation prioritized svchost.exe PID 880 (confirmed injection) and winlogon.exe PID 616 (11 RWX hits) for Phase 5 Round 2. `msmsgs.exe` was never substantiated or explicitly closed with a FP determination. On XP, Windows Messenger frequently maps RWX regions for its COM and browser control components — this is very likely a false positive, but it was left open without explicit disposition in the incident report. **Minor gap.**

### 4.2 taskmgr.exe (PID 1880) — Flagged in Phase 1, Closed Without Explicit Reasoning
`taskmgr.exe` (PID 1880, PPID 1484/explorer.exe, 0 threads) appeared in the Phase 1 analysis table with "0 threads — anomalous for task manager." It was not included in Phase 5 Round 1 (rootkit.exe and cmd.exe were prioritized instead) and does not appear in the incident report. On XP, Task Manager opened and closed by the user while the memory dump was being prepared would produce exactly this zombie entry. The investigation implicitly de-prioritized it correctly, but did not explicitly close it as FP in the incident report. **Minor gap.**

### 4.3 svchost.exe Injection — Persistence Mechanism Not Resolved
The injected PE in PID 880 is confirmed running at capture time. The investigation recommended disk forensics to find `rootkit.exe` on disk and check persistence mechanisms (Run keys, Services). However, the memory dump itself contains a recoverable PE at `0x00980000` in PID 880's address space. The investigation recommended this for a *follow-on* disk forensics step, but did not note that the PE itself could be partially reconstructed from the dump using Volatility 2's `procdump` (as was actually recommended in Action Item 2). The in-memory binary was not analyzed for its own import table, export table, or embedded strings — which would have revealed whether it contained a network beacon, persistence installer, or other payload components. **Moderate gap** — but correctly scoped as a next-step action given the XP/Vol3 tool limitations.

### 4.4 No Network IOCs Recovered — C2 Hypothesis Left Entirely Open
The investigation found no active network connections in Phase 1 netscan. The injected PE has a mutex suggestive of C2/crypto activity, but no IP address, domain, or port was recovered. On XP, the Engram netscan tool likely enumerates `_TCPT_OBJECT` structures which may not be as reliable as on Vista+. The incident report correctly labels network C2 as "NOT OBSERVED" (not "UNVERIFIED") because netscan on XP returned explicit empty results without rootkit driver interference. This distinction is correct. However, the recommendation to hunt for the mutex `746bbf3569adEncrypt` on other hosts is only useful if those hosts are also XP with the same malware — the report did not note the mutex's documented association with a specific malware family that might also be present on other OS versions. **Minor gap.**

---

## 5. Hallucinated Claims — None Identified from Tool Output

No fabricated PIDs, invented process names, invented hex values, or invented mutex names were found. Every confirmed IOC in the incident report traces directly to a JSON field in the raw Engram tool outputs:
- rootkit.exe PID 964 → Phase 1 psscan topology
- cmd.exe PID 1960 → Phase 1 psscan topology
- svchost.exe PID 880 injection @ 0x00980000 → Phase 2 ldrmodules + malfind + Phase 5 hex
- Mutex `746bbf3569adEncrypt` → Phase 5 handles output for PID 880
- notepad.exe PIDs 528, 1444, 1432 → Phase 1 psscan topology

The `FF EE FF EE` GDI sentinel interpretation and the XP KUSER_SHARED_DATA address reasoning are analyst knowledge applied to raw hex output — not hallucinations.

The Empty Data Protocol was applied correctly in both Phase 3 and Phase 4, preventing false-negative declarations that the kernel and evasion subsystems were clean.

---

## 6. Methodology Assessment

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Primary IOC detection (rootkit.exe, injection) | Excellent | Unambiguous identification; triple-corroborated injection evidence |
| False positive handling — malfind | Excellent | winlogon.exe 11-hit downgrade via hex analysis is the investigation's strongest self-correction |
| False positive handling — ldrmodules | Excellent | csrss.exe fonts and explorer.exe theme DLLs correctly assessed |
| Stale zombie EPROCESS handling | Excellent | Empty Phase 5 correctly not used to exonerate zombie PIDs |
| XP-specific platform knowledge | Excellent | Font mapping, KUSER_SHARED_DATA, AppCompatCache format, KTHREAD limitations all correctly applied |
| Phase 5 triggering (OODA compliance) | Excellent | Two rounds triggered at correct decision points |
| Empty Data Protocol (Phases 3, 4) | Excellent | Both applied correctly; dual-hypothesis (OS limitation vs. rootkit evasion) held in Phase 3 |
| Attack narrative accuracy | Good | Core reconstruction sound; cmd.exe role and rootkit.exe→injection causal chain are inferences |
| Phase 1 process parent knowledge | Partial | wscntfy.exe parent claim is incorrect; did not affect conclusions |
| Open items closure | Partial | msmsgs.exe and taskmgr.exe left without explicit FP determination |
| Malware family attribution | N/A (Correct Omission) | BlackEnergy not attributed — correct under anti-hallucination guardrail |
| Anti-hallucination discipline | Excellent | No fabricated artifacts across any phase; robust self-correction on winlogon.exe |

---

## 7. Summary

This investigation produced the highest-quality forensic evidence chain of the three cases analyzed: PE injection confirmed via triple cross-phase corroboration (ldrmodules + malfind + Phase 5 hex dump), and a major false positive (winlogon.exe 11-region malfind alert) correctly self-corrected via raw hex analysis. These are hallmarks of disciplined memory forensics.

The primary limitations are in the narrative reconstruction layer. The causal chain (rootkit.exe as the injector, cmd.exe as the pivot, drop-inject-exit pattern) is mechanistically plausible but unsupported by extractable tool evidence — all key processes are zombie/terminated. The wscntfy.exe parent claim is a minor factual error that did not affect conclusions.

The XP platform imposed structural blind spots (Phases 3 and 4 entirely unverifiable) that were correctly handled via the Empty Data Protocol. The investigation never declared the kernel clean despite having no kernel telemetry — the correct stance given a process explicitly named `rootkit.exe`.

No claims were fabricated. All confirmed IOCs are traceable to raw Engram MCP tool output in the conversation log.
