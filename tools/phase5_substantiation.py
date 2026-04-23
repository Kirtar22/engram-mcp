import subprocess
import json
import os

# Dynamically fetch the path, fallback to standard 'vol.py' if not set
VOLATILITY_PATH = os.environ.get("VOLATILITY_PATH", "vol.py")
EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports")

def run_volatility_plugin_pids(memory_image: str, plugin: str, pids: list, extra_args: list = None) -> list:
    """Runs a Volatility plugin restricted to specific PIDs with optional extra arguments."""
    if not pids: return []
    
    # FIX: Volatility 3 expects separate arguments for each PID, NOT a comma-separated string.
    cmd = [
        "python3", VOLATILITY_PATH, 
        "-f", memory_image, 
        "-r", "json", 
        plugin,
        "--pid"
    ]
    # Add each PID as a separate space-delimited argument in the subprocess list
    cmd.extend([str(p) for p in pids])
    
    if extra_args:
        cmd.extend(extra_args)
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        json_start = output.find('[')
        if json_start != -1:
            return json.loads(output[json_start:])
        return []
    except subprocess.CalledProcessError as e:
        # We can log this locally if needed, but return empty list on failure
        return []
    except json.JSONDecodeError:
        return []

def run_phase5_substantiation(memory_image: str, target_pids: list) -> dict:
    """Executes Phase 5: Deep extraction of IOCs, exact privileges, and physical file dumping."""
    if not os.path.exists(memory_image):
        return {"error": f"Memory image not found at {memory_image}"}
    if not target_pids:
        return {"error": "No target PIDs provided."}

    # Ensure export directory exists for dumpfiles
    os.makedirs(EXPORT_DIR, exist_ok=True)

    # Gather targeted data
    cmdline_data = run_volatility_plugin_pids(memory_image, "windows.cmdline", target_pids)
    handles_data = run_volatility_plugin_pids(memory_image, "windows.handles", target_pids)
    malfind_data = run_volatility_plugin_pids(memory_image, "windows.malfind", target_pids)
    getsids_data = run_volatility_plugin_pids(memory_image, "windows.getsids", target_pids)
    memmap_data = run_volatility_plugin_pids(memory_image, "windows.memmap", target_pids)
    
    # Execute Dumpfiles to safely extract the PE/segments to disk
    dumpfiles_data = run_volatility_plugin_pids(
        memory_image, "windows.dumpfiles", target_pids, extra_args=["--dump-dir", EXPORT_DIR]
    )

    report = {}
    for pid in target_pids:
        report[pid] = {
            "Command_Line": "Unknown",
            "Privilege_SIDs": [],
            "Suspicious_Handles": {"Mutants": [], "Files": []},
            "Malfind_Injections": [],
            "Memmap_RWX_Regions": [],
            "Dumped_Files": []
        }

    # 1. Map Command Lines
    for entry in cmdline_data:
        pid = entry.get("PID")
        if pid in report:
            report[pid]["Command_Line"] = entry.get("Args", "Unknown")

    # 2. Map SIDs (Privileges)
    for entry in getsids_data:
        pid = entry.get("PID")
        if pid in report:
            sid_name = entry.get("Name")
            if sid_name and sid_name not in report[pid]["Privilege_SIDs"]:
                report[pid]["Privilege_SIDs"].append(sid_name)

    # 3. Map Handles (Filtered for mutants and interesting files)
    for entry in handles_data:
        pid = entry.get("PID")
        if pid in report:
            h_type = entry.get("Type", "")
            h_name = entry.get("Name", "")
            if h_name and str(h_name).strip():
                if h_type == "Mutant":
                    report[pid]["Suspicious_Handles"]["Mutants"].append(h_name)
                elif h_type == "File" and ("\\Users\\" in str(h_name) or ".exe" in str(h_name)):
                    report[pid]["Suspicious_Handles"]["Files"].append(h_name)

    # 4. Map Malfind (Truncated Hex)
    for entry in malfind_data:
        pid = entry.get("PID")
        if pid in report:
            raw_hex = entry.get("Hexdump", "")
            trunc_hex = raw_hex[:150] + "... [TRUNCATED]" if len(raw_hex) > 150 else raw_hex
            report[pid]["Malfind_Injections"].append({
                "Start_VPN": entry.get("Start VPN", "Unknown"),
                "Hex_Dump_Preview": trunc_hex
            })

    # 5. Map Memmap (Filtered for RWX to avoid token explosion)
    for entry in memmap_data:
        pid = entry.get("PID")
        if pid in report:
            protection = str(entry.get("Protection", ""))
            # We specifically hunt for RWX (PAGE_EXECUTE_READWRITE) which proves injection
            if "EXECUTE_READWRITE" in protection:
                report[pid]["Memmap_RWX_Regions"].append({
                    "Virtual_Address": entry.get("VirtualAddress", "Unknown"),
                    "Size": entry.get("Size", "Unknown"),
                    "Protection": protection
                })

    # 6. Map Dumped Files
    for entry in dumpfiles_data:
        # Dumpfiles often doesn't strictly link back to PID in the same way, but we parse the output
        file_path = entry.get("FileName", "Unknown")
        if file_path != "Unknown":
            # Just append to the first PID for reporting purposes, or track globally
            report[target_pids[0]]["Dumped_Files"].append({
                "Status": "Extracted to Disk",
                "File": file_path,
                "Export_Directory": EXPORT_DIR
            })

    # Deduplicate handle lists
    for pid in target_pids:
        report[pid]["Suspicious_Handles"]["Mutants"] = list(set(report[pid]["Suspicious_Handles"]["Mutants"]))
        report[pid]["Suspicious_Handles"]["Files"] = list(set(report[pid]["Suspicious_Handles"]["Files"]))

    return report