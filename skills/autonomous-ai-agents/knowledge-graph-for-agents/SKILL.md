---
name: knowledge-graph-for-agents
description: "Build and operate a shared knowledge graph (Memgraph/Neo4j-style) that multiple AI agents (Hermes, Claude Code, OpenClaw) can read/write so they share context without manual handoff prompts."
version: 1.0.0
author: Hermes / Hasami
platforms: [linux]
metadata:
  hermes:
    tags: [multi-agent, knowledge-graph, memgraph, context-sharing, openclaw, claude-code]
    related_skills: [hermes-agent, claude-code]
---

# Knowledge Graph for Multi-Agent Context

Use a lightweight graph database as the shared memory layer between AI agents
working on the same project. Notion stays the human dashboard; the graph is the
agent reasoning layer.

## When to use this

- Two or more agents (Hermes, Claude Code, OpenClaw/Hasami, subagents) need to
  see the same evolving project state.
- The user is tired of re-explaining "what's going on with candidate X" or
  "what did we decide yesterday."
- You want chat updates from one agent to automatically inform another agent
  later.
- Operational data (candidates, orders, clients) lives in Notion/Airtable but
  the *relationships, decisions, blockers, and session notes* need a queryable
  graph.

## What NOT to use this for

- Replacing a structured operational dashboard (Notion) — mirror key entities,
  don't move the UI.
- Long-term durable archives — keep those in git + Notion; the graph is for
  active context.
- Heavy vector/semantic search at scale — add that later if the graph grows.

## Tooling choice

**Memgraph** (preferred on a VPS):
- Single-node Docker image is free and fast.
- Cypher query language; Bolt protocol; Python driver `pymgclient`.
- Authentication (users/passwords) requires an **enterprise license** — the
  free image has no native auth.
- Therefore: bind to `127.0.0.1` only and rely on host-level access control.

**Neo4j** (alternative):
- Community edition has user/password auth built-in.
- Slightly heavier image, more docs, easier for other agents to understand.
- Use if you need remote access or multi-user isolation.

## Quick start

```bash
# 1. Run Memgraph bound to localhost only
docker run -d --name memgraph-hub \
  -p 127.0.0.1:7687:7687 \
  -p 127.0.0.1:7444:7444 \
  --restart unless-stopped \
  memgraph/memgraph:latest

# 2. Install Python driver in project venv
cd /root/rec-auth-app
python3 -m venv .venv
.venv/bin/pip install pymgclient>=1.5.0

# 3. Add env stubs
# /root/rec-auth-app/.env:
#   MEMGRAPH_HOST=localhost
#   MEMGRAPH_PORT=7687
#   MEMGRAPH_USER=
#   MEMGRAPH_PASSWORD=
```

## Minimal schema

Node labels:
- `Fact {id, type, content, tags, source, created_at}` — unstructured notes,
  decisions, blockers, session summaries.
- `Candidate {id, name, notion_id, stage, summary, updated_at}` — mirrored from
  Notion ATB.
- `Order {id, role, company, notion_id, status, updated_at}` — mirrored from
  Notion OT.
- `Task {id, title, status, owner, notion_id, updated_at}` — action items.
- `Session {id, title, date, source, path}` — project session logs.
- `Tag {name}` — reusable tags.

Relationship types:
- `(Candidate)-[:MATCHES {score, reason}]->(Order)`
- `(Candidate)-[:HAS_TASK]->(Task)`
- `(Task)-[:ABOUT]->(Candidate|Order)`
- `(Fact)-[:ABOUT]->(Candidate|Order|Task)`
- `(Session)-[:MENTIONS]->(Candidate|Order|Task)`
- `(Fact)-[:TAGGED]->(Tag)`

## Reference implementations

- `references/memgraph_hub_impl.md` — Python connector script, `pymgclient`
  pitfalls, and Cypher snippets used in production.
- `references/memgraph_lab_ui_access.md` — how to run Memgraph Lab UI on the
  VPS and access it safely from your local browser.
- `templates/auth_server.py` — bearer-token auth server for Traefik
  ForwardAuth middleware.
- `scripts/deploy_traefik_auth.py` — one-shot token generation + container
  deployment for the auth server.

## Pitfalls

### `pymgclient` is not the same as `mgclient`
- PyPI package is `pymgclient`. It exposes module name `mgclient`.
- Cursor does **not** support `for row in cur:` or `with conn.cursor() as cur:`.
  Use explicit `cur = conn.cursor()` + `cur.fetchone()` + `cur.close()`.

