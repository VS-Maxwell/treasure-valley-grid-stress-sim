#!/usr/bin/env python3
"""Pack EIA-860 regional generator records for the browser renderer."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


TECHNOLOGY_CODES = {
    "hydropower": 0,
    "solar": 1,
    "wind": 2,
    "storage": 3,
    "natural-gas": 4,
    "geothermal": 5,
    "biomass": 6,
    "petroleum": 7,
    "nuclear": 8,
    "other": 9,
}
LIFECYCLE_CODES = {
    "operable": 0,
    "proposed": 1,
    "retired": 2,
    "canceled": 3,
    "indefinitely-postponed": 4,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--table",
        type=Path,
        default=Path("data/tables/eia-regional-energy-snake-plain-v1.json"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("app/public/data/eia-regional-energy-manifest-v1.json"),
    )
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path("app/public/data/eia-regional-energy-f32-v1.bin"),
    )
    args = parser.parse_args()
    table = json.loads(args.table.read_text(encoding="utf-8"))
    plants = {plant["plant_id"]: plant for plant in table["plants"]}
    values: list[float] = []
    for generator in table["generators"]:
        plant = plants[generator["plant_id"]]
        values.extend(
            (
                plant["longitude"],
                plant["latitude"],
                generator["nameplate_capacity_mw"] or 0.0,
                TECHNOLOGY_CODES[generator["technology_category"]],
                LIFECYCLE_CODES[generator["lifecycle"]],
            )
        )
    args.binary.parent.mkdir(parents=True, exist_ok=True)
    args.binary.write_bytes(struct.pack(f"<{len(values)}f", *values))
    manifest = {
        "schema_version": 1,
        "id": "eia860-2025-snake-plain-regional-energy-points-v1",
        "truth_state": "ingested",
        "normalized_table": str(args.table),
        "normalized_table_sha256": sha256(args.table),
        "bbox_epsg_4326": table["bbox_epsg_4326"],
        "plant_count": table["plant_count"],
        "plants_with_generators": table["plants_with_generators"],
        "generator_count": table["generator_count"],
        "generator_lifecycle_counts": table["generator_lifecycle_counts"],
        "generator_technology_counts": table["generator_technology_counts"],
        "reported_nameplate_capacity_mw_by_lifecycle": table[
            "reported_nameplate_capacity_mw_by_lifecycle"
        ],
        "technology_codes": TECHNOLOGY_CODES,
        "lifecycle_codes": LIFECYCLE_CODES,
        "binary": {
            "file": args.binary.name,
            "bytes": args.binary.stat().st_size,
            "sha256": sha256(args.binary),
            "encoding": "little-endian-float32",
            "stride": 5,
            "order": "longitude-latitude-reported-nameplate-capacity-mw-technology-code-lifecycle-code",
        },
        "limitations": table["limitations"],
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Packed {manifest['generator_count']} generators across "
        f"{manifest['plant_count']} plants into {manifest['binary']['bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
