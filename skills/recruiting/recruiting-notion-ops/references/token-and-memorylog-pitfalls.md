# Token + MemoryLog pitfalls — recruiting OS

Live observations from the VPS for Job Impulse Japan K.K.

## Token location (canonical)

The working Notion integration token lives in the OpenClaw container env:

```bash
/docker/openclaw-xr8h/.env
```

Key name: `NOTION_API_TOKEN`.

## If a freshly pasted token returns 401

- Notion returns `401 unauthorized` when the token string is wrong or the integration was deleted/revoked.
- A valid token can still return 404 for one database if the integration is not shared with that database. Both ATB and OT returned 200 here, while MemoryLog returned 404 for the new token because the integration had not been added to MemoryLog.
- Default verification probe (source the env, then run all three):

```bash
source /docker/openclaw-xr8h/.env >/dev/null 2>&1
for db in e37f5e41-309d-83ae-960b-01684491b924 838f5e41-309d-8330-b074-8179cf9b6684 eb07126f-83f9-402c-baaf-076f67239e9d; do
  echo -n "$db: "
  curl -s -o /dev/null -w "%{http_code}" -X POST "https://api.notion.com/v1/databases/$db/query" \
    -H "Authorization: Bearer $NOTION_API_TOKEN" \
    -H "Notion-Version: 2022-06-28" \
    -H "Content-Type: application/json" \
    -d '{"page_size":1}'
  echo
done
```

Expected: `200 200 200`. If any are `401`, the token is bad. If any are `404`, share the integration with that database in Notion UI (`...` → Connect to → integration name).

## MEMORY.md — which copy is live?

There are two copies. Future agents must read the right one.

| Path | What it is |
|---|---|
| `/docker/openclaw-xr8h/data/.openclaw/workspace/MEMORY.md` | **Live OpenClaw memory.** This is what the running OpenClaw brain loads. |
| `/root/rec-auth-app/openclaw/playbooks/MEMORY.md` | Repo snapshot/duplicate. Older or stale relative to the live copy. |

When OpenClaw is restarted or hardened, the repo copy may be copied over the live copy (observed 2026-06-24). Treat the container path as the source of truth for runtime behavior.

## Logging a long status snapshot to MemoryLog

Long reports exceed the 2000-character `Content` limit. Verified pattern:

1. Create page with stub Content.
2. Append the report as paragraph blocks (each ≤1900 chars).

Python helper:

```python
import os, subprocess, requests
from datetime import datetime, timezone, timedelta

token = subprocess.run(
    ["bash", "-c", "source /docker/openclaw-xr8h/.env >/dev/null 2>&1; echo $NOTION_API_TOKEN"],
    capture_output=True, text=True
).stdout.strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

now = datetime.now(timezone(timedelta(hours=9))).isoformat()

page = requests.post("https://api.notion.com/v1/pages", headers=headers, json={
    "parent": {"database_id": "eb07126f-83f9-402c-baaf-076f67239e9d"},
    "properties": {
        "Title": {"title": [{"text": {"content": f"Status snapshot {now[:10]}"}}]},
        "Content": {"rich_text": [{"text": {"content": "Full report in blocks below."}}]},
        "Date": {"date": {"start": now}},
        "Source": {"select": {"name": "Text Update"}},
        "Processed by AI": {"checkbox": True},
    }
}).json()

chunks = [report[i:i+1900] for i in range(0, len(report), 1900)]
blocks = [{"object": "block", "type": "paragraph",
           "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]}} for c in chunks]
requests.patch(f"https://api.notion.com/v1/blocks/{page['id']}/children",
               headers=headers, json={"children": blocks})
```

This produces a durable, timestamped MemoryLog entry that both agents can read back.
