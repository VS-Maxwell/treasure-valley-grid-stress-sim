#!/usr/bin/env python3
"""Derive a compact, receipt-backed terrain mesh from verified USGS 3DEP tiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT = ROOT / "receipts/usgs-3dep-terrain-20260914.json"
DEFAULT_MANIFEST = ROOT / "app/public/data/usgs-3dep-regional-terrain-manifest.json"
DEFAULT_BINARY = ROOT / "app/public/data/usgs-3dep-regional-terrain-f32.bin"
ROWS = 101
COLUMNS = 151
REGIONAL_BOUNDS = {"west": -118.0, "east": -115.0, "south": 43.0, "north": 45.0}
NODATA_FLOOR = -100_000.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bilinear(start: float, end: float, amount: float) -> float:
    return start + (end - start) * amount


def parse_bounds(value: str) -> dict[str, float]:
    try:
        west, south, east, north = [float(part) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bounds must be west,south,east,north") from exc
    if west >= east or south >= north:
        raise argparse.ArgumentTypeError("bounds must be west,south,east,north")
    return {"west": west, "east": east, "south": south, "north": north}


def tile_id(longitude: float, latitude: float) -> str:
    return f"n{math.ceil(latitude):02d}w{math.ceil(-longitude):03d}"


class RasterTile:
    def __init__(self, path: Path) -> None:
        self.image = Image.open(path)
        if self.image.mode != "F":
            raise ValueError(f"Expected float32 TIFF, got {self.image.mode}: {path.name}")
        tiepoint = self.image.tag_v2.get(33922)
        scale = self.image.tag_v2.get(33550)
        nodata = self.image.tag_v2.get(42113)
        if not tiepoint or not scale:
            raise ValueError(f"Missing GeoTIFF transform tags: {path.name}")
        self.origin_x = float(tiepoint[3])
        self.origin_y = float(tiepoint[4])
        self.scale_x = float(scale[0])
        self.scale_y = float(scale[1])
        self.nodata = float(nodata) if nodata is not None else -999999.0
        self.pixels = self.image.load()

    def close(self) -> None:
        self.image.close()

    def sample(self, longitude: float, latitude: float) -> float:
        # The source declares RasterPixelIsArea. Convert geographic coordinates
        # to pixel-center coordinates before bilinear interpolation.
        x = (longitude - self.origin_x) / self.scale_x - 0.5
        y = (self.origin_y - latitude) / self.scale_y - 0.5
        x = min(max(x, 0.0), self.image.width - 1.0)
        y = min(max(y, 0.0), self.image.height - 1.0)
        left = int(math.floor(x))
        top = int(math.floor(y))
        right = min(left + 1, self.image.width - 1)
        bottom = min(top + 1, self.image.height - 1)
        fx = x - left
        fy = y - top
        samples = [
            float(self.pixels[left, top]),
            float(self.pixels[right, top]),
            float(self.pixels[left, bottom]),
            float(self.pixels[right, bottom]),
        ]
        if any(value <= NODATA_FLOOR or value == self.nodata for value in samples):
            raise ValueError(
                f"No-data encountered at longitude {longitude}, latitude {latitude}"
            )
        upper = bilinear(samples[0], samples[1], fx)
        lower = bilinear(samples[2], samples[3], fx)
        return bilinear(upper, lower, fy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--rows", type=int, default=ROWS)
    parser.add_argument("--columns", type=int, default=COLUMNS)
    parser.add_argument(
        "--bounds",
        type=parse_bounds,
        default=REGIONAL_BOUNDS,
        help="west,south,east,north mesh envelope",
    )
    parser.add_argument("--manifest-id", default="usgs-3dep-regional-terrain-v1")
    parser.add_argument(
        "--coverage-label",
        default="the requested regional terrain envelope",
        help="plain-language scope used in the manifest limitation",
    )
    args = parser.parse_args()
    args.receipt = args.receipt.resolve()
    args.manifest = args.manifest.resolve()
    args.binary = args.binary.resolve()
    if args.rows < 2 or args.columns < 2:
        raise ValueError("Terrain mesh needs at least two rows and columns")
    bounds = args.bounds

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    source_root = Path(receipt["local_root"])
    if receipt["status"] != "original-bytes-and-format-verified":
        raise ValueError("Terrain source receipt has not passed byte and format checks")

    rasters: dict[str, RasterTile] = {}
    try:
        for item in receipt["files"]:
            path = source_root / item["file"]
            if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                raise ValueError(f"Source receipt mismatch: {item['file']}")
            rasters[item["tile"]] = RasterTile(path)

        values: list[float] = []
        for row in range(args.rows):
            v = row / (args.rows - 1)
            latitude = bilinear(bounds["north"], bounds["south"], v)
            for column in range(args.columns):
                u = column / (args.columns - 1)
                longitude = bilinear(bounds["west"], bounds["east"], u)
                # Exact integer tile boundaries have equivalent overlap pixels;
                # nudge only the tile lookup into the western/northern tile.
                lookup_lon = longitude if longitude < bounds["east"] else longitude - 1e-9
                lookup_lat = min(latitude + 1e-9, bounds["north"] - 1e-9)
                source_tile = tile_id(lookup_lon, lookup_lat)
                if source_tile not in rasters:
                    raise ValueError(f"No receipted tile covers {longitude}, {latitude}")
                values.append(rasters[source_tile].sample(longitude, latitude))
    finally:
        for raster in rasters.values():
            raster.close()

    args.binary.parent.mkdir(parents=True, exist_ok=True)
    args.binary.write_bytes(struct.pack(f"<{len(values)}f", *values))
    receipt_hash = sha256(args.receipt)
    binary_hash = sha256(args.binary)
    minimum = min(values)
    maximum = max(values)
    manifest = {
        "schema_version": 1,
        "id": args.manifest_id,
        "truth_state": "observed",
        "provider": "U.S. Geological Survey 3D Elevation Program",
        "product": "1 arc-second seamless DEM",
        "source_receipt": str(args.receipt.relative_to(ROOT)),
        "source_receipt_sha256": receipt_hash,
        "horizontal_datum": "NAD83",
        "vertical_datum": "NAVD88",
        "elevation_unit": "meters",
        "mesh": {
            "rows": args.rows,
            "columns": args.columns,
            "vertex_count": len(values),
            "geographic_interpolation": "regular longitude-latitude grid",
            "sampling": "bilinear GeoTIFF pixel-center interpolation",
            "bounds_wgs84": bounds,
        },
        "statistics": {
            "minimum_meters": round(minimum, 3),
            "maximum_meters": round(maximum, 3),
            "mean_meters": round(sum(values) / len(values), 3),
        },
        "binary": {
            "file": args.binary.name,
            "bytes": args.binary.stat().st_size,
            "sha256": binary_hash,
            "encoding": "little-endian-float32",
            "order": "row-major-northwest-to-southeast-elevation-meters",
        },
        "render_transform": {
            "vertical_exaggeration": 2.2,
            "world_height_span": 18.0,
            "note": "The renderer preserves source values in meters and applies a documented visual scaling only to world-space height.",
        },
        "limitations": [
            f"This compact mesh covers {args.coverage_label} using {receipt['tile_count']} receipted 3DEP tiles.",
            "It is a downsampled visualization surface and is not a substitute for the original 1 arc-second rasters.",
            f"The {receipt['tile_count']} original GeoTIFFs remain outside the browser bundle under their acquisition receipt.",
            "Terrain coverage does not imply groundwater-model coverage; TVGWFM, ESPAM, and framework-only areas retain separate scientific boundaries.",
        ],
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {len(values)} terrain elevations ({minimum:.3f} to {maximum:.3f} m); "
        f"binary SHA-256 {binary_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
