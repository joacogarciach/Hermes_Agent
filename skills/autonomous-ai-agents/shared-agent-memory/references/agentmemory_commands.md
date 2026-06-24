# agentmemory copy-paste commands

Run all from `/root/rec-auth-app` using `.venv/bin/python`.

## Health
```bash
.venv/bin/python scripts/agentmemory_hub.py health
```

## Save a memory
```bash
.venv/bin/python scripts/agentmemory_hub.py save \
  --content "FACT HERE" \
  --tags "infra,memory-mesh,w4" \
  --source hermes
```

## Recall
```bash
.venv/bin/python scripts/agentmemory_hub.py recall \
  --query "TOPIC" --limit 5
```

## Send a signal to Claude Code
```bash
.venv/bin/python scripts/agentmemory_hub.py signal-send \
  --to claude-code --from hermes --content "MESSAGE"
```

## Read incoming signals
```bash
.venv/bin/python scripts/agentmemory_hub.py signal-read
```

## Memgraph candidate/order facts
```bash
.venv/bin/python scripts/memgraph_hub.py recent --limit 5
.venv/bin/python scripts/memgraph_hub.py query --question "open ot candidates"
```

Tags to use: `memgraph`, `openclaw`, `w4`, `infra`, `fix`, `decision`, `session`, `notion`.
Always include `--source hermes` or `--source claude-code`.
