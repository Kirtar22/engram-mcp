from mcp.server.fastmcp import FastMCP
import json
import logging
import os
import sys

# --- HACKATHON REQ #6 & #8: ARCHITECTURAL GUARDRAILS & STRUCTURED LOGGING ---
# Ensure Python knows where our 'tools' directory is
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.phase1_surface_triage import run_phase1_surface_triage
from tools.phase5_substantiation import run_phase5_substantiation
from tools.phase2_deep_userspace import run_phase2_deep_userspace
from tools.phase3_kernel_abyss import run_phase3_kernel_abyss
from tools.phase4_advanced_evasion import run_phase4_advanced_evasion

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "execution_trace.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)

# Initialize the MCP Server
mcp = FastMCP("Engram-MCP-Engine")

@mcp.tool()
def tool_phase1_surface_triage(memory_image: str) -> str:
    """
    PHASE 1: Surface Triage.
    Runs pslist, psscan, pstree, threads, getsids, and netscan.
    Returns the Process Topology, Network Sockets, DKOM flags, ADD Evasion flags, and Privilege (SID) data.
    
    Args:
        memory_image: Absolute path to the raw memory dump.
    """
    tool_name = "tool_phase1_surface_triage"
    logging.info(f"TOOL_CALL | {tool_name} | TARGET: {memory_image}")
    
    try:
        # Execute read-only architectural guardrail logic
        result = run_phase1_surface_triage(memory_image)
        
        if "error" in result:
            logging.error(f"TOOL_ERROR | {tool_name} | ERROR: {result['error']}")
        else:
            # Log summary metrics for the judges without bloating the file with the raw process tree
            metrics = result.get("Phase1_Summary", {})
            anomalies = result.get("Mathematical_Anomalies", {})
            log_payload = {"Summary": metrics, "Anomalies": anomalies}
            logging.info(f"TOOL_SUCCESS | {tool_name} | RESULT: {json.dumps(log_payload)}")
            
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logging.error(f"TOOL_EXCEPTION | {tool_name} | EXCEPTION: {str(e)}")
        return f"Error executing {tool_name}: {str(e)}"

@mcp.tool()
def tool_phase5_substantiation(memory_image: str, target_pids: list[int]) -> str:
    """
    PHASE 5: Substantiation (Targeted Deep Dive).
    Use this to prove malicious intent on specific PIDs found in earlier phases.
    Extracts base64 arguments (cmdline), malicious Mutexes (handles), getsids,
    maps RWX memory regions (memmap), extracts raw assembly (malfind), 
    and safely dumps the binary/memory segment to disk (dumpfiles).
    
    Args:
        memory_image: Absolute path to the raw memory dump.
        target_pids: A list of integer PIDs to investigate (e.g., [1044, 1580]).
    """
    tool_name = "tool_phase5_substantiation"
    logging.info(f"TOOL_CALL | {tool_name} | TARGET: {memory_image} | PIDs: {target_pids}")
    
    try:
        result = run_phase5_substantiation(memory_image, target_pids)
        
        if "error" in result:
            logging.error(f"TOOL_ERROR | {tool_name} | ERROR: {result['error']}")
        else:
            logging.info(f"TOOL_SUCCESS | {tool_name} | Targets Investigated: {target_pids}")
            
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logging.error(f"TOOL_EXCEPTION | {tool_name} | EXCEPTION: {str(e)}")
        return f"Error executing {tool_name}: {str(e)}"
    
@mcp.tool()
def tool_phase2_deep_userspace(memory_image: str) -> str:
    """
    PHASE 2: Deep User-Space (System-Wide Sweep).
    Use this if Phase 1 is clean, or to systematically check for hidden injections.
    Runs ldrmodules to diff the VAD against the PEB to find unlinked DLLs.
    Runs a summarized malfind to locate unbacked RWX memory regions across the system.
    
    Args:
        memory_image: Absolute path to the raw memory dump.
    """
    tool_name = "tool_phase2_deep_userspace"
    logging.info(f"TOOL_CALL | {tool_name} | TARGET: {memory_image}")
    
    try:
        result = run_phase2_deep_userspace(memory_image)
        if "error" in result:
            logging.error(f"TOOL_ERROR | {tool_name} | ERROR: {result['error']}")
        else:
            hidden_count = len(result.get("Unlinked_Hidden_Modules", []))
            malfind_pids = len(result.get("System_Wide_Malfind_Summary", {}))
            logging.info(f"TOOL_SUCCESS | {tool_name} | Hidden_Modules: {hidden_count} | Malfind_PIDs: {malfind_pids}")
            
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logging.error(f"TOOL_EXCEPTION | {tool_name} | EXCEPTION: {str(e)}")
        return f"Error executing {tool_name}: {str(e)}"

