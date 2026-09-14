#!/usr/bin/env python3
"""Pack annual archived ESPAM 2.2 heads onto the verified active-cell order."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_RECEIPT = ROOT / "receipts/idwr-espam22-model-20260914.json"
GRID_RECEIPT = ROOT / "receipts/idwr-espam22-grid-20260914.json"
MANIFEST = ROOT / "app/public/data/idwr-espam22-heads-manifest-v1.json"
BINARY = ROOT / "app/public/data/idwr-espam22-heads-q10-v1.bin"
MODEL_ARCHIVE = "E200723A_07.zip"
HDS_MEMBER = "ESPAM_modflow/bigtrn.hds"
IBOUND_MEMBER = "ESPAM_modflow/ibound.ibd"
MDL_MEMBER = "ESPAM_pest/E200723A.mdl"
ROWS = 104
COLUMNS = 209
ACTIVE_CELLS = 11_236
HEADER = struct.Struct("<iiff16siii")
MISSING = 65_535


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_dates(raw: str) -> dict[int, str]:
    lines = raw.replace("\r", "").splitlines()
    marker = next(index for index, line in enumerate(lines) if line.strip() == "461 9 248")
    dates = {}
    for offset, line in enumerate(lines[marker + 1 : marker + 1 + 461], start=2):
        match = re.search(r"(\d{1,2})\s*/\s*(\d{4})", line)
        if not match:
            raise ValueError(f"ESPAM model date could not be parsed: {line!r}")
        month, year = (int(value) for value in match.groups())
        dates[offset] = f"{year:04d}-{month:02d}"
    return dates


def active_cell_order(grid_receipt: dict) -> list[tuple[int, int]]:
    root = Path(grid_receipt["local_root"])
    cells = []
    for page in grid_receipt["pages"]:
        path = root / page["file"]
        if path.stat().st_size != page["bytes"] or sha256(path) != page["sha256"]:
            raise ValueError(f"Grid receipt mismatch: {page['file']}")
        for feature in json.loads(path.read_text(encoding="utf-8"))["features"]:
            properties = feature["properties"]
            cells.append((int(properties["ROW_ID"]), int(properties["COL_ID"])))
    if len(cells) != ACTIVE_CELLS or len(set(cells)) != ACTIVE_CELLS:
        raise ValueError("ESPAM active-cell order is incomplete or duplicated")
    return cells


def main() -> int:
    model_receipt = json.loads(MODEL_RECEIPT.read_text(encoding="utf-8"))
    grid_receipt = json.loads(GRID_RECEIPT.read_text(encoding="utf-8"))
    archive_record = next(
        item for item in model_receipt["files"] if item["file"] == MODEL_ARCHIVE
    )
    archive_path = Path(model_receipt["local_root"]) / MODEL_ARCHIVE
    if (
        archive_path.stat().st_size != archive_record["bytes"]
        or sha256(archive_path) != archive_record["sha256"]
    ):
        raise ValueError("ESPAM model archive receipt mismatch")
    cells = active_cell_order(grid_receipt)

    selected: list[tuple[int, str, list[float]]] = []
    record_count = 0
    with zipfile.ZipFile(archive_path) as archive:
        dates = model_dates(archive.read(MDL_MEMBER).decode("ascii"))
        ibound = [int(value) for value in archive.read(IBOUND_MEMBER).split()]
        if len(ibound) != ROWS * COLUMNS:
            raise ValueError("ESPAM IBOUND dimensions are invalid")
        ibound_cells = {
            (index // COLUMNS + 1, index % COLUMNS + 1)
            for index, value in enumerate(ibound)
            if value != 0
        }
        if ibound_cells != set(cells):
            raise ValueError("IDWR service cells do not match archived ESPAM IBOUND")

        with archive.open(HDS_MEMBER) as heads:
            while True:
                raw_header = heads.read(HEADER.size)
                if not raw_header:
                    break
                if len(raw_header) != HEADER.size:
                    raise ValueError("Truncated ESPAM head header")
                kstp, kper, _pertim, _totim, text, ncol, nrow, ilay = HEADER.unpack(
                    raw_header
                )
                if (nrow, ncol, ilay, text.strip()) != (
                    ROWS,
                    COLUMNS,
                    1,
                    b"HEAD",
                ):
                    raise ValueError("Unexpected ESPAM head record contract")
                raw_values = heads.read(ROWS * COLUMNS * 4)
                if len(raw_values) != ROWS * COLUMNS * 4:
                    raise ValueError("Truncated ESPAM head values")
                record_count += 1
                date = dates.get(kper)
                if kstp == 2 and date and date.endswith("-09"):
                    all_values = struct.unpack(f"<{ROWS * COLUMNS}f", raw_values)
                    active_values = [
                        all_values[(row - 1) * COLUMNS + column - 1]
                        for row, column in cells
                    ]
                    if any(not math.isfinite(value) or value >= 999_000 for value in active_values):
                        raise ValueError(f"Invalid active-cell head in {date}")
                    selected.append((kper, date, active_values))

    if record_count != 923 or len(selected) != 39:
        raise ValueError(
            f"ESPAM head record mismatch: {record_count} records, {len(selected)} slices"
        )
    minimum = min(value for _kper, _date, values in selected for value in values)
    maximum = max(value for _kper, _date, values in selected for value in values)
    scale = 0.1
    offset = math.floor(minimum / scale) * scale
    encoded: list[int] = []
    slices = []
    for kper, date, values in selected:
        start = len(encoded)
        for value in values:
            quantized = round((value - offset) / scale)
            if not 0 <= quantized < MISSING:
                raise ValueError(f"ESPAM head value cannot be quantized: {value}")
            encoded.append(quantized)
        slices.append(
            {
                "year": int(date[:4]),
                "month": int(date[5:]),
                "stress_period": kper,
                "value_offset": start,
                "value_count": len(values),
                "minimum_feet": round(min(values), 3),
                "maximum_feet": round(max(values), 3),
            }
        )
    BINARY.write_bytes(struct.pack(f"<{len(encoded)}H", *encoded))
    manifest = {
        "schema_version": 1,
        "id": "idwr-espam22-archived-heads-v1",
        "truth_state": "ingested",
        "representation": "archived-modeled-output-not-independently-reproduced",
        "model": "Eastern Snake Plain Aquifer Model version 2.2",
        "source_model_receipt": str(MODEL_RECEIPT.relative_to(ROOT)),
        "source_model_receipt_sha256": sha256(MODEL_RECEIPT),
        "source_grid_receipt": str(GRID_RECEIPT.relative_to(ROOT)),
        "source_grid_receipt_sha256": sha256(GRID_RECEIPT),
        "source_archive_member": HDS_MEMBER,
        "source_head_record_count": record_count,
        "cell_order": "idwr-espam22-grid-cells-f32-v1",
        "active_cell_count": ACTIVE_CELLS,
        "slice_count": len(slices),
        "slices": slices,
        "quantization": {
            "source_unit": "feet",
            "scale_feet": scale,
            "offset_feet": offset,
            "missing_sentinel": MISSING,
        },
        "statistics": {
            "minimum_feet": round(minimum, 3),
            "maximum_feet": round(maximum, 3),
        },
        "binary": {
            "file": BINARY.name,
            "bytes": BINARY.stat().st_size,
            "sha256": sha256(BINARY),
            "encoding": "little-endian-uint16",
            "order": "slice-then-active-cell-service-order",
        },
        "limitations": [
            "These values are a deterministic extraction of archived ESPAM 2.2 output, not a new run.",
            "Independent executable and numerical reproduction remain required before validated-model labeling.",
            "Annual September slices are a browser visualization subset of 923 archived head records.",
        ],
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Packed {len(slices)} ESPAM head slices x {ACTIVE_CELLS} cells; "
        f"{minimum:.3f}-{maximum:.3f} feet; {BINARY.stat().st_size} bytes",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
