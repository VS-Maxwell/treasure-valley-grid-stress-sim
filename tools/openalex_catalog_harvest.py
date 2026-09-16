#!/usr/bin/env python3
"""
OpenAlex Academic & Scientific Literature Harvester for CDA U&A Territory.
Harvests peer-reviewed journals, USGS water resources papers, legal reviews,
tribal sovereignty scholarship, environmental impact statements, and forestry studies.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error

LEDGER_PATH = os.path.expanduser("~/cda_archive_run/openalex_catalog_ledger.jsonl")
LOG_PATH = os.path.expanduser("~/cda_archive_run/harvest_openalex.log")

USER_AGENT = "mailto:archival@cda-sovereign.org (CDA-Sovereign-Harvester/2.0)"

QUERIES = [
    # Coeur d'Alene Core
    "Coeur d'Alene",
    "Lake Coeur d'Alene",
    "Coeur d'Alene River",
    "Coeur d'Alene Tribe",
    "Coeur d'Alene Reservation",
    "Schitsu'umsh",
    "Cataldo Mission",

    # Mining, Geology, Heavy Metals & Contamination (Silver Valley)
    "Silver Valley Idaho",
    "Bunker Hill Superfund",
    "Bunker Hill mining Idaho",
    "Coeur d'Alene mining district",
    "heavy metals Lake Coeur d'Alene",
    "sediment contamination Coeur d'Alene",
    "zinc cadmium lead Lake Coeur d'Alene",
    "Sunshine Mine Idaho",
    "Hecla Mining Idaho",
    "acid mine drainage Idaho Panhandle",

    # Hydrology, Limnology & Hydrodynamics
    "Spokane River Basin",
    "St. Joe River Idaho",
    "St. Maries River Idaho",
    "Lake Coeur d'Alene limnology",
    "Lake Coeur d'Alene phosphorus",
    "Lake Coeur d'Alene dissolved oxygen",
    "Post Falls Dam",
    "Spokane Valley Rathdrum Prairie Aquifer",
    "Pend Oreille River hydrology",
    "Columbia River Basin salmon treaty",

    # Forestry & Ecology
    "Idaho Panhandle National Forests",
    "Coeur d'Alene National Forest",
    "St. Joe National Forest",
    "Kaniksu National Forest",
    "white pine blister rust Idaho",
    "wildfire recovery Inland Northwest",
    "Inland Empire forestry",

    # Tribal Sovereignty, Water Rights & Economics
    "Coeur d'Alene Tribe water rights",
    "Idaho v. Coeur d'Alene Tribe",
    "submerged lands tribal sovereignty",
    "winter doctrine Idaho tribes",
    "tribal land valuation",
    "Indian Claims Commission Coeur d'Alene",
    "Dawes Act allotments Idaho",
    "treaty usual and accustomed Northwest tribes",
    "tribal natural resource economics",
    "Columbia River inter-tribal",

    # Regional Inland Northwest
    "Kootenai County history",
    "Shoshone County history",
    "Benewah County history",
    "Upper Columbia United Tribes",
    "Inland Northwest indigenous agriculture",
    "camas harvest Inland Northwest",
]


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line, flush=True)


def load_known_ids(ledger_path):
    known = set()
    if not os.path.exists(ledger_path):
        return known
    with open(ledger_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                rec = json.loads(line)
                iid = rec.get("id") or rec.get("openalex_id")
                if iid:
                    known.add(iid)
            except Exception:
                pass
    return known


def harvest_query(query, known_ids, out_f):
    encoded_q = urllib.parse.quote(f'"{query}"')
    cursor = "*"
    page_count = 0
    query_new = 0

    while cursor:
        url = f"https://api.openalex.org/works?search={encoded_q}&per-page=100&cursor={cursor}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        # Retry loop for rate limits / network hiccups
        backoff = 2
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    break
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    log(f"    [429] Rate limited on query '{query}', backoff {backoff}s (attempt {attempt+1}/6)")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                else:
                    log(f"    HTTP {he.code} on query '{query}': {he}")
                    time.sleep(2)
            except Exception as e:
                log(f"    Network error on query '{query}': {e}, waiting {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
        else:
            log(f"    Failed page after 6 attempts for query '{query}', skipping remaining pages.")
            break

        results = data.get("results", [])
        if not results:
            break

        for item in results:
            item_id = item.get("id")
            if not item_id or item_id in known_ids:
                continue

            known_ids.add(item_id)
            query_new += 1

            record = {
                "id": item_id,
                "provider": "openalex",
                "doi": item.get("doi"),
                "title": item.get("title"),
                "publication_year": item.get("publication_year"),
                "publication_date": item.get("publication_date"),
                "type": item.get("type"),
                "authorships": [
                    {
                        "author_name": a.get("author", {}).get("display_name"),
                        "institution": (a.get("institutions", [{}])[0].get("display_name") if a.get("institutions") else None),
                    }
                    for a in item.get("authorships", [])
                ],
                "host_venue": (item.get("primary_location", {}) or {}).get("source", {}).get("display_name"),
                "is_oa": item.get("open_access", {}).get("is_oa"),
                "oa_url": item.get("open_access", {}).get("oa_url"),
                "cited_by_count": item.get("cited_by_count", 0),
                "concepts": [c.get("display_name") for c in item.get("concepts", [])],
                "query_matched": query,
                "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

        out_f.flush()
        page_count += 1

        next_cursor = data.get("meta", {}).get("next_cursor")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor

        # Politeness rate limiting (OpenAlex max 10/s)
        time.sleep(0.15)

    return query_new, page_count


def main():
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    known_ids = load_known_ids(LEDGER_PATH)
    start_known = len(known_ids)
    log(f"Starting OpenAlex CDA U&A Harvest. Already indexed: {start_known} works.")

    total_new = 0
    with open(LEDGER_PATH, "a", encoding="utf-8") as out_f:
        for idx, q in enumerate(QUERIES, 1):
            log(f"[{idx}/{len(QUERIES)}] Query: '{q}'...")
            q_new, pages = harvest_query(q, known_ids, out_f)
            total_new += q_new
            log(f"    Done: +{q_new} new records ({pages} pages, {len(known_ids)} total unique)")
            time.sleep(1.0)

    log("=" * 60)
    log(f"OPENALEX HARVEST COMPLETE")
    log(f"Queries: {len(QUERIES)}")
    log(f"Previously known: {start_known}")
    log(f"Newly added: {total_new}")
    log(f"Total unique: {len(known_ids)}")
    log(f"Ledger: {LEDGER_PATH}")
    log("=" * 60)


if __name__ == "__main__":
    main()
