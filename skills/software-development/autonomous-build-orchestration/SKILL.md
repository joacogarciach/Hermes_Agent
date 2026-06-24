---
name: autonomous-build-orchestration
description: "Run long autonomous build sessions with coding subagents (Claude Code, Codex, Kimi) while keeping the user in control of commits, permissions, and destructive operations."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Autonomous-Build, Coding-Agent, Claude-Code, Subagent, Git-Workflow, Safety]
    related_skills: [claude-code, codex, opencode, github-pr-workflow, requesting-code-review]
---

# Autonomous Build Orchestration

Use this skill when the user asks you to **build something autonomously** —
especially when they say things like:

- "build this while I sleep"
- "use Claude at maximum"
- "just do all the building tasks"
- "you two work together"
- "I will commit/merge later"

The goal is to produce real, working artifacts through subagents and direct
tool use, while keeping the human in control of anything that could break
production, delete data, or rewrite shared history.

## Pre-flight checklist

Before starting the build loop:

1. **Recall-first** — query the shared brain (agentmemory / Memgraph) and any project-specific signals before acting. If the user explicitly points to a directive, plan, or sandbox rule, retrieve it and confirm it loaded before writing code.
2. **Read project context files** (`CLAUDE.md`, `AGENTS.md`, `PLAN.md`, etc.).
3. **Check git state** — branch, remotes, recent commits, untracked files. Prefer `git status` + `git log --oneline -5`.
4. **Create a feature branch** from the integration branch (usually `dev`).
   - Never work directly on `main` unless the project explicitly allows it.
   - If the project already has an isolated worktree for autonomous builds, use that worktree and never switch the main checkout's branch.
5. **Initialize a `todo` list** so the user can see progress at a glance.
6. **Set approvals mode** based on user preference:
   - If the user says "don't ask permissions" / "yolo", try `hermes config set approvals.mode off`.
   - If that command fails (missing config/auth), note it and continue in the existing mode; do not block the build.
   - Otherwise, leave it at `smart` or `manual`.
7. **Confirm secrets handling** — check `.env`, credentials, and any existing
   secret-scan githooks. Never commit real secrets.
8. **Inspect live runtime state early** if the task touches a container (OpenClaw, n8n, etc.) — `docker ps`, config path, service status — so later destructive steps are informed.

## Safety defaults (non-negotiable)

Even in YOLO / no-permission mode, these rules stay in effect:

- **No commits, pushes, or merges without explicit user direction.** Build in the feature branch or isolated worktree; stage nothing that the user didn't ask you to commit. If you do commit (e.g., a small docs change the user explicitly ok'd), keep messages conventional and small.
- **No switching the main checkout's branch.** If an isolated worktree exists for autonomous builds, stay inside it; do not alter the main checkout's branch state.
- **No destructive operations without user approval.** `rm -rf`, dropping DBs,
  wiping volumes, deleting live configs, or mass-deleting Notion rows must be
  **listed for the user to approve the next day**, not executed silently.
- **No force-push / history rewrite.**
- **No touching live production runtime** (restarting containers, importing
  workflows, publishing n8n) without explicit go-ahead.
- **Dry-run first** for any automation that touches external state. Prove the
  read-only path works before enabling writes or notifications.

## Build loop

1. **Break the work into modules.** Each module = one script, one config, one
   playbook, or one docs update. Update `todo` as each module completes.
2. **Build repo-side on the host.** If the container (OpenClaw, n8n) has an
   isolated runtime, write host-side scripts that call its APIs/webhooks and
   feed results back to the chat brain. Do not rely on container shell access
   unless it is explicitly exposed and tested.
   - Prefer this when the container's shell/exec tool is broken or when the
     work needs repo-side secrets (`.env`, n8n CLI, docker commands).
   - Use Hermes cron/gateway for scheduled host-side tasks; do not assume a
     container's built-in heartbeat can replace host-level orchestration.
3. **Use subagents for code generation / reasoning-heavy pieces.**
   - Prefer Claude Code print mode (`claude -p ...`) for single-shot tasks.
   - Use tmux for multi-turn interactive Claude sessions.
   - If the subagent usage cap resets, resume where you left off.
   - When delegating in a user-mandated sandbox, pass the exact worktree path,
     tell the subagent to leave all changes **uncommitted**, and explicitly
     forbid commit/push/merge. Verify `git status` shows only uncommitted changes
     when the subagent finishes.
4. **Verify every module** — compile, dry-run, or run against a safe endpoint.
   Favor real API calls to a read-only endpoint over mocked tests when safe.
5. **Write down destructive or gated actions** in the final summary under a
   clearly labeled "NOT DONE — needs your approval" section.
