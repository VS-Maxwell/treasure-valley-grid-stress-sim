#!/usr/bin/env python3
"""Acquire and receipt public USACE NID dams in the verified terrain region."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path


SERVICE = (
    "https://geospatial.sec.usace.army.mil/dls/rest/services/NID/"
    "National_Inventory_of_Dams_Public_Service/FeatureServer/0/query"
)
BOUNDS = [-118.0, 43.0, -115.0, 45.0]
FIELDS = [
    "OBJECTID",
    "NIDID",
    "DATA_UPDATED",
    "NAME",
    "OTHER_NAMES",
    "PRIMARY_OWNER_TYPE",
    "LATITUDE",
    "LONGITUDE",
    "STATE",
    "COUNTYSTATE",
    "RIVER_OR_STREAM",
    "PRIMARY_PURPOSE",
    "PURPOSES",
    "PRIMARY_DAM_TYPE",
    "DAM_TYPES",
    "CORE_TYPES",
    "FOUNDATIONS",
    "DAM_HEIGHT",
    "NID_STORAGE",
    "MAX_STORAGE",
    "NORMAL_STORAGE",
    "YEAR_COMPLETED",
    "SURFACE_AREA",
    "DRAINAGE_AREA",
    "MAX_DISCHARGE",
    "HAZARD_POTENTIAL",
    "CONDITION_ASSESSMENT",
    "OPERATIONAL_STATUS",
    "FED_AGENCY_OWNERS",
    "WEBSITE_URL",
]


def parse_bounds(value: str) -> list[float]:
    try:
        bounds = [float(part) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bounds must contain four numbers") from exc
    if len(bounds) != 4 or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise argparse.ArgumentTypeError("bounds must be west,south,east,north")
    return bounds


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--bounds", type=parse_bounds, default=BOUNDS)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--receipt-id", default="usace-nid-regional-dams-v1")
    parser.add_argument(
        "--source-name", default="nid-regional-118w-115w-43n-45n.geojson"
    )
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    query = urllib.parse.urlencode(
        {
            "where": "1=1",
            "geometry": ",".join(str(value) for value in args.bounds),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4269",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": ",".join(FIELDS),
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
    )
    url = f"{SERVICE}?{query}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "TreasureValleySimulator/0.2 dam-acquisition"}
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        if response.status != 200:
            raise RuntimeError(f"NID returned HTTP {response.status}")
        body = response.read(10_000_001)
    if len(body) > 10_000_000:
        raise ValueError("NID response exceeded 10 MB")
    payload = json.loads(body)
    if payload.get("type") != "FeatureCollection" or not payload.get("features"):
        raise ValueError("NID response is not a non-empty GeoJSON FeatureCollection")
    source_name = args.source_name
    source_path = args.output_directory / source_name
    source_path.write_bytes(body)
    object_ids: set[int] = set()
    nid_ids: list[str] = []
    missing_nidid_count = 0
    hydro_count = 0
    for feature in payload["features"]:
        properties = feature.get("properties", {})
        nid_id = properties.get("NIDID")
        object_id = properties.get("OBJECTID")
        if not isinstance(object_id, int):
            raise ValueError("NID feature has no stable OBJECTID")
        if object_id in object_ids:
            raise ValueError(f"Duplicate NID OBJECTID: {object_id}")
        object_ids.add(object_id)
        if not isinstance(nid_id, str) or not nid_id:
            missing_nidid_count += 1
        else:
            nid_ids.append(nid_id)
        geometry = feature.get("geometry", {})
        if geometry.get("type") != "Point" or len(geometry.get("coordinates", [])) < 2:
            raise ValueError(f"NID feature is not a point: OBJECTID {object_id}")
        longitude, latitude = geometry["coordinates"][:2]
        if not (
            args.bounds[0] <= longitude <= args.bounds[2]
            and args.bounds[1] <= latitude <= args.bounds[3]
        ):
            raise ValueError(f"NID feature lies outside requested bounds: OBJECTID {object_id}")
        if "hydroelectric" in str(properties.get("PURPOSES", "")).lower():
            hydro_count += 1

    receipt = {
        "schema_version": 1,
        "id": args.receipt_id,
        "created_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "provider": "U.S. Army Corps of Engineers National Inventory of Dams",
        "service_url": SERVICE.removesuffix("/query"),
        "query_url": url,
        "bbox_epsg_4326": args.bounds,
        "local_root": str(args.output_directory.resolve()),
        "source_file": source_name,
        "bytes": len(body),
        "sha256": sha256(body),
        "feature_count": len(payload["features"]),
        "unique_provider_record_count": len(object_ids),
        "unique_nidid_count": len(set(nid_ids)),
        "duplicate_nidid_record_count": len(nid_ids) - len(set(nid_ids)),
        "missing_nidid_count": missing_nidid_count,
        "hydroelectric_purpose_count": hydro_count,
        "format_validation": "GeoJSON-FeatureCollection-pass",
        "status": "original-api-response-verified",
        "limitations": [
            "The regional bounding-box inventory does not prove that a dam feeds the Treasure Valley.",
            "NID is informational and is not a real-time emergency-response source.",
            "Hydroelectric purpose does not by itself establish generator capacity or grid connection.",
        ],
    }
    receipt_path = args.receipt or (args.output_directory / "receipt.json")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Verified {receipt['feature_count']} NID dams, including "
        f"{hydro_count} with hydroelectric purpose; {len(body)} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
