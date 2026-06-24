# Real example: Memgraph as shared agent memory

This is how the pattern was wired for Job Impulse Japan K.K. recruiting OS.

## What lives where

- **Notion**: ATB candidates, OT job orders, client dashboard — human interface.
- **Memgraph**: session notes, decisions, blockers, open items — shared agent
  memory between Hermes and Claude Code.

## Files in repo

- `/root/rec-auth-app/openclaw/scripts/memgraph_hub.py` — production connector.
- `/root/rec-auth-app/openclaw/requirements.txt` — adds `pymgclient`.
- `/root/rec-auth-app/project-log/memgraph_hub_setup.md` — canonical project-log
  note.

## Container

```bash
docker run -d --name memgraph-hub \
  -p 7687:7687 -p 7444:7444 \
  --restart unless-stopped \
  memgraph/memgraph:latest
```

## Env

Added to `/root/rec-auth-app/.env`:

```
MEMGRAPH_HOST=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_USER=
MEMGRAPH_PASSWORD=*** command

```bash
cd /root/rec-auth-app
.venv/bin/python openclaw/scripts/memgraph_hub.py write \
  --type session \
  --content "Fixed cron delivery channel." \
  --tags "w4,cron" \
  --source claude
```

Query what the other agent did:

```bash
.venv/bin/python openclaw/scripts/memgraph_hub.py query \
  --question "cron delivery"
```

## Key decision

This hub was created so the user would not need to paste "Claude just did X"
into Hermes (or vice versa). The graph is the shared context.
