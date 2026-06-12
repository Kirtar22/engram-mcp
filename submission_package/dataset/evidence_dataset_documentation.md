# Evidence Dataset Documentation

**Project:** HACKATHON-MEM-001 — Engram MCP Volatility Agent  
**Prepared:** 2026-04-23 (UTC)  
**Evidence Mode:** Read-Only / Chain of Custody

---

## Overview

The Engram agent was tested against three real-world memory images sourced from public DFIR challenge datasets and professional training labs. Each image was analyzed via the agent's 5-phase OODA loop (Surface Triage → Deep User-Space → Kernel Abyss → Advanced Evasion → Substantiation) using exclusively MCP tool calls — no raw CLI access.

---

## Dataset 1 — BlackEnergy CTF Lab

| Field | Value |
|-------|-------|
| **File** | `unknown_dmp.raw` |
| **Source** | CyberDefenders Blue Team CTF — *BlackEnergy* challenge |
| **URL** | https://cyberdefenders.org/blueteam-ctf-challenges/blackenergy/ |
| **OS / Platform** | Windows XP SP3, VirtualBox guest |
| **Capture Tool** | DumpIt.exe (PID 276) |
| **User Context** | Local user `CyberDefenders`, member of local Administrators |
| **Ground Truth** | BlackEnergy v2/v3 rootkit infection |

### What the Agent Found

| Finding | Detail |
|---------|--------|
| **rootkit.exe** (PID 964) | Spawned by `explorer.exe` (PPID 1484); 0 threads (terminated); had local Admin privileges |
| **cmd.exe** (PID 1960) | Child of rootkit.exe — attacker interactive shell |
| **Injected PE in svchost.exe** (PID 880) | MZ header at virtual address 0x980000 in `svchost.exe -k DcomLaunch` (SYSTEM privilege) |
| **Mutex `746bbf3569adEncrypt`** | Encryption-themed mutex consistent with BlackEnergy payload behavior |
| **3 hollow notepad.exe decoys** | PIDs 528, 1444, 1432 — 0-thread ADD Spoofed Decoy processes |

**Attack Chain:** `rootkit.exe` → spawned interactive `cmd.exe` shell + injected PE payload into `svchost.exe` (SYSTEM) via DcomLaunch service host for privilege escalation and persistence.

**False Positives Discarded:** `winlogon.exe`, `csrss.exe`, `msmsgs.exe` malfind hits were `ff ee ff ee` Windows heap debug fill patterns — not PE headers or shellcode.

**Agent Blind Spots:** No active C2 network connections recovered (netscan clean at capture time). Shimcache (Phase 4) and Kernel SSDT (Phase 3) both returned empty due to Windows XP format incompatibility with Volatility 3 plugins. Injected PE could not be dumped to disk.

---

## Dataset 2 — SANS SRL-2018 Workstation

| Field | Value |
|-------|-------|
| **File** | `target_alpha.img` |
| **Source** | SANS Slingshot Reference Lab 2018 — `base-wkstn-01-memory` |
| **URL** | https://sansorg.egnyte.com/fl/HhH7crTYT4JK#folder-link/HACKATHON-2026/Compromised%20APT%20Attack%20Scenarios/SRL-2018-Compromised%20Enterprise%20Network/SRL-2018?p=ebd34b81-dcdd-4086-8147-140079d93db9 |
| **OS / Platform** | Windows 10/11 x64, VMware guest |
| **Environment** | Enterprise workstation; McAfee/Trellix AV installed |
| **Ground Truth** | Red Team exercise image — advanced persistent threat simulation |

### What the Agent Found

| Finding | Detail |
|---------|--------|
| **Mnemosyne.sys** | Ring 0 kernel rootkit at `C:\windows\Mnemosyne.sys` — non-standard Windows path; DKOM-hidden, recovered only via `modscan` |
| **4 anonymous kernel modules** | `Name=null`, `Path=null` — identity-erased rootkit components recovered by modscan |
| **Full DKOM — all processes** | `PsActiveProcessHead` fully unlinked; `pslist` returned 0 processes; 131 entries recovered via `psscan` |
| **Full DKOM — all modules** | `PsLoadedModuleList` fully unlinked; `modules` returned 0; 150+ entries recovered via `modscan` |
| **subject_srv.exe** (PID 12528) | Non-standard binary registered and running as a Windows service under `services.exe` (PID 740) — persistent backdoor |
| **cmd.exe** (PID 5024) | Orphaned attacker shell — parent process (PID 2748) missing from process tree |
| **sc.exe** (PID 3068) | Service control binary with anomalous parent — evidence of service installation activity |

