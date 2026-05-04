> **Evidence Integrity:** See [evidence_integrity.md](evidence_integrity.md) for the architectural approach to read-only chain of custody across all investigations.

# Engram Engine: Accuracy & Self-Assessment Report
**Target:** `target-beta-basedc.img` (Windows Server — Domain Controller)
**MCP Engine:** Engram (`mcp__engram__tool_phase1_surface_triage` through `tool_write_report`)
**Investigator:** Principal DFIR Orchestrator (claude-sonnet-4-6)
**Investigation Date:** 2026-04-23 (UTC)
**Incident Report Reference:** `exports/20260423_064650_Incident_Report_target-beta-basedc.md`
**Conversation Log Reference:** `submission_package/conversation_logs/target-beta(base-dc).md`

---

## 1. Verified Successes & Accurate Findings

### 1.1 DKOM Detection via pslist/psscan Discrepancy
The investigation correctly identified the zero-visible-process condition (`Total_Visible_Processes: 0`, `DKOM_Hidden_Found: 124`) as a full _EPROCESS list wipeout caused by the kernel-mode rootkit rather than as a tool failure or empty image. This is the correct interpretation: when pslist returns 0 but psscan returns 124, physical pool-tag scanning has circumvented the manipulated doubly-linked list. The call was accurate and the evidence chain was unambiguous.

