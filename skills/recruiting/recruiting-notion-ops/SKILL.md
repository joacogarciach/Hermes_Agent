---
name: recruiting-notion-ops
description: "Notion API operations for Joe's recruiting OS (Job Impulse Japan K.K.). Verified DB IDs, working curl recipes, schema-specific property names, and where the live token lives on the VPS."
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [notion, recruiting, job-impulse, atb, ot, memorylog]
    related_skills: [notion]
---

# Recruiting Notion Ops

Targeted Notion API playbook for the recruiting automation stack. Use this skill
whenever you need to read or write Joe's ATB, OT, or MemoryLog databases from the
Hermes/OpenClaw VPS.

This complements the generic `notion` hub skill. The hub skill tracks the latest
Notion API conventions (`2025-09-03`, `/data_sources/`, `Name` as title). The
recruiting stack currently runs on older conventions and a different title
property, so this skill is the source of truth for recruiting work.

## Scope

- Read/write rows in the three recruiting databases.
- Run status/count probes and stale-stage sweeps.
- Log snapshots and text updates to MemoryLog.
- Read from / write to the Memgraph shared agent knowledge hub for cross-agent project memory.
- Never alter database schemas.

## Where the token lives

The live OpenClaw container keeps its Notion token in:

```bash
/docker/openclaw-xr8h/.env
```

Key name there is `NOTION_API_TOKEN` (not `NOTION_API_KEY`). In shell or Python,
source that file before calling Notion:

```bash
source /docker/openclaw-xr8h/.env >/dev/null 2>&1
curl -s -X POST "https://api.notion.com/v1/databases/$ATB_DB/query" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"page_size":100}'
```

If you are inside a Python `execute_code` block, load it like:

```python
import os, subprocess
token = subprocess.run(
    ["bash", "-c", "source /docker/openclaw-xr8h/.env >/dev/null 2>&1; echo $NOTION_API_TOKEN"],
    capture_output=True, text=True
).stdout.strip()
os.environ["NOTION_API_TOKEN"] = token
```

## Verified databases

| DB | Purpose | ID |
|---|---|---|
| ATB | Candidates (100+ rows) | `e37f5e41-309d-83ae-960b-01684491b924` |
| OT | Open job orders | `838f5e41-309d-8330-b074-8179cf9b6684` |
| MemoryLog | Notes, calls, transcripts | `eb07126f-83f9-402c-baaf-076f67239e9d` |

These are REST database IDs. Use them with `/v1/databases/<id>/query` and
`/v1/databases/<id>` schema endpoints.

## API version that works here

Use `Notion-Version: 2022-06-28`. The newer `2025-09-03` / `/data_sources/`
conventions may work for some calls but the whole recruiting stack was validated
against the 2022 endpoints.

## Title-property pitfall (critical)

Do not assume the title property is always `Name`. Query the schema first, or
consult the known mappings:

| Database | Title property |
|---|---|
| ATB | `Name` |
| OT | `Role` (verify) |
| MemoryLog | `Title` |

If a create/update returns `validation_error: "Name is not a property that exists"`,
you are using the wrong title field. Look up the correct one in the schema
response and retry.

## Read recipes

See `references/working-api-recipes.md` for exact, copy-pasteable:

- Count/query ATB, OT, MemoryLog.
- Filter by stage, status, company, skill, language.
- Read recent MemoryLog entries.
- Read page bodies as blocks.

## Write recipes

### Create a MemoryLog entry (known-good shape)

```bash
source /docker/openclaw-xr8h/.env >/dev/null 2>&1

curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "eb07126f-83f9-402c-baaf-076f67239e9d"},
    "properties": {
      "Title": {"title": [{"text": {"content": "Entry title"}}]},
      "Content": {"rich_text": [{"text": {"content": "Body text"}}]},
      "Date": {"date": {"start": "2026-06-24T00:00:00+09:00"}},
      "Source": {"select": {"name": "Text Update"}},
      "Processed by AI": {"checkbox": true}
    }
  }'
```

If the body exceeds 2000 characters, create the page with a short `Content` then
PATCH `/v1/blocks/<page_id>/children` with paragraph blocks.

### Update a row

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/<page_id>" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Stage": {"status": {"name": "Sent to client"}}}}'
```

## Pitfalls

1. **Wrong title property** — MemoryLog uses `Title`, not `Name`.
2. **Wrong env var** — OpenClaw env uses `NOTION_API_TOKEN`, not `NOTION_API_KEY`.
3. **API version drift** — stick to `2022-06-28` for this stack.
4. **Content >2000 chars** — Notion rejects rich_text over 2000 characters; split into appended blocks.
5. **Schema changes** — never create new select options or properties; only write values that already exist in the schema.
6. **Token verification** — a pasted token may return `401` even if a search endpoint works. Verify against all three DB query endpoints; `200` across ATB, OT, and MemoryLog means the token is fully usable.
7. **MemoryLog Source values** — the `Source` select accepts values like `Text Update`, `Phone Call`, `Email`, `Meeting`, `Transcript`, `Voice Note`. Use an existing value; do not invent new options.

## References

- `references/working-api-recipes.md` — exact curl recipes and schema snippets discovered in this environment.
- `references/token-and-memorylog-pitfalls.md` — token verification, which MEMORY.md copy is live, and how to log long snapshots to MemoryLog.
- `references/memgraph-shared-hub.md` — Memgraph shared knowledge hub for agent-to-agent project memory.