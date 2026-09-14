#!/usr/bin/env python3
"""Build a compact offline regional dam table from a verified NID response."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT = ROOT / "receipts/usace-nid-regional-dams-20260914.json"
DEFAULT_OUTPUT = ROOT / "data/tables/usace-nid-regional-dams.json"
DEFAULT_MANIFEST = ROOT / "app/public/data/usace-nid-dams-manifest.json"
DEFAULT_BINARY = ROOT / "app/public/data/usace-nid-dams-f32.bin"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def point_in_ring(longitude: float, latitude: float, ring: list[list[float]]) -> bool:
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        intersects = (y1 > latitude) != (y2 > latitude) and longitude < (
            (x2 - x1) * (latitude - y1) / (y2 - y1) + x1
        )
        if intersects:
            inside = not inside
        previous = current
    return inside


def point_in_polygon(longitude: float, latitude: float, polygon: list[list[list[float]]]) -> bool:
    return bool(polygon) and point_in_ring(longitude, latitude, polygon[0]) and not any(
        point_in_ring(longitude, latitude, hole) for hole in polygon[1:]
    )


def point_in_geometry(longitude: float, latitude: float, geometry: dict[str, object]) -> bool:
    coordinates = geometry.get("coordinates")
    if geometry.get("type") == "Polygon" and isinstance(coordinates, list):
        return point_in_polygon(longitude, latitude, coordinates)
    if geometry.get("type") == "MultiPolygon" and isinstance(coordinates, list):
        return any(point_in_polygon(longitude, latitude, polygon) for polygon in coordinates)
    raise ValueError("Unsupported watershed geometry")


def load_receipted_source(receipt_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    source_path = Path(receipt["local_root"]) / receipt["source_file"]
    if source_path.stat().st_size != receipt["bytes"] or sha256(source_path) != receipt["sha256"]:
        raise ValueError(f"Original response does not match receipt: {receipt_path.name}")
    return receipt, json.loads(source_path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--watershed-receipt", type=Path)
    parser.add_argument("--table-id", default="usace-nid-regional-dams-v1")
    parser.add_argument("--manifest-id", default="usace-nid-regional-dam-points-v1")
    args = parser.parse_args()
    args.receipt = args.receipt.resolve()
    args.output = args.output.resolve()
    args.manifest = args.manifest.resolve()
    args.binary = args.binary.resolve()
    if args.watershed_receipt:
        args.watershed_receipt = args.watershed_receipt.resolve()
    receipt, source = load_receipted_source(args.receipt)
    watersheds: list[dict[str, object]] = []
    watershed_receipt = None
    if args.watershed_receipt:
        watershed_receipt, watershed_source = load_receipted_source(
            args.watershed_receipt
        )
        watersheds = list(watershed_source["features"])
    records = []
    for feature in source["features"]:
        properties = feature["properties"]
        longitude, latitude = feature["geometry"]["coordinates"][:2]
        purposes = properties.get("PURPOSES") or ""
        matches = [
            watershed
            for watershed in watersheds
            if point_in_geometry(longitude, latitude, watershed["geometry"])
        ]
        if len(matches) > 1:
            raise ValueError(f"Dam lies in multiple HUC8 polygons: {properties['OBJECTID']}")
        watershed_properties = matches[0]["properties"] if matches else {}
        member = bool(matches)
        record = {
                "provider_record_id": (
                    f"nid:{properties['NIDID']}:objectid:{properties['OBJECTID']}"
                    if properties.get("NIDID")
                    else f"objectid:{properties['OBJECTID']}"
                ),
                "object_id": properties["OBJECTID"],
                "nid_id": properties.get("NIDID"),
                "name": properties.get("NAME"),
                "longitude": longitude,
                "latitude": latitude,
                "river_or_stream": properties.get("RIVER_OR_STREAM"),
                "purposes": purposes,
                "dam_type": properties.get("PRIMARY_DAM_TYPE"),
                "height_feet": properties.get("DAM_HEIGHT"),
                "storage_acre_feet": properties.get("NID_STORAGE"),
                "year_completed": properties.get("YEAR_COMPLETED"),
                "hazard_potential": properties.get("HAZARD_POTENTIAL"),
                "operational_status": properties.get("OPERATIONAL_STATUS"),
                "hydroelectric_purpose": "hydroelectric" in purposes.lower(),
                "regional_water_connectivity": "huc8-membership-screening-pending-directed-flow-path"
                if member
                else "unresolved",
                "grid_link_state": "unmatched",
            }
        if watersheds:
            record.update(
                {
                    "huc8": watershed_properties.get("huc8"),
                    "huc8_name": watershed_properties.get("name"),
                    "boise_huc8_member": member,
                    "watershed_membership_state": "observed-wbd-membership"
                    if member
                    else "outside-target-huc8",
                }
            )
        records.append(record)
    records.sort(key=lambda record: record["provider_record_id"])
    payload = {
        "schema_version": 1,
        "id": args.table_id,
        "truth_state": "observed",
        "source_receipt": str(args.receipt.relative_to(ROOT)),
        "source_receipt_sha256": sha256(args.receipt),
        "bbox_epsg_4326": receipt["bbox_epsg_4326"],
        "dam_count": len(records),
        "hydroelectric_purpose_count": sum(
            record["hydroelectric_purpose"] for record in records
        ),
        "connectivity_state": "huc8-membership-screening-pending-directed-flow-path"
        if watersheds
        else "unresolved-pending-upstream-watershed-graph",
        "records": records,
        "limitations": receipt["limitations"],
    }
    if watersheds:
        payload.update(
            {
                "boise_huc8_member_count": sum(
                    record["boise_huc8_member"] for record in records
                ),
                "boise_huc8_hydroelectric_purpose_count": sum(
                    record["boise_huc8_member"]
                    and record["hydroelectric_purpose"]
                    for record in records
                ),
                "watershed_source_receipt": str(
                    args.watershed_receipt.relative_to(ROOT)
                ),
                "watershed_source_receipt_sha256": sha256(args.watershed_receipt),
            }
        )
    args.output.write_text(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    values = [
        value
        for record in records
        for value in (
            record["longitude"],
            record["latitude"],
            1.0 if record["hydroelectric_purpose"] else 0.0,
            *([1.0 if record["boise_huc8_member"] else 0.0] if watersheds else []),
        )
    ]
    args.binary.write_bytes(struct.pack(f"<{len(values)}f", *values))
    browser_manifest = {
        "schema_version": 1,
        "id": args.manifest_id,
        "truth_state": "observed",
        "source_receipt": str(args.receipt.relative_to(ROOT)),
        "source_receipt_sha256": sha256(args.receipt),
        "normalized_table": str(args.output.relative_to(ROOT)),
        "normalized_table_sha256": sha256(args.output),
        "bbox_epsg_4326": receipt["bbox_epsg_4326"],
        "dam_count": len(records),
        "hydroelectric_purpose_count": payload["hydroelectric_purpose_count"],
        "connectivity_state": payload["connectivity_state"],
        "binary": {
            "file": args.binary.name,
            "bytes": args.binary.stat().st_size,
            "sha256": sha256(args.binary),
            "encoding": "little-endian-float32",
            "stride": 4 if watersheds else 3,
            "order": "longitude-latitude-hydroelectric-purpose-flag-boise-huc8-member-flag"
            if watersheds
            else "longitude-latitude-hydroelectric-purpose-flag",
        },
        "limitations": payload["limitations"],
    }
    if watersheds:
        browser_manifest.update(
            {
                "boise_huc8_member_count": payload["boise_huc8_member_count"],
                "boise_huc8_hydroelectric_purpose_count": payload[
                    "boise_huc8_hydroelectric_purpose_count"
                ],
                "watershed_source_receipt": payload["watershed_source_receipt"],
                "watershed_source_receipt_sha256": payload[
                    "watershed_source_receipt_sha256"
                ],
            }
        )
    args.manifest.write_text(
        json.dumps(browser_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(records)} dam records; "
        f"{payload['hydroelectric_purpose_count']} hydroelectric-purpose candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
