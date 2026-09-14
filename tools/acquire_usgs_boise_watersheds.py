#!/usr/bin/env python3
"""Acquire and receipt the four official USGS WBD Boise River HUC8 polygons."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path


SERVICE = "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/4/query"
HUC8_IDS = {"17050111", "17050112", "17050113", "17050114"}
FIELDS = "objectid,tnmid,huc8,name,areasqkm,loaddate,sourceoriginator,sourcedatadesc"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    where = "huc8 IN (" + ",".join(f"'{value}'" for value in sorted(HUC8_IDS)) + ")"
    query = urllib.parse.urlencode(
        {
            "where": where,
            "outFields": FIELDS,
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
    )
    url = f"{SERVICE}?{query}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "TreasureValleySimulator/0.2 watershed-acquisition"}
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        if response.status != 200:
            raise RuntimeError(f"USGS WBD returned HTTP {response.status}")
        body = response.read(10_000_001)
    if len(body) > 10_000_000:
        raise ValueError("USGS WBD response exceeded 10 MB")
    payload = json.loads(body)
    if payload.get("type") != "FeatureCollection":
        raise ValueError("USGS WBD response is not a GeoJSON FeatureCollection")
    found: set[str] = set()
    feature_receipts = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        huc8 = properties.get("huc8")
        if huc8 not in HUC8_IDS or huc8 in found:
            raise ValueError(f"Unexpected or duplicate HUC8: {huc8}")
        geometry = feature.get("geometry") or {}
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"HUC8 {huc8} has unsupported geometry")
        found.add(huc8)
        feature_receipts.append(
            {
                "huc8": huc8,
                "name": properties.get("name"),
                "tnmid": properties.get("tnmid"),
                "object_id": properties.get("objectid"),
                "area_sq_km": properties.get("areasqkm"),
                "geometry_type": geometry.get("type"),
            }
        )
    if found != HUC8_IDS:
        raise ValueError(f"Expected {sorted(HUC8_IDS)}, found {sorted(found)}")
    source_name = "usgs-wbd-boise-river-huc8.geojson"
    source_path = args.output_directory / source_name
    source_path.write_bytes(body)
    receipt = {
        "schema_version": 1,
        "id": "usgs-wbd-boise-river-huc8-v1",
        "created_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "provider": "U.S. Geological Survey Watershed Boundary Dataset",
        "service_url": SERVICE.removesuffix("/query"),
        "query_url": url,
        "local_root": str(args.output_directory.resolve()),
        "source_file": source_name,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "feature_count": len(feature_receipts),
        "huc8_ids": sorted(found),
        "features": sorted(feature_receipts, key=lambda item: item["huc8"]),
        "horizontal_crs": "EPSG:4326",
        "format_validation": "GeoJSON-FeatureCollection-four-unique-HUC8-pass",
        "status": "original-api-response-verified",
        "limitations": [
            "HUC8 membership is watershed evidence but is not a directed dam-to-outlet flow path.",
            "The browser derivative is simplified only for display; spatial classification uses this original geometry.",
        ],
    }
    args.receipt.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Verified {len(feature_receipts)} Boise River HUC8 polygons; {len(body)} bytes",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
