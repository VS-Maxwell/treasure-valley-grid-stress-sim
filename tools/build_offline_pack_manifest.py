#!/usr/bin/env python3
"""Build an immutable manifest for browser-safe historical artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "app/public/data/offline-pack-manifest-v10.json"
ARTIFACTS = (
    ("tvgwfm-grid", "app/public/data/tvgwfm-grid.json", "application/json", "ingested"),
    (
        "tvgwfm-baseline-summary",
        "app/public/data/tvgwfm-baseline-summary.json",
        "application/json",
        "modeled-screening",
    ),
    (
        "tvgwfm-heads-manifest",
        "app/public/data/tvgwfm-heads-manifest.json",
        "application/json",
        "modeled-screening",
    ),
    (
        "tvgwfm-heads-q10",
        "app/public/data/tvgwfm-heads-q10.bin",
        "application/octet-stream",
        "modeled-screening",
    ),
    (
        "tvgwfm-timeseries",
        "app/public/data/tvgwfm-timeseries.json",
        "application/json",
        "modeled-screening",
    ),
    (
        "usgs-groundwater-annual",
        "app/public/data/usgs-groundwater-annual.json",
        "application/json",
        "observed",
    ),
    (
        "usgs-groundwater-sites-manifest",
        "app/public/data/usgs-groundwater-sites-manifest.json",
        "application/json",
        "observed",
    ),
    (
        "usgs-groundwater-sites-f32",
        "app/public/data/usgs-groundwater-sites-f32.bin",
        "application/octet-stream",
        "observed",
    ),
    (
        "usgs-3dep-snake-plain-terrain-manifest-v4",
        "app/public/data/usgs-3dep-snake-plain-terrain-manifest-v4.json",
        "application/json",
        "observed",
    ),
    (
        "usgs-3dep-snake-plain-terrain-f32-v4",
        "app/public/data/usgs-3dep-snake-plain-terrain-f32-v4.bin",
        "application/octet-stream",
        "observed",
    ),
    (
        "usace-nid-regional-dams-manifest",
        "app/public/data/usace-nid-dams-manifest.json",
        "application/json",
        "observed",
    ),
    (
        "usace-nid-regional-dams-f32",
        "app/public/data/usace-nid-dams-f32.bin",
        "application/octet-stream",
        "observed",
    ),
    (
        "tvgwfm-bottoms-manifest",
        "app/public/data/tvgwfm-bottoms-manifest.json",
        "application/json",
        "ingested",
    ),
    (
        "tvgwfm-bottoms-f32",
        "app/public/data/tvgwfm-bottoms-f32.bin",
        "application/octet-stream",
        "ingested",
    ),
    (
        "tvgwfm-idomain-i8",
        "app/public/data/tvgwfm-idomain-i8.bin",
        "application/octet-stream",
        "ingested",
    ),
    (
        "grid-screening-model",
        "app/public/data/grid-screening-model.json",
        "application/json",
        "modeled-screening",
    ),
    (
        "idwr-espam22-grid-manifest-v1",
        "app/public/data/idwr-espam22-grid-manifest-v1.json",
        "application/json",
        "ingested",
    ),
    (
        "idwr-espam22-grid-lines-f32-v1",
        "app/public/data/idwr-espam22-grid-lines-f32-v1.bin",
        "application/octet-stream",
        "ingested",
    ),
    (
        "idwr-espam22-grid-cells-f32-v1",
        "app/public/data/idwr-espam22-grid-cells-f32-v1.bin",
        "application/octet-stream",
        "ingested",
    ),
    (
        "idwr-espam22-heads-manifest-v1",
        "app/public/data/idwr-espam22-heads-manifest-v1.json",
        "application/json",
        "ingested",
    ),
    (
        "idwr-espam22-heads-q10-v1",
        "app/public/data/idwr-espam22-heads-q10-v1.bin",
        "application/octet-stream",
        "ingested",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    artifacts = []
    for artifact_id, relative_path, media_type, truth_state in ARTIFACTS:
        path = ROOT / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Offline artifact missing: {relative_path}")
        artifacts.append(
            {
                "id": artifact_id,
                "path": relative_path.removeprefix("app/public/"),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "media_type": media_type,
                "truth_state": truth_state,
            }
        )
    payload = {
        "schema_version": 1,
        "id": "treasure-valley-offline-earth-pack-v10",
        "created_at": "2026-09-14T21:15:00Z",
        "source_doi": "10.5066/P9U6OOPH",
        "network_required": False,
        "artifact_count": len(artifacts),
        "total_bytes": sum(item["bytes"] for item in artifacts),
        "artifacts": artifacts,
        "validation_boundary": (
            "Hashes are verified during build and release validation. Browser loading "
            "checks structure and dimensions; it does not independently re-hash files."
        ),
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {OUTPUT}: {payload['artifact_count']} artifacts, "
        f"{payload['total_bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
