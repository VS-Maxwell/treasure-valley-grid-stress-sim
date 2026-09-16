#!/usr/bin/env python3
"""
Library of Congress (LOC) Catalog Harvester for CDA U&A Territory.
Uses LBOC_API_KEY to harvest historic maps, photographs, manuscripts,
township survey plats, and newspapers from the Library of Congress.
Deduplicates and appends to loc_catalog_ledger.jsonl.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error

ENV_PATHS = [
    os.path.expanduser("~/.config/cda-recovery-studio/archive_api_keys.env"),
    os.path.expanduser("~/Downloads/archive_api_keys.env"),
]
LEDGER_PATH = os.path.expanduser("~/cda_archive_run/loc_catalog_ledger.jsonl")

QUERIES = [
    # Coeur d'Alene Core & Territory
    "Coeur d'Alene",
    "Lake Coeur d'Alene",
    "Coeur d'Alene Tribe",
    "Coeur d'Alene Reservation",
    "Cataldo Mission",
    "St. Joe River Idaho",
    "Spokane River",
    "Kootenai County Idaho",
    "Shoshone County Idaho",
    "Benewah County Idaho",

    # Mining & Sanborn Maps
    "Bunker Hill mine",
    "Silver Valley Idaho",
    "Wallace Idaho",
    "Kellogg Idaho",
    "Wardner Idaho",
    "Mullan Idaho",
    "Coeur d'Alene mining",

    # Regional Treaties & Sovereignty
    "Coeur d'Alene Indian",
    "Salish Indians",
    "Kootenai Indians",
    "Spokane Indians",
    "Kalispel Indians",
    "Upper Columbia tribes",
    "Idaho Indian reservation",
    "Stevens treaties Northwest",
    "Idaho General Land Office survey",

    # Hydrology & Waterways
    "Post Falls Idaho",
    "Pend Oreille Lake",
    "Priest Lake Idaho",
    "Clark Fork River",
    "Spokane Valley Rathdrum",
]


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def get_api_key():
    for p in ENV_PATHS:
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    if line.startswith("LBOC_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip("'\"")
                        if val:
                            return val
    env_val = os.environ.get("LBOC_API_KEY")
    if env_val:
        return env_val
    return "ubMur0FTkljfVOlcWzlV7d7hq8yP7u4ir7BfvtQP"


def load_known_ids(path):
    known = set()
    if not os.path.exists(path):
        return known
    log(f"Reading existing ledger {path}...")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                rec = json.loads(line)
                iid = rec.get("id") or rec.get("loc_id") or rec.get("url")
                if iid:
                    known.add(iid)
            except Exception:
                pass
    log(f"Loaded {len(known)} existing IDs from ledger.")
    return known


def harvest_loc_query(query, api_key, known_ids, out_f):
    encoded_q = urllib.parse.quote(query)
    page_size = 100
    page = 1
    query_new = 0
    total_found = 0

    while page <= 100:  # Cap at 100 pages (10,000 items per query)
        url = f"https://www.loc.gov/search/?q={encoded_q}&fo=json&c={page_size}&sp={page}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "CDA-Sovereign-Harvester/2.0",
            "X-Api-Key": api_key
        })

        data = None
        backoff = 3
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    break
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    log(f"    [429] Rate limited on '{query}', backoff {backoff}s (attempt {attempt+1}/6)")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                else:
                    log(f"    HTTP {he.code} on page {page} of '{query}': {he}")
                    time.sleep(3)
            except Exception as e:
                log(f"    Network error on page {page} of '{query}': {e}, waiting {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
        else:
            log(f"    Failed page {page} after 6 attempts for query '{query}', skipping remaining.")
            break

        results = data.get("results", [])
        total_found = data.get("pagination", {}).get("total", 0)
        if not results:
            break

        for item in results:
            item_url = item.get("id") or item.get("url") or item.get("shelf_id")
            if not item_url or item_url in known_ids:
                continue

            known_ids.add(item_url)
            query_new += 1

            record = {
                "id": f"loc:{item.get('id', item_url)}",
                "provider": "loc",
                "title": item.get("title", ""),
                "creator": item.get("contributor", []) or item.get("creator", []),
                "date": str(item.get("date", "")),
                "description": item.get("description", []) or item.get("notes", []),
                "subject": item.get("subject", []),
                "type": item.get("original_format", []) or [item.get("type", "")],
                "source_url": item_url,
                "location": item.get("location", []),
                "shelf_id": item.get("shelf_id", ""),
                "query_matched": query,
                "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

        out_f.flush()

        if len(results) < page_size or (page * page_size) >= total_found:
            break

        page += 1
        time.sleep(0.4)  # Respectful LOC pacing

    return query_new, total_found


def main():
    api_key = get_api_key()
    known_ids = load_known_ids(LEDGER_PATH)
    start_count = len(known_ids)

    log(f"Starting Library of Congress Harvest ({len(QUERIES)} queries)...")
    total_new = 0

    with open(LEDGER_PATH, "a", encoding="utf-8") as out_f:
        for idx, q in enumerate(QUERIES, 1):
            log(f"[{idx}/{len(QUERIES)}] LOC Query: '{q}'...")
            q_new, total_hits = harvest_loc_query(q, api_key, known_ids, out_f)
            total_new += q_new
            log(f"    {total_hits} total found (+{q_new} net-new, {len(known_ids)} total unique in LOC ledger)")
            time.sleep(1.5)  # Inter-query delay

    log("=" * 60)
    log("  LIBRARY OF CONGRESS HARVEST COMPLETE")
    log(f"  queries run:          {len(QUERIES)}")
    log(f"  previously known:     {start_count}")
    log(f"  newly added:          {total_new}")
    log(f"  total unique:         {len(known_ids)}")
    log(f"  ledger:               {LEDGER_PATH}")
    log("=" * 60)


if __name__ == "__main__":
    main()
