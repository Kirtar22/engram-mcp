import subprocess
import json
import os

# Dynamically fetch the path, fallback to standard 'vol.py' if not set
VOLATILITY_PATH = os.environ.get("VOLATILITY_PATH", "vol.py")

def run_volatility_plugin(memory_image: str, plugin: str) -> list:
    """Runs a system-wide Volatility plugin."""
    cmd = ["python3", VOLATILITY_PATH, "-f", memory_image, "-r", "json", plugin]
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

def run_phase3_kernel_abyss(memory_image: str) -> dict:
    """Executes Phase 3: Ring 0 Rootkit and Hooking detection."""
    if not os.path.exists(memory_image):
        return {"error": f"Memory image not found at {memory_image}"}

    # Run the heavy kernel sweeps
    modules_data = run_volatility_plugin(memory_image, "windows.modules")
    modscan_data = run_volatility_plugin(memory_image, "windows.modscan")
    ssdt_data = run_volatility_plugin(memory_image, "windows.ssdt")
    callbacks_data = run_volatility_plugin(memory_image, "windows.callbacks")
    driverirp_data = run_volatility_plugin(memory_image, "windows.driverirp")

    report = {
        "Hidden_Drivers_Unlinked": [],
        "Suspicious_SSDT_Hooks": [],
        "Anomalous_Callbacks": [],
        "Rogue_Driver_IRPs": []
    }

    # 1. Diff modules vs modscan (Hidden Drivers)
    # Extract known base addresses from the linked modules list
    linked_bases = set()
    for mod in modules_data:
        base = mod.get("Base")
        if base:
            # Handle potential int/string casting issues in Volatility output
            linked_bases.add(str(base).strip())

    # Check modscan physical hits against the linked list
    for mod in modscan_data:
        base = str(mod.get("Base", "")).strip()
        if base and base not in linked_bases:
            name = mod.get("Name", "Unknown")
            path = mod.get("Path", "Unknown")
            # Filter out known Volatility memory artifacts/pagefiles
            if "pagefile" not in str(path).lower() and name != "Unknown":
                report["Hidden_Drivers_Unlinked"].append({
                    "Base_Address": base,
                    "Name": name,
                    "Path": path,
                    "Status": "UNLINKED (Found in physical scan, missing from OS modules list)"
                })

    # 2. Filter SSDT Hooks
    # Legitimate SSDT entries point to ntoskrnl.exe or win32k.sys
    for hook in ssdt_data:
        module = str(hook.get("Module", "")).lower()
        if "ntoskrnl" not in module and "win32k" not in module:
            report["Suspicious_SSDT_Hooks"].append({
                "Index": hook.get("Index"),
                "Function": hook.get("Function", "Unknown"),
                "Hooking_Module": hook.get("Module", "UNKNOWN_MODULE")
            })

    # 3. Filter Callbacks (Process/Thread creation, Bugcheck, etc.)
    # Legitimate callbacks usually come from known Windows AV/EDR drivers or core OS
    for cb in callbacks_data:
        module = str(cb.get("Module", "")).lower()
        if module == "unknown" or module == "":
            report["Anomalous_Callbacks"].append({
                "Type": cb.get("Type", "Unknown"),
                "Callback_Address": cb.get("Callback", "Unknown"),
                "Hooking_Module": "UNKNOWN_MODULE (Unbacked/Hidden)"
            })

    # 4. Filter Driver IRPs (Network/File I/O Intercepts)
    # Similar to SSDT, we look for IRPs handled by unknown or anomalous drivers
    for irp in driverirp_data:
        module = str(irp.get("Module", "")).lower()
        if module == "unknown" or module == "":
            report["Rogue_Driver_IRPs"].append({
                "Driver": irp.get("Driver", "Unknown"),
                "IRP_Type": irp.get("IRP", "Unknown"),
                "Hooking_Module": "UNKNOWN_MODULE (Unbacked/Hidden)"
            })
    # ---------------------------------------------------------
    # 5. --- THE EMPTY DATA GUARDRAIL ---
    # If the plugins silently failed and returned nothing, 
    # overwrite the empty lists with explicit warnings for the LLM
    # ---------------------------------------------------------
    if not modscan_data and not modules_data:
        report["Hidden_Drivers_Unlinked"] = ["UNVERIFIED: modscan/modules returned no data (likely OS limitation). DO NOT declare clean."]
        
    if not ssdt_data:
        report["Suspicious_SSDT_Hooks"] = ["UNVERIFIED: ssdt plugin returned no data (likely OS limitation). DO NOT declare clean."]
        
    if not callbacks_data:
        report["Anomalous_Callbacks"] = ["UNVERIFIED: callbacks plugin returned no data (likely OS limitation). DO NOT declare clean."]
        
    if not driverirp_data:
        report["Rogue_Driver_IRPs"] = ["UNVERIFIED: driverirp plugin returned no data (likely OS limitation). DO NOT declare clean."]

    return report