**Attack Chain:** Initial access likely via phishing (OUTLOOK.EXE heavily represented) → `sc.exe` used to install `subject_srv.exe` as persistent service → `Mnemosyne.sys` deployed to `C:\windows\` and loaded as kernel driver (requires SYSTEM) → Full `_EPROCESS` + `PsLoadedModuleList` DKOM applied → McAfee/Trellix AV fully bypassed.

**Agent Blind Spots:** SSDT hooks unverified (plugin returned no data). User-space injection analysis unverifiable (process list dark). Active C2 network connections unverifiable (netscan empty due to DKOM). Shimcache empty (possible anti-forensic clearing). All Phase 3/4 subsystems classified **Unverified / Cannot Rule Out Compromise**.

---

## Dataset 3 — SANS SRL-2018 Domain Controller

| Field | Value |
|-------|-------|
| **File** | `target-beta-basedc.img` |
| **Source** | SANS Slingshot Reference Lab 2018 — `base-dc-memory` |
| **URL** | https://sansorg.egnyte.com/fl/HhH7crTYT4JK#folder-link/HACKATHON-2026/Compromised%20APT%20Attack%20Scenarios/SRL-2018-Compromised%20Enterprise%20Network/SRL-2018?p=75d28978-a43f-4eff-abd9-a9ff4c98f45b |
| **OS / Platform** | Windows Server x64, VMware guest |
| **Environment** | Active Directory Domain Controller; Windows Defender AV installed |
| **Ground Truth** | Red Team exercise image — advanced persistent threat simulation |

### What the Agent Found

| Finding | Detail |
|---------|--------|
| **Mnemosyne.sys** | Ring 0 kernel rootkit at `C:\windows\Mnemosyne.sys` — identical path to target_alpha; confirmed multi-host campaign deployment |
| **subject_srv.exe** (PID 5128) | Persistent backdoor service under `services.exe` (PID 644) — identical binary name to target_alpha |
| **Full DKOM — all processes** | `pslist` returned 0; 124 entries recovered via `psscan` |
| **Full DKOM — all modules** | `PsLoadedModuleList` wiped; ntoskrnl.exe, hal.dll, tcpip.sys, NDIS.SYS, afd.sys all unlinked |
| **AV defense blinding** | WdFilter.sys and WdNisDrv.sys (Windows Defender) unlinked from kernel — telemetry suppressed |
| **85 ADD Spoofed Decoy processes** | 0-thread fake process entries injected to poison analysis tools |
| **RuntimeBroker.exe → powershell.exe** (PID 5612) | Anomalous parent-child — RuntimeBroker is a sandboxed UWP broker, cannot legitimately spawn PowerShell |
| **powershell.exe → notepad.exe** (PID 7936) | Classic process hollowing host — PowerShell spawning notepad as a payload container |
| **ManagementAgen.exe** (PID 908) | Spawning 20+ `cmd.exe` child shells — hijacked or masquerading McAfee management agent |
| **tasklist.exe + findstr.exe** | Active recon binaries visible in process tree at capture time |

**Attack Chain:** Domain Controller compromise as lateral movement from workstation → `subject_srv.exe` installed as service → `Mnemosyne.sys` rootkit loaded at Ring 0 → Full DKOM applied to processes, modules, network drivers, and AV drivers → `RuntimeBroker.exe` hijacked to spawn PowerShell → notepad.exe used as hollow process host → McAfee management agent weaponized for command execution → active recon (tasklist/findstr) at time of capture.

**Campaign Attribution:** Confirmed same threat actor as Dataset 2 (`target_alpha.img`): identical `Mnemosyne.sys` path, identical `subject_srv.exe` service name, identical DKOM TTPs.

**Agent Blind Spots:** User-space injection unverifiable (VAD/PTE inaccessible due to DKOM cascade). C2 network connections hidden by rootkit — no active connections cannot be declared. SSDT/IRP hook plugins returned no data. LSASS (PID 660) credential extraction failed. Shimcache empty (rootkit-suppressed). All Phase 5 binary extractions empty due to ADD Spoofed Decoy condition on all PIDs.

---

## Cross-Dataset Summary

| Dataset | OS | Source | Key Malware | DKOM | C2 Recovered |
|---------|----|--------|-------------|------|--------------|
| `unknown_dmp.raw` | Windows XP SP3 | CyberDefenders CTF | BlackEnergy / rootkit.exe + svchost injection | Partial (process decoys) | No (clean at capture) |
| `target_alpha.img` | Windows 10/11 x64 | SANS SRL-2018 Workstation | Mnemosyne.sys + subject_srv.exe | Full (_EPROCESS + Modules) | Unverifiable |
| `target-beta-basedc.img` | Windows Server x64 | SANS SRL-2018 Domain Controller | Mnemosyne.sys + subject_srv.exe + hollow chain | Full (_EPROCESS + Modules + Network + AV) | Unverifiable |

**Key Observation:** The SANS SRL-2018 images represent a coordinated campaign — the same Ring 0 rootkit toolkit (`Mnemosyne.sys` + `subject_srv.exe`) was deployed across both the workstation and the domain controller, demonstrating lateral movement with consistent TTPs. The CyberDefenders image represents a separate, older threat family (BlackEnergy) on a legacy Windows XP host.
