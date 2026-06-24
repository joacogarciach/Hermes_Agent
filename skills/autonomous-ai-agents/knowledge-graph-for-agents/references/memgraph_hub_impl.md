# Reference: Memgraph Hub Implementation Used in Production

This is the concrete implementation built for Job Impulse Japan K.K.'s
Recruiting OS so Hermes and Claude Code share project context.

## Files created

- `/root/rec-auth-app/openclaw/scripts/memgraph_hub.py` — CLI connector.
- `/root/rec-auth-app/openclaw/requirements.txt` — adds `pymgclient>=1.5.0`.
- `/root/rec-auth-app/.env` — adds `MEMGRAPH_HOST`, `MEMGRAPH_PORT` stubs.
- `/root/rec-auth-app/project-log/memgraph_hub_setup.md` — operational runbook.
- `/root/rec-auth-app/project-log/plan_memgraph_context_layer.md` — roadmap.

## Connector script API

```bash
cd /root/rec-auth-app

.venv/bin/python openclaw/scripts/memgraph_hub.py write \
  --type session --content "Summary of work done." \
  --tags "w4,cron" --source hermes

.venv/bin/python openclaw/scripts/memgraph_hub.py query \
  --question "cron delivery" --limit 10

.venv/bin/python openclaw/scripts/memgraph_hub.py recent \
  --type note --limit 5
```

## Key code patterns

### Connect

```python
import mgclient  # pymgclient exposes this module name

conn = mgclient.connect(host="localhost", port=7687)
conn.autocommit = False
```

### Cursor handling (no context manager, no iteration)

```python
cur = conn.cursor()
try:
    cur.execute("CREATE (n:Fact {id: $id, content: $c})", {"id": "x", "c": "y"})
    conn.commit()
finally:
    cur.close()
```

Reading:

```python
cur = conn.cursor()
try:
    cur.execute("MATCH (n:Fact) RETURN n.id, n.content LIMIT 10")
    rows = []
    while True:
        row = cur.fetchone()
        if row is None:
            break
        rows.append(row)
finally:
    cur.close()
```

### Storing lists

```python
import json
tags = ["w4", "cron"]
cur.execute(
    "CREATE (n:Fact {tags: $tags})",
    {"tags": json.dumps(tags)}
)
# Read back: json.loads(row[0])
```

### Searching without Python regex features

Bad:
```cypher
WHERE n.content =~ '(?i).*(?:cron|delivery).*'
```

Good:
```cypher
WHERE n.content =~ '.*(?:cron|delivery).*'
```

## Memgraph auth limitation

Free single-node Memgraph does **not** support `CREATE USER` / password auth.
Attempting it yields:

> Access to advanced authentication features requires an enterprise, ai_platform, or oem license.

Mitigation used: bind container to `127.0.0.1` only. For browser UI access from
outside the VPS, proxy through Nginx with basic auth.

## Memgraph Lab UI access

The `memgraph/memgraph:latest` image does **not** include a web UI. Memgraph
Lab is a separate image. Run it on localhost only and access it through an SSH
tunnel:

```bash
# On VPS
docker run -d --name memgraph-lab-ui \
  -p 127.0.0.1:3000:3000 \
  --restart unless-stopped \
  memgraph/lab:latest

# On local machine
ssh -L 3000:localhost:3000 -L 7687:localhost:7687 root@YOUR_VPS_IP
```

Open http://localhost:3000. Quick Connect: host `127.0.0.1`, port `7687`, no
SSL, no auth.

**Do not use a public Nginx proxy.** A public endpoint behind basic auth +
self-signed cert, sitting in front of an unauthenticated graph database, was
flagged as a live security liability. Keep Lab and Bolt localhost-only and use
a tunnel or VPN.


## Entity layer (added 2026-06-24)

The hub now supports structured entity nodes beyond the original `(Fact)` layer.

### Entity types

| Label | Key properties | Source |
|---|---|---|
| `Candidate` | `id, name, notion_id, stage, summary, updated_at` | Notion ATB |
| `Order` | `id, role, company, notion_id, status, summary, updated_at` | Notion OT |
| `Task` | `id, title, status, owner, notion_id, summary, updated_at` | Notion Tasks |

### Entity ID convention

Deterministic: `{label.lower()}-{slug(name)}`. Example: `candidate-liu-lumeng`.

### MERGE pattern (upsert)

```python
cur.execute("""
    MERGE (n:Candidate {id: $id})
    ON CREATE SET n.name = $name, n.stage = $stage, n.created_at = $now, n.updated_at = $now
    ON MATCH SET
        n.name = $name,
        n.stage = CASE WHEN $stage <> '' THEN $stage ELSE n.stage END,
        n.updated_at = $now
    RETURN n.id
""", {"id": eid, "name": name, "stage": stage, "now": now})
```

### Case-insensitive search (Memgraph regex doesn't support `(?i)`)

```cypher
MATCH (n:Candidate)
WHERE toLower(n.name) CONTAINS $term
   OR toLower(n.role) CONTAINS $term
RETURN n.id, n.name
```

### Relationship: Fact → Entity

```cypher
MATCH (f:Fact {id: $fact_id}), (e {id: $entity_id})
MERGE (f)-[:ABOUT]->(e)
```

### Relationship: Candidate → Order (match)

```cypher
MATCH (c:Candidate {id: $cid}), (o:Order {id: $oid})
MERGE (c)-[r:MATCHES]->(o)
SET r.score = $score, r.reason = $reason, r.updated_at = $now
```

## Seeding from Notion

`seed_notion_entities.py` pulls ATB, OT, and MemoryLog into structured nodes:

```bash
.venv/bin/python openclaw/scripts/seed_notion_entities.py
.venv/bin/python openclaw/scripts/seed_notion_entities.py --dry-run
```

Notion DB IDs (verified live 2026-06-24):
- ATB: `e37f5e41-309d-83ae-960b-01684491b924`
- OT: `838f5e41-309d-8330-b074-8179cf9b6684`
- MemoryLog: `eb07126f-83f9-402c-baaf-076f67239e9d`

Key Notion property names (Japanese labels preserved):
- ATB: `お名前・Full Name` (rich_text), `Stage` (status), `国籍 / Nationality` (select),
  `在留資格 / Visa Type` (select), `Language` (multi_select), `Seniority` (select),
  `所在地` (select), `職務経験 / Expertise` (rich_text), `OT` (relation)
- OT: `Role` (title), `Company name` (select), `Status` (status), `Priority` (select),
  `Location` (multi_select), `Notes` (rich_text)
- MemoryLog: `Title` (title), `Content` (rich_text), `Date` (date), `Source` (select),
  `Related Candidate` (relation), `Related Order` (relation), `Action Items` (rich_text)

## Chat context capture

`capture_context.py` writes chat updates as linked graph facts:

```bash
.venv/bin/python openclaw/scripts/capture_context.py \
  --subject "Liu Lumeng" --label Candidate \
  --update "COE received, ready to submit" \
  --tags "candidate,visa,update" --source hasami
```

It auto-detects fact type (decision/blocker/note), finds or creates the entity,
writes the fact, links via `[:ABOUT]`, and appends to the entity summary.

## Next extension

Add `playbooks/memgraph-context.md` so Hasami queries Memgraph before answering
candidate/order questions, and calls `capture_context.py` after every status
update from Joe.
