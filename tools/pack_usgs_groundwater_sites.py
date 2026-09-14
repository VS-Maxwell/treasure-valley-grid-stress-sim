#!/usr/bin/env python3
"""Map verified NAVD88 groundwater sites to the published TVGWFM footprint."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_verified_pages(receipt: dict[str, object]) -> list[dict[str, object]]:
    root = Path(receipt["local_root"])
    features = []
    for page in receipt["pages"]:
        path = root / page["file"]
        if path.stat().st_size != page["bytes"] or sha256(path) != page["sha256"]:
            raise ValueError(f"Source receipt mismatch: {path}")
        features.extend(json.loads(path.read_text(encoding="utf-8"))["features"])
    return features


def grid_cell(
    longitude: float,
    latitude: float,
    corners: dict[str, list[float]],
    rows: int,
    columns: int,
) -> tuple[int, int] | None:
    ul = corners["upper_left"]
    ur = corners["upper_right"]
    ll = corners["lower_left"]
    ax, ay = ur[0] - ul[0], ur[1] - ul[1]
    bx, by = ll[0] - ul[0], ll[1] - ul[1]
    dx, dy = longitude - ul[0], latitude - ul[1]
    determinant = ax * by - ay * bx
    u = (dx * by - dy * bx) / determinant
    v = (ax * dy - ay * dx) / determinant
    if not (0 <= u <= 1 and 0 <= v <= 1):
        return None
    return min(int(v * rows), rows - 1), min(int(u * columns), columns - 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("field_receipt", type=Path)
    parser.add_argument("location_receipt", type=Path)
    parser.add_argument("grid", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    field_receipt = json.loads(args.field_receipt.read_text(encoding="utf-8"))
    location_receipt = json.loads(args.location_receipt.read_text(encoding="utf-8"))
    model = json.loads(args.grid.read_text(encoding="utf-8"))["grid"]

    readings: dict[str, list[tuple[str, float]]] = defaultdict(list)
    null_readings = 0
    for feature in read_verified_pages(field_receipt):
        properties = feature["properties"]
        if properties.get("value") is None:
            null_readings += 1
            continue
        readings[properties["monitoring_location_id"]].append(
            (properties["time"], float(properties["value"]))
        )

    sites = []
    exclusions = defaultdict(int)
    for feature in read_verified_pages(location_receipt):
        properties = feature["properties"]
        site_id = feature["id"]
        site_readings = readings.get(site_id, [])
        if not site_readings:
            exclusions["no_numeric_reading"] += 1
            continue
        if properties.get("vertical_datum") != "NAVD88":
            exclusions["non_navd88"] += 1
            continue
        longitude, latitude = feature["geometry"]["coordinates"][:2]
        cell = grid_cell(
            float(longitude),
            float(latitude),
            model["corners_wgs84"],
            model["rows"],
            model["columns"],
        )
        if cell is None:
            exclusions["outside_grid"] += 1
            continue
        row, column = cell
        if model["top_elevation_feet"][row * model["columns"] + column] <= 0:
            exclusions["inactive_top_cell"] += 1
            continue
        ordered = sorted(site_readings)
        latest_time, latest_depth = ordered[-1]
        altitude = float(properties["altitude"])
        sites.append(
            {
                "id": site_id,
                "longitude": float(longitude),
                "latitude": float(latitude),
                "altitude_navd88_ft": altitude,
                "row": row,
                "column": column,
                "measurement_count": len(ordered),
                "first_date": ordered[0][0][:10],
                "latest_date": latest_time[:10],
                "latest_depth_below_land_ft": latest_depth,
                "latest_water_level_altitude_navd88_ft": altitude - latest_depth,
                "well_depth_ft": properties.get("well_constructed_depth"),
            }
        )

    binary_path = args.output.with_name("usgs-groundwater-sites-f32.bin")
    binary = b"".join(
        struct.pack(
            "<fff",
            site["longitude"],
            site["latitude"],
            site["latest_water_level_altitude_navd88_ft"],
        )
        for site in sites
    )
    binary_path.write_bytes(binary)
    payload = {
        "schema_version": 1,
        "id": "usgs-groundwater-sites-tvgwfm-v1",
        "truth_state": "observed",
        "horizontal_method": "affine inverse of published TVGWFM WGS84 corner coordinates",
        "vertical_method": "NAVD88 site altitude minus parameter-72019 depth below land surface",
        "field_receipt_sha256": sha256(args.field_receipt),
        "location_receipt_sha256": sha256(args.location_receipt),
        "grid_sha256": sha256(args.grid),
        "site_count": len(sites),
        "numeric_reading_count": sum(site["measurement_count"] for site in sites),
        "source_null_reading_count": null_readings,
        "exclusions": dict(sorted(exclusions.items())),
        "binary": {
            "file": binary_path.name,
            "sha256": hashlib.sha256(binary).hexdigest(),
            "bytes": len(binary),
            "encoding": "little-endian-float32",
            "order": "site-longitude-latitude-water-level-altitude-navd88-feet",
            "stride": 3,
        },
        "limitations": [
            "Published corner coordinates are used for a browser-scale affine grid join.",
            "No model layer is assigned because well-screen evidence is not in this pack.",
            "Observed water-level altitude is not compared to modeled head as a validation residual.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.output} and {binary_path}: {payload['site_count']} mapped sites, "
        f"{len(binary)} binary bytes, exclusions={payload['exclusions']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
