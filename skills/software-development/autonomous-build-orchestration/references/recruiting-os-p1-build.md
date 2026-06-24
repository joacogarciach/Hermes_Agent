# Recruiting OS Strategic Plan v2 — P1 build notes

This reference captures the first P1 (Morning Brief MVP) build under Strategic Plan v2: "The Brain".

## Directive load

The start signal referenced:
- `BUILD DIRECTIVE` signal `sig_mqs0xvo9` from claude-code.
- `PLAN_2026-06-24_strategic-plan-v2-the-brain.md` at `/root/rec-auth-app/project-log/`.
- SANDBOX rule: build ONLY in `/root/rec-auth-app-dev1` (branch `dev1`); never commit/push/merge; Claude Code reviews and commits.

## What was already present

The main checkout `/root/rec-auth-app` had a W4 coworker script set in `openclaw/scripts/`:
- `stale_stage_sweep.py` — read-only ATB stale-stage sweep.
- `daily_briefing.py` — morning briefing combining stale sweep, action items, open orders.
- `heartbeat_coworker.py` — cron-style wrapper.
- `health_check.py`, `suggest_candidates.py`, `notion_stage_move.py`, etc.

The dev1 worktree (`/root/rec-auth-app-dev1`) was a clean copy without those scripts and without a populated `.venv`.

## Bootstrap steps

1. Copied `openclaw/`, `scripts/`, `.venv`, `.env`, `.agents.env` from main checkout to dev1 worktree.
2. Rebuilt the dev1 `.venv` because the copied venv pointed to the main checkout's site-packages (`/root/rec-auth-app/.venv/lib/python3.12/site-packages`).
3. Installed `openclaw/requirements.txt` into the new dev1 venv.

## New scripts added in P1-a

- `openclaw/scripts/client_digest.py` — active clients → orders → candidates, stage counts, stale flags.
- `openclaw/scripts/pipeline_report.py` — total/active/stale counts, stage breakdown, top 3 bottlenecks, open orders.
- `openclaw/scripts/smoke_test.py` — dry-run smoke suite over W4 scripts; PASS/FAIL per check.

## Schema details discovered

- ATB DB: `e37f5e41-309d-83ae-960b-01684491b924`
- OT DB: `838f5e41-309d-8330-b074-8179cf9b6684`
- MemoryLog DB: `eb07126f-83f9-402c-baaf-076f67239e9d`
- ATB candidate links to OT via the `OT` relation property.
- OT company is the `Company name` select property.
- OT title is the `Role` title property.
- ATB stage is `Stage` status property.
- ATB title is `Name`.
- `Screened` stage is no longer present in the live data; most new rows are `Lead`.

## Verification results

- `stale_stage_sweep.py --dry-run --json` — 203 candidates, 20 stale (16 Emailed, 2 Sent to client, 1 Client Interview Scheduled, 1 Client Int - Waiting Feedback).
- `daily_briefing.py --dry-run` — 31 open orders, 1 overdue action item.
- `heartbeat_coworker.py --task stale-sweep --notify-telegram` — Telegram delivered, message_id 242.
- `client_digest.py --dry-run` — 203 candidates grouped by 5+ clients, 179 unassigned.
- `pipeline_report.py --dry-run` — 171 active, 20 stale, 31 open orders, top bottleneck = Emailed.
- `smoke_test.py` — 12/12 checks passed.

## Subagent fallback lesson

Claude Code print mode (`claude -p`) hit a session cap mid-task and could not write files in the first attempt. Hermes fell back to direct `write_file`/`patch` tool use to author the scripts, then validated them itself. This confirms the build loop should always have a fallback path when the subagent is unavailable.
