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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    source_path = Path(receipt["local_root"]) / receipt["source_file"]
    if (
        source_path.stat().st_size != receipt["bytes"]
        or sha256(source_path) != receipt["sha256"]
    ):
        raise ValueError("NID original response does not match its receipt")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    records = []
    for feature in source["features"]:
        properties = feature["properties"]
        longitude, latitude = feature["geometry"]["coordinates"][:2]
        purposes = properties.get("PURPOSES") or ""
        records.append(
            {
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
                "regional_water_connectivity": "unresolved",
                "grid_link_state": "unmatched",
            }
        )
    records.sort(key=lambda record: record["provider_record_id"])
    payload = {
        "schema_version": 1,
        "id": "usace-nid-regional-dams-v1",
        "truth_state": "observed",
        "source_receipt": str(args.receipt.relative_to(ROOT)),
        "source_receipt_sha256": sha256(args.receipt),
        "bbox_epsg_4326": receipt["bbox_epsg_4326"],
        "dam_count": len(records),
        "hydroelectric_purpose_count": sum(
            record["hydroelectric_purpose"] for record in records
        ),
        "connectivity_state": "unresolved-pending-upstream-watershed-graph",
        "records": records,
        "limitations": receipt["limitations"],
    }
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
        )
    ]
    args.binary.write_bytes(struct.pack(f"<{len(values)}f", *values))
    browser_manifest = {
        "schema_version": 1,
        "id": "usace-nid-regional-dam-points-v1",
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
            "stride": 3,
            "order": "longitude-latitude-hydroelectric-purpose-flag",
        },
        "limitations": payload["limitations"],
    }
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
