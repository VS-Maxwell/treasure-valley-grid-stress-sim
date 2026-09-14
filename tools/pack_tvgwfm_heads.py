#!/usr/bin/env python3
"""Pack biennial six-layer TVGWFM heads into a browser-safe quantized binary."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import struct
import sys
from array import array
from pathlib import Path


HEADER = struct.Struct("<ii dd 16s iii")
INACTIVE_SOURCE_THRESHOLD = 1e20
INACTIVE_PACKED = 65535
SCALE_FEET = 0.1
# Stress period 1 is the model's initial stabilization period. Stress periods
# 13, 37, ... represent December 1986, 1988, ...; 361 is December 2015.
SELECTED_PERIODS = (*tuple(13 + 24 * index for index in range(15)), 361)
MODEL_START = dt.datetime(1985, 12, 1, 14, 24, tzinfo=dt.timezone.utc)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_selected_heads(path: Path) -> tuple[list[dict[str, object]], list[array]]:
    slices: dict[int, dict[str, object]] = {}
    layers: dict[tuple[int, int], array] = {}
    with path.open("rb") as source:
        while header_bytes := source.read(HEADER.size):
            if len(header_bytes) != HEADER.size:
                raise ValueError("Truncated MODFLOW head header")
            kstp, kper, _pertim, totim, label, ncol, nrow, ilay = HEADER.unpack(
                header_bytes
            )
            values = array("d")
            values.fromfile(source, ncol * nrow)
            if kper not in SELECTED_PERIODS:
                continue
            if kstp != 1 or nrow != 64 or ncol != 65 or label.strip() != b"HEAD":
                raise ValueError("Unexpected selected head record metadata")
            when = MODEL_START + dt.timedelta(days=totim)
            represented_year = when.year - 1 if when.month == 1 else when.year
            slices.setdefault(
                kper,
                {
                    "stress_period": kper,
                    "model_time_days": totim,
                    "period_end_date": when.date().isoformat(),
                    "year": represented_year,
                    "layers": [],
                },
            )
            finite = [value for value in values if abs(value) < INACTIVE_SOURCE_THRESHOLD]
            slices[kper]["layers"].append(
                {
                    "layer": ilay,
                    "active_cells": len(finite),
                    "min_feet": min(finite),
                    "max_feet": max(finite),
                    "mean_feet": sum(finite) / len(finite),
                }
            )
            layers[(kper, ilay)] = values

    if set(slices) != set(SELECTED_PERIODS):
        raise ValueError("Not all requested stress periods were found")
    ordered_slices = [slices[period] for period in SELECTED_PERIODS]
    ordered_layers = [
        layers[(period, layer)]
        for period in SELECTED_PERIODS
        for layer in range(1, 7)
    ]
    return ordered_slices, ordered_layers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("heads", type=Path)
    parser.add_argument("baseline_receipt", type=Path)
    parser.add_argument("binary_output", type=Path)
    parser.add_argument("manifest_output", type=Path)
    args = parser.parse_args()

    slices, ordered_layers = read_selected_heads(args.heads)
    finite_values = [
        value
        for values in ordered_layers
        for value in values
        if abs(value) < INACTIVE_SOURCE_THRESHOLD
    ]
    offset = math.floor(min(finite_values) / SCALE_FEET) * SCALE_FEET
    packed = array("H")
    for values in ordered_layers:
        for value in values:
            if abs(value) >= INACTIVE_SOURCE_THRESHOLD:
                packed.append(INACTIVE_PACKED)
                continue
            quantized = round((value - offset) / SCALE_FEET)
            if not 0 <= quantized < INACTIVE_PACKED:
                raise ValueError("Head value is outside the uint16 packing range")
            packed.append(quantized)
    if sys.byteorder != "little":
        packed.byteswap()

    args.binary_output.parent.mkdir(parents=True, exist_ok=True)
    args.binary_output.write_bytes(packed.tobytes())
    manifest = {
        "schema_version": 1,
        "id": "tvgwfm-heads-biennial-v1",
        "title": "TVGWFM biennial groundwater heads",
        "doi": "10.5066/P9U6OOPH",
        "truth_state": "modeled-screening",
        "source": {
            "name": args.heads.name,
            "sha256": sha256(args.heads),
            "baseline_receipt_sha256": sha256(args.baseline_receipt),
        },
        "layout": {
            "encoding": "little-endian-uint16",
            "order": "slice-layer-row-column",
            "rows": 64,
            "columns": 65,
            "layers": 6,
            "slices": len(slices),
            "value_count": len(packed),
            "bytes": args.binary_output.stat().st_size,
            "offset_feet": offset,
            "scale_feet": SCALE_FEET,
            "inactive_value": INACTIVE_PACKED,
        },
        "slices": slices,
        "binary": {
            "file": args.binary_output.name,
            "sha256": sha256(args.binary_output),
        },
        "limitations": [
            "The pack contains 16 biennial snapshots from the reproduced historical baseline, not every monthly stress period.",
            "Values are quantized to 0.1 foot for interactive visualization; the original double-precision output is preserved outside the web bundle.",
            "This screening visualization is not a replacement for the MODFLOW files, calibration record, or domain review.",
        ],
    }
    args.manifest_output.write_text(
        json.dumps(manifest, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {args.binary_output} ({len(packed)} values, {args.binary_output.stat().st_size} bytes) "
        f"and {args.manifest_output}; years {slices[0]['year']}-{slices[-1]['year']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
