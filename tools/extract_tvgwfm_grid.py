#!/usr/bin/env python3
"""Extract a compact, reviewable grid surface from the preserved USGS TVGWFM archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


def numbers(text: str) -> list[float]:
    return [float(value) for value in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?", text)]


def scalar(pattern: str, text: str) -> float:
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ValueError(f"Missing required model field: {pattern}")
    return float(match.group(1))


def parse_georef(path: Path) -> dict[str, list[float]]:
    corners: dict[str, list[float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        name, longitude, latitude = line.split()
        corners[name] = [float(longitude), float(latitude)]
    required = {"upper_left", "upper_right", "lower_right", "lower_left"}
    if set(corners) != required:
        raise ValueError("Unexpected model georeference corner set")
    return corners


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("georef", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    archive_bytes = args.archive.read_bytes()
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    with zipfile.ZipFile(args.archive) as model_zip:
        model_text = model_zip.read("model/mf6-tv_hist.dis").decode("utf-8")

    nlay = int(scalar(r"^\s*NLAY\s+(\d+)", model_text))
    nrow = int(scalar(r"^\s*NROW\s+(\d+)", model_text))
    ncol = int(scalar(r"^\s*NCOL\s+(\d+)", model_text))
    xorigin = scalar(r"^\s*XORIGIN\s+([-+\d.Ee]+)", model_text)
    yorigin = scalar(r"^\s*YORIGIN\s+([-+\d.Ee]+)", model_text)
    angle = scalar(r"^\s*ANGROT\s+([-+\d.Ee]+)", model_text)

    delr_text = re.search(r"^\s*delr\s*(.*?)^\s*delc\s*$", model_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    delc_text = re.search(r"^\s*delc\s*(.*?)^\s*top\s*$", model_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    top_text = re.search(r"^\s*top\s*(.*?)^\s*botm\s+LAYERED\s*$", model_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not delr_text or not delc_text or not top_text:
        raise ValueError("Could not isolate DIS grid arrays")

    # Each internal array begins with the single FACTOR value; it is metadata,
    # not part of the model grid.
    delr = numbers(delr_text.group(1))[1:]
    delc = numbers(delc_text.group(1))[1:]
    top = numbers(top_text.group(1))[1:]
    if len(delr) != ncol or len(delc) != nrow or len(top) != nrow * ncol:
        raise ValueError(
            f"Unexpected array sizes: delr={len(delr)}, delc={len(delc)}, top={len(top)}"
        )

    positive_top = [value for value in top if value > 0]
    payload = {
        "schema_version": 1,
        "id": "usgs-tvgwfm-grid-v1",
        "title": "Treasure Valley Groundwater Flow Model grid surface",
        "provider": "U.S. Geological Survey",
        "doi": "10.5066/P9U6OOPH",
        "rights": "CC0-1.0",
        "truth_state": "ingested",
        "source_archive": {
            "name": args.archive.name,
            "sha256": archive_sha256,
            "bytes": len(archive_bytes),
        },
        "grid": {
            "layers": nlay,
            "rows": nrow,
            "columns": ncol,
            "length_units": "feet",
            "x_origin": xorigin,
            "y_origin": yorigin,
            "rotation_degrees": angle,
            "cell_widths": delr,
            "cell_heights": delc,
            "corners_wgs84": parse_georef(args.georef),
            "top_elevation_feet": top,
            "active_top_cells": len(positive_top),
            "top_min_feet": min(positive_top),
            "top_max_feet": max(positive_top),
        },
        "limitations": [
            "This is an ingestion transform, not a rerun or validation of the MODFLOW model.",
            "Zero top elevations are retained as inactive or outside-domain source values.",
            "The full model has 361 stress periods beginning 1985-12-01 and requires a separate solver workflow.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.output}: {nlay} layers, {nrow}x{ncol}, "
        f"{len(positive_top)} active top cells, source {archive_sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
