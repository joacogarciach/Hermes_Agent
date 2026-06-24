#!/usr/bin/env python3
"""Template: read-only Notion automation sweep with Telegram nudge.

Copy this as a starting point for any new W4-style heartbeat automation.
It queries a Notion database, flags stale rows, drafts a summary, and
optionally sends it to Telegram. It is dry-run by default.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

DB_ID = os.environ.get("NOTION_DATABASE_ID", "REPLACE_ME")
NOTION_VERSION = "2022-06-28"

STAGE_SLAS = [
    # (status_value, days_threshold, human_reason)
]


def notion_headers() -> dict:
    key = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_API_TOKEN")
    if not key:
        raise RuntimeError("NOTION_API_KEY or NOTION_API_TOKEN required")
    return {
        "Authorization": f"Bearer {key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_db(status_name: str | None = None, limit: int = 100) -> list[dict]:
    url = f"https://api.notion.com/v1/databases/{DB_ID}/query"
    body = {"page_size": limit}
    if status_name:
        body["filter"] = {"property": "Status", "status": {"equals": status_name}}
    results = []
    has_more = True
    start_cursor = None
    while has_more:
        if start_cursor:
            body["start_cursor"] = start_cursor
        r = requests.post(url, headers=notion_headers(), json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    return results


def evaluate_staleness(pages: list[dict], now: datetime) -> list[dict]:
    flagged = []
    for page in pages:
        # Customize per automation
        pass
    return flagged


def draft_summary(flagged: list[dict]) -> str:
    if not flagged:
        return "✅ Nothing stale today."
    return json.dumps(flagged, indent=2, ensure_ascii=False)


def send_telegram(message: str, dry_run: bool = True) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required")
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    if dry_run:
        return {"dry_run": True, "would_send": payload}
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return {"sent": True, "response": r.json()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--notify-telegram", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    pages = query_db()
    flagged = evaluate_staleness(pages, now)
    summary = draft_summary(flagged)
    print(summary)

    if args.notify_telegram:
        print(json.dumps(send_telegram(summary, dry_run=args.dry_run), indent=2))


if __name__ == "__main__":
    main()
