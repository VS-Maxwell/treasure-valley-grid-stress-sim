#!/usr/bin/env python3
"""Pack verified EIA-860 hydropower plants for the browser renderer."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--table",
        type=Path,
        default=Path("data/tables/eia-hydropower-snake-plain-v1.json"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("app/public/data/eia-hydropower-manifest-v1.json"),
    )
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path("app/public/data/eia-hydropower-f32-v1.bin"),
    )
    args = parser.parse_args()
    table = json.loads(args.table.read_text(encoding="utf-8"))
    values: list[float] = []
    operable_count = 0
    total_capacity = 0.0
    for plant in table["plants"]:
        operable = "operable" in plant["statuses"]
        operable_count += int(operable)
        total_capacity += plant["nameplate_capacity_mw"]
        values.extend(
            (
                plant["longitude"],
                plant["latitude"],
                plant["nameplate_capacity_mw"],
                1.0 if operable else 0.0,
            )
        )
    args.binary.parent.mkdir(parents=True, exist_ok=True)
    args.binary.write_bytes(struct.pack(f"<{len(values)}f", *values))
    manifest = {
        "schema_version": 1,
        "id": "eia860-2025-snake-plain-hydropower-points-v1",
        "truth_state": "ingested",
        "normalized_table": str(args.table),
        "normalized_table_sha256": sha256(args.table),
        "bbox_epsg_4326": table["bbox_epsg_4326"],
        "plant_count": len(table["plants"]),
        "generator_count": len(table["generators"]),
        "operable_plant_count": operable_count,
        "reported_nameplate_capacity_mw": round(total_capacity, 3),
        "dam_candidate_counts": table["candidate_state_counts"],
        "dam_link_review_state": "pending-human-review",
        "binary": {
            "file": args.binary.name,
            "bytes": args.binary.stat().st_size,
            "sha256": sha256(args.binary),
            "encoding": "little-endian-float32",
            "stride": 4,
            "order": "longitude-latitude-reported-nameplate-capacity-mw-operable-flag",
        },
        "limitations": table["limitations"],
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"Packed {manifest['plant_count']} plants and {manifest['generator_count']} "
        f"generators into {manifest['binary']['bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
