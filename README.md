# Hermes_Agent

Portable Hermes configuration + skills + SOUL + cron.  
This repo syncs the Hermes setup across machines. **Secrets are excluded** — each machine adds its own local `.env` / API keys.

## What's in this repo

| Path | Purpose |
|---|---|
| `SOUL.md` | Hermes persona / identity |
| `config.yaml` | Portable Hermes config (providers, models, tools, toolsets, etc.) |
| `skills/` | Custom + bundled Hermes skills |
| `cron/` | Scheduled jobs |

## How to use on a new machine

1. Clone this repo:
   ```bash
   git clone git@github.com:joacogarciach/Hermes_Agent.git
   # or
   git clone https://github.com/joacogarciach/Hermes_Agent.git
   ```

2. Point Hermes at it:
   ```bash
   export HERMES_HOME=/path/to/Hermes_Agent
   # or make it permanent in ~/.bashrc / ~/.zshrc
   ```

3. Add local secrets only (never commit):
   - create a `.env` or use your local secret manager
   - fill API keys for the providers you use

4. Sync updates:
   ```bash
   git pull
   ```

## AgentMemorySystem sync

This repo only covers portable config/skills/SOUL/cron.  
Learned memory (`MEMORY.md`, `USER.md`, session facts) syncs through the shared **AgentMemorySystem** on the VPS. Each machine's Hermes connects to the same hub.

## Machines using this repo

- VPS Cloud Hermes (this one — initial pusher)
- MacBook (this) — clone + set HERMES_HOME
- MacBook (other) — clone + set HERMES_HOME
