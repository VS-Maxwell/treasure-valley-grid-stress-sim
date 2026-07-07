#!/usr/bin/env python3
"""Refresh the simulator's embedded EIA-930 IPCO demand window.

This is a local/build-time updater. It reads EIA_API_KEY from the local
environment or a local .env file, fetches measured EIA-930 demand, and rewrites
only the embedded window.EIA_DEMAND block in index.html. It never writes or
prints the key.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable


EIA_REGION_DATA_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
DEFAULT_DATAHUB_ENV = Path(
    r"E:\Sovereign_Organized\_03_RESEARCH_ACADEMIC\ERIC_TV_DataHub_Live_20260605\.env"
)
USER_AGENT = "Treasure-Valley-Sim-Local-EIA-Refresh/1.0"


class RefreshError(RuntimeError):
    """Raised for hard refresh failures."""


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Fetch latest EIA-930 IPCO demand and update index.html."
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=repo_root / "index.html",
        help="HTML file containing window.EIA_DEMAND.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Local .env file containing EIA_API_KEY. Values are never printed.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=240,
        help="Number of latest hourly demand records to embed.",
    )
    parser.add_argument(
        "--respondent",
        default="IPCO",
        help="EIA balancing authority respondent code.",
    )
    parser.add_argument(
        "--series",
        default="D",
        help="EIA region-data type code. D is demand.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate, but do not modify the HTML file.",
    )
    return parser.parse_args()


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise RefreshError(f"Could not read env file: {path} ({exc.__class__.__name__})") from None

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name:
            values[name] = value
    return values


def env_candidates(explicit: Path | None, html: Path) -> Iterable[Path]:
    if explicit is not None:
        yield explicit
        return

    env_file = os.environ.get("TV_EIA_ENV_FILE")
    if env_file:
        yield Path(env_file)

    repo_root = html.resolve().parent
    yield repo_root / ".env"
    yield repo_root.parent / ".env"
    yield DEFAULT_DATAHUB_ENV


def load_eia_key(explicit_env: Path | None, html: Path) -> tuple[str, Path | str]:
    from_process = os.environ.get("EIA_API_KEY")
    if from_process:
        return from_process.strip(), "process environment"

    checked: list[str] = []
    for candidate in env_candidates(explicit_env, html):
        checked.append(str(candidate))
        if not candidate.exists():
            continue
        value = read_dotenv(candidate).get("EIA_API_KEY", "").strip()
        if value:
            return value, candidate

    raise RefreshError(
        "EIA_API_KEY was not found. Checked process environment and: "
        + "; ".join(checked)
    )


def eia_query(key: str, respondent: str, series: str, hours: int) -> list[dict]:
    if hours < 1:
        raise RefreshError("--hours must be positive")

    params = [
        ("api_key", key),
        ("frequency", "hourly"),
        ("data[0]", "value"),
        ("facets[respondent][]", respondent),
        ("facets[type][]", series),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "desc"),
        ("length", str(hours)),
    ]
    url = EIA_REGION_DATA_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RefreshError(f"EIA request failed: HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise RefreshError(f"EIA request failed: network error {exc.reason}") from None
    except json.JSONDecodeError:
        raise RefreshError("EIA request failed: response was not JSON") from None

    rows = payload.get("response", {}).get("data", [])
    if not isinstance(rows, list) or not rows:
        raise RefreshError("EIA response contained no data rows")
    return rows


def normalize_points(rows: list[dict]) -> list[list[object]]:
    by_period: dict[str, int] = {}
    for row in rows:
        period = str(row.get("period", "")).strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}$", period):
            continue
        raw_value = row.get("value")
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if math.isnan(value) or math.isinf(value):
            continue
        by_period[period] = int(round(value))

    points = [[period, value] for period, value in sorted(by_period.items())]
    if len(points) < 24:
        raise RefreshError(f"EIA response yielded too few valid hourly points: {len(points)}")
    return points


def demand_meta(points: list[list[object]], respondent: str, series: str) -> dict[str, object]:
    retrieved_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    retrieved_at = retrieved_at.replace("+00:00", "Z")
    start = str(points[0][0])
    end = str(points[-1][0])
    row_count = len(points)
    return {
        "source": "EIA API v2 electricity/rto/region-data",
        "source_url": EIA_REGION_DATA_URL,
        "respondent": respondent,
        "series": series,
        "series_name": "Demand" if series.upper() == "D" else series,
        "retrieved_at_utc": retrieved_at,
        "period_start": start,
        "period_end": end,
        "row_count": row_count,
        "headerLabel": "CURRENT EIA-930 DEMAND",
        "subLabel": f"Idaho Power - latest {row_count} hourly records",
        "peakLabel": "rolling window peak",
        "playLabel": "Play demand window",
        "sourceLabel": (
            "Source: U.S. EIA API v2 electricity/rto/region-data - "
            f"{respondent} Demand ({series}), latest {row_count} hourly records "
            f"from {start} through {end}; retrieved {retrieved_at}. "
            "This is measured EIA-930 operating data, not a future forecast. "
            "Line colors map demand onto pandapower screening scenarios "
            "(relative stress indicators)."
        ),
    }


def update_html(html_path: Path, points: list[list[object]], meta: dict[str, object]) -> bool:
    try:
        text = html_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RefreshError(f"Could not read HTML: {html_path} ({exc.__class__.__name__})") from None

    demand_js = "window.EIA_DEMAND=" + json.dumps(points, separators=(",", ":")) + ";"
    meta_js = "window.EIA_DEMAND_META=" + json.dumps(meta, separators=(",", ":")) + ";"

    demand_pattern = re.compile(r"window\.EIA_DEMAND=\[.*?\];", re.DOTALL)
    text, demand_replacements = demand_pattern.subn(demand_js, text, count=1)
    if demand_replacements != 1:
        raise RefreshError("Could not find exactly one window.EIA_DEMAND block in HTML")

    meta_pattern = re.compile(r"window\.EIA_DEMAND_META=\{.*?\};", re.DOTALL)
    text, meta_replacements = meta_pattern.subn(meta_js, text, count=1)
    if meta_replacements == 0:
        text = text.replace(demand_js, demand_js + "\n" + meta_js, 1)
    elif meta_replacements != 1:
        raise RefreshError("Found more than one window.EIA_DEMAND_META block in HTML")

    try:
        html_path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise RefreshError(f"Could not write HTML: {html_path} ({exc.__class__.__name__})") from None
    return True


def main() -> int:
    args = parse_args()
    try:
        key, key_source = load_eia_key(args.env_file, args.html)
        rows = eia_query(key, args.respondent, args.series, args.hours)
        points = normalize_points(rows)
        meta = demand_meta(points, args.respondent, args.series)
        if not args.dry_run:
            update_html(args.html, points, meta)

        print("status=ok")
        print(f"html={args.html}")
        print(f"env_source={key_source}")
        print(f"rows={len(points)}")
        print(f"period_start={points[0][0]}")
        print(f"period_end={points[-1][0]}")
        print(f"retrieved_at_utc={meta['retrieved_at_utc']}")
        print("wrote_html=" + str(not args.dry_run).lower())
        return 0
    except RefreshError as exc:
        print(f"status=failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
