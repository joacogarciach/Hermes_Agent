---
name: agent-shared-knowledge-graph
description: "Use a graph database (Memgraph) as shared memory between multiple AI agents on a VPS. Write session notes, decisions, blockers; query cross-agent project state without handoff prompts."
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [memgraph, graph-database, shared-memory, multi-agent, agent-knowledge, vps]
    related_skills: [recruiting-notion-ops]
---

# Agent Shared Knowledge Graph

Use a lightweight graph database (Memgraph) running on the VPS as a shared memory
layer between Hermes, Claude Code, and any other agents. Notion/ATB/OT stay the
human dashboard; this graph is for agent-to-agent project/dev notes.

## When to use

- You are running multiple agents on the same VPS and need them to see the same
  project state without manual copy-paste handoffs.
- You want durable, queryable notes for: session summaries, decisions, blockers,
  open items, debug paths, tool/provider quirks.
- You are working on a long-running project where one session's context must
  survive to the next agent session.

## When NOT to use

- Do not replace operational systems of record (Notion, CRM, ATS) with this hub.
  Mirror or summarize into the graph; keep the authoritative data where it
  already lives.
- Do not store secrets in the graph. Memgraph single-node has no auth by default
  (binds to localhost unless you configure otherwise).

## Quick start

### 1. Start Memgraph

For a safe, localhost-only instance (recommended for agent shared memory):

```bash
docker run -d --name memgraph-hub \
  -p 127.0.0.1:7687:7687 -p 127.0.0.1:7444:7444 \
  --restart unless-stopped \
  memgraph/memgraph:latest
```

### 2. Start Memgraph Lab UI (optional but useful)

The `memgraph/memgraph` image does **not** include the web UI. Run Lab separately:

```bash
docker run -d --name memgraph-lab-ui \
  --network host \
  --restart unless-stopped \
  memgraph/lab:latest
```

### 3. Expose Lab through Nginx with basic auth (optional)

If you want browser access from outside the VPS without opening Memgraph itself,
proxy Lab through Nginx with basic auth. See `references/memgraph-lab-ui-setup.md`
for the full recipe, including WebSocket upgrade headers and self-signed SSL.

### 4. Install Python client

The package is `pymgclient` but the import name is `mgclient`:

```bash
python3 -m venv .venv
.venv/bin/pip install pymgclient
.venv/bin/python -c "import mgclient; print('ok')"
```

### 3. Write and query

See the connector template at `templates/memgraph_hub.py`. Run it:

```bash
.venv/bin/python memgraph_hub.py write \
  --type session \
  --content "Set up shared knowledge graph." \
  --tags "memgraph,setup" \
  --source hermes

.venv/bin/python memgraph_hub.py query --question "memgraph setup"
.venv/bin/python memgraph_hub.py recent --limit 10
```

## Connector design

- Load env from `MEMGRAPH_HOST`, `MEMGRAPH_PORT`, `MEMGRAPH_USER`,
  `MEMGRAPH_PASSWORD` (defaults: localhost, 7687, no auth).
- Fact nodes: `(Fact {id, type, content, tags, source, created_at})`.
- Tag nodes: `(Tag {name})` linked via `[:TAGGED]`.
- Optional relations between facts via `[:RELATED_TO]` when `--related` ids are
  supplied.
- Uniqueness constraint on `Fact.id`.

## pymgclient / Memgraph v3 quirks

Captured from real setup work. Read these before debugging:

1. **Import name mismatch**: pip package `pymgclient`, import `mgclient`.
2. **Cursor not iterable**: use `cur.fetchone()` loop, not `for row in cur`.
3. **Cursor not a context manager**: open/close explicitly with try/finally.
4. **Regex limitations**: `=~` does not support `(?i)` or zero-width
   assertions. Build case-insensitive-ish patterns as `.*(?:word1|word2).*`.
5. **No APOC in base image**: do not rely on `apoc.convert.fromJsonList`.
   Store JSON arrays as strings and parse in Python.

## Cost

Memgraph single-node self-hosted is free. Enterprise features (multi-user RBAC,
high availability) are not needed for this pattern.

## Templates and references

- `templates/memgraph_hub.py` — drop-in connector script with write/query/recent.
- `references/memgraph-quirks.md` — condensed debugging notes.
- `references/memgraph-lab-ui-setup.md` — how to expose Memgraph Lab through Nginx with basic auth.
- `references/project-example.md` — how this was wired for Job Impulse Japan K.K.

## Security

- Keep Memgraph bound to localhost unless you add real auth/network controls.
  The free single-node image does **not** support username/password auth
  (enterprise-only). Localhost binding is the practical security control.
- Never write API keys, tokens, or passwords into graph facts.
- If you need browser access to Memgraph Lab, proxy it through Nginx with basic
  auth and keep the upstream Lab bound to localhost. Do not expose port 7444 or
  7687 directly to the internet.
