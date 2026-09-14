#!/usr/bin/env python3
"""Preserve and receipt the Snake River-at-Weiser directed-network sources."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path


OUTLET_SOURCE = "nwissite"
OUTLET_ID = "USGS-13269000"
OUTLET_COMID = 24193082
NLDI_BASE = "https://api.water.usgs.gov/nldi/linked-data"
EPA_ARCHIVE_URL = (
    "https://dmap-data-commons-ow.s3.amazonaws.com/NHDPlusV21/Data/"
    "NHDPlusPN/NHDPlusV21_PN_17_NHDPlusAttributes_10.7z"
)
EPA_RELEASE_NOTES_URL = (
    "https://dmap-data-commons-ow.s3.amazonaws.com/NHDPlusV21/Data/"
    "NHDPlusPN/0release_notes_VPU17.pdf"
)
USER_AGENT = "TreasureValleySimulator/0.2 receiving-system-acquisition"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, output: Path, maximum_bytes: int) -> None:
    temporary = output.with_suffix(output.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=240) as response:
        if response.status != 200:
            raise RuntimeError(f"Provider returned HTTP {response.status}")
        total = 0
        with temporary.open("wb") as handle:
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > maximum_bytes:
                    raise ValueError(f"Response exceeds {maximum_bytes} bytes")
                handle.write(block)
    temporary.replace(output)


def load_feature_collection(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection" or not isinstance(
        payload.get("features"), list
    ):
        raise ValueError(f"{path.name} is not a GeoJSON FeatureCollection")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)

    urls = {
        "outlet": f"{NLDI_BASE}/{OUTLET_SOURCE}/{OUTLET_ID}?f=json",
        "basin": (
            f"{NLDI_BASE}/{OUTLET_SOURCE}/{OUTLET_ID}/basin"
            "?f=json&simplified=true"
        ),
        "upstream_flowlines": (
            f"{NLDI_BASE}/{OUTLET_SOURCE}/{OUTLET_ID}/navigation/UT/flowlines"
            "?f=json&distance=1500&excludeGeometry=true"
        ),
        "attributes": EPA_ARCHIVE_URL,
        "release_notes": EPA_RELEASE_NOTES_URL,
    }
    paths = {
        "outlet": args.output_directory / "nldi-outlet-usgs-13269000.geojson",
        "basin": args.output_directory / "nldi-upstream-basin-simplified.geojson",
        "upstream_flowlines": args.output_directory
        / "nldi-upstream-flowline-comids-1500km.geojson",
        "attributes": args.output_directory
        / "NHDPlusV21_PN_17_NHDPlusAttributes_10.7z",
        "release_notes": args.output_directory / "0release_notes_VPU17.pdf",
    }
    maximums = {
        "outlet": 100_000,
        "basin": 5_000_000,
        "upstream_flowlines": 20_000_000,
        "attributes": 100_000_000,
        "release_notes": 5_000_000,
    }
    for key, path in paths.items():
        if not path.exists():
            download(urls[key], path, maximums[key])

    outlet = load_feature_collection(paths["outlet"])
    if len(outlet["features"]) != 1:
        raise ValueError("Expected exactly one outlet feature")
    outlet_properties = outlet["features"][0].get("properties") or {}
    if (
        outlet_properties.get("identifier") != OUTLET_ID
        or int(outlet_properties.get("comid")) != OUTLET_COMID
    ):
        raise ValueError("Outlet identity or COMID does not match the verified target")

    basin = load_feature_collection(paths["basin"])
    if len(basin["features"]) != 1:
        raise ValueError("Expected exactly one upstream basin feature")
    basin_geometry = basin["features"][0].get("geometry") or {}
    if basin_geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Upstream basin geometry is not polygonal")

    upstream = load_feature_collection(paths["upstream_flowlines"])
    comids = []
    for feature in upstream["features"]:
        properties = feature.get("properties") or {}
        comid = properties.get("nhdplus_comid")
        if not isinstance(comid, int):
            raise ValueError("Upstream flowline contains a non-integer COMID")
        comids.append(comid)
    if OUTLET_COMID not in comids or len(comids) != len(set(comids)):
        raise ValueError("Upstream COMID set lacks the outlet or contains duplicates")

    if paths["release_notes"].read_bytes()[:4] != b"%PDF":
        raise ValueError("EPA VPU17 release notes are not a PDF")
    archive_listing = subprocess.run(
        ["bsdtar", "-tf", str(paths["attributes"])],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    required_members = {"PlusFlow.dbf", "PlusFlowlineVAA.dbf"}
    found_members = {
        Path(member).name for member in archive_listing if Path(member).name in required_members
    }
    if found_members != required_members:
        raise ValueError(
            f"NHDPlus attribute archive lacks required members: {required_members - found_members}"
        )

    objects = []
    for key, path in paths.items():
        objects.append(
            {
                "role": key,
                "source_url": urls[key],
                "local_path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    receipt = {
        "schema_version": 1,
        "id": "snake-river-at-weiser-directed-network-sources-v1",
        "created_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "providers": [
            "U.S. Geological Survey Network Linked Data Index",
            "U.S. Environmental Protection Agency NHDPlusV2",
        ],
        "target_receiving_system": {
            "name": "Snake River at Weiser ID",
            "nwis_site_id": OUTLET_ID,
            "outlet_comid": OUTLET_COMID,
            "navigation_mode": "upstream-with-tributaries",
            "navigation_distance_km": 1500,
            "published_drainage_area_square_miles": 69200,
        },
        "upstream_flowline_count": len(comids),
        "unique_upstream_comid_count": len(set(comids)),
        "objects": objects,
        "archive_member_count": len(archive_listing),
        "required_archive_members": sorted(found_members),
        "horizontal_crs": "EPSG:4326 for GeoJSON; source-native for archive",
        "format_validation": (
            "outlet-basin-upstream-GeoJSON-and-NHDPlus-7z-members-pass"
        ),
        "status": "original-provider-objects-verified",
        "limitations": [
            "The NLDI navigation is based on the NHDPlusV2 network and may include whole reaches around the indexed outlet location.",
            "A dam is not connected merely because it lies inside the basin; it must be associated with a network COMID and retain a directed path to the outlet.",
            "The 1500-kilometer navigation bound is explicit and must be disclosed with classifications derived from this source set.",
        ],
    }
    args.receipt.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Verified {len(comids)} unique upstream COMIDs and {len(archive_listing)} archive members",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
