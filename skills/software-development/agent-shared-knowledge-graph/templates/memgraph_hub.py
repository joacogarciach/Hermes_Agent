#!/usr/bin/env python3
"""Drop-in Memgraph connector for a shared agent knowledge graph.

Usage:
    python3 memgraph_hub.py write --type session --content "..." --tags "a,b"
    python3 memgraph_hub.py query --question "memgraph setup"
    python3 memgraph_hub.py recent --limit 10
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import mgclient


def _load_env() -> None:
    env_paths = [Path(".env"), Path("/root/rec-auth-app/.env"), Path("/docker/openclaw-xr8h/.env")]
    for p in env_paths:
        if p.exists():
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k not in os.environ:
                        os.environ[k] = v


def _connection_kwargs() -> Dict[str, Any]:
    kw = {
        "host": os.environ.get("MEMGRAPH_HOST", "localhost"),
        "port": int(os.environ.get("MEMGRAPH_PORT", "7687")),
    }
    if os.environ.get("MEMGRAPH_USER"):
        kw["user"] = os.environ["MEMGRAPH_USER"]
    if os.environ.get("MEMGRAPH_PASSWORD"):
        kw["password"] = os.environ["MEMGRAPH_PASSWORD"]
    return kw


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower())[:60].strip("-")


def _ensure_schema(conn) -> None:
    cur = conn.cursor()
    try:
        cur.execute("CREATE CONSTRAINT ON (n:Fact) ASSERT n.id IS UNIQUE;")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()


def write_fact(conn, fact_type: str, content: str, tags: List[str], source: str, related: List[str]) -> str:
    fact_id = f"{fact_type}-{_slug(content)}-{_now()}"
    tags = [t.strip().lower() for t in tags if t.strip()]
    related = [r.strip() for r in related if r.strip()]

    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE (n:Fact {
                id: $id,
                type: $type,
                content: $content,
                tags: $tags,
                source: $source,
                created_at: $created_at
            })
            """,
            {
                "id": fact_id,
                "type": fact_type,
                "content": content,
                "tags": json.dumps(tags),
                "source": source,
                "created_at": _now(),
            },
        )
        cur.fetchone()

        for tag in tags:
            cur.execute(
                """
                MERGE (t:Tag {name: $tag})
                WITH t
                MATCH (n:Fact {id: $id})
                CREATE (n)-[:TAGGED]->(t)
                """,
                {"tag": tag, "id": fact_id},
            )

        for rel_id in related:
            cur.execute(
                """
                MATCH (a:Fact {id: $id}), (b:Fact {id: $rel_id})
                CREATE (a)-[:RELATED_TO]->(b)
                """,
                {"id": fact_id, "rel_id": rel_id},
            )

        conn.commit()
    finally:
        cur.close()
    return fact_id


def search_facts(conn, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    words = [w.strip().lower() for w in re.split(r"[^a-z0-9]+", query) if len(w.strip()) > 2]
    if not words:
        words = [query.lower()]
    pattern = ".*(?:" + "|".join(re.escape(w) for w in words) + ").*"

    cur = conn.cursor()
    try:
        cur.execute(
            """
            MATCH (n:Fact)
            WHERE n.content =~ $pattern OR n.content CONTAINS $plain
            RETURN n.id, n.type, n.content, n.tags, n.source, n.created_at
            ORDER BY n.created_at DESC
            LIMIT $limit
            """,
            {"pattern": pattern, "plain": words[0], "limit": limit},
        )
        rows = []
        while True:
            row = cur.fetchone()
            if row is None:
                break
            rows.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "content": row[2],
                    "tags": json.loads(row[3]) if row[3] else [],
                    "source": row[4],
                    "created_at": row[5],
                }
            )
    finally:
        cur.close()
    return rows


def recent_facts(conn, fact_type: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    where = "WHERE n.type = $type" if fact_type else ""
    params: Dict[str, Any] = {"limit": limit}
    if fact_type:
        params["type"] = fact_type
    cur = conn.cursor()
    try:
        cur.execute(
            f"""
            MATCH (n:Fact)
            {where}
            RETURN n.id, n.type, n.content, n.tags, n.source, n.created_at
            ORDER BY n.created_at DESC
            LIMIT $limit
            """,
            params,
        )
        rows = []
        while True:
            row = cur.fetchone()
            if row is None:
                break
            rows.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "content": row[2],
                    "tags": json.loads(row[3]) if row[3] else [],
                    "source": row[4],
                    "created_at": row[5],
                }
            )
    finally:
        cur.close()
    return rows


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Shared knowledge hub for agents")
    sub = p.add_subparsers(dest="command", required=True)

    w = sub.add_parser("write", help="write a fact/note into the hub")
    w.add_argument("--type", required=True, choices=["session", "decision", "blocker", "note"])
    w.add_argument("--content", required=True)
    w.add_argument("--tags", default="")
    w.add_argument("--source", default="hermes")
    w.add_argument("--related", default="")

    q = sub.add_parser("query", help="search facts by keywords")
    q.add_argument("--question", required=True)
    q.add_argument("--limit", type=int, default=10)

    r = sub.add_parser("recent", help="list recent facts")
    r.add_argument("--type", default="")
    r.add_argument("--limit", type=int, default=10)

    return p


def main(argv: List[str] = None) -> int:
    _load_env()
    args = build_parser().parse_args(argv)

    try:
        conn = mgclient.connect(**_connection_kwargs())
        conn.autocommit = False
    except Exception as e:
        print(json.dumps({"error": f"failed to connect to Memgraph: {e}"}, indent=2))
        return 1

    _ensure_schema(conn)

    if args.command == "write":
        tags = [t for t in args.tags.split(",") if t]
        related = [r for r in args.related.split(",") if r]
        fact_id = write_fact(conn, args.type, args.content, tags, args.source, related)
        print(json.dumps({"ok": True, "id": fact_id}, indent=2))

    elif args.command == "query":
        rows = search_facts(conn, args.question, args.limit)
        print(json.dumps({"count": len(rows), "results": rows}, indent=2, ensure_ascii=False))

    elif args.command == "recent":
        rows = recent_facts(conn, args.type, args.limit)
        print(json.dumps({"count": len(rows), "results": rows}, indent=2, ensure_ascii=False))

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
