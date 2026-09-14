#!/usr/bin/env python3
"""Acquire the official ESPAM 2.2 model-grid service as immutable pages."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = (
    "https://gis.idwr.idaho.gov/hosting/rest/services/Modeling/"
    "EspaModelGrid/FeatureServer/0/query"
)
FIELDS = "OBJECTID,LAYER1,ACTIVE,ROW_ID,COL_ID,ACRES,CELL_INTGR"
PAGE_SIZE = 2_000
MAX_PAGE_BYTES = 12_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(parameters: dict[str, str]) -> tuple[bytes, str]:
    url = f"{SERVICE}?{urllib.parse.urlencode(parameters)}"
    request = urllib.request.Request(
        url, headers={"Accept": "application/geo+json", "User-Agent": "TreasureValleySimulator/0.2"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read(MAX_PAGE_BYTES + 1)
    if len(raw) > MAX_PAGE_BYTES:
        raise ValueError("IDWR grid page exceeded the configured size limit")
    return raw, url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--receipt",
        type=Path,
        default=ROOT / "receipts/idwr-espam22-grid-20260914.json",
    )
    args = parser.parse_args()
    destination = args.destination.resolve()
    receipt_path = args.receipt.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    count_raw, count_url = fetch(
        {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    )
    expected_count = int(json.loads(count_raw)["count"])
    pages = []
    object_ids: set[int] = set()
    active_count = 0
    for page_number, offset in enumerate(range(0, expected_count, PAGE_SIZE), start=1):
        raw, url = fetch(
            {
                "where": "1=1",
                "outFields": FIELDS,
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": "OBJECTID ASC",
                "resultOffset": str(offset),
                "resultRecordCount": str(PAGE_SIZE),
                "f": "geojson",
            }
        )
        payload = json.loads(raw)
        if payload.get("type") != "FeatureCollection":
            raise ValueError(f"IDWR page {page_number} is not GeoJSON")
        features = payload.get("features", [])
        if not features:
            raise ValueError(f"IDWR page {page_number} is empty")
        for feature in features:
            properties = feature.get("properties", {})
            object_id = int(properties["OBJECTID"])
            if object_id in object_ids:
                raise ValueError(f"Duplicate OBJECTID {object_id}")
            object_ids.add(object_id)
            active_count += int(properties.get("ACTIVE") == 1)
            coordinates = feature.get("geometry", {}).get("coordinates")
            if feature.get("geometry", {}).get("type") != "Polygon" or not coordinates:
                raise ValueError(f"Invalid grid geometry for OBJECTID {object_id}")
        path = destination / f"espam22-grid-page-{page_number:02d}.geojson"
        path.write_bytes(raw)
        pages.append(
            {
                "page": page_number,
                "offset": offset,
                "file": path.name,
                "query_url": url,
                "bytes": len(raw),
                "sha256": sha256(path),
                "feature_count": len(features),
            }
        )
        print(f"Verified grid page {page_number}: {len(features)} cells", flush=True)

    if len(object_ids) != expected_count:
        raise ValueError(f"Grid count mismatch: {len(object_ids)} != {expected_count}")
    payload = {
        "schema_version": 1,
        "id": "idwr-espam22-grid-service-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "Idaho Department of Water Resources",
        "model": "Eastern Snake Plain Aquifer Model version 2.2",
        "service": SERVICE.removesuffix("/query"),
        "count_query_url": count_url,
        "local_root": str(destination),
        "spatial_reference": "EPSG:4326 transformed by provider service",
        "field_names": FIELDS.split(","),
        "page_count": len(pages),
        "feature_count": len(object_ids),
        "active_count": active_count,
        "total_bytes": sum(item["bytes"] for item in pages),
        "pages": pages,
        "status": "original-api-pages-and-geometry-verified",
        "scientific_boundary": (
            "The grid defines the ESPAM domain. It does not merge ESPAM with TVGWFM "
            "or extend calibrated properties outside active ESPAM cells."
        ),
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Acquired {payload['feature_count']} ESPAM cells across {payload['page_count']} pages",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
