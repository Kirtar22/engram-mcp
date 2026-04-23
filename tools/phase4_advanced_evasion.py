import subprocess
import json
import os

# Dynamically fetch the path, fallback to standard 'vol.py' if not set
VOLATILITY_PATH = os.environ.get("VOLATILITY_PATH", "vol.py")

def run_volatility_plugin(memory_image: str, plugin: str, extra_args: list = None) -> list:
    """Runs a system-wide Volatility plugin."""
    cmd = ["python3", VOLATILITY_PATH, "-f", memory_image, "-r", "json", plugin]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        json_start = output.find('[')
        if json_start != -1:
            return json.loads(output[json_start:])
        return []
    except subprocess.CalledProcessError:
        return []
    except json.JSONDecodeError:
        return []

def run_phase4_advanced_evasion(memory_image: str) -> dict:
    """Executes Phase 4: Advanced Evasion (RX sweeps, Shimcache, and VadYaraScan)."""
    if not os.path.exists(memory_image):
        return {"error": f"Memory image not found at {memory_image}"}

    report = {
        "Suspicious_Threads_RX_Evasion": [],
        "Transient_Execution_Shimcache": [],
        "VadYaraScan_Hits": []
    }

    # 1. THREADS: Sweep for Unbacked Executable Memory (Gargoyle / RX Evasion)
    threads_data = run_volatility_plugin(memory_image, "windows.threads")
    for t in threads_data:
        start_addr = str(t.get("StartAddress", ""))
        # Heuristic: Unbacked threads often start at raw hex addresses with no mapped module (+)
        if start_addr.startswith("0x") and "+" not in start_addr:
            pid = t.get("PID", 0)
            if pid > 4: # Filter out kernel idle threads
                report["Suspicious_Threads_RX_Evasion"].append({
                    "PID": pid,
                    "TID": t.get("TID"),
                    "Process": t.get("Process", "Unknown"),
                    "StartAddress": start_addr,
                    "State": t.get("State", "Unknown")
                })
    # Cap threads to prevent token bloat
    report["Suspicious_Threads_RX_Evasion"] = report["Suspicious_Threads_RX_Evasion"][:15]

    # 2. SHIMCACHE/AMCACHE: Transient Execution Tracking
    # Volatility 3 uses windows.shimcache and windows.amcache
    shimcache_data = run_volatility_plugin(memory_image, "windows.shimcache")
    
    anomalous_paths = ["\\temp\\", "\\appdata\\", "\\users\\", "\\downloads\\", "\\desktop\\", "\\videos\\"]
    
    for entry in shimcache_data:
        path = str(entry.get("Path", "")).lower()
        last_updated = str(entry.get("Last modified", ""))
        
        # If the executed program ran from a user-writable directory, flag it
        if any(anom in path for anom in anomalous_paths):
            report["Transient_Execution_Shimcache"].append({
                "Executable": entry.get("Path", "Unknown"),
                "Last_Executed": last_updated
            })
            
    report["Transient_Execution_Shimcache"] = report["Transient_Execution_Shimcache"][:20]

    # 3. VADYARASCAN: Sweep for memory ghosts and shellcode
    # We use a generic YARA rule to hunt for common NOP sleds and direct syscall stubs in memory
    yara_rule = 'rule generic_shellcode { strings: $nop = { 90 90 90 90 90 90 90 90 } $syscall = { 41 ba ?? 00 00 00 48 b8 } condition: any of them }'
    vadyarascan_data = run_volatility_plugin(memory_image, "windows.vadyarascan", extra_args=["--yara-rules", yara_rule])
    
    for hit in vadyarascan_data:
        pid = hit.get("PID")
        if pid:
            report["VadYaraScan_Hits"].append({
                "PID": pid,
                "Process": hit.get("Process", "Unknown"),
                "Rule_Matched": hit.get("Rule", "Unknown"),
                "Virtual_Address": hit.get("Offset", "Unknown")
            })

    return report