@mcp.tool()
def tool_phase3_kernel_abyss(memory_image: str) -> str:
    """
    PHASE 3: The Kernel Abyss (Ring 0 Sweep).
    Use this to ensure the OS kernel itself isn't compromised. 
    Runs modules vs modscan to find mathematically unlinked (hidden) drivers.
    Evaluates SSDT hooks, Callbacks, and rogue Driver IRPs to catch rootkits 
    intercepting kernel functions.
    
    Args:
        memory_image: Absolute path to the raw memory dump.
    """
    tool_name = "tool_phase3_kernel_abyss"
    logging.info(f"TOOL_CALL | {tool_name} | TARGET: {memory_image}")
    
    try:
        result = run_phase3_kernel_abyss(memory_image)
        if "error" in result:
            logging.error(f"TOOL_ERROR | {tool_name} | ERROR: {result['error']}")
        else:
            hidden = len(result.get("Hidden_Drivers_Unlinked", []))
            ssdt = len(result.get("Suspicious_SSDT_Hooks", []))
            logging.info(f"TOOL_SUCCESS | {tool_name} | Hidden_Drivers: {hidden} | SSDT_Hooks: {ssdt}")
            
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logging.error(f"TOOL_EXCEPTION | {tool_name} | EXCEPTION: {str(e)}")
        return f"Error executing {tool_name}: {str(e)}"

@mcp.tool()
def tool_phase4_advanced_evasion(memory_image: str) -> str:
    """
    PHASE 4: Advanced Evasion.
    Use this to catch memory ghosts and transient malware.
    Evaluates thread start addresses for Gargoyle (unbacked RX evasion) and 
    sweeps registry execution artifacts (Shimcache/UserAssist) to prove transient malware ran and died.
    
    Args:
        memory_image: Absolute path to the raw memory dump.
    """
    tool_name = "tool_phase4_advanced_evasion"
    logging.info(f"TOOL_CALL | {tool_name} | TARGET: {memory_image}")
    
    try:
        result = run_phase4_advanced_evasion(memory_image)
        if "error" in result:
            logging.error(f"TOOL_ERROR | {tool_name} | ERROR: {result['error']}")
        else:
            threads = len(result.get("Suspicious_Threads_RX_Evasion", []))
            artifacts = len(result.get("Transient_Execution_Artifacts", []))
            logging.info(f"TOOL_SUCCESS | {tool_name} | Suspicious_Threads: {threads} | Execution_Artifacts: {artifacts}")
            
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logging.error(f"TOOL_EXCEPTION | {tool_name} | EXCEPTION: {str(e)}")
        return f"Error executing {tool_name}: {str(e)}"

import os
from datetime import datetime

@mcp.tool()
def tool_write_report(report_content: str, filename: str = "Incident_Report.md") -> str:
    """Writes the final Incident Report to the exports folder in Markdown format."""
    tool_name = "tool_write_report"
    # Log the call, but DO NOT log report_content to avoid bloating the log file
    logging.info(f"TOOL_CALL | {tool_name} | TARGET_FILENAME: {filename}")
    
    exports_dir = os.path.join(os.getcwd(), "exports")
    os.makedirs(exports_dir, exist_ok=True)
    
    # Add a timestamp to the filename so it doesn't overwrite older runs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(exports_dir, safe_filename)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        # Log the successful write and the path it was saved to
        logging.info(f"TOOL_SUCCESS | {tool_name} | RESULT: Report safely written to {file_path}")
        return f"SUCCESS: Final Markdown report successfully saved to {file_path}"
        
    except Exception as e:
        # Log any system errors (like permission denied)
        logging.error(f"TOOL_EXCEPTION | {tool_name} | EXCEPTION: {str(e)}")
        return f"ERROR: Failed to write report. {str(e)}"

if __name__ == "__main__":
    logging.info("SYSTEM | Engram-MCP-Engine Server Started.")
    mcp.run()