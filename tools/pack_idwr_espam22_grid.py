#!/usr/bin/env python3
"""Pack the verified ESPAM 2.2 active grid for bounded browser rendering."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRID_RECEIPT = ROOT / "receipts/idwr-espam22-grid-20260914.json"
MODEL_RECEIPT = ROOT / "receipts/idwr-espam22-model-20260914.json"
MANIFEST = ROOT / "app/public/data/idwr-espam22-grid-manifest-v1.json"
LINES = ROOT / "app/public/data/idwr-espam22-grid-lines-f32-v1.bin"
CELLS = ROOT / "app/public/data/idwr-espam22-grid-cells-f32-v1.bin"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    grid_receipt = json.loads(GRID_RECEIPT.read_text(encoding="utf-8"))
    model_receipt = json.loads(MODEL_RECEIPT.read_text(encoding="utf-8"))
    if grid_receipt["status"] != "original-api-pages-and-geometry-verified":
        raise ValueError("ESPAM grid receipt has not passed")
    if model_receipt["status"] != "original-bytes-and-format-verified":
        raise ValueError("ESPAM model archive receipt has not passed")

    source_root = Path(grid_receipt["local_root"])
    features = []
    for page in grid_receipt["pages"]:
        path = source_root / page["file"]
        if path.stat().st_size != page["bytes"] or sha256(path) != page["sha256"]:
            raise ValueError(f"ESPAM source-page receipt mismatch: {page['file']}")
        features.extend(json.loads(path.read_text(encoding="utf-8"))["features"])
    if len(features) != grid_receipt["feature_count"] or len(features) != 11_236:
        raise ValueError("ESPAM source-page feature count mismatch")

    line_values: list[float] = []
    cell_values: list[float] = []
    rows: set[int] = set()
    columns: set[int] = set()
    west = south = float("inf")
    east = north = float("-inf")
    for feature in features:
        properties = feature["properties"]
        row = int(properties["ROW_ID"])
        column = int(properties["COL_ID"])
        rows.add(row)
        columns.add(column)
        ring = feature["geometry"]["coordinates"][0]
        if len(ring) != 5 or ring[0] != ring[-1]:
            raise ValueError(f"ESPAM cell {properties['OBJECTID']} is not a closed quad")
        for index in range(4):
            start = ring[index]
            end = ring[index + 1]
            line_values.extend((start[0], start[1], end[0], end[1]))
            west = min(west, start[0])
            east = max(east, start[0])
            south = min(south, start[1])
            north = max(north, start[1])
        center_lon = sum(point[0] for point in ring[:4]) / 4
        center_lat = sum(point[1] for point in ring[:4]) / 4
        cell_values.extend((center_lon, center_lat, float(row), float(column)))

    LINES.write_bytes(struct.pack(f"<{len(line_values)}f", *line_values))
    CELLS.write_bytes(struct.pack(f"<{len(cell_values)}f", *cell_values))
    manifest = {
        "schema_version": 1,
        "id": "idwr-espam22-grid-v1",
        "truth_state": "ingested",
        "provider": "Idaho Department of Water Resources",
        "model": "Eastern Snake Plain Aquifer Model version 2.2",
        "source_grid_receipt": str(GRID_RECEIPT.relative_to(ROOT)),
        "source_grid_receipt_sha256": sha256(GRID_RECEIPT),
        "source_model_receipt": str(MODEL_RECEIPT.relative_to(ROOT)),
        "source_model_receipt_sha256": sha256(MODEL_RECEIPT),
        "layout": {
            "layers": 1,
            "rows": 104,
            "columns": 209,
            "stress_periods": 462,
            "cell_width_feet": 5280,
            "cell_height_feet": 5280,
            "active_cells": len(features),
            "row_id_range": [min(rows), max(rows)],
            "column_id_range": [min(columns), max(columns)],
        },
        "bounds_wgs84": {
            "west": round(west, 8),
            "east": round(east, 8),
            "south": round(south, 8),
            "north": round(north, 8),
        },
        "line_binary": {
            "file": LINES.name,
            "bytes": LINES.stat().st_size,
            "sha256": sha256(LINES),
            "encoding": "little-endian-float32",
            "stride": 4,
            "record_count": len(line_values) // 4,
            "fields": ["longitude_1", "latitude_1", "longitude_2", "latitude_2"],
        },
        "cell_binary": {
            "file": CELLS.name,
            "bytes": CELLS.stat().st_size,
            "sha256": sha256(CELLS),
            "encoding": "little-endian-float32",
            "stride": 4,
            "record_count": len(cell_values) // 4,
            "fields": ["center_longitude", "center_latitude", "row_id", "column_id"],
        },
        "limitations": [
            "This pack maps the official active ESPAM 2.2 grid; it does not merge ESPAM with TVGWFM.",
            "Repeated shared edges are retained for a deterministic cell-by-cell wireframe.",
            "Numerical outputs remain inactive until the archived baseline is independently reproduced or explicitly labeled archived output.",
        ],
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Packed {len(features)} active ESPAM cells and {len(line_values) // 4} edges; "
        f"{LINES.stat().st_size + CELLS.stat().st_size} bytes",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
