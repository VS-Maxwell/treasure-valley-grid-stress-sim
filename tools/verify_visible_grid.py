#!/usr/bin/env python3
"""Verify the direct-entry, replayable transmission-grid build slice."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def embedded_data(legacy: str) -> dict[str, object]:
    prefix = "const DATA = "
    suffix = ";\nconst MAXLOAD"
    start = legacy.index(prefix) + len(prefix)
    end = legacy.index(suffix, start)
    return json.loads(legacy[start:end])


def main() -> int:
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    legacy = (ROOT / "legacy.html").read_text(encoding="utf-8")
    live_grid = (ROOT / "live-grid.html").read_text(encoding="utf-8")
    css = (ROOT / "grid-live.css").read_text(encoding="utf-8")
    script = (ROOT / "grid-live.js").read_text(encoding="utf-8")
    canvas_script = (ROOT / "grid-canvas.js").read_text(encoding="utf-8")
    grid_core = json.loads((ROOT / "data" / "grid-core.json").read_text(encoding="utf-8"))
    data = embedded_data(legacy)
    transmission = data["trans"]
    features = transmission["features"]

    require('src="live-grid.html"' in index, "wrapper loads the crash-safe grid view")
    require("srcdoc" not in index and "fetch('legacy.html')" not in index,
            "wrapper avoids duplicate multi-megabyte srcdoc construction")
    require('href="grid-live.css"' in live_grid, "grid view loads live-grid styles")
    require('src="grid-canvas.js"' in live_grid, "grid view loads bounded Canvas controls")
    require("maplibre" not in live_grid.lower() and "https://" not in live_grid,
            "first playable has no remote map or WebGL startup dependency")
    require("#game-entry-screen" in css and "display: none !important" in css,
            "intro gate is hidden so the map is the first screen")
    require(len(features) == 244, "embedded map snapshot contains 244 drawable corridors")
    require(len(grid_core["trans"]["features"]) == 244,
            "crash-safe grid core retains all 244 drawable corridors")
    require(len(grid_core["subs"]["features"]) == 94,
            "crash-safe grid core retains all 94 mapped substations")
    require(grid_core["source_sha256"] == __import__("hashlib").sha256((ROOT / "legacy.html").read_bytes()).hexdigest(),
            "grid core has a receipt matching the preserved legacy source")
    require("source.setData(" not in script,
            "animation does not repeatedly serialize the multi-megabyte GeoJSON source")
    require("map.setFilter" in script and "BUILD_STEPS = 32" in script,
            "grid replay uses 32 bounded renderer-filter updates")
    require("setVisibleCorridors(0)" in script,
            "grid replay visibly clears the rendered corridor layer")
    require("setTimeout(buildGrid, 650)" in script,
            "grid automatically builds on simulator load")
    require("refreshGrid" in script and "TV_GRID_BUILD" in script,
            "manual refresh and public replay controls are present")
    require("fetch(" not in script,
            "grid replay reuses the embedded historical snapshot without network reload")
    require('fetch("data/grid-core.json")' in canvas_script,
            "Canvas view loads only the local receipt-backed grid core")
    require("BUILD_STEPS = 32" in canvas_script and "requestAnimationFrame" in canvas_script,
            "Canvas animation is bounded to 32 redraw states")
    require("setInterval" not in canvas_script,
            "Canvas view has no perpetual render timer")
    require("INL RAVEN Probabilistic Risk Output" not in legacy,
            "unreceipted RAVEN output is not labeled as validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
