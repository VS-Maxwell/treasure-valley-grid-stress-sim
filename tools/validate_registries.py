#!/usr/bin/env python3
"""Fail closed when release, dependency, model, or data registries drift."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def main() -> int:
    required_files = [
        "THIRD_PARTY_LICENSES.csv",
        "MODEL_REGISTRY.json",
        "DATA_SOURCES.csv",
        "RESTRICTED_DATA_POLICY.md",
        "RELEASE_STATUS.json",
        "receipts/usgs-tvgwfm-core-20260914.json",
        "receipts/tvgwfm-baseline-reproduction-20260914.json",
        "app/public/data/offline-pack-manifest.json",
        "app/public/data/offline-pack-manifest-v2.json",
        "app/public/data/offline-pack-manifest-v3.json",
        "app/public/data/offline-pack-manifest-v4.json",
        "app/public/data/offline-pack-manifest-v5.json",
        "app/public/data/offline-pack-manifest-v6.json",
        "app/public/data/offline-pack-manifest-v7.json",
        "app/public/data/offline-pack-manifest-v8.json",
        "app/public/data/offline-pack-manifest-v9.json",
        "app/public/data/offline-pack-manifest-v10.json",
        "app/public/data/offline-pack-manifest-v11.json",
        "app/public/data/grid-screening-model.json",
        "receipts/usgs-groundwater-field-measurements-20260914.json",
        "receipts/usgs-monitoring-locations-20260914.json",
        "receipts/usgs-3dep-terrain-20260914.json",
        "receipts/usgs-3dep-snake-plain-20260914.json",
        "receipts/usace-nid-regional-dams-20260914.json",
        "receipts/usace-nid-snake-plain-20260914.json",
        "receipts/idwr-espam22-model-20260914.json",
        "receipts/idwr-espam22-grid-20260914.json",
        "app/public/data/idwr-espam22-heads-manifest-v1.json",
        "app/public/data/idwr-espam22-heads-q10-v1.bin",
        "app/public/data/usace-nid-snake-plain-dams-manifest-v2.json",
        "app/public/data/usace-nid-snake-plain-dams-f32-v2.bin",
    ]
    for name in required_files:
        require((ROOT / name).is_file(), f"{name} exists")

    dependencies = read_csv("THIRD_PARTY_LICENSES.csv")
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    registered = {(row["component"], row["version"]) for row in dependencies}
    declared = {
        (name, version)
        for section in ("dependencies", "devDependencies")
        for name, version in package.get(section, {}).items()
    }
    require(declared <= registered, "all direct npm dependencies are registered at their exact versions")
    three = next(row for row in dependencies if row["component"] == "three")
    require(
        three["bundled_in_dist"] == "yes" and three["license"] == "MIT" and three["status"] == "verified",
        "the bundled Three.js runtime has a verified separate license record",
    )

    model_registry = json.loads((ROOT / "MODEL_REGISTRY.json").read_text(encoding="utf-8"))
    models = model_registry["models"]
    require(len(models) >= 3, "planned offline guide, transcription, and surrogate roles are registered")
    for model in models:
        if model["bundled"]:
            require(bool(model["sha256"]), f"bundled model {model['id']} has a SHA-256")
            require(model["license"] not in {"unverified", "unknown"}, f"bundled model {model['id']} has verified terms")

    sources = read_csv("DATA_SOURCES.csv")
    local_sources = [row for row in sources if row["local_path"] and row["local_path"] not in {"not-acquired", "not-configured"}]
    for row in local_sources:
        path = ROOT / row["local_path"]
        require(path.is_file(), f"registered local source exists: {row['id']}")
        if len(row["sha256"]) == 64:
            require(sha256(path) == row["sha256"], f"registered source hash matches: {row['id']}")

    grid = next(row for row in sources if row["id"] == "grid-core-v1")
    require(grid["redistribution"] == "blocked", "incomplete composite grid provenance blocks redistribution")

    receipt = json.loads(
        (ROOT / "receipts/usgs-tvgwfm-core-20260914.json").read_text(encoding="utf-8")
    )
    receipt_root = Path(receipt["local_root"])
    require(receipt["status"] == "original-bytes-verified", "USGS archive receipt records original-byte verification")
    require(sum(item["bytes"] for item in receipt["files"]) == 71_707_343, "USGS bounded acquisition byte total matches")
    for item in receipt["files"]:
        path = receipt_root / item["name"]
        require(path.is_file(), f"USGS receipt file exists: {item['name']}")
        require(path.stat().st_size == item["bytes"], f"USGS receipt byte count matches: {item['name']}")
        require(sha256(path) == item["sha256"], f"USGS receipt SHA-256 matches: {item['name']}")

    baseline = json.loads(
        (ROOT / "receipts/tvgwfm-baseline-reproduction-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    require(baseline["status"] == "numerically-reproduced", "TVGWFM baseline is numerically reproduced")
    require(baseline["normal_termination"] is True, "TVGWFM baseline terminated normally")
    require(
        baseline["rounded_budget_discrepancy_zero_percent"] is True,
        "TVGWFM baseline rounded budget discrepancy is zero percent",
    )
    require(
        baseline["heads"]["max_absolute_difference_feet"] <= 0.001,
        "TVGWFM head comparison meets its recorded tolerance",
    )
    require(
        all(
            result["values_with_text_precision_difference"] == 0
            for result in baseline["observation_outputs"].values()
        ),
        "TVGWFM observation outputs match archived text precision",
    )

    offline_pack = json.loads(
        (ROOT / "app/public/data/offline-pack-manifest-v11.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        offline_pack["network_required"] is False,
        "historical earth pack has no runtime network dependency",
    )
    require(
        offline_pack["artifact_count"] == len(offline_pack["artifacts"]) == 21,
        "offline earth pack v11 has twenty-one manifested artifacts",
    )
    verified_bytes = 0
    for artifact in offline_pack["artifacts"]:
        path = ROOT / "app/public" / artifact["path"]
        require(path.is_file(), f"offline artifact exists: {artifact['id']}")
        require(path.stat().st_size == artifact["bytes"], f"offline artifact byte count matches: {artifact['id']}")
        require(sha256(path) == artifact["sha256"], f"offline artifact SHA-256 matches: {artifact['id']}")
        verified_bytes += path.stat().st_size
    require(
        verified_bytes == offline_pack["total_bytes"],
        "historical earth pack byte total balances",
    )

    energy = json.loads(
        (ROOT / "data/tables/grid-screening-model.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        energy["counts"]["buses"] == len(energy["buses"]) == 94,
        "energy screening pack has 94 buses",
    )
    require(
        energy["counts"]["branches"] == len(energy["branches"]) == 156,
        "energy screening pack has 156 branches",
    )
    require(
        energy["operational_use"] is False
        and energy["truth_state"] == "modeled-screening",
        "energy screening pack rejects operational use",
    )
    require(
        all(
            branch["branch_id"] == branch["corridor_line_id"]
            for branch in energy["branches"]
        ),
        "all energy branches retain exact corridor line IDs",
    )
    require(
        energy["counts"]["branches_with_unique_endpoint_labels"] == 75
        and energy["counts"]["branches_with_ambiguous_endpoint_labels"] == 81,
        "energy endpoint ambiguity remains explicit",
    )

    field_receipt = json.loads(
        (
            ROOT / "receipts/usgs-groundwater-field-measurements-20260914.json"
        ).read_text(encoding="utf-8")
    )
    require(
        field_receipt["status"] == "original-api-pages-verified",
        "USGS field-measurement receipt records verified original API pages",
    )
    require(
        field_receipt["parameter_code"] == "72019"
        and field_receipt["bbox_epsg_4326"]
        == [-117.1163, 43.1762, -115.8097, 44.1081],
        "USGS field measurements retain parameter and spatial bounds",
    )
    field_root = Path(field_receipt["local_root"])
    field_bytes = 0
    field_features = 0
    for page in field_receipt["pages"]:
        path = field_root / page["file"]
        require(path.is_file(), f"field-measurement page exists: {page['page']}")
        require(path.stat().st_size == page["bytes"], f"field-measurement page byte count matches: {page['page']}")
        require(sha256(path) == page["sha256"], f"field-measurement page SHA-256 matches: {page['page']}")
        field_bytes += path.stat().st_size
        field_features += page["feature_count"]
    require(
        field_bytes == field_receipt["total_bytes"]
        and field_features == field_receipt["measurement_count"],
        "USGS field-measurement page totals balance",
    )

    location_receipt = json.loads(
        (ROOT / "receipts/usgs-monitoring-locations-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        location_receipt["status"] == "original-api-pages-verified"
        and location_receipt["requested_location_count"]
        == location_receipt["returned_location_count"]
        == field_receipt["monitoring_location_count"]
        and location_receipt["missing_location_count"] == 0,
        "USGS metadata covers every measured groundwater location",
    )
    require(
        location_receipt["altitude_count"]
        == location_receipt["returned_location_count"]
        and location_receipt["vertical_datum_counts"]
        == {"NAVD88": 2920, "NGVD29": 248},
        "USGS well elevations and vertical-datum counts are explicit",
    )
    location_root = Path(location_receipt["local_root"])
    location_bytes = 0
    location_rows = 0
    for page in location_receipt["pages"]:
        path = location_root / page["file"]
        if (
            not path.is_file()
            or path.stat().st_size != page["bytes"]
            or sha256(path) != page["sha256"]
        ):
            raise AssertionError(
                f"monitoring-location page receipt mismatch: {page['page']}"
            )
        location_bytes += path.stat().st_size
        location_rows += page["returned_count"]
    require(
        location_bytes == location_receipt["total_bytes"]
        and location_rows == location_receipt["returned_location_count"]
        and len(location_receipt["pages"]) == location_receipt["page_count"] == 32,
        "USGS monitoring-location page hashes and totals balance",
    )

    terrain_receipt = json.loads(
        (ROOT / "receipts/usgs-3dep-terrain-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        terrain_receipt["status"] == "original-bytes-and-format-verified"
        and terrain_receipt["horizontal_datum"] == "NAD83"
        and terrain_receipt["vertical_datum"] == "NAVD88"
        and terrain_receipt["elevation_unit"] == "meters",
        "USGS 3DEP receipt records format and datum verification",
    )
    expected_terrain_hashes = {
        "n44w116": "7e7d2690ed1855a4fc25953b3b24bb818d77443070253d7563bdd3565a28fe4c",
        "n44w117": "8541835a7f27956e40603945997398688b3911c92e86b1b324a68de9c26181f5",
        "n44w118": "30810efe49936116e994c4feb11691174d733c635310155fc8efeb60e6754906",
        "n45w116": "d5df76542ad0aa72f17ad503552b7334b2cd0f28311a817284d5bb99e9c9dae6",
        "n45w117": "c5c826e779453eaa6bfd4f42c22bd300579595cee39713ad06fa0b25f3178fbc",
        "n45w118": "d16a3537e9f21f7a005e0d71b83ea38d7293a9b7fc1017d1a157c9cc5882cc70",
    }
    terrain_root = Path(terrain_receipt["local_root"])
    terrain_bytes = 0
    require(
        {item["tile"] for item in terrain_receipt["files"]}
        == set(expected_terrain_hashes),
        "USGS 3DEP receipt contains the exact six-tile regional baseline",
    )
    for item in terrain_receipt["files"]:
        path = terrain_root / item["file"]
        require(
            path.is_file()
            and path.stat().st_size == item["bytes"]
            and sha256(path) == item["sha256"] == expected_terrain_hashes[item["tile"]],
            f"USGS 3DEP source tile matches receipt: {item['tile']}",
        )
        terrain_bytes += path.stat().st_size
    require(
        terrain_bytes == terrain_receipt["total_bytes"] == 316_921_023,
        "USGS 3DEP source byte total balances",
    )

    terrain_manifest = json.loads(
        (
            ROOT / "app/public/data/usgs-3dep-regional-terrain-manifest.json"
        ).read_text(encoding="utf-8")
    )
    terrain_binary = ROOT / "app/public/data/usgs-3dep-regional-terrain-f32.bin"
    require(
        terrain_manifest["mesh"]["vertex_count"] == 15_251
        and terrain_manifest["mesh"]["rows"] == 101
        and terrain_manifest["mesh"]["columns"] == 151
        and terrain_manifest["mesh"]["bounds_wgs84"]
        == {"west": -118.0, "east": -115.0, "south": 43.0, "north": 45.0},
        "regional terrain mesh dimensions and geographic bounds match",
    )
    require(
        terrain_binary.stat().st_size == terrain_manifest["binary"]["bytes"] == 61_004
        and sha256(terrain_binary) == terrain_manifest["binary"]["sha256"],
        "regional terrain binary hash and byte count match",
    )

    plain_receipt = json.loads(
        (ROOT / "receipts/usgs-3dep-snake-plain-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        plain_receipt["status"] == "original-bytes-and-format-verified"
        and plain_receipt["tile_count"] == 32
        and plain_receipt["bbox_epsg_4326"] == [-119.0, 42.0, -111.0, 46.0],
        "Snake Plain 3DEP receipt has the exact 32-tile full-scene envelope",
    )
    plain_root = Path(plain_receipt["local_root"])
    plain_bytes = 0
    for item in plain_receipt["files"]:
        path = plain_root / item["file"]
        require(
            path.is_file()
            and path.stat().st_size == item["bytes"]
            and sha256(path) == item["sha256"],
            f"Snake Plain 3DEP tile matches receipt: {item['tile']}",
        )
        plain_bytes += path.stat().st_size
    require(
        plain_bytes == plain_receipt["total_bytes"] == 1_639_886_219,
        "Snake Plain 3DEP source byte total balances",
    )
    plain_manifest = json.loads(
        (
            ROOT / "app/public/data/usgs-3dep-snake-plain-terrain-manifest-v4.json"
        ).read_text(encoding="utf-8")
    )
    plain_binary = (
        ROOT / "app/public/data/usgs-3dep-snake-plain-terrain-f32-v4.bin"
    )
    require(
        plain_manifest["mesh"]["vertex_count"] == 80_601
        and plain_manifest["mesh"]["rows"] == 201
        and plain_manifest["mesh"]["columns"] == 401
        and plain_manifest["mesh"]["bounds_wgs84"]
        == {"west": -119.0, "east": -111.0, "south": 42.0, "north": 46.0},
        "Snake Plain terrain mesh dimensions and geographic bounds match",
    )
    require(
        plain_binary.stat().st_size
        == plain_manifest["binary"]["bytes"]
        == 322_404
        and sha256(plain_binary) == plain_manifest["binary"]["sha256"],
        "Snake Plain terrain binary hash and byte count match",
    )

    espam_model = json.loads(
        (ROOT / "receipts/idwr-espam22-model-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        espam_model["status"] == "original-bytes-and-format-verified"
        and espam_model["file_count"] == 3
        and espam_model["total_bytes"] == 494_832_320,
        "ESPAM 2.2 model archives have verified counts and status",
    )
    espam_model_root = Path(espam_model["local_root"])
    for item in espam_model["files"]:
        path = espam_model_root / item["file"]
        require(
            path.is_file()
            and path.stat().st_size == item["bytes"]
            and sha256(path) == item["sha256"],
            f"ESPAM 2.2 archive matches receipt: {item['file']}",
        )

    espam_grid_receipt = json.loads(
        (ROOT / "receipts/idwr-espam22-grid-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        espam_grid_receipt["status"]
        == "original-api-pages-and-geometry-verified"
        and espam_grid_receipt["feature_count"]
        == espam_grid_receipt["active_count"]
        == 11_236
        and espam_grid_receipt["page_count"] == 6,
        "ESPAM 2.2 grid service returns the complete active-cell set",
    )
    espam_grid_root = Path(espam_grid_receipt["local_root"])
    for page in espam_grid_receipt["pages"]:
        path = espam_grid_root / page["file"]
        require(
            path.is_file()
            and path.stat().st_size == page["bytes"]
            and sha256(path) == page["sha256"],
            f"ESPAM grid page matches receipt: {page['page']}",
        )
    espam_manifest = json.loads(
        (ROOT / "app/public/data/idwr-espam22-grid-manifest-v1.json").read_text(
            encoding="utf-8"
        )
    )
    espam_lines = ROOT / "app/public/data/idwr-espam22-grid-lines-f32-v1.bin"
    espam_cells = ROOT / "app/public/data/idwr-espam22-grid-cells-f32-v1.bin"
    require(
        espam_manifest["layout"]
        | {"row_id_range": [5, 104], "column_id_range": [5, 204]}
        == espam_manifest["layout"]
        and espam_manifest["layout"]["layers"] == 1
        and espam_manifest["layout"]["rows"] == 104
        and espam_manifest["layout"]["columns"] == 209
        and espam_manifest["layout"]["stress_periods"] == 462
        and espam_manifest["layout"]["active_cells"] == 11_236,
        "ESPAM 2.2 browser grid retains source model dimensions",
    )
    require(
        espam_lines.stat().st_size
        == espam_manifest["line_binary"]["bytes"]
        == 719_104
        and sha256(espam_lines) == espam_manifest["line_binary"]["sha256"]
        and espam_cells.stat().st_size
        == espam_manifest["cell_binary"]["bytes"]
        == 179_776
        and sha256(espam_cells) == espam_manifest["cell_binary"]["sha256"],
        "ESPAM 2.2 line and cell binaries match their hashes",
    )
    espam_heads_manifest = json.loads(
        (
            ROOT / "app/public/data/idwr-espam22-heads-manifest-v1.json"
        ).read_text(encoding="utf-8")
    )
    espam_heads = ROOT / "app/public/data/idwr-espam22-heads-q10-v1.bin"
    require(
        espam_heads_manifest["truth_state"] == "ingested"
        and espam_heads_manifest["representation"]
        == "archived-modeled-output-not-independently-reproduced"
        and espam_heads_manifest["active_cell_count"] == 11_236
        and espam_heads_manifest["slice_count"] == 39
        and espam_heads_manifest["source_head_record_count"] == 923
        and espam_heads_manifest["slices"][0]["year"] == 1980
        and espam_heads_manifest["slices"][-1]["year"] == 2018,
        "ESPAM archived-head pack retains scope and non-reproduction boundary",
    )
    require(
        espam_heads.stat().st_size
        == espam_heads_manifest["binary"]["bytes"]
        == 876_408
        and sha256(espam_heads) == espam_heads_manifest["binary"]["sha256"],
        "ESPAM archived-head binary matches its byte count and hash",
    )

    dam_receipt = json.loads(
        (ROOT / "receipts/usace-nid-regional-dams-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    dam_source = Path(dam_receipt["local_root"]) / dam_receipt["source_file"]
    require(
        dam_receipt["status"] == "original-api-response-verified"
        and dam_receipt["feature_count"]
        == dam_receipt["unique_provider_record_count"]
        == 193
        and dam_receipt["hydroelectric_purpose_count"] == 11,
        "USACE NID regional source counts and status match",
    )
    require(
        dam_receipt["unique_nidid_count"] == 189
        and dam_receipt["duplicate_nidid_record_count"] == 3
        and dam_receipt["missing_nidid_count"] == 1,
        "USACE NID shared and missing identifier cases are retained",
    )
    require(
        dam_source.is_file()
        and dam_source.stat().st_size == dam_receipt["bytes"] == 173_719
        and sha256(dam_source) == dam_receipt["sha256"],
        "USACE NID original GeoJSON bytes match the receipt",
    )
    dam_manifest = json.loads(
        (ROOT / "app/public/data/usace-nid-dams-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    dam_binary = ROOT / "app/public/data/usace-nid-dams-f32.bin"
    require(
        dam_manifest["dam_count"] == 193
        and dam_manifest["hydroelectric_purpose_count"] == 11
        and dam_manifest["connectivity_state"]
        == "unresolved-pending-upstream-watershed-graph",
        "regional dam layer retains its connectivity boundary",
    )
    require(
        dam_binary.stat().st_size == dam_manifest["binary"]["bytes"] == 2_316
        and sha256(dam_binary) == dam_manifest["binary"]["sha256"],
        "regional dam point binary hash and byte count match",
    )
    plain_dam_receipt = json.loads(
        (ROOT / "receipts/usace-nid-snake-plain-20260914.json").read_text(
            encoding="utf-8"
        )
    )
    plain_dam_source = (
        Path(plain_dam_receipt["local_root"]) / plain_dam_receipt["source_file"]
    )
    require(
        plain_dam_receipt["status"] == "original-api-response-verified"
        and plain_dam_receipt["bbox_epsg_4326"]
        == [-119.0, 42.0, -111.0, 46.0]
        and plain_dam_receipt["feature_count"]
        == plain_dam_receipt["unique_provider_record_count"]
        == 647
        and plain_dam_receipt["hydroelectric_purpose_count"] == 55,
        "full-scene NID source retains exact scope and counts",
    )
    require(
        plain_dam_source.is_file()
        and plain_dam_source.stat().st_size
        == plain_dam_receipt["bytes"]
        == 581_335
        and sha256(plain_dam_source) == plain_dam_receipt["sha256"],
        "full-scene NID original GeoJSON bytes match the receipt",
    )
    plain_dam_manifest = json.loads(
        (
            ROOT / "app/public/data/usace-nid-snake-plain-dams-manifest-v2.json"
        ).read_text(encoding="utf-8")
    )
    plain_dam_binary = (
        ROOT / "app/public/data/usace-nid-snake-plain-dams-f32-v2.bin"
    )
    require(
        plain_dam_manifest["dam_count"] == 647
        and plain_dam_manifest["hydroelectric_purpose_count"] == 55
        and plain_dam_manifest["bbox_epsg_4326"]
        == [-119.0, 42.0, -111.0, 46.0]
        and plain_dam_manifest["connectivity_state"]
        == "unresolved-pending-upstream-watershed-graph",
        "full-scene dam layer retains its geographic and connectivity boundary",
    )
    require(
        plain_dam_binary.stat().st_size
        == plain_dam_manifest["binary"]["bytes"]
        == 7_764
        and sha256(plain_dam_binary) == plain_dam_manifest["binary"]["sha256"],
        "full-scene dam point binary matches its byte count and hash",
    )

    bottoms_manifest = json.loads(
        (ROOT / "app/public/data/tvgwfm-bottoms-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    bottoms_binary = ROOT / "app/public/data/tvgwfm-bottoms-f32.bin"
    idomain_binary = ROOT / "app/public/data/tvgwfm-idomain-i8.bin"
    require(
        bottoms_manifest["truth_state"] == "ingested"
        and bottoms_manifest["source_archive"]["sha256"]
        == "bdefb11eaf7b75ab63dc0b23b0de4f65fe9d68798c0ff229420322bf8abb0dd6"
        and bottoms_manifest["source_archive"]["member"]
        == "model/mf6-tv_hist.dis",
        "TVGWFM layer bottoms retain their exact source archive and member",
    )
    layout = bottoms_manifest["layout"]
    require(
        layout["layers"] == 6
        and layout["rows"] == 64
        and layout["columns"] == 65
        and layout["cell_count"] == 4_160
        and layout["order"] == "layer-row-column"
        and layout["length_unit"] == "feet"
        and layout["vertical_datum"] == "NAVD88",
        "TVGWFM bottom-surface dimensions, order, unit and datum match",
    )
    require(
        len(bottoms_manifest["layer_statistics"]) == 6
        and [item["active_cells"] for item in bottoms_manifest["layer_statistics"]]
        == [1_861] * 6,
        "TVGWFM bottom manifest retains six active-layer statistics",
    )
    require(
        bottoms_binary.stat().st_size
        == bottoms_manifest["bottoms_binary"]["bytes"]
        == 99_840
        and sha256(bottoms_binary)
        == bottoms_manifest["bottoms_binary"]["sha256"],
        "TVGWFM bottom float32 binary hash and byte count match",
    )
    require(
        idomain_binary.stat().st_size
        == bottoms_manifest["idomain_binary"]["bytes"]
        == 24_960
        and sha256(idomain_binary)
        == bottoms_manifest["idomain_binary"]["sha256"],
        "TVGWFM IDOMAIN int8 binary hash and byte count match",
    )

    policy = (ROOT / "RESTRICTED_DATA_POLICY.md").read_text(encoding="utf-8")
    require("does not apply" in policy and "sovereignty-sensitive" in policy, "restricted-data policy excludes non-code material from the project license")

    release = json.loads((ROOT / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    require(release["public_release_approved"] is False, "public release remains fail-closed while provenance gates are open")
    require(bool(release["open_gates"]), "release status lists concrete open gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
