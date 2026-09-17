#!/usr/bin/env python3
"""Resolve only evidence-supported endpoint identities in the legacy grid pack."""

from __future__ import annotations

import hashlib
import json
import math
import argparse
import os
import tempfile
from collections import defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/tables/grid-screening-model.json"
GRID = ROOT / "data/grid-core.json"
OUTPUTS = (
    ROOT / "data/tables/grid-screening-model-v2.json",
    ROOT / "app/public/data/grid-screening-model-v2.json",
)
MAX_ENDPOINT_DISTANCE_KM = 0.005
MIN_RUNNER_UP_MARGIN_KM = 0.005


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def haversine_km(left: list[float], right: list[float]) -> float:
    lon1, lat1 = map(math.radians, left)
    lon2, lat2 = map(math.radians, right)
    delta_lon = lon2 - lon1
    delta_lat = lat2 - lat1
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 6371.0088 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def geometry_endpoints(geometry: dict) -> tuple[list[float], list[float]]:
    if geometry["type"] == "LineString":
        coordinates = geometry["coordinates"]
        return coordinates[0], coordinates[-1]
    if geometry["type"] == "MultiLineString":
        coordinates = geometry["coordinates"]
        return coordinates[0][0], coordinates[-1][-1]
    raise ValueError(f"Unsupported corridor geometry: {geometry['type']}")


def endpoint_receipt(
    candidates: list[str],
    endpoint: list[float],
    buses_by_id: dict[str, dict],
) -> dict:
    ranked = sorted(
        (
            haversine_km(
                endpoint,
                [buses_by_id[bus_id]["longitude"], buses_by_id[bus_id]["latitude"]],
            ),
            bus_id,
        )
        for bus_id in candidates
    )
    nearest_distance, nearest_id = ranked[0]
    runner_up_margin = (
        ranked[1][0] - nearest_distance if len(ranked) > 1 else None
    )
    if len(candidates) == 1:
        return {
            "bus_id": nearest_id,
            "method": "unique-preserved-label",
            "nearest_distance_km": round(nearest_distance, 6),
            "runner_up_margin_km": None,
        }
    accepted = (
        nearest_distance <= MAX_ENDPOINT_DISTANCE_KM
        and runner_up_margin is not None
        and runner_up_margin >= MIN_RUNNER_UP_MARGIN_KM
    )
    return {
        "bus_id": nearest_id if accepted else None,
        "method": (
            "exact-corridor-endpoint"
            if accepted
            else "blocked-insufficient-geometry-evidence"
        ),
        "nearest_distance_km": round(nearest_distance, 6),
        "runner_up_margin_km": round(runner_up_margin, 6),
    }


def connected_component_count(bus_ids: set[str], edges: list[tuple[str, str]]) -> int:
    neighbors: dict[str, set[str]] = defaultdict(set)
    for left, right in edges:
        neighbors[left].add(right)
        neighbors[right].add(left)
    unseen = set(bus_ids)
    components = 0
    while unseen:
        components += 1
        queue = deque([unseen.pop()])
        while queue:
            current = queue.popleft()
            for neighbor in neighbors[current] & unseen:
                unseen.remove(neighbor)
                queue.append(neighbor)
    return components


