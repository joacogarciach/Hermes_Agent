#!/usr/bin/env bash
set -e

# ═══════════════════════════════════════════════════════════════════════════════
# HERMES MULTI-MACHINE SETUP — MacBook Pro
# Run this entire script in your terminal (not inside Hermes chat)
# ═══════════════════════════════════════════════════════════════════════════════

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     HERMES MULTI-MACHINE SETUP — MacBook Pro                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ─── Step 1: Collect secrets interactively ────────────────────────────────────
echo "━━━ Step 1/6: AgentMemorySystem credentials ───"

# Default URL is fixed; only the secret changes per user.
AGENTMEMORY_URL="${AGENTMEMORY_URL:-https://agentmemory-l4ww.srv1743914.hstgr.cloud}"

if [ -z "$AGENTMEMORY_SECRET" ]; then
  echo "Paste your AGENTMEMORY_SECRET from the VPS .agents.env file:"
  # Read without echoing so it doesn't get logged or redacted in copy-paste
  read -rs AGENTMEMORY_SECRET
  echo ""
else
  echo "  Using AGENTMEMORY_SECRET from environment."
fi

if [ -z "$AGENTMEMORY_SECRET" ]; then
  echo "  ❌ AGENTMEMORY_SECRET is required. Exiting."
  exit 1
fi

# Make permanent in ~/.zshrc (idempotent)
if ! grep -q "AGENTMEMORY_SECRET=" ~/.zshrc 2>/dev/null; then
  echo "export AGENTMEMORY_SECRET=\"$AGENTMEMORY_SECRET\"" >> ~/.zshrc
  echo "  ✅ AGENTMEMORY_SECRET saved to ~/.zshrc"
else
  echo "  ⚠️  AGENTMEMORY_SECRET already in ~/.zshrc; leaving it untouched."
  echo "      If the value changed, edit ~/.zshrc manually."
fi

if ! grep -q "AGENTMEMORY_URL=" ~/.zshrc 2>/dev/null; then
  echo "export AGENTMEMORY_URL=\"$AGENTMEMORY_URL\"" >> ~/.zshrc
  echo "  ✅ AGENTMEMORY_URL saved to ~/.zshrc"
else
  echo "  ⚠️  AGENTMEMORY_URL already in ~/.zshrc; leaving it untouched."
fi
echo ""

# ─── Step 2: Test connection ─────────────────────────────────────────────────
echo "━━━ Step 2/6: Testing AgentMemorySystem connection ───"

HEALTH=$(curl -s -H "Authorization: Bearer $AGENTMEMORY_SECRET" "$AGENTMEMORY_URL/agentmemory/health")
STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null || echo "?")

if [ "$STATUS" = "healthy" ]; then
  echo "  ✅ Connection OK — Status: $STATUS"
else
  echo "  ❌ Connection failed. Response:"
  echo "$HEALTH"
  exit 1
fi
echo ""

# ─── Step 3: Pull existing memories ──────────────────────────────────────────
echo "━━━ Step 3/6: Pulling existing shared memories ───"

MEMORIES=$(curl -s -X POST \
  -H "Authorization: Bearer $AGENTMEMORY_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name":"memory_recall","arguments":{"query":"Hermes config skills memory recruiting","limit":20}}' \
  "$AGENTMEMORY_URL/agentmemory/mcp/call")

python3 - "$MEMORIES" <<'PY' 2>/dev/null || echo "  ⚠️  Could not parse memories (might be empty)"
import sys, json
try:
    data = json.load(sys.stdin)
    text = data.get("content", [{}])[0].get("text", "{}")
    payload = json.loads(text)
    items = payload.get("results", [])
    print(f"  Found {len(items)} memories in shared store:")
    for r in items:
        obs = r.get("observation", {})
        cid = obs.get("id", "?")
        content = obs.get("narrative", obs.get("content", ""))[:100]
        tags = obs.get("tags", obs.get("concepts", []))
        print(f"    [{cid}] {content}")
        if tags:
            print(f"           tags: {tags}")
except Exception as e:
    print(f"  Parse error: {e}")
PY
echo ""

# ─── Step 4: Save this machine's memory ──────────────────────────────────────
echo "━━━ Step 4/6: Saving this machine's context to shared store ───"

# Save user profile
RESP=$(curl -s -X POST \
  -H "Authorization: Bearer $AGENTMEMORY_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name":"memory_save","arguments":{"content":"User runs Hermes on MacBook Pro. Uses AgentMemorySystem for cross-machine memory sync. Git repo at github.com/joacogarciach/Hermes_Agent for shared config/skills/SOUL.md/cron. Secrets stay local. Uses DeepSeek model on this machine.","tags":["hermes","user-profile","macbook-pro","multi-machine","deepseek"]}}' \
  "$AGENTMEMORY_URL/agentmemory/mcp/call")

if echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success',False))" 2>/dev/null | grep -q "True"; then
  echo "  ✅ User profile saved"
else
  echo "  ❌ Failed to save user profile"
  echo "$RESP"
fi
echo ""

# ─── Step 5: Ensure the multi-machine-sync skill exists in repo ───────────────
echo "━━━ Step 5/6: Ensuring shared skill is in Hermes_Agent repo ───"

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)/skills/multi-machine-sync"
mkdir -p "$SKILL_DIR"

if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
cat > "$SKILL_DIR/SKILL.md" <<'MD'
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
MD
  echo "  ✅ Created skills/multi-machine-sync/SKILL.md"
else
  echo "  ⚠️  skills/multi-machine-sync/SKILL.md already exists"
fi

# Try to commit + push if inside a git repo
if [ -d "$(cd "$(dirname "$0")" && pwd)/.git" ]; then
  cd "$(dirname "$0")"
  git add skills/multi-machine-sync/SKILL.md setup-macbook-pro.sh 2>/dev/null || true
  if ! git diff --cached --quiet; then
    git commit -m "Add multi-machine sync skill + interactive setup script" || true
    git push || echo "  ⚠️  Push failed — commit locally and push manually."
    echo "  ✅ Pushed to GitHub"
  else
    echo "  ⚠️  No changes to commit"
  fi
else
  echo "  ⚠️  Not a git repo — skill created but not pushed"
fi
echo ""

# ─── Step 6: Final verification ──────────────────────────────────────────────
echo "━━━ Step 6/6: Final verification ───"
echo "  • AGENTMEMORY_URL:  $AGENTMEMORY_URL"
echo "  • AGENTMEMORY_SECRET: ${AGENTMEMORY_SECRET:0:8}... (hidden)"
echo "  • HERMES_HOME:        $(cd "$(dirname "$0")" && pwd)"
echo ""
echo "Next steps:"
echo "  1. Run: source ~/.zshrc"
echo "  2. Verify: echo \$AGENTMEMORY_SECRET"
echo "  3. Start Hermes with HERMES_HOME=$(cd "$(dirname "$0")" && pwd)"
echo ""
echo "🎉 Setup complete."
