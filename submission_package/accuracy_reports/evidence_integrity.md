# Evidence Integrity Approach — Engram MCP

**Applies to all three investigations:**
- `unknown_dmp.raw` (BlackEnergy CTF)
- `target_alpha.img` (SANS SRL-2018 Workstation)
- `target-beta-basedc.img` (SANS SRL-2018 Domain Controller)

---

## 1. How the Architecture Prevents Evidence Modification

**Architectural layer (Python MCP server):**
- All Volatility 3 plugins are invoked via Python `subprocess` with read-only flags. No plugin writes to or modifies the evidence file.
- The MCP server exposes no tool that accepts a write path targeting the evidence image. The only write operation in the entire server is `tool_write_report`, which writes exclusively to the `exports/` directory — a path entirely separate from the evidence.
- Volatility 3 itself operates in read-only mode by design: it maps the memory image into memory for parsing but does not write back to the source file.

**Prompt layer (CLAUDE.md):**
- `CLAUDE.md` explicitly declares: `Evidence Mode: Strict read-only (chain of custody)`.
- The agent is strictly forbidden from executing raw `vol.py` commands directly via the terminal. All Volatility access is mediated through the MCP server's typed Python functions.
- The agent is forbidden from using BashTool, GrepTool, or any built-in CLI skill that could provide a bypass pathway to the evidence file.

---

## 2. What Happens if the Agent Attempts to Bypass These Protections

**If the agent attempts raw bash execution:**
The CLAUDE.md `NO RAW BASH` guardrail explicitly prohibits this. The system prompt instruction reads: *"You are strictly forbidden from running raw `vol.py` commands in the terminal."* Claude Code enforces this via the agent's own system prompt — it will refuse to call BashTool or equivalent when this guardrail is active.

**If a tool returns unexpected output:**
The MCP server catches all subprocess exceptions and returns a structured error string rather than raw stderr. The agent receives a clean error state and applies the Empty Data Protocol — it cannot be confused into writing to the evidence path by a malformed tool response.

**If the agent hallucinates a write command:**
The MCP server exposes exactly six tools. None of them accept an evidence file path as a write target. There is no tool the agent can call that would modify the source image — the API simply does not expose that capability.

---

## 3. Chain of Custody Statement

All three evidence images were analyzed in read-only mode throughout every investigation. No tool call in any phase (1–5) writes to or modifies the source memory image. The `tool_write_report` output is written to `exports/` with a timestamp prefix, ensuring each investigation produces a distinct, non-overwriting artifact. The original evidence files remain byte-for-byte identical to their state at acquisition.
