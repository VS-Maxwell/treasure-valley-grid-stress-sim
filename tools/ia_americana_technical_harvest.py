#!/usr/bin/env python3
"""
Internet Archive Americana & Technical Harvester for CDA U&A Territory.
Harvests historical monographs from the Americana collection, USGS bulletins,
Bureau of Mines metallurgical reports, and water-supply papers.
Deduplicates against all prior IA ledgers and appends to ia_regional_ledger.jsonl.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error

PRIOR_LEDGERS = [
    os.path.expanduser("~/cda_archive_run/catalog_ledger_expanded.jsonl"),
    os.path.expanduser("~/cda_archive_run/catalog_ledger.jsonl"),
]
OUTPUT_LEDGER = os.path.expanduser("~/cda_archive_run/ia_regional_ledger.jsonl")

QUERIES = [
    ('collection:americana AND (Idaho OR Spokane OR "Coeur d\'Alene")', 'Americana Idaho/Spokane'),
    ('collection:americana AND ("Pacific Northwest" OR "Columbia River")', 'Americana PNW/Columbia'),
    ('subject:"Mines and mineral resources" AND (Idaho OR "Coeur d\'Alene" OR Shoshone)', 'Mines & Minerals ID'),
    ('subject:"Water-supply" AND (Idaho OR Washington OR Spokane)', 'Water Supply ID/WA'),
    ('creator:"Geological Survey (U.S.)" AND (Idaho OR Shoshone OR Kootenai OR "Coeur d\'Alene")', 'USGS Panhandle'),
    ('creator:"United States. Bureau of Mines" AND (Idaho OR "Coeur d\'Alene" OR "Silver Valley")', 'USBM Silver Valley'),
    ('subject:"Northwest, Pacific -- History"', 'PNW History'),
    ('subject:"Idaho -- History"', 'Idaho History'),
    ('subject:"Indians of North America -- Idaho"', 'Tribal History Idaho'),
    ('subject:"Indians of North America -- Washington (State)"', 'Tribal History Washington'),
]


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def load_all_known_ia_ids():
    known = set()
    for path in PRIOR_LEDGERS + [OUTPUT_LEDGER]:
        if not os.path.exists(path):
            continue
        log(f"Reading ledger {path}...")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    iid = rec.get("identifier") or rec.get("id")
                    if iid:
                        known.add(iid)
                except Exception:
                    pass
    log(f"Total known IA identifiers across all ledgers: {len(known)}")
    return known


def harvest_ia_query(query, label, known_ids, out_f):
    fields = "identifier,title,creator,date,year,description,subject,mediatype,collection,downloads"
    cursor = None
    query_new = 0
    page_count = 0

    while True:
        params = {
            "q": query,
            "fields": fields,
            "count": 1000,
        }
        if cursor:
            params["cursor"] = cursor

        url = f"https://archive.org/services/search/v1/scrape?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "CDA-Sovereign-Harvester/2.0"})

        data = None
        backoff = 2
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    break
            except urllib.error.HTTPError as he:
                log(f"    HTTP {he.code} on {label} (attempt {attempt+1}/6): {he}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
            except Exception as e:
                log(f"    Network error on {label}: {e}, waiting {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
        else:
            log(f"    Failed page after 6 attempts for {label}, skipping remaining.")
            break

        items = data.get("items", [])
        if not items:
            break

        for it in items:
            ident = it.get("identifier")
            if not ident or ident in known_ids:
                continue

            known_ids.add(ident)
            query_new += 1

            record = {
                "identifier": ident,
                "provider": "internet_archive",
                "title": it.get("title", ""),
                "creator": it.get("creator", ""),
                "date": it.get("date", ""),
                "year": it.get("year", ""),
                "description": it.get("description", ""),
                "subject": it.get("subject", []),
                "mediatype": it.get("mediatype", ""),
                "collection": it.get("collection", []),
                "downloads": it.get("downloads", 0),
                "query_matched": label,
                "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

        out_f.flush()
        page_count += 1

        cursor = data.get("cursor")
        if not cursor:
            break

        time.sleep(0.4)

    return query_new, page_count


def main():
    os.makedirs(os.path.dirname(OUTPUT_LEDGER), exist_ok=True)
    known_ids = load_all_known_ia_ids()
    start_count = len(known_ids)

    log(f"Starting IA Americana & Technical Harvest ({len(QUERIES)} queries)...")
    total_new = 0

    with open(OUTPUT_LEDGER, "a", encoding="utf-8") as out_f:
        for idx, (q, label) in enumerate(QUERIES, 1):
            log(f"[{idx}/{len(QUERIES)}] Harvesting {label} ('{q}')...")
            q_new, pages = harvest_ia_query(q, label, known_ids, out_f)
            total_new += q_new
            log(f"    +{q_new} new records ({pages} pages, {len(known_ids)} total unique IA IDs)")
            time.sleep(1.0)

    log("=" * 60)
    log("  IA AMERICANA & TECHNICAL HARVEST COMPLETE")
    log(f"  queries run:          {len(QUERIES)}")
    log(f"  previously known:     {start_count}")
    log(f"  newly added:          {total_new}")
    log(f"  total unique IA IDs:  {len(known_ids)}")
    log(f"  ledger:               {OUTPUT_LEDGER}")
    log("=" * 60)


if __name__ == "__main__":
    main()
