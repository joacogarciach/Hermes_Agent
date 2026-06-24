# Working Notion API recipes — recruiting OS

Discovered on the live VPS for Job Impulse Japan K.K. These use the token in
`/docker/openclaw-xr8h/.env` (`NOTION_API_TOKEN`) and API version `2022-06-28`.

## Verified database IDs

- ATB: `e37f5e41-309d-83ae-960b-01684491b924`
- OT: `838f5e41-309d-8330-b074-8179cf9b6684`
- MemoryLog: `eb07126f-83f9-402c-baaf-076f67239e9d`

## Load the token

```bash
source /docker/openclaw-xr8h/.env > /dev/null 2>&1
```

## Count / query a database

```bash
curl -s -X POST "https://api.notion.com/v1/databases/e37f5e41-309d-83ae-960b-01684491b924/query" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"page_size":100}' | python3 -m json.tool
```

## Query open OT orders

```bash
curl -s -X POST "https://api.notion.com/v1/databases/838f5e41-309d-8330-b074-8179cf9b6684/query" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"property":"Status","status":{"equals":"Open"}},"page_size":100}' | python3 -m json.tool
```

## Recent MemoryLog entries

```bash
curl -s -X POST "https://api.notion.com/v1/databases/eb07126f-83f9-402c-baaf-076f67239e9d/query" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{"sorts":[{"property":"Date","direction":"descending"}],"page_size":15}' | python3 -m json.tool
```

## Read a schema

```bash
curl -s "https://api.notion.com/v1/databases/eb07126f-83f9-402c-baaf-076f67239e9d" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" | python3 -m json.tool
```

## MemoryLog create (short body)

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "eb07126f-83f9-402c-baaf-076f67239e9d"},
    "properties": {
      "Title": {"title": [{"text": {"content": "Note title"}}]},
      "Content": {"rich_text": [{"text": {"content": "Short body under 2000 chars."}}]},
      "Date": {"date": {"start": "2026-06-24T00:00:00+09:00"}},
      "Source": {"select": {"name": "Text Update"}},
      "Processed by AI": {"checkbox": true}
    }
  }' | python3 -m json.tool
```

## MemoryLog create (long body: page + appended blocks)

1. Create the page with a stub `Content`:

```bash
PAGE=$(curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "eb07126f-83f9-402c-baaf-076f67239e9d"},
    "properties": {
      "Title": {"title": [{"text": {"content": "Long note"}}]},
      "Content": {"rich_text": [{"text": {"content": "See below."}}]},
      "Date": {"date": {"start": "2026-06-24T00:00:00+09:00"}},
      "Source": {"select": {"name": "Text Update"}},
      "Processed by AI": {"checkbox": true}
    }
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

2. Append body blocks (one per paragraph, ≤2000 chars each):

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/$PAGE/children" \
  -H "Authorization: Bearer $NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Paragraph one."}}]}},
      {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Paragraph two."}}]}}
    ]
  }'
```

## Schema snapshot — MemoryLog (as observed 2026-06-24)

Title property: `Title`
Other properties: `Action Items` (rich_text), `Related Order` (relation), `Language`
(select), `Related Candidate` (relation), `Processed by AI` (checkbox), `Date`
(date), `Content` (rich_text), `Source` (select).

Source select options include: `Transcript`, `Meeting`, `Phone Call`, `Email`,
`Text Update`, `Voice Note`, `G2 Export`.

## Schema snapshot — ATB (partial)

Title property: `Name`
Key properties: `お名前・Full Name`, `年齢/ Age`, `職務経験 / Expertise`,
`最近の給料 / Recent Salary`, `希望年収/Desired Salary`, `電話番号`, `メールアドレス`,
`Seniority`, `就業状況`, `Stage` (status), `Match Reasoning`, `OT` (relation).

Selects with fixed options (do not invent new values): `国籍 / Nationality`,
`在留資格 / Visa Type`, `所在地`, `Language`, `スキル`.

## Schema snapshot — OT (partial)

Title property: `Role`
Key properties: `Status` (status, value `Open` for live orders), `Company name`
(select), `Priority` (select), `Location` (rich_text), `ATB` (relation),
`Candidates` (relation), `Notes` (rich_text), `Interview guide` (rich_text).

## Cross-linking notes

- ATB row → OT order via the `OT` relation property (ID `PZ@n`).
- OT order → ATB rows via the `ATB` relation property (ID `H_Ag`).
- OT order → candidate pages via the `Candidates` relation property (ID `OUlh`).
- These relation names are the property keys returned by the API; the display
  names in Notion may differ.

## Pitfall: copied virtualenvs

When copying a Python virtualenv from one path to another (e.g. bootstrapping an
isolated git worktree), the copied `.venv/bin/python` symlink and
`pyvenv.cfg` may still point at the original location's site-packages. Always
rebuild the venv in the new path and reinstall requirements rather than relying
on a copied venv.
