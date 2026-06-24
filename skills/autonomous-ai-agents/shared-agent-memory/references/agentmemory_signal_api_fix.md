# agentmemory signal API fix — `agentId is required`

**Error seen:**
```json
{"error": "{\"error\":\"agentId is required\"}"}
```

**Where:** `scripts/agentmemory_hub.py signal-read` and `signal-send`.

**Fix:** The `memory_signal_read` and `memory_signal_send` MCP tools require an `agentId` argument. Patch the hub script internal calls:

```python
elif args.command == "signal-send":
    res = _call("memory_signal_send",
                {"from": args.sender, "to": args.to, "content": args.content,
                 "agentId": args.sender})
elif args.command == "signal-read":
    res = _call("memory_signal_read", {"agentId": "hermes"})
```

**Notes:**
- For `signal-read`, the agent reads its own inbox, so hardcode the local agent name (`hermes` in Hermes's copy, `claude-code` in Claude's copy) or derive it from `getpass.getuser()` / an env var if both agents will use a single canonical script.
- This fix was applied to the canonical `/root/rec-auth-app/scripts/agentmemory_hub.py` on 2026-06-24.
- If the legacy `openclaw/scripts/agentmemory_hub.py` is still in use, apply the same patch there or migrate callers to the canonical path.
