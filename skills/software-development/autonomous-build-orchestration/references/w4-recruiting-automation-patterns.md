# W4 recruiting automation patterns

Session-specific reference for the Job Impulse Japan recruiting OS.

## Verified IDs and names (do not guess)

- ATB database ID: `e37f5e41-309d-83ae-960b-01684491b924`
- OT database ID: `838f5e41-309d-8330-b074-8179cf9b6684`
- MemoryLog database ID: `eb07126f-83f9-402c-baaf-076f67239e9d`
- R2 bucket: `rec-cv-store`
- Live OpenClaw: `/docker/openclaw-xr8h/data/.openclaw/openclaw.json`
- Live OpenClaw memory: `/docker/openclaw-xr8h/data/.openclaw/workspace/MEMORY.md`
- Telegram bot: `@HasamiBotBot`

## Notion API gotchas

- OT database has **no `Name` title property**. The visible title is the
  property named `Role`, with `type: title` and `id: title`. Filter with
  `{"property": "Role", "rich_text": {"contains": "..."}}` is wrong — use
  `{"property": "Role", "title": {"contains": "..."}}` if filtering by title.
  In practice, fetch all and filter client-side for small DBs.
- `Status` properties are of type `status`, not `select`. Use
  `props.get("Status", {}).get("status", {}).get("name")`.
- `select` properties can be `None` if unset; guard with
  `(props.get("X", {}).get("select") or {}).get("name", "—")`.

## R2 CV archive format

W2 writes CV locations into ATB page body blocks as:

```
📁 <filename> — R2: archive/<slug>_<date>_<pageid>/<filename.pdf>
```

Object keys contain spaces; regex must be `R2:\s*(archive/.+?\.pdf)`.

## Host vs OpenClaw split

- OpenClaw runs in its own container and cannot shell out to the host.
- Hermes gateway runs on the host and can execute repo Python scripts.
- The cron path is: Hermes gateway → `heartbeat_coworker.py` → direct APIs →
  Telegram. This is reliable and version-controlled.
- A future OpenClaw-native heartbeat would require rewriting logic as an
  OpenClaw playbook using its Notion skill; defer until GLM-5.2 reliability is
  proven.

## Hermes gateway installation in LXC

`hermes gateway install --system` refuses root by default. In containers use:

```bash
yes | hermes gateway install --system --run-as-user root
```

After install, `hermes gateway status --system` and `hermes cron status`
verify it is firing.

## Destructive application order for OpenClaw

1. Back up live files with timestamped names.
2. `chmod 0600 openclaw.json`
3. Overwrite `workspace/MEMORY.md` with repo-fixed version.
4. `docker compose restart openclaw` inside `/docker/openclaw-xr8h`.
5. Verify with `docker ps`, `docker logs`, and a Telegram test if needed.
