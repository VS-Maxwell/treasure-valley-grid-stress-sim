#!/usr/bin/env python3
"""Compare a TVGWFM rerun with the archived USGS MODFLOW 6 outputs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import struct
from array import array
from pathlib import Path


HEAD_HEADER = struct.Struct("<ii dd 16s iii")
CSV_OUTPUTS = (
    "sim_equiv-tv_hist-drn_obs.csv",
    "sim_equiv-tv_hist-lowell_obs.csv",
    "sim_equiv-tv_hist-ny_canal_riv_obs.csv",
    "sim_equiv-tv_hist-riv_obs.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_heads(actual: Path, expected: Path) -> dict[str, float | int | str]:
    records = values = differences = 0
    max_absolute = max_relative = squared = 0.0
    with actual.open("rb") as observed, expected.open("rb") as reference:
        while True:
            observed_header = observed.read(HEAD_HEADER.size)
            reference_header = reference.read(HEAD_HEADER.size)
            if not observed_header and not reference_header:
                break
            if len(observed_header) != HEAD_HEADER.size or len(reference_header) != HEAD_HEADER.size:
                raise ValueError("Truncated MODFLOW head record")
            oh = HEAD_HEADER.unpack(observed_header)
            rh = HEAD_HEADER.unpack(reference_header)
            if oh != rh:
                raise ValueError(f"Head record metadata differs at record {records + 1}")
            ncol, nrow = oh[-3], oh[-2]
            count = ncol * nrow
            observed_values = array("d")
            reference_values = array("d")
            observed_values.fromfile(observed, count)
            reference_values.fromfile(reference, count)
            for value, baseline in zip(observed_values, reference_values, strict=True):
                if abs(baseline) >= 1e20 and abs(value) >= 1e20:
                    continue
                delta = abs(value - baseline)
                values += 1
                if delta:
                    differences += 1
                max_absolute = max(max_absolute, delta)
                max_relative = max(max_relative, delta / max(abs(baseline), 1.0))
                squared += delta * delta
            records += 1
    return {
        "records": records,
        "finite_values_compared": values,
        "values_with_binary_difference": differences,
        "max_absolute_difference_feet": max_absolute,
        "max_relative_difference": max_relative,
        "rmse_feet": math.sqrt(squared / values),
        "actual_sha256": sha256(actual),
        "archived_sha256": sha256(expected),
    }


def compare_csv(actual: Path, expected: Path) -> dict[str, float | int | str]:
    max_absolute = max_relative = squared = 0.0
    values = differences = rows = 0
    with actual.open(newline="", encoding="utf-8") as observed_file, expected.open(
        newline="", encoding="utf-8"
    ) as reference_file:
        observed_rows = csv.reader(observed_file)
        reference_rows = csv.reader(reference_file)
        observed_header = next(observed_rows)
        reference_header = next(reference_rows)
        if observed_header != reference_header:
            raise ValueError(f"CSV headers differ: {actual.name}")
        for observed, reference in zip(observed_rows, reference_rows, strict=True):
            if len(observed) != len(reference):
                raise ValueError(f"CSV row widths differ: {actual.name}")
            rows += 1
            for value_text, baseline_text in zip(observed, reference, strict=True):
                value, baseline = float(value_text), float(baseline_text)
                delta = abs(value - baseline)
                values += 1
                if delta:
                    differences += 1
                max_absolute = max(max_absolute, delta)
                max_relative = max(max_relative, delta / max(abs(baseline), 1.0))
                squared += delta * delta
    return {
        "rows": rows,
        "values_compared": values,
        "values_with_text_precision_difference": differences,
        "max_absolute_difference": max_absolute,
        "max_relative_difference": max_relative,
        "rmse": math.sqrt(squared / values),
        "actual_sha256": sha256(actual),
        "archived_sha256": sha256(expected),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("reference_directory", type=Path)
    parser.add_argument("compiler", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    model_listing = (args.run_directory / "mf6-tv_hist.lst").read_text(
        encoding="utf-8"
    )
    simulation_listing = (args.run_directory / "mfsim.lst").read_text(
        encoding="utf-8"
    )
    heads = compare_heads(
        args.run_directory / "mf6-tv_hist.hds",
        args.reference_directory / "mf6-tv_hist.hds",
    )
    csv_results = {
        name: compare_csv(
            args.run_directory / name, args.reference_directory / name
        )
        for name in CSV_OUTPUTS
    }
    normal = "Normal termination of simulation." in simulation_listing
    budget_closed = "PERCENT DISCREPANCY =          -0.00" in model_listing
    # Different compilers can produce non-identical floating-point bytes. The
    # acceptance threshold is a sub-millifoot head difference plus the model's
    # own rounded zero-percent budget discrepancy.
    accepted = (
        normal
        and budget_closed
        and float(heads["max_absolute_difference_feet"]) <= 0.001
        and all(
            float(result["max_relative_difference"]) <= 1e-5
            for result in csv_results.values()
        )
    )
    receipt = {
        "schema_version": 1,
        "receipt_id": "tvgwfm-baseline-reproduction-20260914",
        "completed_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "model": "USGS Treasure Valley Groundwater Flow Model 1986-2015",
        "doi": "10.5066/P9U6OOPH",
        "engine": {
            "version": "MODFLOW 6.1.1 06/12/2020",
            "binary_path": str(args.compiler),
            "binary_sha256": sha256(args.compiler),
            "build_note": "Compiled serially from the source_code.zip preserved with the USGS release using GNU Fortran 16.2.1.",
        },
        "run_directory": str(args.run_directory),
        "reference_directory": str(args.reference_directory),
        "normal_termination": normal,
        "rounded_budget_discrepancy_zero_percent": budget_closed,
        "heads": heads,
        "observation_outputs": csv_results,
        "acceptance_thresholds": {
            "head_max_absolute_difference_feet": 0.001,
            "observation_max_relative_difference": 1e-5,
            "normal_termination_required": True,
            "rounded_zero_percent_budget_discrepancy_required": True,
        },
        "status": "numerically-reproduced" if accepted else "comparison-failed",
        "acceptance_boundary": "Numerical reproduction compares the archived USGS outputs. Scientific suitability for a new scenario still requires domain review.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