6. **End with a concise status report** — what's built, what's tested, what's
   pending.

## Git pacing

- Branch: `feat/<short-name>` from `dev`.
- Commit only when the user explicitly says to commit, or when the project
  requires small checkpoint commits inside a feature branch.
- Never open PRs or merge without user review.
- If the user said "I will commit later", leave changes unstaged/uncommitted in
  the feature branch.

## When the user says "run it" or "do the destructive part too"

The user may approve destructive work mid-session with phrases like:
- "can we run it then?"
- "a,..... how abt the rrest" (asking for remaining items)

When that happens:

1. **Restate the scope** and ask for explicit "yes" if any item is risky (container restart, live config overwrite, mass data deletion, history rewrite).
2. **Explain trade-offs first if the user asks conceptual questions.** Phrases like "i dont get it what hermes for.." or "isnt it possible to run this with openclaw and not hermess?" mean they want the host-vs-container split, single-vs-dual-scheduler trade-off, and a recommendation *before* more code changes. Give a concise comparison, then ask which path.
3. **Back up live files before mutating them.** Timestamped `.bak-YYYYMMDDhhmmss` copies in the same directory.
4. **Apply changes in dependency order:** permissions → config → container restart → verification.
5. **Verify each step** with a real health check, log tail, or end-to-end dry run.
6. **Do not commit** unless the user explicitly says so, even after destructive work.

## Pitfalls & Gotchas

- **Claude Code print mode (`-p`) is not always available** — it depends on the
  user's plan and subscription state. If `claude -p` exits immediately with
  "You've hit your session limit", the print-mode subagent path is temporarily
  blocked. In that case, fall back to writing the code yourself (Hermes direct
  tool use with `write_file`/`patch`) and continue the build; report the cap
  hit to the user so they can resume with Claude later if desired.
- **Subagents may lose session state across restarts.** Save progress to the
  shared brain (agentmemory / Memgraph) after each completed sub-task so recovery
  is possible.
- **Headless `-p` may fail to write files due to permissions prompts.** If the
  subagent reports it cannot write despite being in an allowed directory, fall
  back to direct tool use rather than retrying permission dialog gymnastics.
- **Interactive mode REQUIRES tmux** — Claude Code is a full TUI app. Using
  `pty=true` alone in Hermes terminal works but tmux gives you `capture-pane`
  for monitoring and `send-keys` for input, which is essential for orchestration.
- **`--dangerously-skip-permissions` dialog defaults to "No, exit"** — you must
  send Down then Enter to accept. Print mode (`-p`) skips this entirely.
- **`--max-turns` is print-mode only** — ignored in interactive sessions.
- **Background tmux sessions persist** — always clean up with
  `tmux kill-session -t <name>` when done.
- **Never trust a subagent's "committed" claim** — verify with `git status` /
  `git log` before telling the user the work is committed.

## End-of-session report shape

```
## Built
- file/path: what it does
- verified: how you tested it

## Scheduled / automated
- cron job X at Y time

## Applied (was deferred)
- live config change X
- container restart Y
- permission change Z

## NOT DONE — needs your approval
- destructive op 1
- destructive op 2
- commit + PR
```

## References

- `references/rec-auth-app-w4-session.md` — worked example from the first
  autonomous W4 build session (secrets lockdown, stale-stage sweep, model
  drift fix, cron scheduling).
- `references/w4-recruiting-automation-patterns.md` — verified IDs, Notion API
  gotchas, R2 CV archive format, host-vs-OpenClaw split, gateway install in
  LXC, and safe destructive-application order for the recruiting OS.
- `references/notion-r2-openclaw-pitfalls.md` — property-name vs display-name
  mismatches, status/select `None` guards, R2 key regex with spaces, model
  endpoint fallback order, and OpenClaw restart verification.
- `references/recruiting-os-p1-build.md` — Strategic Plan v2 P1 Morning Brief
  MVP build: dev1 worktree bootstrap, new digest/report/smoke scripts, and
  subagent-cap fallback.
- `templates/notion-sweep-bot.py` — starter script for read-only Notion sweeps
  with Telegram nudges.
- `scripts/probe_openclaw_config.sh` — verify host access to the live OpenClaw
  config path before any migration.

## User-preference notes

Joe Garcia (Job Impulse Japan) prefers:
- YOLO approvals during autonomous build sessions.
- Destructive work listed for next-day approval by default, but will sometimes
  say "run it" mid-session.
- Literal copy-paste commands and one-question-at-a-time explanations.
- No commits during the build session; he handles merge/PR himself.
- Cutting-edge brainstorming, not just minimal fixes.