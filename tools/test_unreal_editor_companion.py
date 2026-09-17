#!/usr/bin/env python3
"""
Treasure Valley Simulator — Unreal Engine Companion Diagnostic
Probes local and fleet Unreal Engine 5.8.2 installations, verifies
dynamic libraries, and checks readiness for ArcGIS Maps SDK and OpenUSD.

License: Apache-2.0
"""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

CANDIDATE_PATHS = [
    Path("/run/media/madame-butterfly/Stargate/Linux_Unreal_Engine_5.8.2/Engine/Binaries/Linux/UnrealEditor"),
    Path("/home/madame-butterfly/Downloads/Linux_Unreal_Engine_5.8.2/Engine/Binaries/Linux/UnrealEditor"),
    Path("/home/palimpsest/Downloads/Linux_Unreal_Engine_5.8.2/Engine/Binaries/Linux/UnrealEditor"),
    Path("/home/nixie/Downloads/Linux_Unreal_Engine_5.8.2/Engine/Binaries/Linux/UnrealEditor"),
]


def candidate_paths() -> list[Path]:
    configured = os.environ.get("UNREAL_EDITOR")
    paths = [Path(configured)] if configured else []
    discovered = shutil.which("UnrealEditor")
    if discovered:
        paths.append(Path(discovered))
    paths.extend(CANDIDATE_PATHS)
    return list(dict.fromkeys(paths))


def check_unreal_binary() -> dict:
    found_path = None
    for path in candidate_paths():
        if path.is_file():
            found_path = path
            break

    if not found_path:
        return {
            "status": "not_installed",
            "message": "UnrealEditor not found in configured, PATH, or candidate paths",
            "candidates": [str(path) for path in candidate_paths()],
        }

    is_exec = os.access(found_path, os.X_OK)
    missing_libs = []
    ldd_error = None
    if is_exec:
        try:
            ldd_out = subprocess.run(
                ["ldd", "--", str(found_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            combined_output = f"{ldd_out.stdout}\n{ldd_out.stderr}"
            missing_libs = [
                line.strip()
                for line in combined_output.splitlines()
                if "not found" in line
            ]
            if ldd_out.returncode != 0:
                ldd_error = f"ldd exited with status {ldd_out.returncode}"
        except (OSError, subprocess.TimeoutExpired) as error:
            ldd_error = f"ldd check failed: {error}"
    else:
        ldd_error = "UnrealEditor is not executable"

    engine_dir = found_path.parents[2]
    usd_plugin = engine_dir / "Plugins/Importers/USDImporter"
    usd_plugin_present = usd_plugin.is_dir()
    status = (
        "ready"
        if is_exec and not missing_libs and ldd_error is None and usd_plugin_present
        else "degraded"
    )
    result = {
        "status": status,
        "path": str(found_path),
        "executable": is_exec,
        "missing_libraries": missing_libs,
        "usd_importer_plugin_present": usd_plugin_present,
        "engine_version": next(
            (part.removeprefix("Linux_Unreal_Engine_") for part in found_path.parts if part.startswith("Linux_Unreal_Engine_")),
            "unknown",
        ),
    }
    if ldd_error:
        result["ldd_error"] = ldd_error
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local Unreal Engine runtime readiness.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless the result is ready.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check_unreal_binary()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not args.json:
        if result["status"] == "ready":
            print(f"\n[OK] Unreal Engine {result['engine_version']} is ready at: {result['path']}")
        else:
            print(f"\n[WARN] Unreal Engine status: {result['status']}")
    return 0 if result["status"] == "ready" or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
