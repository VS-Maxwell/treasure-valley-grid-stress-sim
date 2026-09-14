#!/usr/bin/env python3
"""Acquire USGS metadata for sites in a verified field-measurement receipt."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


ENDPOINT = (
    "https://api.waterdata.usgs.gov/ogcapi/v0/collections/"
    "monitoring-locations/items"
)
BATCH_SIZE = 100


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("field_receipt", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    field_receipt = json.loads(args.field_receipt.read_text(encoding="utf-8"))
    field_root = Path(field_receipt["local_root"])
    site_ids: set[str] = set()
    for page in field_receipt["pages"]:
        path = field_root / page["file"]
        if path.stat().st_size != page["bytes"] or sha256_file(path) != page["sha256"]:
            raise ValueError(f"Field-measurement source receipt mismatch: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        site_ids.update(
            feature["properties"]["monitoring_location_id"]
            for feature in payload["features"]
        )
    ordered_ids = sorted(site_ids)
    if len(ordered_ids) != field_receipt["monitoring_location_count"]:
        raise ValueError("Field receipt monitoring-location count does not match source")

    args.output_directory.mkdir(parents=True, exist_ok=True)
    pages = []
    returned: set[str] = set()
    datum_counts: dict[str, int] = {}
    altitude_count = 0
    for offset in range(0, len(ordered_ids), BATCH_SIZE):
        requested = ordered_ids[offset : offset + BATCH_SIZE]
        query = urllib.parse.urlencode(
            {"f": "json", "id": ",".join(requested), "limit": BATCH_SIZE}
        )
        url = f"{ENDPOINT}?{query}"
        body = fetch(url)
        payload = json.loads(body)
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("USGS monitoring-location page has no feature list")
        page_ids = {str(feature.get("id", "")) for feature in features}
        if not page_ids <= set(requested):
            raise ValueError("USGS returned an unrequested monitoring location")
        if returned & page_ids:
            raise ValueError("USGS returned duplicate monitoring-location metadata")
        returned.update(page_ids)
        for feature in features:
            properties = feature["properties"]
            datum = properties.get("vertical_datum") or "missing"
            datum_counts[datum] = datum_counts.get(datum, 0) + 1
            if properties.get("altitude") is not None:
                altitude_count += 1
        page_number = len(pages) + 1
        path = args.output_directory / f"monitoring-locations-page-{page_number:04d}.json"
        path.write_bytes(body)
        pages.append(
            {
                "page": page_number,
                "file": path.name,
                "bytes": len(body),
                "sha256": sha256_bytes(body),
                "requested_count": len(requested),
                "returned_count": len(features),
                "request_url": url,
            }
        )
        time.sleep(0.1)

    missing = sorted(set(ordered_ids) - returned)
    receipt = {
        "schema_version": 1,
        "id": "usgs-tvgwfm-monitoring-locations-1986-2015",
        "created_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "provider": "U.S. Geological Survey Water Data APIs",
        "collection": "monitoring-locations",
        "field_measurement_receipt": args.field_receipt.name,
        "field_measurement_receipt_sha256": sha256_file(args.field_receipt),
        "requested_location_count": len(ordered_ids),
        "returned_location_count": len(returned),
        "missing_location_count": len(missing),
        "missing_location_ids": missing,
        "altitude_count": altitude_count,
        "vertical_datum_counts": dict(sorted(datum_counts.items())),
        "page_count": len(pages),
        "total_bytes": sum(page["bytes"] for page in pages),
        "pages": pages,
        "status": "original-api-pages-verified",
    }
    (args.output_directory / "receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Acquired metadata for {len(returned)}/{len(ordered_ids)} locations in "
        f"{len(pages)} pages; {receipt['total_bytes']} bytes; datums={receipt['vertical_datum_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
