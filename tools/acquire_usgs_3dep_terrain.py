#!/usr/bin/env python3
"""Acquire the newest USGS 3DEP 1-arc-second tiles for the TVGWFM footprint."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image


PRODUCTS_URL = "https://tnmaccess.nationalmap.gov/api/v1/products"
DEFAULT_BOUNDS = [-117.1163, 43.1762, -115.8097, 44.1081]
DEFAULT_EXPECTED_TILES = {
    "n44w116",
    "n44w117",
    "n44w118",
    "n45w116",
    "n45w117",
    "n45w118",
}
TITLE = re.compile(r"USGS 1 Arc Second (n\d+w\d+) (\d{8})$")


def parse_bounds(value: str) -> list[float]:
    try:
        bounds = [float(part) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bounds must contain four numbers") from exc
    if len(bounds) != 4 or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise argparse.ArgumentTypeError("bounds must be west,south,east,north")
    return bounds


def parse_tiles(value: str) -> set[str]:
    tiles = {part.strip().lower() for part in value.split(",") if part.strip()}
    if not tiles or any(not re.fullmatch(r"n\d{2}w\d{3}", tile) for tile in tiles):
        raise argparse.ArgumentTypeError("expected tiles must be comma-separated n##w### IDs")
    return tiles


def build_query_url(bounds: list[float]) -> str:
    query = urllib.parse.urlencode(
        {
            "bbox": ",".join(str(value) for value in bounds),
            "datasets": "National Elevation Dataset (NED) 1 arc-second",
            "prodFormats": "GeoTIFF",
            "outputFormat": "JSON",
            "max": "500",
        }
    )
    return f"{PRODUCTS_URL}?{query}"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "TreasureValleySimulator/0.2 terrain-acquisition"}
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        if response.status != 200:
            raise RuntimeError(f"USGS returned HTTP {response.status}")
        return response.read()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    parser.add_argument(
        "--bounds",
        type=parse_bounds,
        default=DEFAULT_BOUNDS,
        help="west,south,east,north query envelope",
    )
    parser.add_argument(
        "--expected-tiles",
        type=parse_tiles,
        default=DEFAULT_EXPECTED_TILES,
        help="comma-separated n##w### tile IDs",
    )
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--receipt-id", default="usgs-3dep-tvgwfm-1arcsec-v1")
    parser.add_argument("--reuse-directory", type=Path)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    query_url = build_query_url(args.bounds)
    query_bytes = fetch(query_url)
    query_path = args.output_directory / "tnm-products-query.json"
    query_path.write_bytes(query_bytes)
    query = json.loads(query_bytes)
    selected: dict[str, tuple[str, dict[str, object]]] = {}
    for item in query["items"]:
        match = TITLE.fullmatch(item.get("title", ""))
        if not match or match.group(1) not in args.expected_tiles:
            continue
        tile, version = match.groups()
        if tile not in selected or version > selected[tile][0]:
            selected[tile] = (version, item)
    if set(selected) != args.expected_tiles:
        raise ValueError(
            f"Expected {sorted(args.expected_tiles)}, found {sorted(selected)}"
        )

    files = []
    for tile in sorted(selected):
        version, item = selected[tile]
        file_name = Path(str(item["downloadURL"])).name
        path = args.output_directory / file_name
        reused = False
        reuse_path = (
            args.reuse_directory / file_name if args.reuse_directory else None
        )
        if not path.exists() and reuse_path and reuse_path.exists():
            if reuse_path.stat().st_size != int(item["sizeInBytes"]):
                raise ValueError(f"Reusable tile byte count changed: {file_name}")
            try:
                os.link(reuse_path, path)
            except OSError:
                shutil.copy2(reuse_path, path)
            reused = True
        if path.exists():
            byte_count = path.stat().st_size
            if byte_count != int(item["sizeInBytes"]):
                raise ValueError(f"Existing tile byte count changed: {file_name}")
            sha256 = file_sha256(path)
            print(
                f"Verifying {'reused' if reused else 'existing'} {tile}: {file_name}",
                flush=True,
            )
        else:
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
                "acquisition_action": "reused-verified-original"
                if reused
                else "downloaded-or-existing-verified-original",
            }
        )
        print(f"Verified {tile}: {file_name} ({byte_count} bytes)", flush=True)

    receipt = {
        "schema_version": 1,
        "id": args.receipt_id,
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
        "query_url": query_url,
        "bbox_epsg_4326": args.bounds,
        "local_root": str(args.output_directory.resolve()),
        "query_file": query_path.name,
        "query_sha256": hashlib.sha256(query_bytes).hexdigest(),
        "tile_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "files": files,
        "status": "original-bytes-and-format-verified",
    }
    receipt_path = args.receipt or (args.output_directory / "receipt.json")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Acquired {len(files)} tiles; {receipt['total_bytes']} bytes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
