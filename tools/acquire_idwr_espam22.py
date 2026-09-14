#!/usr/bin/env python3
"""Acquire and receipt bounded official ESPAM 2.2 model archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://research.idwr.idaho.gov/files/projects/espam/browse/model_files/Version_22"
FILES = (
    ("FinalCalibration/E200723A_07.zip", 493_453_286),
    ("AquiferProperties/SpecificYield.zip", 642_441),
    ("AquiferProperties/Transmissivity.zip", 736_593),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path, expected_bytes: int) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "TreasureValleySimulator/0.2"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        if offset and response.status != 206:
            partial.unlink()
            offset = 0
        mode = "ab" if offset else "wb"
        with partial.open(mode) as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                size = output.tell()
                if size > expected_bytes:
                    raise ValueError(f"Provider response exceeded expected bytes: {destination.name}")
                if size // (25 * 1024 * 1024) != (size - len(chunk)) // (25 * 1024 * 1024):
                    print(f"  {destination.name}: {size // (1024 * 1024)} MiB", flush=True)
    if partial.stat().st_size != expected_bytes:
        raise ValueError(
            f"Byte count mismatch for {destination.name}: "
            f"{partial.stat().st_size} != {expected_bytes}"
        )
    partial.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=ROOT / "receipts/idwr-espam22-model-20260914.json",
    )
    args = parser.parse_args()
    destination = args.destination.resolve()
    receipt_path = args.receipt.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    records = []
    for relative_url, expected_bytes in FILES:
        name = Path(relative_url).name
        path = destination / name
        url = f"{BASE}/{relative_url}"
        if path.exists() and path.stat().st_size == expected_bytes:
            print(f"Verifying existing {name}", flush=True)
        else:
            print(f"Downloading {name}", flush=True)
            download(url, path, expected_bytes)
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"ZIP CRC failed for {name}: {bad_member}")
            member_count = len(archive.infolist())
            uncompressed_bytes = sum(item.file_size for item in archive.infolist())
        records.append(
            {
                "file": name,
                "source_url": url,
                "bytes": expected_bytes,
                "sha256": sha256(path),
                "zip_member_count": member_count,
                "zip_uncompressed_bytes": uncompressed_bytes,
                "format_validation": "zip-central-directory-and-member-crc-passed",
            }
        )
        print(f"Verified {name}: {expected_bytes} bytes, {member_count} members", flush=True)

    payload = {
        "schema_version": 1,
        "id": "idwr-espam22-official-model-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "Idaho Department of Water Resources",
        "model": "Eastern Snake Plain Aquifer Model version 2.2",
        "source_index": f"{BASE}/",
        "local_root": str(destination),
        "file_count": len(records),
        "total_bytes": sum(item["bytes"] for item in records),
        "files": records,
        "status": "original-bytes-and-format-verified",
        "scientific_boundary": (
            "Acquisition and archive integrity do not establish numerical reproduction, "
            "scenario suitability, or coupling acceptance."
        ),
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Acquired {len(records)} ESPAM 2.2 archives; {payload['total_bytes']} bytes",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
