#!/usr/bin/env python3
"""Preserve and verify the final 2025 Form EIA-860 archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


SOURCE_URL = "https://www.eia.gov/electricity/data/eia860/xls/eia8602025.zip"
EXPECTED_BYTES = 23_622_347
USER_AGENT = "Treasure-Valley-Sim-EIA860-Acquisition/1.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path(
            "/run/media/madame-butterfly/Toshiba/Treasure_Valley_Model/"
            "data/raw/eia/form-860-2025-final-20260914"
        ),
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("receipts/eia860-2025-final-20260914.json"),
    )
    args = parser.parse_args()
    args.raw_root.mkdir(parents=True, exist_ok=True)
    destination = args.raw_root / "eia8602025.zip"

    if not destination.is_file() or destination.stat().st_size != EXPECTED_BYTES:
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            with tempfile.NamedTemporaryFile(dir=args.raw_root, delete=False) as temporary:
                while block := response.read(1024 * 1024):
                    temporary.write(block)
                temporary_path = Path(temporary.name)
        if temporary_path.stat().st_size != EXPECTED_BYTES:
            raise RuntimeError(
                f"EIA archive byte mismatch: {temporary_path.stat().st_size}"
            )
        temporary_path.replace(destination)

    with zipfile.ZipFile(destination) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP CRC failed: {bad_member}")
        members = [
            {
                "name": info.filename,
                "bytes": info.file_size,
                "crc32": f"{info.CRC:08x}",
            }
            for info in archive.infolist()
            if not info.is_dir()
        ]
    required_prefixes = ("2___Plant", "3_1_Generator")
    if not all(any(Path(item["name"]).name.startswith(prefix) for item in members) for prefix in required_prefixes):
        raise RuntimeError("EIA archive lacks the required plant or generator workbook")

    receipt = {
        "schema_version": 1,
        "source_id": "eia860-2025-final",
        "provider": "U.S. Energy Information Administration",
        "source_url": SOURCE_URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "original-bytes-and-zip-verified",
        "local_root": str(args.raw_root),
        "object": {
            "file": destination.name,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "media_type": "application/zip",
        },
        "archive_member_count": len(members),
        "members": members,
        "validation": {
            "expected_bytes": EXPECTED_BYTES,
            "zip_central_directory": "passed",
            "all_member_crc32": "passed",
            "required_workbooks": list(required_prefixes),
        },
        "limitations": [
            "Form EIA-860 includes plants with at least one megawatt of combined nameplate capacity.",
            "Spatial and normalized-name proximity are candidate match evidence, not automatic dam identity acceptance.",
            "Electrical topology requires independent connection evidence.",
        ],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(
        f"Verified {destination.stat().st_size} EIA bytes, "
        f"{len(members)} members, SHA-256 {receipt['object']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
