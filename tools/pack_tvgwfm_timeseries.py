#!/usr/bin/env python3
"""Create compact columnar budget and observation tables from a TVGWFM run."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path


MODEL_START = dt.datetime(1985, 12, 1, 14, 24, tzinfo=dt.timezone.utc)
NUMBER = r"[-+]?\d+(?:\.\d*)?(?:E[-+]?\d+)?"
BUDGET_BLOCK = re.compile(
    r"VOLUME BUDGET FOR ENTIRE MODEL AT END OF TIME STEP\s+1, STRESS PERIOD\s+(\d+)(.*?)(?=end timestep)",
    re.DOTALL,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def paired_values(label: str, block: str) -> tuple[float, float]:
    match = re.search(
        rf"^\s*{re.escape(label)}\s*=\s*({NUMBER}).*?{re.escape(label)}\s*=\s*({NUMBER})",
        block,
        re.MULTILINE,
    )
    if not match:
        raise ValueError(f"Missing budget row {label}")
    return float(match.group(1)), float(match.group(2))


def parse_budgets(
    path: Path, exact_model_times: list[float]
) -> list[dict[str, float | int | str]]:
    text = path.read_text(encoding="utf-8")
    rows = []
    total_days = 0.0
    for period_text, block in BUDGET_BLOCK.findall(text):
        total_match = re.search(rf"TOTAL TIME.*?\s({NUMBER})\s+({NUMBER})\s*$", block, re.MULTILINE)
        if not total_match:
            raise ValueError(f"Missing total time for stress period {period_text}")
        reported_total_days = float(total_match.group(1))
        total_days = exact_model_times[len(rows)]
        if abs(total_days - reported_total_days) > 0.51:
            raise ValueError(f"Listing and observation time differ at {period_text}")
        when = MODEL_START + dt.timedelta(days=total_days)
        cumulative_in, rate_in = paired_values("TOTAL IN", block)
        cumulative_out, rate_out = paired_values("TOTAL OUT", block)
        cumulative_delta, rate_delta = paired_values("IN - OUT", block)
        discrepancy_cumulative, discrepancy_rate = paired_values(
            "PERCENT DISCREPANCY", block
        )
        rows.append(
            {
                "stress_period": int(period_text),
                "period_end_date": when.date().isoformat(),
                "model_time_days": total_days,
                "cumulative_in_ft3": cumulative_in,
                "cumulative_out_ft3": cumulative_out,
                "cumulative_delta_ft3": cumulative_delta,
                "rate_in_ft3_per_day": rate_in,
                "rate_out_ft3_per_day": rate_out,
                "rate_delta_ft3_per_day": rate_delta,
                "cumulative_discrepancy_percent": discrepancy_cumulative,
                "rate_discrepancy_percent": discrepancy_rate,
            }
        )
    if len(rows) != 361:
        raise ValueError(f"Expected 361 budget rows, found {len(rows)}")
    return rows


def parse_observations(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.reader(source)
        header = next(reader)
        columns: dict[str, list[float]] = {name: [] for name in header}
        for row in reader:
            for name, value in zip(header, row, strict=True):
                columns[name].append(float(value))
    if len(columns["time"]) != 361:
        raise ValueError(f"Expected 361 observation rows in {path.name}")
    return {
        "source_file": path.name,
        "source_sha256": sha256(path),
        "row_count": len(columns["time"]),
        "series_count": len(header) - 1,
        "columns": columns,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("baseline_receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    listing = args.run_directory / "mf6-tv_hist.lst"
    csv_names = (
        "sim_equiv-tv_hist-drn_obs.csv",
        "sim_equiv-tv_hist-lowell_obs.csv",
        "sim_equiv-tv_hist-ny_canal_riv_obs.csv",
        "sim_equiv-tv_hist-riv_obs.csv",
    )
    observations = {
        name.removeprefix("sim_equiv-tv_hist-").removesuffix(".csv"): parse_observations(
            args.run_directory / name
        )
        for name in csv_names
    }
    budgets = parse_budgets(listing, observations["drn_obs"]["columns"]["time"])
    payload = {
        "schema_version": 1,
        "id": "tvgwfm-historical-tables-v1",
        "title": "TVGWFM monthly water-budget and simulated-observation tables",
        "doi": "10.5066/P9U6OOPH",
        "truth_state": "modeled-screening",
        "source": {
            "model_listing": listing.name,
            "model_listing_sha256": sha256(listing),
            "baseline_receipt_sha256": sha256(args.baseline_receipt),
        },
        "budget": {
            "units": {
                "volume": "cubic feet",
                "rate": "cubic feet per day",
                "discrepancy": "percent",
            },
            "rows": budgets,
        },
        "observations": observations,
        "limitations": [
            "These are reproduced model outputs, not direct field observations.",
            "The observation tables are simulated equivalents for comparison with measured groups described by the USGS archive.",
            "Scenario suitability and interpretation require domain review.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.output}: {len(budgets)} budget rows, "
        f"{sum(group['series_count'] for group in observations.values())} observation series"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