### Cypher regex != Python regex
- Memgraph's `=~` operator does not support Python lookahead/lookbehind or
  zero-width assertions like `(?i)` for case-insensitive matching.
- Build patterns as simple alternation: `".*(?:word1|word2).*"`.
- For case-insensitive substring search, use `toLower(n.name) CONTAINS $term`
  instead of regex — it's simpler and avoids the `(?i)` trap entirely.

### Free Memgraph has no auth
- `CREATE USER` fails with: "Access to advanced authentication features requires
  an enterprise, ai_platform, or oem license."
- Mitigation: bind only to `127.0.0.1`. Do not expose port 7687 to `0.0.0.0`.

### Lists stored as JSON strings
- `pymgclient` does not auto-serialize Python lists. Store list properties as
  `json.dumps(tags)` and parse with `json.loads()` on read. Do not rely on
  `any(tag IN n.tags ...)` unless you convert the string back to a list inside
  Cypher (Memgraph has no built-in JSON parse in free edition).

### Seeding from existing sources
1. Read `project-log/sessions/*.md` and create `Session` nodes.
2. Extract candidate/order names heuristically or from Notion titles.
3. Create `Candidate`/`Order` nodes with Notion page IDs as foreign keys.
4. Link facts/decisions to the entities they mention.
5. Tag everything with `source` and `date`.

## Wiring into OpenClaw / Hasami

Three scripts are built and live at `/root/rec-auth-app/openclaw/scripts/`:

### `memgraph_hub.py` — read/write hub (fact + entity layers)

```bash
# Facts
.venv/bin/python openclaw/scripts/memgraph_hub.py write \
  --type decision --content "Decided to pass on candidate X" --tags "decision" --source hasami
.venv/bin/python openclaw/scripts/memgraph_hub.py query --question "cron delivery"
.venv/bin/python openclaw/scripts/memgraph_hub.py recent --limit 10

# Entities
.venv/bin/python openclaw/scripts/memgraph_hub.py entity upsert \
  --label Candidate --name "Liu Lumeng" --stage "Screening" --summary "N2, waiting on visa"
.venv/bin/python openclaw/scripts/memgraph_hub.py entity query --label Candidate --name "Liu"
.venv/bin/python openclaw/scripts/memgraph_hub.py entity facts --entity-id candidate-liu-lumeng
.venv/bin/python openclaw/scripts/memgraph_hub.py entity link --fact-id "fact-xxx" --entity-id "candidate-liu-lumeng"
.venv/bin/python openclaw/scripts/memgraph_hub.py entity match --candidate-id "..." --order-id "..." --score 8
```

### `seed_notion_entities.py` — one-shot Notion → Memgraph seeder

Pulls every ATB candidate, every OT order, and recent MemoryLog entries into
structured graph nodes with relationships. Re-run to refresh:

```bash
.venv/bin/python openclaw/scripts/seed_notion_entities.py
.venv/bin/python openclaw/scripts/seed_notion_entities.py --dry-run
.venv/bin/python openclaw/scripts/seed_notion_entities.py --memorylog-limit 100
```

### `capture_context.py` — chat update → linked graph fact

Hasami calls this after every status update from Joe. Auto-detects fact type
(decision/blocker/note), finds or creates the entity, writes the fact, links
them via `[:ABOUT]`, and appends to the entity summary:

```bash
.venv/bin/python openclaw/scripts/capture_context.py \
  --subject "Liu Lumeng" --label Candidate \
  --update "COE received, ready to submit" \
  --tags "candidate,visa,update" --source hasami

# Standalone fact (no entity link)
.venv/bin/python openclaw/scripts/capture_context.py \
  --update "All W4 scripts smoke-tested" --tags "w4,milestone" --source hermes
```

### Playbook integration (Phase 4 — next)

1. Create `playbooks/memgraph-context.md` telling Hasami to query Memgraph
   before answering candidate/order questions.
2. Patch `candidate-assessment.md` and `notion-search.md` to add a "check
   Memgraph first" step.
3. Keep Notion as the source of truth for structured recruiting data; use the
   graph for context, relations, and session memory.

## Verification

```bash
cd /root/rec-auth-app
.venv/bin/python openclaw/scripts/memgraph_hub.py write \
  --type note --content "Smoke test from skill" --tags "smoke,skill" \
  --source hermes

.venv/bin/python openclaw/scripts/memgraph_hub.py query --question "smoke test"
```

