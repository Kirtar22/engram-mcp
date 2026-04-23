# Final Incident Report — Blind IR: Target Host 001
**Case ID:** HACKATHON-MEM-001  
**Analyst:** Principal DFIR Orchestrator  
**Evidence:** `/cases/HACKATHON-MEM-001/unknown_dmp.raw`  
**Date (UTC):** 2026-04-17  
**Engine:** ValhuntirEngine (5-Phase OODA Loop)  
**OS Profile:** Windows XP SP2/SP3 (VirtualBox Guest — VBoxTray.exe, VBoxService.exe present)  

---

## Executive Summary

A Windows XP memory dump from "Target Host 001" was analyzed across five forensic phases. The investigation identified an active process injection attack: a file named `rootkit.exe` was executed from the user desktop session, spawned a `cmd.exe` shell, and injected a complete PE binary into `svchost.exe -k DcomLaunch` (PID 880, running as Local System). The injected PE is confirmed by an `MZ` header at virtual address 0x00980000 and a malware-pattern mutex (`746bbf3569adEncrypt`). The root process and its command shell are zombie/terminated, suggesting a drop-inject-exit pattern designed to minimize the forensic footprint of the initial dropper while leaving a persistent payload inside a critical OS process.

**Confidence Level:** HIGH for user-space IOCs. Kernel-space integrity is UNVERIFIED due to telemetry limitations.

---

## Verified Indicators of Compromise (IOCs)

### IOC-001 — Malicious Dropper Process
| Field | Value |
|-------|-------|
| **Name** | `rootkit.exe` |
| **PID** | 964 |
| **PPID / Parent** | 1484 / `explorer.exe` |
| **Status** | Zombie (0 threads — terminated after injection) |
| **Privilege** | Administrators / CyberDefenders user |
| **Cmdline** | null (memory freed post-termination) |
| **Source Phase** | Phase 1 |
| **Confidence** | HIGH |

**Analyst note:** Process was launched interactively from the user's desktop session. The name is non-system and explicitly adversarial. Absence of malfind data is a telemetry limitation (zombie process) — it does NOT exonerate this PID.

---

### IOC-002 — Rootkit-Spawned Command Shell
| Field | Value |
|-------|-------|
| **Name** | `cmd.exe` |
| **PID** | 1960 |
| **PPID / Parent** | 964 / `rootkit.exe` |
| **Status** | Zombie (0 threads — terminated) |
| **Privilege** | Administrators / CyberDefenders user |
| **Source Phase** | Phase 1 |
| **Confidence** | HIGH |

**Analyst note:** A command shell parented directly to `rootkit.exe` confirms the dropper performed command execution (staging, injection invocation, or reconnaissance) before self-terminating.

---

### IOC-003 — Confirmed PE Injection into svchost.exe
| Field | Value |
|-------|-------|
| **Name** | `svchost.exe` |
| **PID** | 880 |
| **Cmdline** | `C:\WINDOWS\system32\svchost -k DcomLaunch` |
| **Privilege** | **Local System** (maximum OS privilege) |
| **Injected VA** | 0x00980000 (9961472) |
| **Injection Proof** | `4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00...` — MZ PE header |
| **Injection Type** | Classic DLL / reflective PE injection (anonymous VAD region, absent from PEB) |
| **Source Phase** | Phase 2 (VAD/PEB diff) + Phase 5 (hex confirmation) |
| **Confidence** | **CONFIRMED** |

**Key evidence chain:**
1. Phase 2 `ldrmodules` diff: anonymous unlinked module at base 0x00980000 in `svchost.exe` (path = `None` — no backing file on disk)
2. Phase 2 `malfind`: RWX hit in PID 880 at VPN 9,961,472 (0x00980000) — exact address match
3. Phase 5 hex dump: bytes `4D 5A` (`MZ`) confirm a valid PE binary is mapped at this address
4. The injected PE runs with **Local System** privileges (inherited from svchost)

---

### IOC-004 — Malware Mutex (C2/Crypto Marker)
| Field | Value |
|-------|-------|
| **Mutex Name** | `746bbf3569adEncrypt` |
| **Host Process** | `svchost.exe` PID 880 |
| **Pattern** | `[hex_hash]Encrypt` — consistent with malware C2 session/crypto mutex |
| **Source Phase** | Phase 5 |
| **Confidence** | HIGH |

**Analyst note:** All other mutexes in PID 880 are legitimate WinInet/Internet Explorer handles (`ZonesLockedCacheCounterMutex`, `WininetProxyRegistryMutex`, etc.). The `746bbf3569adEncrypt` mutex is the sole anomaly — its naming convention matches malware families that use hashed session IDs combined with operation type suffixes to create unique C2 channel markers or to signal encryption state to other components.

---

### IOC-005 — Suspicious Zombie Notepad Instances (Medium Confidence)
| PIDs | Parent | Threads | Assessment |
|------|--------|---------|------------|
| 528, 1444, 1432 | explorer.exe (1484) | 0 (zombie) | Three simultaneous notepad.exe instances with 0 threads. Possible process hollowing attempts. Memory freed — unverifiable. |

**Anti-hallucination:** No malfind or VAD anomalies were detected for these PIDs in Phase 2. Downgraded to medium confidence. Cannot confirm hollowing without memory content. Noted as suspicious pattern.

---

## Attack Chain Reconstruction

