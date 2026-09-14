#!/usr/bin/env python3
"""Build a lifecycle-explicit EIA-860 regional energy inventory."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

from build_eia_hydropower_inventory import BBOX, integer, number, records, sha256_bytes


TECHNOLOGY_CATEGORIES = (
    "hydropower",
    "solar",
    "wind",
    "storage",
    "natural-gas",
    "geothermal",
    "biomass",
    "petroleum",
    "nuclear",
    "other",
)
LIFECYCLES = (
    "operable",
    "proposed",
    "retired",
    "canceled",
    "indefinitely-postponed",
)


def technology_category(technology: str, energy_source: str) -> str:
    lowered = technology.lower()
    if "hydro" in lowered or energy_source == "WAT":
        return "hydropower"
    if "solar" in lowered or energy_source == "SUN":
        return "solar"
    if "wind" in lowered or energy_source == "WND":
        return "wind"
    if "batter" in lowered:
        return "storage"
    if "natural gas" in lowered or energy_source == "NG":
        return "natural-gas"
    if "geothermal" in lowered or energy_source == "GEO":
        return "geothermal"
    if "biomass" in lowered or "landfill gas" in lowered:
        return "biomass"
    if "petroleum" in lowered:
        return "petroleum"
    if "nuclear" in lowered or energy_source == "NUC":
        return "nuclear"
    return "other"


def lifecycle(sheet_lifecycle: str, status: str) -> str:
    if sheet_lifecycle != "retired-or-canceled":
        return sheet_lifecycle
    if status == "RE":
        return "retired"
    if status == "CN":
        return "canceled"
    if status == "IP":
        return "indefinitely-postponed"
    raise ValueError(f"Unrecognized retired/canceled sheet status: {status!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("receipts/eia860-2025-final-20260914.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/tables/eia-regional-energy-snake-plain-v1.json"),
    )
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    archive_path = Path(receipt["local_root"]) / receipt["object"]["file"]
    archive_bytes = archive_path.read_bytes()
    if len(archive_bytes) != receipt["object"]["bytes"]:
        raise RuntimeError("EIA archive byte receipt mismatch")
    if sha256_bytes(archive_bytes) != receipt["object"]["sha256"]:
        raise RuntimeError("EIA archive hash receipt mismatch")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        plant_member = "2___Plant_Y2025.xlsx"
        generator_member = "3_1_Generator_Y2025.xlsx"
        plant_workbook = archive.read(plant_member)
        generator_workbook = archive.read(generator_member)

    plants: dict[int, dict] = {}
    for row in records(plant_workbook, "xl/worksheets/sheet1.xml"):
        latitude = number(row.get("Latitude", ""))
        longitude = number(row.get("Longitude", ""))
        plant_id = integer(row.get("Plant Code", ""))
        if latitude is None or longitude is None or plant_id is None:
            continue
        if not (BBOX[0] <= longitude <= BBOX[2] and BBOX[1] <= latitude <= BBOX[3]):
            continue
        plants[plant_id] = {
            "plant_id": plant_id,
            "plant_name": row.get("Plant Name") or None,
            "utility_id": integer(row.get("Utility ID", "")),
            "utility_name": row.get("Utility Name") or None,
            "state": row.get("State") or None,
            "county": row.get("County") or None,
            "latitude": latitude,
            "longitude": longitude,
            "balancing_authority_code": row.get("Balancing Authority Code") or None,
            "water_source_name": row.get("Name of Water Source") or None,
            "generator_count": 0,
            "reported_nameplate_capacity_mw": 0.0,
            "technology_categories": [],
            "lifecycles": [],
        }

    generators: list[dict] = []
    sheet_statuses = (
        ("operable", "xl/worksheets/sheet1.xml"),
        ("proposed", "xl/worksheets/sheet2.xml"),
        ("retired-or-canceled", "xl/worksheets/sheet3.xml"),
    )
    for sheet_lifecycle, sheet in sheet_statuses:
        for row in records(generator_workbook, sheet):
            plant_id = integer(row.get("Plant Code", ""))
            if plant_id not in plants:
                continue
            status = row.get("Status", "")
            resolved_lifecycle = lifecycle(sheet_lifecycle, status)
            technology = row.get("Technology", "")
            energy_source = row.get("Energy Source 1", "")
            category = technology_category(technology, energy_source)
            capacity = number(row.get("Nameplate Capacity (MW)", ""))
            generator_id = row.get("Generator ID", "")
            generator = {
                "record_id": (
                    f"eia860-2025:{plant_id}:{generator_id}:{resolved_lifecycle}"
                ),
                "plant_id": plant_id,
                "generator_id": generator_id,
                "lifecycle": resolved_lifecycle,
                "reported_status_code": status or None,
                "technology": technology or None,
                "technology_category": category,
                "prime_mover": row.get("Prime Mover") or None,
                "energy_source_code": energy_source or None,
                "nameplate_capacity_mw": capacity,
                "operating_year": integer(row.get("Operating Year", "")),
                "planned_effective_year": integer(row.get("Effective Year", "")),
                "retirement_year": integer(row.get("Retirement Year", "")),
            }
            generators.append(generator)
            plant = plants[plant_id]
            plant["generator_count"] += 1
            plant["reported_nameplate_capacity_mw"] += capacity or 0.0
            plant["technology_categories"].append(category)
            plant["lifecycles"].append(resolved_lifecycle)

    for plant in plants.values():
        plant["reported_nameplate_capacity_mw"] = round(
            plant["reported_nameplate_capacity_mw"], 3
        )
        plant["technology_categories"] = sorted(set(plant["technology_categories"]))
        plant["lifecycles"] = sorted(set(plant["lifecycles"]))

    lifecycle_counts = Counter(item["lifecycle"] for item in generators)
    technology_counts = Counter(item["technology_category"] for item in generators)
    lifecycle_capacity = {
        name: round(
            sum(
                item["nameplate_capacity_mw"] or 0.0
                for item in generators
                if item["lifecycle"] == name
            ),
            3,
        )
        for name in LIFECYCLES
    }
    output = {
        "schema_version": 1,
        "id": "eia860-2025-snake-plain-regional-energy-v1",
        "truth_state": "ingested",
        "source_receipt": str(args.receipt),
        "source_receipt_sha256": hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
        "source_archive": {
            "sha256": receipt["object"]["sha256"],
            "plant_member": plant_member,
            "plant_member_sha256": sha256_bytes(plant_workbook),
            "generator_member": generator_member,
            "generator_member_sha256": sha256_bytes(generator_workbook),
        },
        "bbox_epsg_4326": list(BBOX),
        "plant_count": len(plants),
        "plants_with_generators": sum(
            1 for plant in plants.values() if plant["generator_count"] > 0
        ),
        "generator_count": len(generators),
        "generator_lifecycle_counts": {
            name: lifecycle_counts.get(name, 0) for name in LIFECYCLES
        },
        "generator_technology_counts": {
            name: technology_counts.get(name, 0) for name in TECHNOLOGY_CATEGORIES
        },
        "reported_nameplate_capacity_mw_by_lifecycle": lifecycle_capacity,
        "plants": sorted(plants.values(), key=lambda item: item["plant_id"]),
        "generators": sorted(
            generators,
            key=lambda item: (
                item["plant_id"],
                item["generator_id"],
                item["lifecycle"],
            ),
        ),
        "limitations": [
            "Plant and generator locations are reported EIA records inside the explicit scene bounds.",
            "Lifecycle is derived from the official EIA workbook sheet and retained status code; canceled and indefinitely postponed records are not called planned or active.",
            "Reported nameplate capacity is not a claim of current output, dispatch, availability, or grid interconnection.",
            "No EIA plant is linked to a NID dam, model bus, or branch by this transform.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(
        f"Verified {output['plant_count']} plants and {output['generator_count']} "
        f"generators: {json.dumps(output['generator_lifecycle_counts'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