def write_atomically(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent, text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        Path(temporary_name).replace(path)
    except BaseException:
        os.unlink(temporary_name)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the evidence-constrained grid screening topology pack."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate inputs and topology counts without replacing output files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        grid = json.loads(GRID.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Unable to read topology inputs: {error}") from error
    if source["schema_version"] != 1:
        raise ValueError("Expected grid screening schema v1")
    if source["source_grid_core_sha256"] != sha256(GRID):
        raise ValueError("Grid-core hash no longer matches screening v1")
    if len(source["buses"]) != 94 or len(source["branches"]) != 156:
        raise ValueError("Unexpected screening model dimensions")
    if len(grid["trans"]["features"]) != 244:
        raise ValueError("Unexpected mapped corridor count")

    buses_by_id = {bus["bus_id"]: bus for bus in source["buses"]}
    resolved_edges: list[tuple[str, str]] = []
    geometry_resolved_taps: set[str] = set()
    branches = []
    resolved_endpoints = 0
    geometry_resolved_endpoints = 0
    unresolved_endpoints = 0

    for original in source["branches"]:
        feature = grid["trans"]["features"][original["corridor_feature_index"]]
        if feature["properties"]["line_id"] != original["corridor_line_id"]:
            raise ValueError(f"Corridor join drifted for {original['branch_id']}")
        start, end = geometry_endpoints(feature["geometry"])
        from_receipt = endpoint_receipt(
            original["from_bus_candidates"], start, buses_by_id
        )
        to_receipt = endpoint_receipt(
            original["to_bus_candidates"], end, buses_by_id
        )
        for receipt in (from_receipt, to_receipt):
            if receipt["bus_id"] is None:
                unresolved_endpoints += 1
            else:
                resolved_endpoints += 1
                if receipt["method"] == "exact-corridor-endpoint":
                    geometry_resolved_endpoints += 1
                    if buses_by_id[receipt["bus_id"]]["label"] == "TAP":
                        geometry_resolved_taps.add(receipt["bus_id"])
        fully_resolved = (
            from_receipt["bus_id"] is not None
            and to_receipt["bus_id"] is not None
            and from_receipt["bus_id"] != to_receipt["bus_id"]
        )
        if fully_resolved:
            resolved_edges.append((from_receipt["bus_id"], to_receipt["bus_id"]))
        branch = dict(original)
        branch.update(
            {
                "from_bus_id": from_receipt["bus_id"],
                "to_bus_id": to_receipt["bus_id"],
                "from_endpoint_receipt": from_receipt,
                "to_endpoint_receipt": to_receipt,
                "topology_state": "resolved" if fully_resolved else "blocked-missing",
            }
        )
        branches.append(branch)

    resolved_branches = len(resolved_edges)
    blocked_branches = len(branches) - resolved_branches
    component_count = connected_component_count(set(buses_by_id), resolved_edges)
    expected = (resolved_branches, blocked_branches, resolved_endpoints, unresolved_endpoints)
    if expected != (139, 17, 292, 20):
        raise ValueError(f"Topology crosswalk counts drifted: {expected}")
    if geometry_resolved_endpoints != 75 or len(geometry_resolved_taps) != 27:
        raise ValueError("Exact endpoint resolution counts drifted")
    if component_count != 1:
        raise ValueError("Resolved topology no longer contains one connected component")

    payload = dict(source)
    payload.update(
        {
            "schema_version": 2,
            "id": "treasure-valley-grid-screening-model-v2",
            "created_at": "2026-09-14T22:10:00Z",
            "source_screening_v1_sha256": sha256(SOURCE),
            "endpoint_resolution": {
                "method": "preserved unique label or exact mapped-corridor endpoint",
                "maximum_endpoint_distance_km": MAX_ENDPOINT_DISTANCE_KM,
                "minimum_runner_up_margin_km": MIN_RUNNER_UP_MARGIN_KM,
                "orientation": "GeoJSON start maps to legacy from label; end maps to legacy to label",
            },
            "fresh_solve_ready": False,
            "missing_solver_inputs": [
                "branch resistance and reactance",
                "branch thermal ratings",
                "bus load and generator dispatch",
                "slack bus identity and operating basis",
            ],
            "counts": {
                **source["counts"],
                "topology_resolved_branches": resolved_branches,
                "topology_blocked_branches": blocked_branches,
                "resolved_endpoint_identities": resolved_endpoints,
                "geometry_resolved_ambiguous_endpoints": geometry_resolved_endpoints,
                "unresolved_endpoint_identities": unresolved_endpoints,
                "geometry_resolved_tap_buses": len(geometry_resolved_taps),
                "resolved_graph_components": component_count,
            },
            "branches": branches,
            "limitations": [
                *source["limitations"],
                "Endpoint identity is accepted only from a preserved unique label or a corridor endpoint within 5 meters with at least a 5-meter runner-up margin.",
                "Seventeen branches retain at least one unresolved endpoint and are excluded from the topology-ready set.",
                "The 139 resolved branches connect all 94 buses as one screening component, but impedance, ratings, dispatch, load, and slack-bus evidence are still absent.",
                "Historical loadings remain preserved modeled-screening outputs; this crosswalk is not a fresh solver reproduction.",
            ],
        }
    )
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not args.check_only:
        for output in OUTPUTS:
            write_atomically(output, serialized)
    print(
        f"{'Checked' if args.check_only else 'Wrote'} grid topology v2: "
        f"{resolved_branches} resolved branches, "
        f"{blocked_branches} blocked, {resolved_endpoints} resolved endpoints"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
