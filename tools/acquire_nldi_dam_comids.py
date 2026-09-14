#!/usr/bin/env python3
"""Resolve each full-scene NID dam point to an NLDI NHDPlusV2 COMID."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


SERVICE = "https://api.water.usgs.gov/nldi/linked-data/comid/position"
USER_AGENT = "TreasureValleySimulator/0.2 dam-comid-acquisition"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def resolve(record: dict, output_directory: Path) -> dict:
    object_id = int(record["object_id"])
    longitude = float(record["longitude"])
    latitude = float(record["latitude"])
    query = urllib.parse.urlencode(
        {"f": "json", "coords": f"POINT({longitude:.12f} {latitude:.12f})"}
    )
    url = f"{SERVICE}?{query}"
    output_path = output_directory / f"objectid-{object_id}.geojson"
    response_status = 200
    if output_path.exists():
        body = output_path.read_bytes()
    else:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                try:
                    with urllib.request.urlopen(request, timeout=90) as response:
                        response_status = response.status
                        body = response.read(250_001)
                except urllib.error.HTTPError as exc:
                    if exc.code != 404:
                        raise
                    response_status = exc.code
                    body = exc.read(250_001)
                if len(body) > 250_000:
                    raise ValueError("NLDI position response exceeded 250000 bytes")
                temporary = output_path.with_suffix(".geojson.part")
                temporary.write_bytes(body)
                temporary.replace(output_path)
                break
            except Exception as exc:  # retain bounded retry evidence in final receipt
                last_error = exc
                if attempt == 3:
                    raise
                time.sleep(0.5 * (2**attempt))
        else:  # pragma: no cover
            raise RuntimeError(str(last_error))
    payload = json.loads(body)
    features = payload.get("features") if response_status == 200 else []
    if response_status == 200 and payload.get("type") != "FeatureCollection":
        raise ValueError(f"Dam OBJECTID {object_id} response is not a FeatureCollection")
    if not isinstance(features, list) or len(features) > 1:
        raise ValueError(f"Dam OBJECTID {object_id} returned an invalid feature count")
    comid = None
    if features:
        properties = features[0].get("properties") or {}
        value = properties.get("identifier") or properties.get("comid")
        if value is not None:
            comid = int(value)
    return {
        "provider_record_id": record["provider_record_id"],
        "object_id": object_id,
        "nid_id": record.get("nid_id"),
        "longitude": longitude,
        "latitude": latitude,
        "query_url": url,
        "http_status": response_status,
        "source_file": output_path.name,
        "bytes": len(body),
        "sha256": sha256_bytes(body),
        "comid": comid,
        "resolution_state": (
            "resolved"
            if comid is not None
            else "unresolved-no-indexed-catchment"
            if response_status == 404
            else "unresolved-no-feature"
        ),
    }


def write_receipt(path: Path, entries: list[dict], expected: int, state: str) -> None:
    resolved = sum(entry["comid"] is not None for entry in entries)
    receipt = {
        "schema_version": 1,
        "id": "usgs-nldi-full-scene-dam-comids-v1",
        "created_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "provider": "U.S. Geological Survey Network Linked Data Index",
        "service_url": SERVICE,
        "method": "NHDPlusV2 catchment position lookup at each NID point",
        "expected_dam_count": expected,
        "processed_dam_count": len(entries),
        "resolved_comid_count": resolved,
        "unresolved_count": len(entries) - resolved,
        "status": state,
        "records": sorted(entries, key=lambda entry: entry["object_id"]),
        "limitations": [
            "Catchment membership is not yet a directed path to the target outlet.",
            "The NID point is treated as the dam location supplied by USACE; no positional correction is invented.",
            "Only a COMID present in the preserved upstream set and a complete PlusFlow path may be classified as connected.",
        ],
    }
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dam_table", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.workers <= 12:
        raise ValueError("workers must be between 1 and 12")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    table = json.loads(args.dam_table.read_text(encoding="utf-8"))
    records = table.get("records")
    if not isinstance(records, list) or table.get("dam_count") != len(records):
        raise ValueError("Dam table count does not match its records")

    entries: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(resolve, record, args.output_directory): record
            for record in records
        }
        for future in concurrent.futures.as_completed(futures):
            entries.append(future.result())
            if len(entries) % 25 == 0:
                write_receipt(args.receipt, entries, len(records), "acquisition-in-progress")
                print(f"Resolved {len(entries)}/{len(records)} dam positions", flush=True)

    write_receipt(args.receipt, entries, len(records), "original-api-responses-verified")
    resolved = sum(entry["comid"] is not None for entry in entries)
    print(f"Verified {len(entries)} dam responses; {resolved} COMIDs resolved", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
