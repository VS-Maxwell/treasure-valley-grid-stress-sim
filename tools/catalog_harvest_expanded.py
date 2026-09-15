#!/usr/bin/env python3
"""Expanded CDA catalog harvester — covers all U&A economic, environmental, and
infrastructure domains that the original 9-query set missed.

Adds: land use, land valuation, urban planning, socioeconomics, energy
infrastructure, environmental remediation, water rights, census/demographics,
Esri-relevant GIS data, and cost-offset analysis sources.

Uses the same IA Scraping API (cursor-based) as catalog_harvest.py so it can
run alongside it. Output appends to the same catalog_ledger.jsonl format.

Copyright (c) 2026 LAS Consulting & V.S. Maxwell-Miller
SPDX-License-Identifier: Apache-2.0 OR MIT
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "SovereignArchivalStandard/1.0 (CDA estate preservation)"
SCRAPE = "https://archive.org/services/search/v1/scrape"

# ---------------------------------------------------------------------------
# EXPANDED QUERY SET — domains that the original harvest missed
# ---------------------------------------------------------------------------
QUERIES = [
    # === LAND USE & LAND EVALUATION ===
    '"land use" AND (Idaho OR "Coeur d\'Alene" OR "Treasure Valley" OR Boise)',
    '"land evaluation" AND (Idaho OR Oregon OR Washington)',
    '"land cover" AND (Idaho OR "Pacific Northwest")',
    'subject:("land use planning" OR "zoning") AND Idaho',
    '"comprehensive plan" AND (Idaho OR "Kootenai County" OR "Benewah")',

    # === LAND VALUATION & COST OFFSET (Master's thesis) ===
    '"land value" AND (Idaho OR "Pacific Northwest")',
    '"property tax" AND (Idaho OR "Coeur d\'Alene" OR Boise)',
    '"real estate" AND (Idaho OR "Treasure Valley")',
    '"fair market value" AND (Idaho OR reservation OR "Indian lands")',
    '"cost offset" AND (tribal OR reservation OR "Indian")',
    '"just compensation" AND ("Indian" OR tribal OR treaty)',
    '"eminent domain" AND (Idaho OR Washington OR Oregon)',
    'subject:("Indian Claims Commission" OR "Indian Claims")',
    '"land appraisal" AND (Idaho OR Washington OR Oregon)',

    # === URBAN PLANNING / ESRI-RELEVANT GIS ===
    '"urban planning" AND (Idaho OR Boise OR "Coeur d\'Alene" OR Spokane)',
    '"urban development" AND (Idaho OR "Pacific Northwest")',
    '"city planning" AND (Idaho OR Boise OR "Treasure Valley")',
    'subject:("urban renewal" OR "urban development") AND (Idaho OR Washington)',
    '"geographic information systems" AND (Idaho OR "Pacific Northwest")',
    '"GIS" AND (Idaho OR "land use" OR "water resources")',

    # === SOCIOECONOMICS & DEMOGRAPHICS ===
    '"socioeconomic" AND (Idaho OR "Coeur d\'Alene" OR "Nez Perce")',
    '"economic development" AND (Idaho OR tribal OR reservation)',
    '"census" AND Idaho AND (population OR housing OR income)',
    '"cost of living" AND (Idaho OR Boise OR "Coeur d\'Alene")',
    '"economic impact" AND (Idaho OR dam OR hydroelectric OR salmon)',
    '"poverty" AND (Idaho OR reservation OR tribal)',
    '"employment" AND (Idaho OR "Pacific Northwest") AND (timber OR mining OR agriculture)',

    # === ENERGY INFRASTRUCTURE ===
    '"hydroelectric" AND (Idaho OR "Snake River" OR "Columbia River")',
    '"Bonneville Power Administration" OR "BPA" AND (Idaho OR transmission)',
    '"Idaho Power" OR "Avista" OR "Pacific Power"',
    '"energy" AND ("Coeur d\'Alene" OR "Treasure Valley" OR Boise)',
    '"power plant" AND (Idaho OR "Snake River" OR "Columbia Basin")',
    '"dam" AND (Idaho OR "Snake River" OR "Clearwater" OR "Salmon River")',
    '"transmission line" AND (Idaho OR "Pacific Northwest")',
    '"renewable energy" AND (Idaho OR "Pacific Northwest")',

    # === ENVIRONMENTAL / WATER / SALMON ===
    '"water rights" AND (Idaho OR "Snake River" OR "Coeur d\'Alene")',
    '"water quality" AND (Idaho OR "Coeur d\'Alene" OR "Silver Valley")',
    '"Superfund" AND ("Coeur d\'Alene" OR "Bunker Hill" OR "Silver Valley")',
    '"salmon" AND (Idaho OR "Snake River" OR "Columbia" OR "Clearwater")',
    '"endangered species" AND (Idaho OR salmon OR steelhead OR bull_trout)',
    '"irrigation" AND (Idaho OR "Boise Project" OR "Minidoka")',
    '"Bureau of Reclamation" AND Idaho',
    '"Army Corps of Engineers" AND (Idaho OR "Snake River" OR "Columbia")',
    '"flood control" AND (Idaho OR "Boise River" OR "Snake River")',
    '"Clean Water Act" AND (Idaho OR "Coeur d\'Alene")',

    # === TREATY & SOVEREIGNTY (expanded) ===
    '"Stevens Treaty" OR "Isaac Stevens" AND (Idaho OR Washington)',
    '"Hellgate Treaty" OR "Treaty of Hellgate"',
    '"Executive Order Reservation" AND (Idaho OR "Coeur d\'Alene")',
    '"allotment" AND ("Coeur d\'Alene" OR "Nez Perce" OR Idaho)',
    '"General Allotment Act" OR "Dawes Act" AND Idaho',
    '"Indian Reorganization Act" AND Idaho',
    '"tribal sovereignty" AND (Idaho OR "Pacific Northwest")',
    '"fishing rights" AND (Idaho OR Washington OR Oregon OR "Columbia River")',
    '"hunting rights" AND (Idaho OR "Coeur d\'Alene" OR "Nez Perce")',
    '"water compact" AND (Idaho OR "Coeur d\'Alene" OR "Nez Perce")',
    '"Winters doctrine" OR "reserved water rights" AND Idaho',

    # === AGRICULTURE & TIMBER (economic value of ceded lands) ===
    '"agriculture" AND (Idaho OR "Palouse" OR "Camas Prairie" OR "Treasure Valley")',
    '"timber" AND (Idaho OR "Coeur d\'Alene" OR "St. Joe" OR "Clearwater")',
    '"mining" AND (Idaho OR "Coeur d\'Alene" OR "Silver Valley" OR "Bunker Hill")',
    '"grazing" AND (Idaho OR "Bureau of Land Management")',

    # === INFRASTRUCTURE & IMPROVEMENTS (value since cession) ===
    '"highway" AND (Idaho OR "Interstate 90" OR "Interstate 84" OR "US-95")',
    '"railroad" AND (Idaho OR "Northern Pacific" OR "Union Pacific" OR "Milwaukee Road")',
    '"Coeur d\'Alene Lake" OR "Lake Coeur d\'Alene"',
    '"Spokane River" AND (Idaho OR Washington)',
    '"St. Joe River" OR "Saint Joe River"',

    # === BROAD PNW CATCH-ALL (things that may have slipped) ===
    'collection:americana AND Idaho',
    'collection:usfederalcourts AND Idaho',
    'collection:usgovernmentdocuments AND Idaho',
    'collection:biodiversity AND Idaho',
    '"Idaho Territory" OR "Washington Territory" AND treaty',
    '"Pacific Northwest" AND ("land claim" OR "aboriginal" OR "ceded")',
]


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


def scrape_query(query: str) -> list[dict]:
    """Return all items for a query via cursor paging."""
    items: list[dict] = []
    cursor = None
    fields = "identifier,title,year,mediatype,format,subject,creator,description"
    while True:
        params = {"q": query, "fields": fields, "count": "1000"}
        if cursor:
            params["cursor"] = cursor
        data = http_json(f"{SCRAPE}?{urllib.parse.urlencode(params)}")
        items.extend(data.get("items", []))
        cursor = data.get("cursor")
        if not cursor:
            break
        time.sleep(0.4)  # politeness
    return items


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("catalog_ledger_expanded.jsonl")
    
    # Load existing identifiers to avoid duplicates with the original harvest
    existing_ledger = out.parent / "catalog_ledger.jsonl"
    seen: dict[str, dict] = {}
    if existing_ledger.exists():
        with existing_ledger.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    it = json.loads(line)
                    ident = it.get("identifier")
                    if ident:
                        seen[ident] = it
                except json.JSONDecodeError:
                    pass
        print(f"Loaded {len(seen)} existing identifiers from {existing_ledger}")
    
    initial_count = len(seen)
    per_query: dict[str, int] = {}

    for i, query in enumerate(QUERIES, 1):
        print(f"\n[{i}/{len(QUERIES)}] {query[:72]}...")
        try:
            items = scrape_query(query)
        except Exception as exc:
            print(f"  [ERR] {exc}")
            continue
        new_count = 0
        for it in items:
            ident = it.get("identifier")
            if ident and ident not in seen:
                it["_first_query"] = query
                it["_harvest_batch"] = "expanded_20260915"
                seen[ident] = it
                new_count += 1
        per_query[query] = len(items)
        print(f"  {len(items):>6} results  (+{new_count} new, {len(seen)} total unique)")

    # Write expanded ledger
    with out.open("w", encoding="utf-8") as fh:
        for it in seen.values():
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")

    new_total = len(seen) - initial_count
    texts = sum(1 for it in seen.values() if it.get("mediatype") == "texts")
    
    print(f"\n{'='*60}")
    print(f"  EXPANDED HARVEST COMPLETE")
    print(f"  queries run:          {len(QUERIES)}")
    print(f"  previously known:     {initial_count}")
    print(f"  newly discovered:     {new_total}")
    print(f"  total unique:         {len(seen)}")
    print(f"  mediatype=texts:      {texts}")
    print(f"  ledger:               {out}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
