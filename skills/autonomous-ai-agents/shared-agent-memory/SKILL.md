---
name: shared-agent-memory
title: Shared Agent Memory Mesh
version: 1.0
description: Wire multiple VPS agents (Hermes, Claude Code, etc.) into the same agentmemory brain and Memgraph domain graph so they read, write, and signal the same shared state.
triggers:
  - User wants two or more agents to share memory or reach the same data
  - Setting up agentmemory or Memgraph integration for a new agent peer
  - Cross-agent signals or "tell Claude/Hermes about X" requests
  - Verifying an agent can read/write the shared brain
related_skills:
  - agent-shared-knowledge-graph
  - knowledge-graph-for-agents
  - hermes-agent
---

# Shared Agent Memory Mesh

This skill governs connecting an agent to the shared memory systems on the VPS:

- **agentmemory** — agent process memory (sessions, decisions, fixes, lessons, cross-agent signals).
- **Memgraph** — recruiting domain graph (candidates, orders, facts; see `agent-shared-knowledge-graph`).

Both systems live under `/root/rec-auth-app`. Hermes and Claude Code are full peers.

## Files and paths

| Thing | Path |
|---|---|
| Canonical client | `/root/rec-auth-app/scripts/agentmemory_hub.py` |
| Legacy duplicate | `/root/rec-auth-app/openclaw/scripts/agentmemory_hub.py` (may exist; prefer canonical) |
| Config | `/root/rec-auth-app/.agents.env` (`AGENTMEMORY_URL`, `AGENTMEMORY_SECRET`) |
| Interpreter | `.venv/bin/python` (system python lacks `mgclient`) |
| OpenClaw brain file | `/docker/openclaw-xr8h/data/.openclaw/workspace/MEMORY.md` |

## Wire-in checklist

1. **Health check**
   ```bash
   cd /root/rec-auth-app && .venv/bin/python scripts/agentmemory_hub.py health
   ```
   Expected: `{"http_status": 200, "status": "healthy"}`

2. **Read incoming signals**
   ```bash
   cd /root/rec-auth-app && .venv/bin/python scripts/agentmemory_hub.py signal-read
   ```

3. **Smoke test write + read**
   ```bash
   cd /root/rec-auth-app
   .venv/bin/python scripts/agentmemory_hub.py save \
     --content "<agent> wired into agentmemory mesh." \
     --tags "infra,memory-mesh" --source <hermes|claude-code>
   .venv/bin/python scripts/agentmemory_hub.py recall \
     --query "<agent> wired" --limit 2
   ```

4. **Update the agent's own brain file**
   - For OpenClaw/Hasami: append a short recall-first rule to `/docker/openclaw-xr8h/data/.openclaw/workspace/MEMORY.md`.
   - Back up the file first.
   - Rule should name exact commands and `--source <agent>`.

5. **Notify the peer agent**
   ```bash
   cd /root/rec-auth-app
   .venv/bin/python scripts/agentmemory_hub.py signal-send \
     --to claude-code --from hermes --content "..."
   ```

## Conventions

- **Recall before acting**, save after meaningful work.
- Use `--source hermes` or `--source claude-code` on every save.
- Common tags: `memgraph`, `openclaw`, `w4`, `infra`, `fix`, `decision`, `session`, `notion`.
- For Memgraph candidate/order facts, use `scripts/memgraph_hub.py`.

## Pitfalls

- **`signal-read` and `signal-send` require `agentId`.** If the hub script fails with `agentId is required`, patch the internal call to pass `"agentId": sender`. See `references/agentmemory_signal_api_fix.md`.
- **Use `.venv/bin/python`, never bare `python3`.** System python lacks `mgclient` and other project deps; bare invocation causes false negatives.
- **Do not edit `.agents.env` or change the secret.** It is shared and gitignored.
- **Never run bulk/governance deletes** on agentmemory, Memgraph, or Notion without explicit user approval. There is no per-user auth; one bad bulk write corrupts everything.
- **Back up OpenClaw brain files** (`MEMORY.md`, `USER.md`) before editing.

## When this skill does NOT apply

- Setting up the agentmemory daemon itself (server install) — use upstream docs or `hermes-agent`.
- Memgraph query/schema design for recruiting data — use `agent-shared-knowledge-graph`.
- Hermes CLI/config changes — use `hermes-agent`.

## References

- `references/agentmemory_commands.md` — copy-paste command cheat sheet
- `references/agentmemory_signal_api_fix.md` — why `agentId` is needed and the patch
