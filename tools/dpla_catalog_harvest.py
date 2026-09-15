#!/usr/bin/env python3
"""DPLA catalog harvester for the CDA U&A expanded scope.

Pages the DPLA API v2 across CDA-relevant keyword sets, de-duplicates, and
writes to a JSONL ledger. Metadata only — no downloads.

Requires DPLA_API_KEY in environment or in the env-file at argv[2].

Copyright (c) 2026 LAS Consulting & V.S. Maxwell-Miller
SPDX-License-Identifier: Apache-2.0 OR MIT
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "SovereignArchivalStandard/1.0 (CDA estate preservation)"
DPLA = "https://api.dp.la/v2/items"
MAX_PAGE = 100  # DPLA caps at page 100 per query

# CDA U&A keyword sets — broad enough to catch everything relevant
QUERIES = [
    # Core tribal
    "Coeur d'Alene",
    "Nez Perce",
    "Schitsu'umsh",
    "Kalispel OR Spokane tribe OR Salish OR Palouse",
    "tribal sovereignty Idaho",
    "Indian treaty Idaho OR Washington OR Oregon",
    "usual and accustomed",
    "aboriginal title",
    "ceded lands",
    "Indian Claims Commission",
    "Bureau of Indian Affairs Idaho",
    # Land use & valuation
    "land use Idaho",
    "land value Idaho",
    "real estate Idaho",
    "property tax Idaho",
    "land appraisal Idaho OR Washington",
    "zoning Idaho",
    "comprehensive plan Idaho",
    # Urban & socioeconomic
    "urban planning Idaho OR Boise",
    "socioeconomic Idaho",
    "economic development Idaho",
    "census Idaho",
    "cost of living Idaho",
    "poverty Idaho reservation",
    # Energy
    "hydroelectric Idaho OR Snake River",
    "Bonneville Power Administration",
    "Idaho Power",
    "dam Idaho OR Snake River",
    "energy Idaho",
    "transmission line Idaho",
    # Environmental & water
    "water rights Idaho",
    "water quality Coeur d'Alene",
    "Superfund Coeur d'Alene OR Bunker Hill",
    "salmon Idaho OR Snake River OR Columbia",
    "Bureau of Reclamation Idaho",
    "Army Corps of Engineers Idaho",
    "irrigation Idaho",
    "Clean Water Act Idaho",
    # Agriculture & resources
    "agriculture Idaho OR Palouse OR Treasure Valley",
    "timber Idaho OR Clearwater",
    "mining Idaho OR Silver Valley",
    "grazing Idaho",
    # Infrastructure
    "highway Idaho",
    "railroad Idaho OR Northern Pacific",
    "Coeur d'Alene Lake",
    # Geography
    "Idaho",
    "Treasure Valley Idaho",
    "Snake River",
    "Clearwater River Idaho",
    "Pacific Northwest",
]


def load_api_key(env_file: str | None = None) -> str:
    key = os.environ.get("DPLA_API_KEY")
    if key:
        return key
    if env_file and Path(env_file).exists():
        for line in Path(env_file).read_text().splitlines():
            if line.startswith("DPLA_API_KEY="):
                return line.split("=", 1)[1].strip("\"'")
    raise RuntimeError("DPLA_API_KEY not found in environment or env-file")


def http_json(url: str, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    return {}


def harvest_query(query: str, api_key: str) -> list[dict]:
    """Page through all results for a DPLA query (max 100 pages × 500 items)."""
    items: list[dict] = []
    for page in range(1, MAX_PAGE + 1):
        params = {
            "q": query,
            "page_size": "500",
            "page": str(page),
            "api_key": api_key,
        }
        url = f"{DPLA}?{urllib.parse.urlencode(params)}"
        data = http_json(url)
        docs = data.get("docs", [])
        items.extend(docs)
        if len(docs) < 500:
            break
        time.sleep(0.3)  # politeness
    return items


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dpla_catalog_ledger.jsonl")
    env_file = sys.argv[2] if len(sys.argv) > 2 else None
    api_key = load_api_key(env_file)

    seen: dict[str, dict] = {}
    # Load existing if present
    if out.exists():
        with out.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    it = json.loads(line)
                    dpla_id = it.get("id") or it.get("_id")
                    if dpla_id:
                        seen[dpla_id] = it
                except json.JSONDecodeError:
                    pass
        print(f"Loaded {len(seen)} existing DPLA records from {out}")

    initial_count = len(seen)

    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] {query[:72]}...")
        try:
            items = harvest_query(query, api_key)
        except Exception as exc:
            print(f"  [ERR] {exc}")
            continue
        new_count = 0
        for it in items:
            dpla_id = it.get("id") or it.get("_id")
            if dpla_id and dpla_id not in seen:
                it["_first_query"] = query
                it["_harvest_batch"] = "dpla_expanded_20260915"
                seen[dpla_id] = it
                new_count += 1
        print(f"  {len(items):>6} results  (+{new_count} new, {len(seen)} total unique)")

    with out.open("w", encoding="utf-8") as fh:
        for it in seen.values():
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")

    new_total = len(seen) - initial_count
    print(f"\n{'='*60}")
    print(f"  DPLA EXPANDED HARVEST COMPLETE")
    print(f"  queries run:          {len(QUERIES)}")
    print(f"  previously known:     {initial_count}")
    print(f"  newly discovered:     {new_total}")
    print(f"  total unique:         {len(seen)}")
    print(f"  ledger:               {out}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
