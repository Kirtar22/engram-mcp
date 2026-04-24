# Engram MCP — Execution Log Notes & Token Usage Summary

## 1. Server Rename — Development History

During development, the MCP server was internally named `Valhuntir-Volatility-Engine`.
Upon completion of the full architecture and final branding, it was renamed to
`Engram-MCP-Engine`. Entries in `execution_trace.log` prior to April 23 (late)
reflect the pre-rename server name. The codebase is fully original — the name
change was a development milestone marker, not a codebase change.

The rename is visible in `mcp_server.py` line 29:
```python
mcp = FastMCP("Engram-MCP-Engine")
```

---

## 2. Token Usage by Investigation Session

Claude Code uses prompt caching. Effective input tokens are split across three
fields: `input_tokens` (uncached new content), `cache_creation_input_tokens`
(first-time cache write), and `cache_read_input_tokens` (reused cached context).

The low raw `input_tokens` values confirm the MCP architecture's efficiency —
Volatility's large JSON telemetry payloads were cached on first receipt and
reused across all subsequent turns rather than re-transmitted each time.

The high `cache_read_input_tokens` values reflect the agent re-reading the full
investigation history on every turn to cross-correlate phase findings, trigger
Phase 5 substantiation, maintain the OODA state tracker, attribute cross-host
campaign IOCs, and synthesise the final incident report. The same Phase 1–4
JSON payloads are re-read approximately 15–20 times per session — prompt caching
means each re-read costs a fraction of normal input pricing.

| Session | Target | Output Tokens | Cache Created | Cache Read | Effective Total |
|---------|--------|--------------|---------------|------------|-----------------|
| `c1cf43a2` | target_alpha.img (Apr 18) | 92,374 | 449,132 | 3,678,642 | ~4.2M |
| `687456f3` | target-beta-basedc.img (Apr 23) | 235,042 | 480,788 | 6,049,636 | ~6.8M |
| `858a5132` | target-beta-basedc.img (Apr 23, continuation) | 181,836 | 960,858 | 5,552,808 | ~6.7M |
| `4ed16b55` | unknown_dmp.raw / BlackEnergy (Apr 17) | 116,362 | 337,672 | 3,269,144 | ~3.7M |
| | **Grand Total** | **625,614** | **2,228,450** | **18,550,230** | **~21.4M** |

For full extraction methodology, commands used, and per-field explanations see
`token_usage_methodology.md` in this directory.
