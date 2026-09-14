#!/usr/bin/env python3
"""Acquire bounded USGS groundwater field measurements with page receipts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.request
from pathlib import Path


BBOX = (-117.1163, 43.1762, -115.8097, 44.1081)
START_DATE = "1986-01-01"
END_DATE = "2015-12-31"
PARAMETER_CODE = "72019"
INITIAL_URL = (
    "https://api.waterdata.usgs.gov/ogcapi/v0/collections/"
    "field-measurements/items?f=json&bbox=-117.1163,43.1762,-115.8097,44.1081"
    "&parameter_code=72019&datetime=1986-01-01/2015-12-31&limit=10000"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/geo+json, application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "TreasureValleySimulator/0.2 research-data-acquisition",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuntimeError(f"USGS returned HTTP {response.status}")
        return response.read()


def validate_feature(feature: dict[str, object]) -> tuple[str, str]:
    properties = feature["properties"]
    geometry = feature["geometry"]
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise ValueError("Feature properties or geometry are invalid")
    if properties.get("parameter_code") != PARAMETER_CODE:
        raise ValueError("Unexpected parameter code")
    time_value = str(properties.get("time", ""))
    date = time_value[:10]
    if not START_DATE <= date <= END_DATE:
        raise ValueError(f"Measurement outside requested dates: {time_value}")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError("Measurement has no point coordinates")
    longitude, latitude = float(coordinates[0]), float(coordinates[1])
    west, south, east, north = BBOX
    if not (west <= longitude <= east and south <= latitude <= north):
        raise ValueError("Measurement outside requested footprint")
    return str(properties.get("monitoring_location_id", "")), date


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.max_pages <= 100:
        raise ValueError("max-pages must be between 1 and 100")
    args.output_directory.mkdir(parents=True, exist_ok=True)

    pages = []
    measurement_ids: set[str] = set()
    site_ids: set[str] = set()
    earliest = END_DATE
    latest = START_DATE
    url: str | None = INITIAL_URL
    for page_number in range(1, args.max_pages + 1):
        if url is None:
            break
        body = fetch(url)
        payload = json.loads(body)
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("USGS page has no feature list")
        for feature in features:
            feature_id = str(feature.get("id", ""))
            if not feature_id or feature_id in measurement_ids:
                raise ValueError(f"Missing or duplicate measurement ID: {feature_id}")
            measurement_ids.add(feature_id)
            site_id, date = validate_feature(feature)
            site_ids.add(site_id)
            earliest = min(earliest, date)
            latest = max(latest, date)
        path = args.output_directory / f"field-measurements-page-{page_number:04d}.json"
        path.write_bytes(body)
        pages.append(
            {
                "page": page_number,
                "file": path.name,
                "bytes": len(body),
                "sha256": digest(body),
                "feature_count": len(features),
                "request_url": url,
            }
        )
        next_links = [
            link.get("href")
            for link in payload.get("links", [])
            if link.get("rel") == "next"
        ]
        url = str(next_links[0]) if next_links else None
        if url is not None:
            time.sleep(0.25)
    if url is not None:
        raise RuntimeError(
            f"Acquisition exceeded {args.max_pages} pages; increase the explicit bound"
        )

    receipt = {
        "schema_version": 1,
        "id": "usgs-tvgwfm-field-measurements-1986-2015",
        "created_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "provider": "U.S. Geological Survey Water Data APIs",
        "collection": "field-measurements",
        "parameter_code": PARAMETER_CODE,
        "parameter_meaning": "Depth to water level, feet below land surface",
        "bbox_epsg_4326": list(BBOX),
        "requested_dates": [START_DATE, END_DATE],
        "observed_dates": [earliest, latest],
        "measurement_count": len(measurement_ids),
        "monitoring_location_count": len(site_ids),
        "page_count": len(pages),
        "total_bytes": sum(page["bytes"] for page in pages),
        "pages": pages,
        "status": "original-api-pages-verified",
        "limitations": [
            "Field measurements are irregular discrete readings, not a regular time series.",
            "Depth values retain provider qualifiers, approval status, procedure, and datum fields.",
            "A displayed comparison to modeled head requires an explicit datum and spatial-matching method.",
        ],
    }
    receipt_path = args.output_directory / "receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Acquired {receipt['measurement_count']} measurements from "
        f"{receipt['monitoring_location_count']} locations in {receipt['page_count']} pages; "
        f"{receipt['total_bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
