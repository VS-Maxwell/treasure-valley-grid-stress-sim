#!/usr/bin/env python3
"""Extract the legacy 94-bus/156-branch screening model without inventing topology."""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "legacy.html"
GRID = ROOT / "data/grid-core.json"
OUTPUTS = (
    ROOT / "data/tables/grid-screening-model.json",
    ROOT / "app/public/data/grid-screening-model.json",
)
SCENARIOS = ("base", "dc25", "dc50", "all25", "all50", "drought", "n1")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assigned_json(source: str, marker: str) -> Any:
    """Read one JSON object assigned inside the preserved legacy HTML."""
    cursor = source.index(marker) + len(marker)
    while source[cursor].isspace():
        cursor += 1
    start = cursor
    stack: list[str] = []
    quote: str | None = None
    escaped = False
    pairs = {"{": "}", "[": "]"}
    for cursor in range(start, len(source)):
        char = source[cursor]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
            if not stack:
                return json.loads(source[start : cursor + 1])
    raise ValueError(f"Unterminated JSON assignment: {marker}")


def normalized_label(value: object) -> str:
    return " ".join(str(value or "").upper().split())


def main() -> int:
    legacy_source = LEGACY.read_text(encoding="utf-8")
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    n1 = assigned_json(legacy_source, "window.N1_CONTINGENCY=")
    loadings = assigned_json(legacy_source, "window.LINE_LOADINGS=")

    if tuple(loadings) != SCENARIOS:
        raise ValueError(f"Unexpected screening scenarios: {tuple(loadings)}")
    contingencies = n1["contingencies"]
    if len(grid["subs"]["features"]) != 94 or len(contingencies) != 156:
        raise ValueError("Expected the preserved 94-bus/156-branch screening model")
    corridors = {
        str(feature["properties"]["line_id"]): feature
        for feature in grid["trans"]["features"]
    }
    if set(contingencies) - set(corridors):
        raise ValueError("A screening branch has no exact source corridor line_id")
    if any(set(values) != set(contingencies) for values in loadings.values()):
        raise ValueError("Scenario loading keys do not match the 156 branches")

    label_counts = Counter(
        normalized_label(feature["properties"]["name"])
        for feature in grid["subs"]["features"]
    )
    label_seen: defaultdict[str, int] = defaultdict(int)
    bus_ids_by_label: defaultdict[str, list[str]] = defaultdict(list)
    buses = []
    for index, feature in enumerate(grid["subs"]["features"]):
        properties = feature["properties"]
        label = normalized_label(properties["name"])
        label_seen[label] += 1
        bus_id = f"bus-{index + 1:03d}"
        bus_ids_by_label[label].append(bus_id)
        suffix = f" {label_seen[label]:02d}" if label_counts[label] > 1 else ""
        buses.append(
            {
                "bus_id": bus_id,
                "label": label,
                "display_label": f"{label}{suffix}",
                "label_is_unique": label_counts[label] == 1,
                "source_feature_index": index,
                "longitude": feature["geometry"]["coordinates"][0],
                "latitude": feature["geometry"]["coordinates"][1],
                "minimum_voltage_kv": properties["min_voltage_kv"],
                "maximum_voltage_kv": properties["max_voltage_kv"],
                "mapped_corridor_count": properties["lines"],
                "truth_state": "ingested",
            }
        )

    branches = []
    unique_endpoint_branches = 0
    for branch_id, contingency in contingencies.items():
        corridor = corridors[branch_id]
        properties = corridor["properties"]
        from_label = normalized_label(contingency["fromBus"])
        to_label = normalized_label(contingency["toBus"])
        from_candidates = bus_ids_by_label[from_label]
        to_candidates = bus_ids_by_label[to_label]
        endpoints_unique = len(from_candidates) == 1 and len(to_candidates) == 1
        unique_endpoint_branches += int(endpoints_unique)
        branches.append(
            {
                "branch_id": branch_id,
                "corridor_line_id": branch_id,
                "corridor_feature_index": grid["trans"]["features"].index(corridor),
                "display_name": contingency["trippedName"],
                "from_bus_label": from_label,
                "to_bus_label": to_label,
                "from_bus_candidates": from_candidates,
                "to_bus_candidates": to_candidates,
                "endpoint_identity_state": (
                    "unique-label" if endpoints_unique else "ambiguous-label"
                ),
                "source_sub_from": properties["sub_from"],
                "source_sub_to": properties["sub_to"],
                "voltage_kv": properties["voltage_kv"],
                "status": properties["status"],
                "owner": properties["owner"],
                "loading_pct": {
                    scenario: loadings[scenario][branch_id]
                    for scenario in SCENARIOS
                },
                "n1": {
                    "converged": contingency["converged"],
                    "maximum_loading_pct": contingency["maxLoadingPct"],
                    "overload_count": contingency["nOverloads"],
                },
                "truth_state": "modeled-screening",
            }
        )

    scenario_summaries = {}
    for scenario in SCENARIOS:
        values = [float(branch["loading_pct"][scenario]) for branch in branches]
        scenario_summaries[scenario] = {
            "maximum_loading_pct": max(values),
            "median_loading_pct": round(statistics.median(values), 3),
            "branches_at_or_above_80_pct": sum(value >= 80 for value in values),
            "branches_at_or_above_100_pct": sum(value >= 100 for value in values),
        }

    payload = {
        "schema_version": 1,
        "id": "treasure-valley-grid-screening-v1",
        "created_at": "2026-09-14T22:10:00Z",
        "source": "Exact extraction of legacy pandapower/DC screening outputs",
        "source_legacy_sha256": sha256(LEGACY),
        "source_grid_core_sha256": sha256(GRID),
        "truth_state": "modeled-screening",
        "operational_use": False,
        "model": n1["model"],
        "calibration": n1["calibration"],
        "base_maximum_loading_pct": n1["base_max_pct"],
        "source_generated_at": n1["generated"],
        "counts": {
            "buses": len(buses),
            "branches": len(branches),
            "map_corridors": len(grid["trans"]["features"]),
            "branches_with_unique_endpoint_labels": unique_endpoint_branches,
            "branches_with_ambiguous_endpoint_labels": len(branches)
            - unique_endpoint_branches,
        },
        "scenarios": list(SCENARIOS),
        "scenario_summaries": scenario_summaries,
        "buses": buses,
        "branches": branches,
        "limitations": [
            "This is a calibrated DC screening graph, not an operational utility model.",
            "Thermal ratings, impedance, dispatch, and demand assumptions are not independently validated.",
            "The 27 source buses labeled TAP cannot be uniquely recovered from legacy endpoint labels alone.",
            "Every branch is joined to map geometry only by its exact preserved corridor line_id.",
        ],
    }
    encoded = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
        print(f"Wrote {output.relative_to(ROOT)} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
