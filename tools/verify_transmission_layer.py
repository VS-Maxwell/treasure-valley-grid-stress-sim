#!/usr/bin/env python3
"""Verify the expert transmission-modeling layer is present in index.html."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "index.html"


REQUIRED_MARKERS = {
    "layer toggle": 'id="t-team-transmission-model"',
    "section id": 'id="team-transmission-model-sect"',
    "domain": 'data-domain="energy nexus"',
    "load clusters source": "Substation load clusters",
    "population correlation": "population-to-load",
    "load factor": "load factor",
    "sector division": "sector-wise load",
    "generation assumptions": "Generation assumptions",
    "transformer assumption": "ideal transformer",
    "steady state": "steady-state DC power-flow",
    "real time": "real-time EIA demand scaling",
    "ybus matrix": "Ybus matrix",
    "bus table": "Voltage / angle by bus",
    "model source object": "window.TEAM_TRANSMISSION_MODEL",
    "model render function": "renderTeamTransmissionModel",
    "model map source": "team-load-clusters",
}


def main() -> int:
    html = INDEX_HTML.read_text(encoding="utf-8")
    missing = [name for name, marker in REQUIRED_MARKERS.items() if marker not in html]
    if missing:
        print("status=failed")
        for name in missing:
            print(f"missing={name}: {REQUIRED_MARKERS[name]}")
        return 1

    print("status=ok")
    print(f"checked={INDEX_HTML}")
    print(f"markers={len(REQUIRED_MARKERS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