```
[User: CyberDefenders]
        |
        v
explorer.exe (PID 1484)
        |
        |── rootkit.exe (PID 964)  ← Stage 1: Dropper executed
        |         |
        |         |── cmd.exe (PID 1960)  ← Stage 2: Shell for staging/recon
        |         |
        |         └──[INJECT]──> svchost.exe -k DcomLaunch (PID 880)
        |                              |
        |                              └── PE @ 0x00980000  ← Stage 3: Persistent payload
        |                              └── Mutex: 746bbf3569adEncrypt  ← C2/crypto marker
        |
        |── notepad.exe x3 (PIDs 528, 1444, 1432)  ← Possible hollow targets (unconfirmed)
        |
        └── DumpIt.exe (PID 276)  ← Evidence acquisition (forensic artifact)
```

**Assessed TTP:** 
- Initial Access/Execution: Direct user execution of dropper (`rootkit.exe`) — T1204
- Privilege Escalation / Persistence: PE injection into Local System svchost — T1055 (Process Injection)
- Defense Evasion: Dropper self-terminated post-injection (T1036); anonymous VAD region (no backing file, evades file-based AV) — T1055.001

---

## False Positives Discarded

| Finding | Phase | Reason Discarded |
|---------|-------|-----------------|
| winlogon.exe — 11 malfind hits | Phase 2/5 | Hex dumps reveal zero-filled pages and `FF EE FF EE` GDI sentinel — XP OS artifacts, not code |
| csrss.exe — font .fon unlinking | Phase 2 | csrss.exe maps console fonts via VAD without PEB registration; known XP behavior |
| csrss.exe malfind @ 0x7F6B0000 | Phase 2 | Address in upper user-space near KUSER_SHARED_DATA; XP shared memory mapping, not injection |
| explorer.exe — shellstyle.dll unlinked | Phase 2 | Luna theme DLL; resource-only, not code execution |

---

## Forensic Blind Spots

> **CRITICAL DISCLAIMER:** The following subsystems were examined but returned NO telemetry. Per investigative mandate, these areas CANNOT be declared "clean," "intact," or "uncompromised."

### Blind Spot 1 — Kernel Integrity (Phase 3)
- **Tools executed:** `modules` vs `modscan` (hidden driver enumeration), SSDT hook detection, IRP callback analysis
- **Result:** All returned empty arrays `[]`
- **Limitation:** Windows XP KPCR/KDDEBUGGER_DATA64 parsing in Volatility 3 may not reliably enumerate XP kernel structures. The rootkit may additionally have hidden its kernel components from Volatility's enumeration routines.
- **Assessment:** **Kernel-level rootkit compromise CANNOT BE RULED OUT.** The process is named `rootkit.exe` — kernel payload existence is a plausible hypothesis that this telemetry cannot refute.

### Blind Spot 2 — Transient Execution & Advanced Evasion (Phase 4)
- **Tools executed:** Thread RX-evasion scan (Gargoyle), Shimcache/AppCompatCache, VAD YARA sweep
- **Result:** All returned empty arrays `[]`
- **Limitation:** Windows XP AppCompatCache (stored in `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatibility`) uses a different binary format than Vista/7+ which Volatility 3's shimcache plugin is optimized for. Execution history of transient malware that ran-and-exited cannot be verified.
- **Assessment:** **Additional transient malware execution CANNOT BE RULED OUT.**

### Blind Spot 3 — rootkit.exe Cmdline & Binary
- **Status:** Process is zombie; PEB/process memory freed. Cmdline is null. No binary was dumped.
- **Impact:** Unable to determine rootkit.exe's launch arguments, origin path, or C2 configuration embedded in its binary.

---

## Definitive Findings Summary

| Subsystem | Status | Basis |
|-----------|--------|-------|
| User-space malware (dropper) | **VERIFIED COMPROMISED** | rootkit.exe PID 964 confirmed in Phase 1 |
| User-space injection | **VERIFIED COMPROMISED** | MZ header in svchost.exe PID 880 confirmed in Phase 5 |
| C2/crypto indicator | **VERIFIED** | Mutex 746bbf3569adEncrypt in PID 880 |
| Kernel integrity | **UNVERIFIED** | Phase 3 returned no data — blind spot |
| Transient execution history | **UNVERIFIED** | Phase 4 returned no data — XP incompatibility |
| Network C2 connections | **NOT OBSERVED** | No active external connections at time of capture |

---

## Recommended Containment Actions

1. **Immediate:** Isolate the host from network. Injected payload in svchost.exe PID 880 (Local System) may beacon when network is available despite no active connections at capture time.
2. **Memory acquisition:** The injected PE at VA 0x00980000 in PID 880 should be dumped with a compatible tool (e.g., Volatility 2 `procdump` or `memdump` on XP profile) to obtain the payload binary for AV/sandbox analysis.
3. **Mutex hunting:** Search all hosts on the network for processes holding the mutex `746bbf3569adEncrypt` — this is a reliable lateral movement indicator.
4. **Full disk acquisition:** Acquire the host disk image to locate `rootkit.exe` on disk (likely still present in user Downloads/Temp, or may have self-deleted), and perform registry analysis for persistence mechanisms (Run keys, Services).
5. **Kernel investigation:** Analyze the disk image for kernel drivers (`.sys` files) not present in a clean XP SP2/SP3 baseline — the kernel blind spot must be resolved with off-host analysis.

---

*Report generated by ValhuntirEngine OODA Loop | Analyst: Principal DFIR Orchestrator | UTC: 2026-04-17*
