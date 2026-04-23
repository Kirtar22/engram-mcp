# 🗺️ Engram MCP: AI DFIR Architecture Diagram

This diagram visualizes the deterministic data pipeline of Engram MCP. It illustrates how the architecture decouples the LLM Orchestrator from raw tool execution, enforcing the 5-Phase OODA Loop methodology via Model Context Protocol (MCP) JSON telemetry.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#003366', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#fff'}}}%%
graph TD
    %% --- Evidence Layer ---
    subgraph Evidence_Layer ["📁 1. Evidence Layer (Offline)"]
        Dump[("Memory Dump<br>(.raw / .img / .vmem)")]
    end

    %% --- Telemetry Layer ---
    subgraph Telemetry_Layer ["🔍 2. Telemetry Extraction (Forensic Engine)"]
        Vol3[("Volatility 3 Framework<br>(Symbol Tables & Plugins)")]
    end

    %% --- Control & Safety Layer (The MCP Server) ---
    subgraph Control_Layer ["🛡️ 3. Control & Safety Layer (The Guardrail)"]
        FastMCP[("Engram FastMCP Server<br>(Python Router)")]
        
        subgraph Guardrails ["Deterministic Python Guardrails"]
            EmptyProtocol{"Intercept<br>Empty Arrays?"}
            GracefulDegrade["Handle Plugin<br>Crashes / Timeouts"]
        end
    end

    %% --- Orchestration Layer ---
    subgraph Orchestration_Layer ["🧠 4. Orchestration Layer (The AI)"]
        LLM[("Claude Code Agent<br>(Sonnet 3.5)")]
        CLAUDE_md[["CLAUDE.md<br>(System Prompt)"]]
        
        subgraph StateTracker ["6-Phase OODA State Tracker"]
            OODA1["[x] Phase 1: Triage"]
            OODA2["[x] Phase 2: User-Space"]
            OODA3["[x] Phase 3: Kernel Abyss"]
            OODA4["[x] Phase 4: Advanced"]
            OODA5["[x] Phase 5: Substantiation"]
            OODA6["[ ] Phase 6: Report"]
        end
    end

    %% --- Output Layer ---
    subgraph Output_Layer ["📄 5. Output Layer"]
        Report[("Local File System<br>(exports/Incident_Report.md)")]
        Logs[("Local File System<br>(logs/execution_trace.txt)")]
    end

    %% --- Flows ---
    Dump ==>|Raw Physical Memory| Vol3
    
    Vol3 ==>|Raw Tabular Stdout| FastMCP
    FastMCP ==>| construction & Execution| Vol3
    
    FastMCP -.->|Cleanse & Serialize| EmptyProtocol
    FastMCP -.->|try/except| GracefulDegrade
    
    EmptyProtocol ==>|Inject 'UNVERIFIED' string| LLM
    GracefulDegrade ==>|Return Error State| LLM
    FastMCP ==>|Structured JSON Telemetry| LLM
    
    LLM ==>|JSON-RPC Tool Calls| FastMCP
    
    CLAUDE_md -.->|Enforce 6-Phase OODA| LLM
    OODA6 -.->|Call tool_write_report| Report
    
    %% Output Flows
    LLM -.->|Reasoning Trace| Logs
    FastMCP -.->|Call tool_write_report| Report

    %% --- Styling ---
    classDef evidence fill:#f9f,stroke:#333,stroke-width:2px,color:black;
    classDef telemetry fill:#ccf,stroke:#333,stroke-width:2px,color:black;
    classDef control fill:#ff9,stroke:#333,stroke-width:2px,color:black;
    classDef guard fill:#fff,stroke:#f00,stroke-width:1px,stroke-dasharray: 5 5,color:black;
    classDef orchestrator fill:#dfd,stroke:#333,stroke-width:2px,color:black;
    classDef output fill:#eee,stroke:#333,stroke-width:2px,color:black;
    
    class Dump evidence;
    class Vol3 telemetry;
    class FastMCP control;
    class EmptyProtocol,GracefulDegrade guard;
    class LLM,CLAUDE_md orchestrator;
    class OODA1,OODA2,OODA3,OODA4,OODA5,OODA6 orchestrator;
    class Report,Logs output;
```