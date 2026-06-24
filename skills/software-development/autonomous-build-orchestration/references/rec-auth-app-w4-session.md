# Worked example: autonomous W4 build session

This is the reference trace from the session that produced the skill.

## User signals that triggered this skill

- "how to make hermes not ask me for permissions" → set approvals.mode off
- "just do all building tasks" → autonomous build loop
- "make my automation a cutting edge solution" → aim high but stay safe
- "please do proper git branch management dont commit without my permission" → no commits without explicit ok
- "for deleting... jus list the deletion changes and i will do them tomorrow" → destructive ops deferred
- "interact with claude and you 2 work together" → subagent-heavy mode

## What was built

1. **Feature branch** `feat/w4-automation` off `dev`.
2. **OpenClaw secrets lockdown** (`openclaw/scripts/lockdown_openclaw_secrets.py`):
   - `--check` found 7 plaintext secret paths in live openclaw.json.
   - `--generate-template` created env-driven template + example env.
   - `--generate-injector` created script to rebuild live config from env.
   - Live file permissions not yet hardened (destructive, deferred).
3. **Model/doc drift fix** (`openclaw/scripts/fix_memory_drift.py`):
   - Updated MEMORY.md to canonical model split (Sonnet interactive, GLM heartbeat, Kimi workers).
   - Repo mirror created; live file not overwritten (destructive, deferred).
4. **Stale-stage sweep automation** (`openclaw/scripts/stale_stage_sweep.py`):
   - Read-only Notion query over ATB.
   - Flags Emailed>3d, Sent to client>5d, Client Interview Scheduled>5d, Waiting Feedback>5d.
   - Drafts and optionally sends Telegram nudge.
5. **Heartbeat wrapper** (`openclaw/scripts/heartbeat_coworker.py`) + cron job at 09:00 daily.
6. **Extension roadmap** (`openclaw/docs/w4_extensions_roadmap.md`).

## Verification

- All scripts compiled and dry-ran successfully.
- Stale sweep found 20 real stale candidates in live Notion.
- Telegram test sent successfully (message_id 200).
- Cron job created but gateway not running — noted for user.

## Destructive/gated items deferred

- Apply `0600` to live `/docker/openclaw-xr8h/data/.openclaw/openclaw.json`.
- Overwrite live OpenClaw `MEMORY.md`.
- Boehnert duplicate cleanup in Notion.
- Restart OpenClaw container.
- Commit/merge the feature branch.

## Key technique: safe subagent + host executor split

The user environment has:
- **OpenClaw container** with an autonomous brain but no host shell access.
- **Hermes/Claude Code on host** with full repo + docker + n8n access.

The winning pattern was: host-side scripts use direct Notion/R2/Telegram APIs,
OpenClaw only consumes results. This keeps the expensive/dangerous runtime
accessible to the trusted host agent while the chat brain stays conversational.
