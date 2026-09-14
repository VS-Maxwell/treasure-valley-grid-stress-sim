#!/usr/bin/env python3
"""Extract TVGWFM layer bottoms and IDOMAIN into compact browser binaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = Path(
    "/run/media/madame-butterfly/Toshiba/Treasure_Valley_Model/data/raw/usgs/"
    "tvgwfm_2023/model.zip"
)
DEFAULT_MANIFEST = ROOT / "app/public/data/tvgwfm-bottoms-manifest.json"
DEFAULT_BOTTOMS = ROOT / "app/public/data/tvgwfm-bottoms-f32.bin"
DEFAULT_IDOMAIN = ROOT / "app/public/data/tvgwfm-idomain-i8.bin"
LAYERS = 6
ROWS = 64
COLUMNS = 65
CELLS = ROWS * COLUMNS
SOURCE_SHA256 = "bdefb11eaf7b75ab63dc0b23b0de4f65fe9d68798c0ff229420322bf8abb0dd6"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def numbers(text: str) -> list[float]:
    return [
        float(value)
        for value in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?", text)
    ]


def layered_arrays(block: str, label: str) -> list[list[float]]:
    parts = re.split(
        r"^\s*INTERNAL\s+FACTOR\s+[-+\d.Ee]+\s*$",
        block,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    arrays = [numbers(part) for part in parts[1:]]
    if len(arrays) != LAYERS or any(len(array) != CELLS for array in arrays):
        raise ValueError(
            f"Unexpected {label} arrays: layers={len(arrays)}, "
            f"sizes={[len(array) for array in arrays]}"
        )
    return arrays


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--bottoms", type=Path, default=DEFAULT_BOTTOMS)
    parser.add_argument("--idomain", type=Path, default=DEFAULT_IDOMAIN)
    args = parser.parse_args()
    if sha256(args.archive) != SOURCE_SHA256:
        raise ValueError("TVGWFM model archive SHA-256 does not match its receipt")
    with zipfile.ZipFile(args.archive) as source:
        model_text = source.read("model/mf6-tv_hist.dis").decode("utf-8")
    bottom_match = re.search(
        r"^\s*botm\s+LAYERED\s*(.*?)^\s*idomain\s+LAYERED\s*$",
        model_text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    idomain_match = re.search(
        r"^\s*idomain\s+LAYERED\s*(.*?)^\s*END\s+griddata\s*$",
        model_text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not bottom_match or not idomain_match:
        raise ValueError("Could not isolate TVGWFM BOTM and IDOMAIN blocks")
    bottoms = layered_arrays(bottom_match.group(1), "bottom")
    raw_idomain = layered_arrays(idomain_match.group(1), "IDOMAIN")
    idomain: list[list[int]] = []
    for layer in raw_idomain:
        integers = [int(value) for value in layer]
        if any(value not in {-1, 0, 1} for value in integers):
            raise ValueError("TVGWFM IDOMAIN contains an unexpected value")
        idomain.append(integers)

    flat_bottoms = [value for layer in bottoms for value in layer]
    flat_idomain = [value for layer in idomain for value in layer]
    args.bottoms.write_bytes(struct.pack(f"<{len(flat_bottoms)}f", *flat_bottoms))
    args.idomain.write_bytes(struct.pack(f"<{len(flat_idomain)}b", *flat_idomain))
    layer_statistics = []
    for layer_index, (layer_bottoms, layer_domain) in enumerate(
        zip(bottoms, idomain, strict=True), start=1
    ):
        active_values = [
            elevation
            for elevation, active in zip(layer_bottoms, layer_domain, strict=True)
            if active != 0
        ]
        layer_statistics.append(
            {
                "layer": layer_index,
                "active_cells": len(active_values),
                "minimum_bottom_feet": round(min(active_values), 6),
                "maximum_bottom_feet": round(max(active_values), 6),
                "mean_bottom_feet": round(sum(active_values) / len(active_values), 6),
            }
        )
    manifest = {
        "schema_version": 1,
        "id": "usgs-tvgwfm-layer-bottoms-v1",
        "truth_state": "ingested",
        "provider": "U.S. Geological Survey",
        "doi": "10.5066/P9U6OOPH",
        "source_archive": {
            "file": args.archive.name,
            "sha256": SOURCE_SHA256,
            "member": "model/mf6-tv_hist.dis",
        },
        "layout": {
            "layers": LAYERS,
            "rows": ROWS,
            "columns": COLUMNS,
            "cell_count": CELLS,
            "order": "layer-row-column",
            "length_unit": "feet",
            "vertical_datum": "NAVD88",
        },
        "bottoms_binary": {
            "file": args.bottoms.name,
            "bytes": args.bottoms.stat().st_size,
            "sha256": sha256(args.bottoms),
            "encoding": "little-endian-float32",
        },
        "idomain_binary": {
            "file": args.idomain.name,
            "bytes": args.idomain.stat().st_size,
            "sha256": sha256(args.idomain),
            "encoding": "signed-int8",
            "values": {"-1": "constant-head", "0": "inactive", "1": "active"},
        },
        "layer_statistics": layer_statistics,
        "limitations": [
            "These are model-layer bottoms, not direct borehole or core observations.",
            "The geometry is authoritative to the published TVGWFM discretization and does not extend to ESPAM.",
            "The renderer applies a documented vertical exaggeration for legibility.",
        ],
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {len(flat_bottoms)} bottoms and {len(flat_idomain)} IDOMAIN values; "
        f"active cells by layer {[item['active_cells'] for item in layer_statistics]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
