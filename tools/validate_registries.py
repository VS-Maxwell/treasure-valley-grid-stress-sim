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
        "receipts/usgs-groundwater-field-measurements-20260914.json",
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
        (ROOT / "app/public/data/offline-pack-manifest-v2.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        offline_pack["network_required"] is False,
        "historical water pack has no runtime network dependency",
    )
    require(
        offline_pack["artifact_count"] == len(offline_pack["artifacts"]) == 6,
        "historical water pack has six manifested artifacts",
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
        "historical water pack byte total balances",
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

    policy = (ROOT / "RESTRICTED_DATA_POLICY.md").read_text(encoding="utf-8")
    require("does not apply" in policy and "sovereignty-sensitive" in policy, "restricted-data policy excludes non-code material from the project license")

    release = json.loads((ROOT / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    require(release["public_release_approved"] is False, "public release remains fail-closed while provenance gates are open")
    require(bool(release["open_gates"]), "release status lists concrete open gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