### 1.2 Mnemosyne.sys Ring 0 Rootkit Identification
The rootkit was correctly identified via Phase 3 modscan (physical scan) confirming its presence in memory while being absent from the OS-maintained `PsLoadedModuleList`. Two indicators were accurately combined to elevate confidence: (a) non-standard installation path (`C:\windows\` rather than `System32\drivers\`), and (b) the binary name `Mnemosyne.sys` matching a confirmed malicious driver from a prior investigation (`target_alpha.img`). This cross-host correlation was a sound and valuable attribution.

### 1.3 PsLoadedModuleList Total Wipeout — Root Cause Attribution
The investigation correctly traced the complete network blindness (empty netscan), AV blindness (WdFilter.sys / WdNisDrv.sys unlinked), and filesystem driver blindness (NTFS.sys, FLTMGR.SYS unlinked) back to a single root cause: Mnemosyne.sys having wiped the entire `PsLoadedModuleList`. This is mechanistically accurate. The causality chain (rootkit loads → unlinks module list → OS and analysis tools lose visibility of all drivers → cascading blind spots) is correctly stated and not overstated.

### 1.4 subject_srv.exe as Backdoor Service — Campaign IOC Match
`subject_srv.exe` (PID 5128, PPID 644/services.exe) was correctly flagged as a high-confidence IOC. The claim rests on two pillars: (a) PPID of services.exe confirms it is registered as a Windows service (legitimate persistence anchor), and (b) the binary name exactly matches a confirmed backdoor from the prior `target_alpha.img` case. This is correctly labeled **CONFIRMED — CRITICAL** given the campaign IOC match, with the caveat (addressed in Section 3) that binary hash verification was unavailable.

### 1.5 Process Tree Anomaly Detection (RuntimeBroker → powershell → notepad)
The investigation correctly identified `powershell.exe` (PID 5612) spawned by `RuntimeBroker.exe` (PID 4932) as anomalous. RuntimeBroker.exe is a Windows UWP broker process that manages application permissions; it has no legitimate execution path to spawn PowerShell. The subsequent `notepad.exe` (PID 7936) as a direct child of powershell.exe is consistent with documented process hollowing tradecraft. Both findings are grounded in raw psscan topology data, not inference.

### 1.6 ManagementAgen.exe cmd.exe Proliferation
The identification of `ManagementAgen.exe` (PID 908) as the root of a large cmd.exe tree (20+ total descendants across the process tree) is accurate per the topology data. PID 908 directly spawns PIDs 1036, 3380, 4588, and 6628, which in turn spawn further cmd.exe chains. The binary name matches McAfee's Management Agent but is truncated at 15 characters (a Windows process name limitation), making masquerade possible. The dual hypothesis (hijacked legitimate agent OR name-spoofing masquerade) was correctly stated and neither was ruled out.

### 1.7 Domain Controller Context — Service Processes Not False-Positived
The host is identified as a domain controller (`base-dc`). The investigation correctly did not flag DC-normal processes as suspicious: `dns.exe` (DNS Server role), `dfssvc.exe` / `dfsrs.exe` (Distributed File System), `ismserv.exe` / `iashost.exe` (IAS/Network Policy Server), multiple `mmc.exe` instances (Server Manager), and `spoolsv.exe`. These are consistent with an Active Directory Domain Controller's service footprint and were correctly treated as baseline noise.

### 1.8 Null-Name Modscan Entries — Correctly Self-Assessed as False Positives
Four modscan entries with null name/path and base addresses outside normal Windows x64 kernel VA ranges (e.g., `0x8946631`, `0xA0CF30C8` range) were correctly assessed as **False Positives (low confidence)** — likely pool-scan carving artifacts from unrelated or freed memory. The investigation appropriately did not escalate these to confirmed IOCs.

### 1.9 MpKsl657a2bb2.sys — Not Hallucinated as Additional Malware
`MpKsl657a2bb2.sys` (a Windows Defender dynamic kernel shim under `ProgramData\...Definition Updates`) appeared in the UNLINKED driver list. The investigation correctly treated this as a Defender component caught in the global PsLoadedModuleList wipeout rather than hallucinating it as a second independent malicious driver. Good self-correction.

### 1.10 Empty Data Protocol — Correctly Applied Across Phases 2, 4, and 5
All three phases returned empty arrays. In all three cases, the investigation correctly refused to declare the subsystems "clean" and instead applied the **Empty Data Protocol**, explicitly labeling the findings as **UNVERIFIED blind spots**. This is the correct behavior under the anti-hallucination guardrail. A less disciplined analysis would have declared user-space injection, AV coverage, and credential theft as "not present" — all of which would have been false negatives.

---

## 2. Handled False Positives (Self-Correction During Investigation)

| Potential False Positive | Disposition | Correct? |
|--------------------------|-------------|----------|
| 4 null-name modscan entries | Assessed as pool-scan artifacts; labeled "False Positive (low confidence)"; not escalated | Yes — base addresses outside valid x64 kernel VA range |
| MpKsl657a2bb2.sys (UNLINKED) | Treated as Defender shim caught in global wipeout; not flagged as 2nd rootkit | Yes — legitimate Defender component |
| Domain Controller service processes (dns.exe, dfssvc.exe, ismserv.exe, iashost.exe) | Not flagged — recognized as DC-normal service footprint | Yes — all are expected on Windows AD DC |
| Multiple WmiPrvSE.exe instances | Not flagged — recognized as normal WMI provider host behavior | Yes — multiple instances are expected |
| regedit.exe (PID 1272, PPID 4300/explorer.exe) | Not escalated to IOC | Arguably correct — regedit from explorer is user-normal; however, on a rootkit-compromised host during active attacker dwell, this warrants at least a notation (see Section 4) |

---

## 3. Accuracy Limitations — Unverifiable Claims (Honest Assessment)

### 3.1 subject_srv.exe — "CONFIRMED" Label Overstates Binary Verification
**Claim:** `subject_srv.exe` labeled as **CONFIRMED — CRITICAL** backdoor.
**Limitation:** Phase 5 returned empty for PID 5128. The binary hash, import table, and command-line arguments were never extracted. "Confirmed" is grounded entirely in: (a) matching process name from prior case and (b) services.exe parent (persistence indicator). A different binary using the same filename to masquerade would produce identical telemetry.
**Honest Rating:** The finding is **HIGH CONFIDENCE**, not definitively CONFIRMED. The CONFIRMED label reflects cross-campaign attribution strength but would not satisfy a court evidentiary standard without hash verification.

### 3.2 notepad.exe — "Classic Process Hollowing Host" Assessment Unsubstantiated
**Claim:** `notepad.exe` (PID 7936) labeled as **HIGH CONFIDENCE — classic process hollow host**.
**Limitation:** Process hollowing would require Phase 5 to show RWX memory regions, VAD anomalies, or injected PE headers. All Phase 5 data was empty. The hollow host characterization is purely inferred from parent-child topology (powershell spawning notepad). This topology is suspicious but notepad.exe can also be legitimately launched via PowerShell by users or scripts.
**Honest Rating:** **MEDIUM-HIGH CONFIDENCE** anomaly — the hollow host label is a reasonable investigative hypothesis but cannot be confirmed without code injection artifacts.

### 3.3 Campaign Attribution — Hash-Level Verification Missing
**Claim:** "Same threat actor, same toolset, likely same campaign" as `target_alpha.img`.
**Limitation:** Attribution rests on three matching indicators: identical Mnemosyne.sys path, identical subject_srv.exe service pattern, identical DKOM TTP. These are strong structural IOCs. However, without binary hash comparison of Mnemosyne.sys across both images, it is theoretically possible (though improbable) that a different actor independently deployed a rootkit to the same path using the same name. In intelligence terms, this is **high-confidence attribution** but not **confirmed attribution**.
**Honest Rating:** Attribution is well-reasoned and defensible for incident response purposes. Would require hash-level cross-image comparison to meet a formal attribution standard.

### 3.4 ADD Spoofed Decoy Interpretation — Dual Hypothesis Not Fully Resolved
**Claim:** 85 processes carry "ADD Spoofed Decoy (0 Threads)" markers indicating attacker-seeded decoy entries to contaminate analysis tools.
**Limitation:** In an environment with a Ring 0 rootkit that has already wiped all EPROCESS list entries, the 0-thread count equally indicates terminated processes whose pool memory was not reclaimed before the memory capture. The two explanations (attacker decoys vs. stale terminated process structs) produce identical tool output. The investigation correctly stated both possibilities but the incident report primarily characterizes them as "attacker-seeded decoy entries," which may over-attribute intent.
**Honest Rating:** 0-thread entries are correctly flagged as anomalous. The "attacker decoy" framing is plausible but not definitively provable; "stale terminated process structs" is an equally valid explanation.

### 3.5 ManagementAgen.exe — Hijack vs. Masquerade Unresolved
**Claim:** ManagementAgen.exe is either "hijacked McAfee agent or masquerade."
**Limitation:** The process name matches the McAfee Endpoint Security Management Agent. The parent (PID 644/services.exe) is consistent with a legitimate installed service. Phase 5 returned empty (no command line, no hash). Without binary extraction, the distinction between a legitimate-but-hijacked agent (code injection) and a malicious binary claiming the same service name cannot be drawn.
**Honest Rating:** Correctly flagged as suspicious given the 20+ cmd.exe spawn behavior. Dual hypothesis appropriately held open.

---

## 4. Missed Artifacts / Investigation Gaps

### 4.1 regedit.exe (PID 1272, PPID 4300/explorer.exe) — Not Prioritized
`regedit.exe` spawned from `explorer.exe` during an active compromise on a domain controller should have been noted as a candidate attacker persistence activity (registry key creation for Mnemosyne.sys driver autoload or Run key backdoor). It was present in the topology data but not called out in the incident report. On a standalone workstation this might be benign; on a DC with an active Ring 0 rootkit, it warrants at least a notation. **Minor gap.**

### 4.2 WmiPrvSE.exe — WMI Lateral Movement Not Assessed
Multiple `WmiPrvSE.exe` instances were visible in the process tree. WMI is a documented lateral movement and persistence mechanism (WMI subscriptions, WMIC remote execution). On a domain controller, WMI abuse is particularly high-value for attackers seeking domain-wide lateral movement. None of the WmiPrvSE.exe instances were specifically queried via Phase 5 or flagged as anomalous. **Minor gap** — their parent (`svchost.exe` PID 836) is the expected WMI host, so this would likely have been a dead-end, but it should have been noted.

### 4.3 DC-Specific Credential Risk Escalation — Not Fully Quantified
The host is a Domain Controller. The investigation noted lsass.exe (PID 660) credential theft as unverifiable, and recommended credential rotation. However, the incident report did not specifically call out that a DC lsass dump yields NTLM hashes for **all domain accounts** (not just local accounts), meaning the blast radius of an unconfirmed lsass access on a DC is domain-wide. The recommendation was correct but the severity amplification specific to DC lsass access was understated.

### 4.4 Kerberos / Active Directory Persistence Not Assessed
On a DC, attacker tools can create Golden Ticket or Silver Ticket conditions by modifying the krbtgt account or injecting Kerberos service account hashes. The investigation did not assess for Kerberos-related persistence artifacts (e.g., scheduled task abuse, KRBTGT modification). This is a blind spot inherent to Phase 4's empty return (Shimcache suppressed) but was not explicitly called out as a DC-specific risk.

### 4.5 UpdaterUI.exe (PID 4544) and masvc.exe / macompatsvc.exe — McAfee Ecosystem Not Fully Explored
Given that ManagementAgen.exe (PID 908) appears to be the root of the cmd.exe explosion, the broader McAfee ecosystem processes (`masvc.exe` PID 2444, `macompatsvc.exe` PID 3320, `mfemactl.exe` PID 3476, `UpdaterUI.exe` PID 4544, `mctray.exe` PID 3872) should have been cross-referenced. If the attacker hijacked ManagementAgen.exe, they may have leveraged the other McAfee processes as well. **Moderate gap** — these were present in the topology data but not explicitly assessed.

---

## 5. Hallucinated Claims — None Identified

No fabricated artifacts, invented PIDs, or unsupported conclusions were identified during review of the conversation log against the raw Engram MCP tool outputs. Every named PID, process name, and kernel module in the incident report can be directly traced to a JSON data field in one of the five Engram phase outputs (`tool_phase1_surface_triage` through `tool_phase5_substantiation`). The investigation maintained strict grounding in raw tool output throughout.

The Empty Data Protocol was applied correctly every time an Engram tool returned `[]` or `{}`, preventing false-negative hallucination ("the system is clean because the tool returned nothing").

---

## 6. Methodology Assessment

| Criterion | Rating | Notes |
|-----------|--------|-------|
| DKOM detection accuracy | Excellent | Correct pslist/psscan discrepancy interpretation |
| Rootkit identification | Excellent | Physical modscan, non-standard path, cross-campaign correlation |
| Empty data handling | Excellent | Empty Data Protocol applied consistently; no false negatives |
| False positive rate | Good | All 5 identified FP candidates correctly down-graded |
| Process tree analysis | Good | Key anomalies correctly flagged; minor gaps (regedit, WmiPrvSE) |
| Phase 5 substantiation | Limited | Systematic failure due to ADD Spoofed Decoy condition — no binary-level confirmation achievable |
| DC-specific risk assessment | Partial | Service processes correctly not FP'd; DC-specific credential risk and Kerberos persistence under-developed |
| Attribution confidence calibration | Good | Cross-campaign attribution well-reasoned; "CONFIRMED" label slightly overconfident without hash |
| Anti-hallucination discipline | Excellent | No fabricated artifacts across any phase |
| Report completeness | Good | Blind spots section comprehensive; recommended actions appropriate |

---

## 7. Summary

The investigation correctly identified the two highest-value IOCs (`Mnemosyne.sys` rootkit and `subject_srv.exe` backdoor service), accurately attributed both to the same cross-host campaign, correctly applied the Empty Data Protocol across three phases, and produced zero hallucinated artifacts.

The primary limitations are structural: the Ring 0 rootkit's ADD Spoofed Decoy condition rendered Phase 5 systematically non-functional, making binary-level confirmation of process hollowing, credential theft, and command-line extraction impossible. This is a tool telemetry limitation, not an analyst error.

Minor investigation gaps include: (a) insufficient attention to the McAfee service ecosystem as a secondary compromise vector, (b) DC-specific amplification of the credential theft risk (domain-wide vs. local), (c) regedit.exe during active attacker dwell not flagged, and (d) WMI lateral movement potential not assessed.

No claims were fabricated. All conclusions are traceable to raw MCP tool output in the conversation log.
