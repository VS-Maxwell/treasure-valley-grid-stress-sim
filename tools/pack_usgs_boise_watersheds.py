#!/usr/bin/env python3
"""Build a compact display-only GeoJSON from verified Boise River HUC8 polygons."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def perpendicular_distance(point: list[float], start: list[float], end: list[float]) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0 and dy == 0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    return abs(dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0]) / math.hypot(dx, dy)


def simplify_line(points: list[list[float]], tolerance: float) -> list[list[float]]:
    if len(points) <= 2:
        return points
    maximum = 0.0
    index = 0
    for candidate in range(1, len(points) - 1):
        distance = perpendicular_distance(points[candidate], points[0], points[-1])
        if distance > maximum:
            index = candidate
            maximum = distance
    if maximum <= tolerance:
        return [points[0], points[-1]]
    left = simplify_line(points[: index + 1], tolerance)
    right = simplify_line(points[index:], tolerance)
    return left[:-1] + right


def simplify_ring(ring: list[list[float]], tolerance: float) -> list[list[float]]:
    if len(ring) < 5:
        return ring
    open_ring = ring[:-1] if ring[0] == ring[-1] else ring
    # Start at the point farthest from the centroid so the artificial line
    # break is placed at a stable extreme rather than inside a tight bend.
    center_x = sum(point[0] for point in open_ring) / len(open_ring)
    center_y = sum(point[1] for point in open_ring) / len(open_ring)
    start = max(
        range(len(open_ring)),
        key=lambda i: (open_ring[i][0] - center_x) ** 2 + (open_ring[i][1] - center_y) ** 2,
    )
    rotated = open_ring[start:] + open_ring[: start + 1]
    simplified = simplify_line(rotated, tolerance)
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return simplified if len(simplified) >= 4 else ring


def geometry_vertex_count(geometry: dict[str, Any]) -> int:
    coordinates = geometry["coordinates"]
    rings = coordinates if geometry["type"] == "Polygon" else [ring for polygon in coordinates for ring in polygon]
    return sum(len(ring) for ring in rings)


def simplify_geometry(geometry: dict[str, Any], tolerance: float) -> dict[str, Any]:
    if geometry["type"] == "Polygon":
        coordinates = [simplify_ring(ring, tolerance) for ring in geometry["coordinates"]]
    else:
        coordinates = [
            [simplify_ring(ring, tolerance) for ring in polygon]
            for polygon in geometry["coordinates"]
        ]
    return {"type": geometry["type"], "coordinates": coordinates}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=0.0015)
    args = parser.parse_args()
    receipt_path = args.receipt.resolve()
    output_path = args.output.resolve()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    source_path = Path(receipt["local_root"]) / receipt["source_file"]
    if source_path.stat().st_size != receipt["bytes"] or sha256(source_path) != receipt["sha256"]:
        raise ValueError("WBD original response does not match its receipt")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    features = []
    source_vertices = 0
    display_vertices = 0
    for feature in source["features"]:
        geometry = feature["geometry"]
        simplified = simplify_geometry(geometry, args.tolerance)
        source_vertices += geometry_vertex_count(geometry)
        display_vertices += geometry_vertex_count(simplified)
        properties = feature["properties"]
        features.append(
            {
                "type": "Feature",
                "id": properties["huc8"],
                "properties": {
                    "huc8": properties["huc8"],
                    "name": properties["name"],
                    "area_sq_km": properties["areasqkm"],
                    "truth_state": "observed",
                    "display_geometry": "simplified-from-receipted-wbd",
                },
                "geometry": simplified,
            }
        )
    output = {
        "type": "FeatureCollection",
        "metadata": {
            "schema_version": 1,
            "id": "usgs-wbd-boise-river-huc8-display-v1",
            "truth_state": "observed",
            "source_receipt": str(receipt_path.relative_to(ROOT)),
            "source_receipt_sha256": sha256(receipt_path),
            "feature_count": len(features),
            "source_vertex_count": source_vertices,
            "display_vertex_count": display_vertices,
            "simplification_tolerance_degrees": args.tolerance,
            "analysis_geometry": "original-source-only",
            "limitations": receipt["limitations"],
        },
        "features": sorted(features, key=lambda item: item["id"]),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(features)} HUC8 display boundaries; {source_vertices} to {display_vertices} vertices; SHA-256 {sha256(output_path)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
