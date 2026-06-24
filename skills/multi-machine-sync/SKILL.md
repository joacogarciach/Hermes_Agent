---
title: Multi-Machine Hermes Sync
description: Sync Hermes config, skills, SOUL.md, cron, and memory across machines using git + AgentMemorySystem.
tags: ["hermes", "sync", "agentmemory", "multi-machine"]
---

# Multi-Machine Hermes Sync

## Two sync layers

| Layer | Syncs | Mechanism |
|---|---|---|
| Git repo (`Hermes_Agent`) | `SOUL.md`, `config.yaml`, `skills/`, `cron/` | GitHub |
| AgentMemorySystem | Learned memories, user profile, signals | HTTPS API on VPS |

## Env vars required on every machine

```bash
export AGENTMEMORY_URL=https://agentmemory-l4ww.srv1743914.hstgr.cloud
export AGENTMEMORY_SECRET=<from VPS .agents.env>
```

## API endpoints

- Health: `GET /agentmemory/health`
- Tool call: `POST /agentmemory/mcp/call` with body `{"name":"memory_save|memory_recall|memory_signal_send|memory_signal_read","arguments":{}}`
- Auth: `Authorization: Bearer $AGENTMEMORY_SECRET`

## Adding a new machine

1. Clone repo: `git clone https://github.com/joacogarciach/Hermes_Agent.git`
2. Set `HERMES_HOME=~/Hermes_Agent`
3. Set `AGENTMEMORY_URL` and `AGENTMEMORY_SECRET`
4. Run `bash setup-macbook-pro.sh` (or adapt for the machine name)

## Updating shared config

```bash
cd ~/Hermes_Agent
git pull
```

## Saving machine-specific facts

Use tags that include the machine name, e.g. `macbook-pro`, `macbook-air`, `vps-cloud`.
