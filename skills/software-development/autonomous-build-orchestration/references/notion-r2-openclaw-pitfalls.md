# Notion, R2, and OpenClaw pitfalls from W4 build sessions

Condensed gotchas discovered while wiring host-side automation to the
Job Impulse Japan recruiting OS.

## Notion property names vs display names

- **OT database title property is named `Role` internally**, even though the UI
  may label it "Role title". Its `type` is `title` and its `id` is `title`.
  Filtering must use `{"property": "Role", "title": {"contains": "..."}}` or
  `{"property": "Role", "rich_text": {"contains": "..."}}` depending on Notion
  version. If Notion rejects the filter with "Could not find property", try
  fetching the DB schema to confirm the real property name.
- **Status properties are type `status`**, not `select`. Read the current value
  with `props.get("Stage", {}).get("status", {}).get("name")`.
- **Select/status properties may be `None` when unset.** Guard with:
  ```python
  (props.get("Priority", {}).get("select") or {}).get("name", "—")
  ```

## R2 CV archive parsing

W2 writes CV locations into ATB page body blocks as:

```
📁 <filename> — R2: archive/<slug>_<date>_<pageid>/<filename.pdf>
```

Object keys can contain spaces. The safe regex is:

```python
R2_KEY_RE = re.compile(r"R2:\s*(archive/.+?\.pdf)", re.IGNORECASE)
```

`[^\s]+` will fail because of spaces in the PDF filename.

## Model endpoint fallback order

When building on-demand re-assessment scripts, do not assume local Ollama is
reachable from the host. In this environment:

- Ollama/GLM/Kimi are available only inside the OpenClaw container or via its
  gateway, not on `localhost:11434` from the host.
- Gemini Flash may rate-limit (`429`) under burst.
- Anthropic keys in `.env` may be unauthorized (`401`) if they belong to a
  different project.

Reliable pattern: try the cheapest configured external key first, fail fast,
and surface the error clearly. For production, route through the OpenClaw
gateway's model endpoint rather than hand-rolling API calls.

## Hermes gateway in LXC / root-only containers

`hermes gateway install --system` refuses root. In containers:

```bash
yes | hermes gateway install --system --run-as-user root
```

After install, verify with:

```bash
hermes gateway status --system
hermes cron status
```

Gateway must be running for cron jobs to fire automatically.

## OpenClaw restart verification

After mutating live config or memory:

1. `docker compose restart openclaw` from `/docker/openclaw-xr8h`.
2. `docker ps --filter name=openclaw --format "{{.Names}}:{{.Status}}"`
3. `docker logs --tail 20 openclaw-xr8h-openclaw-1` — look for `[gateway] ready`
   and `[telegram] starting provider (@HasamiBotBot)`.

No need to manually test Telegram if the provider started cleanly, but a single
`stale_stage_sweep.py --notify-telegram` run is a good end-to-end smoke test.