## Remote access via Traefik reverse proxy (no SSH tunnel)

When the VPS already runs Traefik (e.g. for n8n), use Docker labels to expose
Memgraph services through HTTPS + Let's Encrypt + bearer-token auth. No SSH
tunnel needed — the user opens a URL in their browser.

### Prerequisites

- Traefik running with Docker provider, Let's Encrypt resolver, and host
  network mode (binds ports 80/443).
- A domain or nip.io wildcard DNS pointing at the VPS IP.

### Pattern: Docker labels on the service container

```bash
docker run -d --name memgraph-lab-ui \
  -p 127.0.0.1:3000:3000 \
  -l "traefik.enable=true" \
  -l "traefik.http.routers.memgraph-lab.entrypoints=websecure" \
  -l "traefik.http.routers.memgraph-lab.rule=Host(\`lab.72.62.243.12.nip.io\`)" \
  -l "traefik.http.routers.memgraph-lab.tls.certresolver=letsencrypt" \
  -l "traefik.http.routers.memgraph-lab.middlewares=auth@docker" \
  -l "traefik.http.services.memgraph-lab.loadbalancer.server.port=3000" \
  memgraph/lab:latest
```

Same pattern works for the MCP server (port 8000) and any other backend.

### Auth for exposed services

Free Memgraph has no auth, so anything Traefik exposes must be protected.
Prefer **Traefik's native `basicAuth` middleware** over a custom ForwardAuth
server — browsers cache Basic credentials per realm reliably, which avoids
re-prompting when the Lab UI frontend makes API calls after the initial page
load.

```bash
# 1. Pick a username (e.g. memgraph) and generate a password
TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "Password: $TOKEN"

# 2. Create htpasswd file
htpasswd -nbB memgraph "$TOKEN" > /docker/traefik/.htpasswd

# 3. Mount htpasswd into Traefik's container and declare the middleware
#    in the Traefik compose file:
#    volumes:
#      - /docker/traefik/.htpasswd:/htpasswd:ro
#    labels on a router:
#      - "traefik.http.routers.<name>.middlewares=auth@docker"
#    labels on the middleware:
#      - "traefik.http.middlewares.auth.basicauth.usersfile=/htpasswd"
#      - "traefik.http.middlewares.auth.basicauth.realm=Memgraph"
```

Then every protected service adds:
`-l "traefik.http.routers.<name>.middlewares=auth@docker"`

**Why not ForwardAuth?** A custom Python auth server works for `curl`/MCP
clients, but browsers do not consistently reuse ForwardAuth credentials for
XHR/fetch requests that happen after the page loads. This causes a second
login prompt inside apps like Memgraph Lab. Native Basic Auth solves this.

### For non-browser clients (MCP, scripts)

Basic Auth works for them too — send `Authorization: Basic <base64>` where
the credentials are `username:password`.

If you prefer a Bearer-token style for machine clients, a custom ForwardAuth
server is fine; just don't use it for browser apps that make follow-up API
calls.

### Verify

```bash
# No token → 401
curl -s -o /dev/null -w "%{http_code}\n" https://lab.72.62.243.12.nip.io/

# With token → 200
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer I0J8GVL24S4YBHvGz4-fK7ndJN9z3hxAx3S0BnED1mA" \
  https://lab.72.62.243.12.nip.io/
```

### claude.ai MCP connector

The MCP server (`memgraph/mcp-memgraph:latest`) exposed through Traefik works
with claude.ai custom connectors. Paste `https://memgraph.<ip>.nip.io/mcp/`
into Settings → Connectors and set the Authorization header with the bearer
token. The MCP server uses streamable-http transport — claude.ai sends proper
headers; raw `curl` without `Accept: text/event-stream` gets a 406, which is
normal.

### When Traefik isn't available

Fall back to the SSH tunnel method in `references/memgraph_lab_ui_access.md`.

## Security

- Never commit graph credentials if you later add them.
- Keep Memgraph containers on `127.0.0.1` — Traefik is the only entry point.
- Always add bearer-token auth when exposing through Traefik. Free Memgraph
  has no native auth; the token is the only gate.
- `MCP_READ_ONLY=true` blocks writes, not reads — without auth, the graph is
  a data leak, not a tamper risk.
- Treat the graph as internal project memory; don't store user PII or secrets
  in nodes unless encrypted.
