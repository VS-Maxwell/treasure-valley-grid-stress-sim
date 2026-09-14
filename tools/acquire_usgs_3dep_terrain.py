#!/usr/bin/env python3
"""Acquire the newest USGS 3DEP 1-arc-second tiles for the TVGWFM footprint."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image


QUERY_URL = (
    "https://tnmaccess.nationalmap.gov/api/v1/products?"
    "bbox=-117.1163,43.1762,-115.8097,44.1081&"
    "datasets=National%20Elevation%20Dataset%20(NED)%201%20arc-second&"
    "prodFormats=GeoTIFF&outputFormat=JSON&max=100"
)
EXPECTED_TILES = {"n44w116", "n44w117", "n44w118", "n45w116", "n45w117", "n45w118"}
TITLE = re.compile(r"USGS 1 Arc Second (n\d+w\d+) (\d{8})$")


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "TreasureValleySimulator/0.2 terrain-acquisition"}
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        if response.status != 200:
            raise RuntimeError(f"USGS returned HTTP {response.status}")
        return response.read()


def download_verified(item: dict[str, Any], destination: Path) -> tuple[int, str]:
    """Stream one provider object to disk and verify its declared byte count."""
    request = urllib.request.Request(
        str(item["downloadURL"]),
        headers={"User-Agent": "TreasureValleySimulator/0.2 terrain-acquisition"},
    )
    temporary = destination.with_suffix(destination.suffix + ".partial")
    digest = hashlib.sha256()
    byte_count = 0
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as output:
            if response.status != 200:
                raise RuntimeError(f"USGS returned HTTP {response.status}")
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
                byte_count += len(chunk)
                if byte_count % (10 * 1024 * 1024) < len(chunk):
                    print(
                        f"  {destination.name}: {byte_count / (1024 * 1024):.0f} MiB",
                        flush=True,
                    )
        expected_bytes = int(item["sizeInBytes"])
        if byte_count != expected_bytes:
            raise ValueError(
                f"Provider byte count mismatch for {destination.name}: "
                f"received {byte_count}, expected {expected_bytes}"
            )
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return byte_count, digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    query_bytes = fetch(QUERY_URL)
    query_path = args.output_directory / "tnm-products-query.json"
    query_path.write_bytes(query_bytes)
    query = json.loads(query_bytes)
    selected: dict[str, tuple[str, dict[str, object]]] = {}
    for item in query["items"]:
        match = TITLE.fullmatch(item.get("title", ""))
        if not match or match.group(1) not in EXPECTED_TILES:
            continue
        tile, version = match.groups()
        if tile not in selected or version > selected[tile][0]:
            selected[tile] = (version, item)
    if set(selected) != EXPECTED_TILES:
        raise ValueError(f"Expected six terrain tiles, found {sorted(selected)}")

    files = []
    for tile in sorted(selected):
        version, item = selected[tile]
        file_name = Path(str(item["downloadURL"])).name
        path = args.output_directory / file_name
        print(f"Downloading {tile}: {file_name}", flush=True)
        byte_count, sha256 = download_verified(item, path)
        with Image.open(path) as raster:
            raster.verify()
        with Image.open(path) as raster:
            dimensions = list(raster.size)
            mode = raster.mode
        files.append(
            {
                "tile": tile,
                "version": version,
                "publication_date": item["publicationDate"],
                "file": file_name,
                "download_url": item["downloadURL"],
                "bytes": byte_count,
                "sha256": sha256,
                "dimensions": dimensions,
                "mode": mode,
                "format_validation": "PIL-TIFF-pass",
            }
        )
        print(f"Verified {tile}: {file_name} ({byte_count} bytes)", flush=True)

    receipt = {
        "schema_version": 1,
        "id": "usgs-3dep-tvgwfm-1arcsec-v1",
        "created_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "provider": "U.S. Geological Survey 3D Elevation Program",
        "product": "1 arc-second seamless DEM",
        "horizontal_datum": "NAD83",
        "vertical_datum": "NAVD88",
        "elevation_unit": "meters",
        "rights": "public-domain",
        "query_url": QUERY_URL,
        "query_file": query_path.name,
        "query_sha256": hashlib.sha256(query_bytes).hexdigest(),
        "tile_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "files": files,
        "status": "original-bytes-and-format-verified",
    }
    (args.output_directory / "receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Acquired {len(files)} tiles; {receipt['total_bytes']} bytes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
