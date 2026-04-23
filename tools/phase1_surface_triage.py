import subprocess
import json
import os

# Dynamically fetch the path, fallback to standard 'vol.py' if not set
VOLATILITY_PATH = os.environ.get("VOLATILITY_PATH", "vol.py")

def run_volatility_plugin(memory_image: str, plugin: str) -> list:
    """Runs a Volatility plugin with JSON output and safely parses the result."""
    cmd = ["python3", VOLATILITY_PATH, "-f", memory_image, "-r", "json", plugin]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        json_start = output.find('[')
        if json_start != -1:
            return json.loads(output[json_start:])
        return []
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Volatility failed on {plugin}. Error: {e.stderr}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse JSON from {plugin} output.")

def run_phase1_surface_triage(memory_image: str) -> dict:
    """Executes Phase 1: Correlated Process, Network, and Privilege Triage."""
    if not os.path.exists(memory_image):
        return {"error": f"Memory image not found at {memory_image}"}

    # 1. Gather all sub-system data in the background
    pslist_data = run_volatility_plugin(memory_image, "windows.pslist")
    psscan_data = run_volatility_plugin(memory_image, "windows.psscan")
    threads_data = run_volatility_plugin(memory_image, "windows.threads")
    # Graceful degradation for OS incompatibility (Windows XP lacks netscan structures)
    try:
        netscan_data = run_volatility_plugin(memory_image, "windows.netscan")
    except RuntimeError as e:
        print(f"[*] Warning: netscan failed (likely OS incompatibility). Proceeding without network data.")
        netscan_data = [] # Provide an empty list so the correlation loops below don't break
    getsids_data = run_volatility_plugin(memory_image, "windows.getsids")

    # 2. Map Data to PIDs (Correlation)
    thread_counts = {}
    for t in threads_data:
        pid = t.get("PID")
        if pid is not None:
            thread_counts[pid] = thread_counts.get(pid, 0) + 1

    network_map = {}
    for conn in netscan_data:
        pid = conn.get("PID")
        f_addr = conn.get("ForeignAddr", "")
        # Filter out local loopback/ANY noise
        if f_addr not in ["0.0.0.0", "::", "127.0.0.1", "::1", "*"]:
            if pid not in network_map:
                network_map[pid] = []
            network_map[pid].append(f"{f_addr}:{conn.get('ForeignPort')} ({conn.get('State', 'Unknown')})")

    # Map Privilege Levels (Checking for SYSTEM execution)
    privilege_map = {}
    for sid in getsids_data:
        pid = sid.get("PID")
        sid_name = sid.get("Name", "")
        if pid not in privilege_map:
            privilege_map[pid] = []
        # Keep it concise to save tokens: Only tag notable high-privilege SIDs or unique users
        if sid_name and ("SYSTEM" in str(sid_name) or "Administrator" in str(sid_name)):
            if sid_name not in privilege_map[pid]:
                privilege_map[pid].append(sid_name)

    pslist_pids = {p.get("PID") for p in pslist_data if p.get("PID") is not None}
    
    hidden_dkom = []
    add_spoofs = []
    exited_zombies = []
    flat_topology = []

    # 3. Deep Audit using the Pool Scan (EPROCESS blocks)
    for proc in psscan_data:
        pid = proc.get("PID")
        name = proc.get("ImageFileName", "Unknown")
        exit_time = proc.get("ExitTime")
        active_threads = thread_counts.get(pid, 0)

        # Baseline context for Claude (Highly Correlated)
        flat_topology.append({
            "PID": pid,
            "PPID": proc.get("PPID"),
            "Name": name,
            "Threads": active_threads,
            "High_Privileges": privilege_map.get(pid, ["Standard/Unknown"]),
            "External_Network": network_map.get(pid, [])
        })

        # --- MATHEMATICAL EVASION CHECKS ---
        if pid not in pslist_pids:
            hidden_dkom.append({"PID": pid, "Name": name, "Reason": "DKOM"})
        
        if active_threads == 0 and not exit_time:
            add_spoofs.append({"PID": pid, "Name": name, "Reason": "ADD Spoofed Decoy (0 Threads)"})

        if exit_time and str(exit_time).strip() not in ["", "N/A", "NaT", "None"]:
            # If it has an exit time, but still has active network connections, flag it!
            active_net = network_map.get(pid, [])
            if active_net:
                exited_zombies.append({
                    "PID": pid, 
                    "Name": name, 
                    "Reason": f"Zombie: OS reports Exited at {exit_time}, but holds active sockets: {active_net}"
                })

    # 4. Construct the Final Report
    report = {
        "Phase1_Summary": {
            "Total_Visible_Processes": len(pslist_pids),
            "DKOM_Hidden_Found": len(hidden_dkom),
            "ADD_Spoofs_Found": len(add_spoofs),
            "Zombie_Connections": len(exited_zombies)
        },
        "Mathematical_Anomalies": {
            "DKOM_Processes": hidden_dkom,
            "ADD_Spoofed_Decoys": add_spoofs,
            "Zombie_Processes": exited_zombies
        },
        "Correlated_Topology": flat_topology
    }

    return report