#!/usr/bin/env python3
"""Build a bounded EIA-860 hydropower inventory and reviewable dam links."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from difflib import SequenceMatcher
from pathlib import Path


SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
BBOX = (-119.0, 42.0, -111.0, 46.0)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def column_index(reference: str) -> int:
    match = re.match(r"[A-Z]+", reference)
    if not match:
        raise ValueError(f"Invalid cell reference: {reference}")
    result = 0
    for char in match.group():
        result = result * 26 + ord(char) - 64
    return result - 1


def workbook_rows(workbook: bytes, sheet: str):
    with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.iter(SHEET_NS + "t"))
                for item in root
            ]
        with archive.open(sheet) as stream:
            for _, row in ET.iterparse(stream, events=("end",)):
                if row.tag != SHEET_NS + "row":
                    continue
                values: dict[int, str] = {}
                for cell in row.findall(SHEET_NS + "c"):
                    index = column_index(cell.attrib["r"])
                    value_node = cell.find(SHEET_NS + "v")
                    value = "" if value_node is None else value_node.text or ""
                    cell_type = cell.attrib.get("t")
                    if cell_type == "s" and value:
                        value = shared[int(value)]
                    elif cell_type == "inlineStr":
                        value = "".join(
                            node.text or "" for node in cell.iter(SHEET_NS + "t")
                        )
                    values[index] = value.strip()
                yield values
                row.clear()


def records(workbook: bytes, sheet: str):
    rows = iter(workbook_rows(workbook, sheet))
    next(rows)
    header = next(rows)
    for row in rows:
        yield {name: row.get(index, "") for index, name in header.items()}


def number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def integer(value: str) -> int | None:
    parsed = number(value)
    return None if parsed is None else int(parsed)


def normalized_name(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.lower())
    ignored = {
        "dam",
        "hydro",
        "hydroelectric",
        "id",
        "plant",
        "power",
        "project",
        "the",
    }
    return " ".join(word for word in words if word not in ignored)


def haversine_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius_km = 6371.0088
    lat1, lat2 = math.radians(a_lat), math.radians(b_lat)
    dlat = lat2 - lat1
    dlon = math.radians(b_lon - a_lon)
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("receipts/eia860-2025-final-20260914.json"),
    )
    parser.add_argument(
        "--dams",
        type=Path,
        default=Path("data/tables/usace-nid-snake-plain-dams-v3.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/tables/eia-hydropower-snake-plain-v1.json"),
    )
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    archive_path = Path(receipt["local_root"]) / receipt["object"]["file"]
    if archive_path.stat().st_size != receipt["object"]["bytes"]:
        raise RuntimeError("EIA archive byte receipt mismatch")
    archive_bytes = archive_path.read_bytes()
    if sha256_bytes(archive_bytes) != receipt["object"]["sha256"]:
        raise RuntimeError("EIA archive hash receipt mismatch")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        plant_member = "2___Plant_Y2025.xlsx"
        generator_member = "3_1_Generator_Y2025.xlsx"
        plant_workbook = archive.read(plant_member)
        generator_workbook = archive.read(generator_member)

    plants: dict[int, dict] = {}
    for row in records(plant_workbook, "xl/worksheets/sheet1.xml"):
        latitude = number(row["Latitude"])
        longitude = number(row["Longitude"])
        plant_id = integer(row["Plant Code"])
        if latitude is None or longitude is None or plant_id is None:
            continue
        if not (BBOX[0] <= longitude <= BBOX[2] and BBOX[1] <= latitude <= BBOX[3]):
            continue
        plants[plant_id] = {
            "plant_id": plant_id,
            "plant_name": row["Plant Name"],
            "utility_id": integer(row["Utility ID"]),
            "utility_name": row["Utility Name"],
            "state": row["State"],
            "county": row["County"],
            "latitude": latitude,
            "longitude": longitude,
            "balancing_authority_code": row["Balancing Authority Code"] or None,
            "water_source_name": row["Name of Water Source"] or None,
            "generator_ids": [],
            "nameplate_capacity_mw": 0.0,
            "statuses": [],
        }

    generators: list[dict] = []
    sheet_statuses = (
        ("operable", "xl/worksheets/sheet1.xml"),
        ("proposed", "xl/worksheets/sheet2.xml"),
        ("retired-or-canceled", "xl/worksheets/sheet3.xml"),
    )
    regional_generator_count = 0
    for lifecycle, sheet in sheet_statuses:
        for row in records(generator_workbook, sheet):
            plant_id = integer(row["Plant Code"])
            if plant_id not in plants:
                continue
            regional_generator_count += 1
            technology = row.get("Technology", "")
            energy_source = row.get("Energy Source 1", "")
            if "hydro" not in technology.lower() and energy_source != "WAT":
                continue
            capacity = number(row.get("Nameplate Capacity (MW)", ""))
            generator = {
                "plant_id": plant_id,
                "generator_id": row["Generator ID"],
                "lifecycle": lifecycle,
                "reported_status_code": row.get("Status") or None,
                "technology": technology,
                "prime_mover": row.get("Prime Mover") or None,
                "energy_source_code": energy_source or None,
                "nameplate_capacity_mw": capacity,
                "operating_year": integer(row.get("Operating Year", "")),
                "planned_effective_year": integer(row.get("Effective Year", "")),
            }
            generators.append(generator)
            plant = plants[plant_id]
            plant["generator_ids"].append(generator["generator_id"])
            plant["nameplate_capacity_mw"] += capacity or 0.0
            plant["statuses"].append(lifecycle)

    hydro_plants = [plant for plant in plants.values() if plant["generator_ids"]]
    for plant in hydro_plants:
        plant["nameplate_capacity_mw"] = round(plant["nameplate_capacity_mw"], 3)
        plant["statuses"] = sorted(set(plant["statuses"]))

    dam_table = json.loads(args.dams.read_text(encoding="utf-8"))
    links: list[dict] = []
    for dam in dam_table["records"]:
        if not dam["hydroelectric_purpose"]:
            continue
        candidates = []
        dam_normalized = normalized_name(dam["name"])
        for plant in hydro_plants:
            distance = haversine_km(
                dam["latitude"],
                dam["longitude"],
                plant["latitude"],
                plant["longitude"],
            )
            plant_normalized = normalized_name(plant["plant_name"])
            similarity = SequenceMatcher(None, dam_normalized, plant_normalized).ratio()
            candidates.append((distance, -similarity, plant, similarity))
        distance, _, plant, similarity = min(candidates)
        if distance <= 0.5:
            match_state = "strong-candidate-pending-review"
        elif distance <= 2.0 and similarity >= 0.45:
            match_state = "strong-candidate-pending-review"
        elif distance <= 10.0:
            match_state = "candidate-pending-review"
        else:
            match_state = "unmatched"
        links.append(
            {
                "dam_provider_record_id": dam["provider_record_id"],
                "dam_nid_id": dam["nid_id"],
                "dam_name": dam["name"],
                "dam_connectivity_class": dam["watershed_path"]["classification"],
                "candidate_plant_id": plant["plant_id"],
                "candidate_plant_name": plant["plant_name"],
                "distance_km": round(distance, 3),
                "normalized_name_similarity": round(similarity, 4),
                "match_state": match_state,
                "review_state": "pending-human-review",
            }
        )

    state_counts: dict[str, int] = {}
    for link in links:
        state_counts[link["match_state"]] = state_counts.get(link["match_state"], 0) + 1
    output = {
        "schema_version": 1,
        "id": "eia860-2025-snake-plain-hydropower-v1",
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
        "regional_plant_count": len(plants),
        "regional_generator_count": regional_generator_count,
        "hydropower_plant_count": len(hydro_plants),
        "hydropower_generator_count": len(generators),
        "hydroelectric_purpose_dam_count": len(links),
        "candidate_state_counts": state_counts,
        "plants": sorted(hydro_plants, key=lambda item: item["plant_id"]),
        "generators": sorted(
            generators,
            key=lambda item: (item["plant_id"], item["generator_id"], item["lifecycle"]),
        ),
        "dam_hydropower_links": links,
        "limitations": [
            "Every dam-to-plant link is pending human review; no candidate is an accepted identity crosswalk.",
            "Nearest distance and normalized-name similarity are retained separately.",
            "EIA-860 covers plants with at least one megawatt of combined nameplate capacity.",
            "A hydropower plant match does not establish an electrical branch or bus connection.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"Verified {len(hydro_plants)} hydro plants, {len(generators)} hydro generators, "
        f"{len(links)} dam candidates: {json.dumps(state_counts, sort_keys=True)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
