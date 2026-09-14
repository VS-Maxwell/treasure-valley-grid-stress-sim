#!/usr/bin/env python3
"""Aggregate verified USGS discrete groundwater depths for browser display."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    source_root = Path(receipt["local_root"])
    depths: dict[int, list[float]] = defaultdict(list)
    sites: dict[int, set[str]] = defaultdict(set)
    approvals: dict[int, Counter[str]] = defaultdict(Counter)
    missing_value_count = 0

    for page in receipt["pages"]:
        path = source_root / page["file"]
        if path.stat().st_size != page["bytes"] or sha256(path) != page["sha256"]:
            raise ValueError(f"Source receipt mismatch: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload["features"]:
            properties = feature["properties"]
            if properties.get("value") is None:
                missing_value_count += 1
                continue
            year = int(properties["year"])
            value = float(properties["value"])
            depths[year].append(value)
            sites[year].add(properties["monitoring_location_id"])
            approvals[year][properties.get("approval_status") or "Unknown"] += 1

    years = []
    for year in sorted(depths):
        values = depths[year]
        years.append(
            {
                "year": year,
                "measurement_count": len(values),
                "monitoring_location_count": len(sites[year]),
                "minimum_depth_ft": min(values),
                "p25_depth_ft": percentile(values, 0.25),
                "median_depth_ft": percentile(values, 0.5),
                "p75_depth_ft": percentile(values, 0.75),
                "maximum_depth_ft": max(values),
                "approval_status_counts": dict(sorted(approvals[year].items())),
            }
        )
    payload = {
        "schema_version": 1,
        "id": "usgs-groundwater-depth-annual-1986-2015-v1",
        "truth_state": "observed",
        "parameter_code": "72019",
        "unit": "feet below land surface",
        "aggregation": "annual distribution across irregular discrete readings",
        "source_receipt": args.receipt.name,
        "source_receipt_sha256": sha256(args.receipt),
        "source_measurement_count": receipt["measurement_count"],
        "numeric_measurement_count": sum(
            row["measurement_count"] for row in years
        ),
        "excluded_null_value_count": missing_value_count,
        "year_count": len(years),
        "years": years,
        "limitations": [
            "Annual values summarize an irregular and changing set of monitoring locations.",
            "Depth below land surface is not equivalent to modeled hydraulic head elevation.",
            "No measured-to-model comparison is asserted without datum and cell matching.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {args.output}: {payload['numeric_measurement_count']} numeric measurements, "
        f"{payload['excluded_null_value_count']} null values excluded, "
        f"{payload['year_count']} annual rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
