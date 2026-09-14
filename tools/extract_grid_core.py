#!/usr/bin/env python3
"""Extract the exact grid geometry needed by the crash-safe first view."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "legacy.html"
OUTPUT = ROOT / "data" / "grid-core.json"


def embedded_data(source: str) -> dict[str, object]:
    prefix = "const DATA = "
    suffix = ";\nconst MAXLOAD"
    start = source.index(prefix) + len(prefix)
    end = source.index(suffix, start)
    return json.loads(source[start:end])


def main() -> int:
    legacy_bytes = LEGACY.read_bytes()
    data = embedded_data(legacy_bytes.decode("utf-8"))
    core = {
        "schema_version": 1,
        "source": "Exact extraction from legacy.html; no geometry simplification",
        "source_sha256": hashlib.sha256(legacy_bytes).hexdigest(),
        "trans": data["trans"],
        "subs": data["subs"],
        "plants": data["plants"],
    }
    payload = json.dumps(core, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, OUTPUT)
    print(f"wrote={OUTPUT}")
    print(f"bytes={len(payload)}")
    print(f"sha256={hashlib.sha256(payload).hexdigest()}")
    print(f"corridors={len(core['trans']['features'])}")
    print(f"substations={len(core['subs']['features'])}")
    print(f"plants={len(core['plants']['features'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
