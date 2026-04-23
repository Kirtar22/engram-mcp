# Engram Engine: Accuracy & Self-Assessment Report
**Target:** `target_alpha.img` (Windows 10/11 x64 — VMware Workstation, base-wkstn-01)
**MCP Engine:** Engram (`mcp__engram__tool_phase1_surface_triage` through `tool_write_report`)
**Investigator:** Principal DFIR Orchestrator (claude-sonnet-4-6)
**Investigation Date:** 2026-04-18 (UTC)
**Incident Report Reference:** `submission_package/20260418_070623_Incident_Report_target_alpha_2026-04-18.md`
**Conversation Log Reference:** `submission_package/conversation_logs/target_alpha(base-wakstn-01)_execution_trace.txt`

---

## 1. Verified Successes & Accurate Findings

### 1.1 DKOM Detection via pslist/psscan Discrepancy
The investigation correctly identified `Total_Visible_Processes: 0` paired with `DKOM_Hidden_Found: 131` as a full `PsActiveProcessHead` wipeout, not a tool failure. The interpretation — pslist traverses the OS doubly-linked list (dark), psscan scans physical memory pool tags (finds 131) — is mechanistically correct. The call was accurate and unambiguous.

### 1.2 Mnemosyne.sys Ring 0 Rootkit Identification
`Mnemosyne.sys` was correctly identified via Phase 3 physical modscan as present in raw memory but absent from `PsLoadedModuleList`. The non-standard installation path (`C:\windows\Mnemosyne.sys` instead of `C:\Windows\System32\drivers\`) and the `\\??\` device-namespace prefix were correctly flagged as hallmarks of stealthed/unsigned driver deployment. Both observations are directly supported by the raw Phase 3 JSON output.

### 1.3 PsLoadedModuleList Total Wipeout — Root Cause Attribution
The investigation correctly traced the process list suppression, AV invisibility, and network blindness back to the same root cause: Mnemosyne.sys performing a dual DKOM operation — unlinking both `PsActiveProcessHead` (processes) and `PsLoadedModuleList` (drivers). This single-root-cause attribution is accurate and avoids over-fragmenting the findings into unrelated anomalies.

### 1.4 subject_srv.exe as Backdoor Service
`subject_srv.exe` (PID 12528, PPID 740/services.exe) was correctly flagged as a high-priority IOC. The PPID of `services.exe` places it as a registered Windows service — a persistence anchor. Phase 5 returned empty (stale EPROCESS), but the investigation correctly noted this means the process *terminated before capture*, not that it is benign. The distinction "executed on this host — cannot rule out persistence" is precisely correct.

### 1.5 Stale EPROCESS Handling — Terminated vs. Active
A key analytical strength in this investigation: all user-mode IOCs (subject_srv.exe, cmd.exe, sc.exe, sd.exe) were found only via psscan, and Phase 5 returned empty for all of them. The investigation correctly diagnosed this as **stale EPROCESS objects** (terminated prior to memory capture) rather than treating the empty Phase 5 as evidence of non-malicious behavior. This is the correct interpretation and prevented a significant false-negative.

### 1.6 cmd.exe (PID 5024) and sc.exe (PID 3068) as Suspicious
`cmd.exe` with an orphaned PPID (2748 — parent no longer in memory) was correctly assessed as a candidate interactive attacker shell. `sc.exe` spawned from `svchost.exe` (PPID 496) was correctly flagged — service control tools are not legitimately launched by svchost. Both calls are grounded in the raw Phase 1 topology data.

### 1.7 OUTLOOK.EXE Instances — Correctly De-Prioritized
15+ `OUTLOOK.EXE` entries appeared in the psscan output with various orphaned PPIDs. The investigation correctly assessed these as "possibly stale/historical scan entries; lower priority" rather than escalating them as active threats or fabricating an email compromise story. This is sound triage reasoning — stale pool entries from a commonly-run application do not constitute an IOC.

### 1.8 Phase 5 Triggered Correctly Twice (OODA Compliance)
Per the CLAUDE.md OODA mandate, Phase 5 must be triggered immediately after any phase producing high-confidence anomalies. The investigation correctly fired Phase 5 after Phase 1 (targeting subject_srv.exe, cmd.exe, sc.exe) and again after Phase 3 (targeting sd.exe and additional orphaned PIDs). Both rounds returned empty, which was correctly handled via the Empty Data Protocol rather than declaring substantiation failed or the system clean.

### 1.9 Empty Data Protocol — Correctly Applied Across Phases 2, 4, and Both Phase 5 Rounds
All four empty-return events triggered the protocol correctly. Particularly notable: the empty Shimcache in Phase 4 was correctly flagged as a potential anti-forensic artifact ("deliberate anti-forensic clearing of execution traces cannot be ruled out") rather than treated as a normal result on a system with 131 detected processes.

### 1.10 OS and Environment Fingerprinting
The investigation correctly identified the host as Windows 10/11 x64 running in a VMware virtual machine from presence of `vmtoolsd.exe`, `vmci.sys`, and `vmxnet3.sys` in the process/driver data. McAfee/Trellix AV presence was correctly catalogued. Both observations required no inference — they came directly from process names and driver paths in the raw output.

---

## 2. Handled False Positives (Self-Correction During Investigation)

| Potential False Positive | Disposition | Correct? |
|--------------------------|-------------|----------|
| 15+ OUTLOOK.EXE psscan entries | De-prioritized as stale historical entries; not escalated to active IOC | Yes — orphaned PPID entries of common user apps are expected in pool-tag scan |
| Phase 5 empty for all PIDs | Correctly attributed to stale EPROCESS (terminated before capture), not used to exonerate the system | Yes — mechanistically sound |
| Network connections empty (netscan) | Correctly left as UNVERIFIED (rootkit may hide sockets) rather than declared "no C2" | Yes — correct Empty Data Protocol application |
| McAfee/Trellix process list | Not flagged as anomalous; recognized as installed AV service footprint | Yes — masvc, macmnsvc, mfevtps etc. are standard McAfee components |

---

## 3. Accuracy Limitations — Unverifiable or Overstated Claims (Honest Assessment)

### 3.1 4 Null-Name Kernel Entries — Over-Escalated to "HIGH SUSPICION"
**Claim:** Phase 3 flagged 4 anonymous kernel entries (Name=null, Path=null) as **"HIGH SUSPICION — Rootkit components with deliberate identity erasure."**
**Limitation:** In the subsequent `target_beta` investigation, the identical artifact type (4 null-name/null-path modscan entries with base addresses outside normal x64 kernel VA range) was correctly downgraded to **"False Positive (low confidence) — pool-scan carving artifacts."** The same pool-scan carving artifacts were handled inconsistently between the two investigations. In target_alpha, the higher-severity label was applied without checking whether the base addresses fell within valid Windows x64 kernel virtual address ranges. Pool-tag scanning routinely surfaces unrelated freed or uninitialized memory as apparent "driver entries."
**Honest Rating:** The "HIGH SUSPICION" label for these 4 entries is **likely an overstatement**. They should have been flagged at "Low Confidence — possible pool artifact, cannot be confirmed as malicious without VA range validation." The target_beta self-correction on the same artifact type was the more disciplined call.

### 3.2 "Mnemosyne" as a "Known Threat Actor Naming Convention"
**Claim:** Incident report states: *"'Mnemosyne' (Greek goddess of memory) is a known threat actor naming convention for memory-resident implants."*
**Limitation:** This claim is not supported by any tool output or cited intelligence source. It is an analytical narrative assertion that cannot be verified from the raw Engram data. The binary is malicious based on path and DKOM behavior — the naming convention commentary adds no verifiable value and risks being perceived as hallucinated threat-intel context.
**Honest Rating:** This is an **unsupported narrative embellishment**. The finding is valid; the attribution context is unverifiable and should have been omitted or marked as analyst inference only.

### 3.3 OUTLOOK.EXE → Email Delivery Vector Inference
**Claim:** Attack narrative states: *"Unknown delivery vector (email attachment via OUTLOOK.EXE presence likely; multiple OUTLOOK.EXE instances in psscan suggest heavy email use)."*
**Limitation:** Multiple OUTLOOK.EXE entries in a physical pool-tag scan indicates the application ran on the system — nothing more. OUTLOOK.EXE is a common enterprise application. Its presence does not indicate that Outlook was the delivery mechanism. The word "likely" qualifies the inference, but including a specific delivery vector hypothesis in the attack narrative when no supporting evidence exists (no attachment spawn chain, no OLE/COM parent-child relationship) risks creating a false investigative lead.
**Honest Rating:** This is an **unsupported inference** presented as a probable finding. The delivery vector is genuinely unknown; the attack narrative should state "Initial access vector: UNKNOWN" without speculating on Outlook.

### 3.4 sc.exe → "Likely used to install subject_srv.exe as a service"
**Claim:** Attack narrative states: *"sc.exe (PID 3068) invoked — likely used to install subject_srv.exe as a service."*
**Limitation:** Phase 5 returned empty for sc.exe (PID 3068) — command-line arguments were not extractable. The claim that sc.exe specifically installed subject_srv.exe is an inference unsupported by any tool output. sc.exe could have been invoked for any number of service operations. The causal chain (sc.exe → subject_srv.exe installation) is plausible but not evidenced.
**Honest Rating:** This is a **reasonable but unsupported narrative inference**. Should be labeled "possible" or moved to a hypothesis section rather than stated as part of the attack reconstruction.

### 3.5 subject_srv.exe — "DUAL Persistence" Framing Potentially Misleading
**Claim:** Risk Assessment section lists: *"Persistence Mechanism: DUAL: Kernel driver (Mnemosyne.sys) + User-mode service (subject_srv.exe)."*
**Limitation:** `subject_srv.exe` is a **stale EPROCESS object** — it terminated before the memory capture. The dual-persistence framing implies both mechanisms are concurrently active at time of capture. In fact, only Mnemosyne.sys is confirmed active in memory. subject_srv.exe's Service registry key may still exist (which would constitute persistence), but that was not verified from the memory dump. The "dual persistence" label conflates confirmed-active (Mnemosyne.sys) with confirmed-executed-but-currently-stale (subject_srv.exe).
**Honest Rating:** Framing is **slightly misleading**. More accurate: "Confirmed active persistence: Mnemosyne.sys (Ring 0). Historical persistence indicator: subject_srv.exe service registration (executed; terminated at capture time; registry key not verified from dump)."

### 3.6 Mnemosyne.sys Loading "Confirms Prior Privilege Escalation"
**Claim:** Attack narrative states: *"Driver loaded (requires SYSTEM / kernel-level access — confirms prior privilege escalation)."*
**Limitation:** Loading a kernel driver requires SYSTEM-level privileges, but this does not strictly "confirm privilege escalation." The attacker may have had administrative credentials from the outset (valid account compromise, supply chain, or physical access) without performing a technical privilege escalation exploit. "Confirms" is too strong; "implies" or "indicates" would be more accurate.
**Honest Rating:** **Minor overstatement** — mechanistically valid but the distinction between "had admin credentials" and "escalated privileges" is forensically meaningful, especially for attribution.

### 3.7 McAfee Driver AV Evasion — Specificity Overstated
**Claim:** Attack narrative states: *"McAfee AV bypassed (likely via mfehidk.sys / mfewfpk.sys hooking — both McAfee-specific kernel drivers are unlinked, suggesting rootkit interacted with them)."*
**Limitation:** mfehidk.sys and mfewfpk.sys are unlinked from PsLoadedModuleList — but so are ALL kernel modules (including ntoskrnl.exe and hal.dll). The PsLoadedModuleList was globally wiped by Mnemosyne.sys. The investigation implies a targeted interaction with McAfee drivers specifically, when the actual mechanism is a blanket wipeout of the entire module list. Stating that the rootkit "interacted with" McAfee drivers specifically is not supported over any other driver — they were all caught in the same global unlink.
**Honest Rating:** **Narrative overreach** — the AV evasion conclusion is correct (McAfee is blind due to the DKOM wipeout), but the specific "via mfehidk.sys/mfewfpk.sys hooking" mechanism is inferred and not supported by the available data.

---

## 4. Missed Artifacts / Investigation Gaps

### 4.1 sd.exe (PID 5588) — Binary Identity Not Resolved
`sd.exe` with an orphaned PPID was flagged as MEDIUM confidence. Phase 5 returned empty. The investigation correctly left it open as "Unknown binary, orphaned parent." However, no attempt was made to consider candidate identities: `sd.exe` is the binary name for Microsoft's legacy Source Depot (internal version control) CLI, which has appeared on enterprise workstations. On a workstation with Outlook and McAfee, this could be legitimate. The MEDIUM confidence label is appropriate, but a one-line note about the candidate identity would have improved the report quality.

### 4.2 OUTLOOK.EXE Instance Count — Dwell Time Estimation Not Attempted
15+ OUTLOOK.EXE entries in the psscan output, with varying PIDs and orphaned parents, could have been used to roughly estimate attacker dwell time or session count (each new Outlook instance gets a new PID). This opportunity for timeline enrichment was not explored. Not a significant gap, but a missed analytical opportunity.

### 4.3 McAfee Full Process List — Potential Service Hijack Not Assessed
The investigation documented the full McAfee/Trellix process footprint (masvc, macmnsvc, mfemms, HipMgmt, FireSvc, mfevtps, mcshield, mfefire, mfehcs, mfemactl, mfeann, macompatsvc). Given the confirmed rootkit, whether any McAfee process was itself hijacked (code injection into mcshield.exe, for example) was not assessed — Phase 2 was empty, making this technically unverifiable. The gap should have been explicitly noted in Forensic Blind Spots.

### 4.4 Kernel Callbacks — Present in Blind Spots but Not Discussed in Report Body
The Forensic Blind Spots table includes "Kernel callbacks (process/image/thread) — Anomalous_Callbacks returned empty." This is correct to include, but the body of the report does not discuss what kernel callbacks represent or their significance. For completeness, a note that process notification callbacks are a common rootkit persistence and detection-evasion mechanism (used to get notified of new process creation, terminate security tools, etc.) would have added analytical depth.

### 4.5 Registry Forensics Recommended but Not Executed
The Recommended Actions include: *"REGISTRY FORENSICS — Extract SYSTEM hive for offline Shimcache/Amcache/Services analysis to confirm subject_srv.exe installation timeline."* This is a sound recommendation. However, this analysis was not performed during the investigation (it would require disk forensics, not memory forensics). The recommendation is correctly scoped as a next-step action rather than a completed finding — no gap here, but noting it for completeness.

---

## 5. Hallucinated Claims — None Identified from Tool Output

No fabricated PIDs, invented driver names, or non-existent process names were found in the incident report. Every PID and process name cited (subject_srv.exe PID 12528, cmd.exe PID 5024, sc.exe PID 3068, sd.exe PID 5588, Mnemosyne.sys) can be traced directly to a JSON field in the raw Engram tool outputs.

The "Mnemosyne as known threat actor naming convention" claim (Section 3.2) is the closest instance to a hallucinated fact — it cannot be traced to tool output and reads as analyst-injected threat intelligence. It is classified as an unverifiable narrative assertion rather than a factual hallucination, because the rootkit is demonstrably malicious regardless of the naming commentary.

The Empty Data Protocol was applied correctly every time an Engram tool returned `[]` or `{}`, preventing false-negative hallucination.

---

## 6. Cross-Investigation Consistency Notes

Where the same artifact type appeared in both `target_alpha.img` and `taregt-beta-basedc.img`, consistency was not maintained:

| Artifact | target_alpha Assessment | target_beta Assessment | Correct Call |
|----------|------------------------|----------------------|--------------|
| 4 null-name/null-path modscan entries | HIGH SUSPICION — rootkit components | False Positive (low confidence) — pool artifacts | **target_beta** — VA range validation is the correct approach |
| ADD Spoofed Decoy (0-thread) entries | Noted as suspicious combined with DKOM | Both "attacker decoy" and "stale terminated" hypotheses held | target_beta handled dual-hypothesis more explicitly |
| Empty Phase 5 for all PIDs | Stale EPROCESS objects (terminated before capture) | ADD Spoofed Decoy degraded EPROCESS (active but undumpable) | Different root causes correctly identified per host |

The key difference in Phase 5 failure modes is notable and was correctly diagnosed: in target_alpha, processes were stale (terminated before capture, no live memory); in target_beta, processes were active ADD Spoofed Decoys (live but EPROCESS too degraded to dump). Both correctly received the Empty Data Protocol.

---

## 7. Methodology Assessment

| Criterion | Rating | Notes |
|-----------|--------|-------|
| DKOM detection accuracy | Excellent | Correct pslist/psscan discrepancy interpretation |
| Rootkit identification | Excellent | Physical modscan, non-standard path, confirmed |
| Stale EPROCESS handling | Excellent | Correctly distinguished terminated-before-capture from active; did not exonerate |
| Empty data handling | Excellent | Empty Data Protocol applied correctly across all 4 empty events |
| False positive rate | Good | OUTLOOK.EXE and McAfee service processes correctly handled; null-name entries over-escalated |
| OODA loop compliance | Excellent | Phase 5 triggered correctly after Phase 1 and Phase 3 per mandate |
| Attack narrative accuracy | Partial | Core reconstruction sound; Outlook delivery vector and sc.exe→subject_srv causal link are unsupported inferences |
| Confidence calibration | Good | Most labels appropriate; "HIGH SUSPICION" on null-name entries and "DUAL persistence" framing need downgrade |
| Anti-hallucination discipline | Good | No fabricated artifacts; one unverifiable threat-intel assertion (Mnemosyne naming convention) |
| Cross-host consistency | Partial | Null-name entry handling inconsistent with target_beta; stale vs. active EPROCESS distinction handled correctly |

---

## 8. Summary

The investigation correctly identified the two primary IOCs (`Mnemosyne.sys` Ring 0 rootkit and `subject_srv.exe` backdoor service), correctly applied the Empty Data Protocol across four empty-return events, correctly distinguished stale EPROCESS objects from active processes, and produced no fabricated artifacts.

The primary inaccuracies are in the attack narrative layer — not the artifact identification layer. The OUTLOOK.EXE delivery vector inference, the sc.exe→subject_srv installation causal link, and the Mnemosyne naming convention comment are all narrative elements unsupported by tool output. The 4 null-name kernel entry escalation to "HIGH SUSPICION" was inconsistent with how the same artifact was handled in the follow-on `target_beta` investigation (where it was correctly downgraded to a probable pool artifact).

The stale EPROCESS handling and the dual DKOM attribution (PsActiveProcessHead + PsLoadedModuleList from a single rootkit operation) were analytical strengths distinguishing this investigation from a tool-output transcription. No claims were fabricated. All IOCs are traceable to raw Engram MCP tool output.
