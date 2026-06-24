# Memgraph shared knowledge hub — recruiting OS

Small Memgraph graph database running on the VPS so Hermes and Claude Code share
project/dev knowledge without copy-paste handoff prompts.

## Container

Already running on the VPS:

```bash
docker run -d --name memgraph-hub -p 7687:7687 -p 7444:7444 --restart unless-stopped memgraph/memgraph:latest
```

Check status:

```bash
docker ps | grep memgraph-hub
```

## Connector script

`/root/rec-auth-app/openclaw/scripts/memgraph_hub.py`

```bash
cd /root/rec-auth-app
.venv/bin/python openclaw/scripts/memgraph_hub.py write \
  --type session \
  --content "Fixed cron delivery channel." \
  --tags "w4,cron" \
  --source claude

.venv/bin/python openclaw/scripts/memgraph_hub.py query \
  --question "cron delivery"

.venv/bin/python openclaw/scripts/memgraph_hub.py recent --limit 10
```

`--type` choices: `session`, `decision`, `blocker`, `note`.

## Python dependency

Added to `openclaw/requirements.txt`:

```
pymgclient>=1.5.0
```

Installed in the repo venv at `/root/rec-auth-app/.venv`.

## Env vars

Stubs in `/root/rec-auth-app/.env`:

```
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_USER=
MEMGRAPH_PASSWORD=*** uses the env from `/root/rec-auth-app/.env` and falls back to
`/docker/openclaw-xr8h/.env`.

## pymgclient quirks discovered

1. **Import name**: the package is `pymgclient` but the module to import is
   `mgclient`, i.e. `import mgclient`.
2. **Cursor is not iterable**: use `cur.fetchone()` in a loop, not `for row in cur`.
3. **Cursor is not a context manager**: do not use `with conn.cursor() as cur`.
   Create the cursor, use it, close it in a `finally` block.
4. **Regex limitations**: Memgraph v3 `=~` regex does not support `(?i)` or
   other PCRE zero-width assertions. Build patterns like `.*(?:word1|word2).*`.
5. **No APOC by default**: base image does not ship `apoc`. Avoid
   `apoc.convert.fromJsonList`; instead store tags as JSON string and parse in
   Python after retrieval.

## Schema

- `(Fact {id, type, content, tags, source, created_at})`
- `(Tag {name})`
- `(Fact)-[:TAGGED]->(Tag)`
- `(Fact)-[:RELATED_TO]->(Fact)`

Uniqueness constraint on `Fact.id`.

## What goes here vs Notion

- **Memgraph**: session notes, decisions, blockers, open items — the shared
  agent memory that changes every session.
- **Notion**: ATB candidates, OT job orders, client dashboard — the human
  operational interface.

## Project log note

See `/root/rec-auth-app/project-log/memgraph_hub_setup.md` for the canonical
session note that introduced this hub.
