#!/usr/bin/env python3
"""Update the bounded, secret-free visible development status feed."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "dev" / "status.json"
MAX_EVENTS = 100
SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret|password)\s*[=:]\s*)[^\s,&]+"),
    re.compile(r"(?i)([?&](?:key|api_key|token)=)[^&\s]+"),
)


def redact(value: str) -> str:
    result = value
    for pattern in SECRET_PATTERNS:
        result = pattern.sub(r"\1[REDACTED]", result)
    return result


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", choices=("queued", "active", "passed", "failed", "blocked", "note"))
    parser.add_argument("summary")
    parser.add_argument("--detail", default="")
    parser.add_argument("--phase")
    parser.add_argument("--task")
    parser.add_argument("--progress", type=int)
    parser.add_argument("--file", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    now = utc_now()
    event = {
        "at": now,
        "state": args.state,
        "summary": redact(args.summary),
        "detail": redact(args.detail),
    }
    events = [*data.get("events", []), event][-MAX_EVENTS:]
    data["events"] = events
    data["updated_at"] = now
    data["state"] = args.state
    if args.phase:
        data["phase"] = redact(args.phase)
    if args.task:
        data["task"] = redact(args.task)
    if args.progress is not None:
        data["progress_percent"] = max(0, min(100, args.progress))
    changed = list(data.get("changed_files", []))
    for file_name in args.file:
        clean = redact(file_name)
        if clean not in changed:
            changed.append(clean)
    data["changed_files"] = changed[-100:]
    temp_path = STATUS_PATH.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp_path, STATUS_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
