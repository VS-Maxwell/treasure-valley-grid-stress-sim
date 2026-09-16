#!/usr/bin/env python3
"""
DPLA Wave 3 Institutional Harvester for CDA U&A Territory.
Targets University of Washington, Washington State University, Smithsonian,
NARA, and Eastern Washington University regional archives using date-banded shards.
Deduplicates against existing dpla_catalog_ledger.jsonl and appends new records.
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
LEDGER_PATH = os.path.expanduser("~/cda_archive_run/dpla_catalog_ledger.jsonl")

# Institutional queries with date-band sharding to avoid DPLA page 100 deep-pagination cap
SHARDS = [
    # Washington State University (Inland Northwest & Palouse/Panhandle core)
    {"provider": "Washington State University", "params": "&sourceResource.date.before=1900", "label": "WSU pre-1900"},
    {"provider": "Washington State University", "params": "&sourceResource.date.after=1899&sourceResource.date.before=1921", "label": "WSU 1900-1920"},
    {"provider": "Washington State University", "params": "&sourceResource.date.after=1920&sourceResource.date.before=1941", "label": "WSU 1921-1940"},
    {"provider": "Washington State University", "params": "&sourceResource.date.after=1940&sourceResource.date.before=1961", "label": "WSU 1941-1960"},
    {"provider": "Washington State University", "params": "&sourceResource.date.after=1960&sourceResource.date.before=1981", "label": "WSU 1961-1980"},
    {"provider": "Washington State University", "params": "&sourceResource.date.after=1980&sourceResource.date.before=2001", "label": "WSU 1981-2000"},
    {"provider": "Washington State University", "params": "&sourceResource.date.after=2000", "label": "WSU post-2000"},

    # University of Washington (Pacific Northwest Collection)
    {"provider": "University of Washington", "params": "&sourceResource.date.before=1900", "label": "UW pre-1900"},
    {"provider": "University of Washington", "params": "&sourceResource.date.after=1899&sourceResource.date.before=1921", "label": "UW 1900-1920"},
    {"provider": "University of Washington", "params": "&sourceResource.date.after=1920&sourceResource.date.before=1941", "label": "UW 1921-1940"},
    {"provider": "University of Washington", "params": "&sourceResource.date.after=1940&sourceResource.date.before=1961", "label": "UW 1941-1960"},
    {"provider": "University of Washington", "params": "&sourceResource.date.after=1960&sourceResource.date.before=1981", "label": "UW 1961-1980"},
    {"provider": "University of Washington", "params": "&sourceResource.date.after=1980&sourceResource.date.before=2001", "label": "UW 1981-2000"},
    {"provider": "University of Washington", "params": "&sourceResource.date.after=2000", "label": "UW post-2000"},

    # Eastern Washington University (Spokane & Upper Columbia)
    {"provider": "Eastern Washington University", "params": "", "label": "EWU Regional Collection"},

    # Smithsonian Institution (Pacific Northwest & Tribal Collections)
    {"provider": "Smithsonian Institution", "params": "&q=Idaho+OR+Washington+OR+Columbia+OR+Spokane+OR+Salish+OR+%22Coeur+d%27Alene%22", "label": "Smithsonian PNW & Tribal"},

    # National Archives and Records Administration (via DPLA)
    {"provider": "National Archives and Records Administration", "params": "&q=Idaho+OR+Washington+OR+Columbia+OR+Spokane+OR+%22Coeur+d%27Alene%22", "label": "NARA PNW Regional"},
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
                    if line.startswith("DPLA_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip("'\"")
                        if val:
                            return val
    env_val = os.environ.get("DPLA_API_KEY")
    if env_val:
        return env_val
    raise RuntimeError("DPLA_API_KEY not found in env paths or environment.")


def load_known_ids(path):
    known = set()
    if not os.path.exists(path):
        return known
    log(f"Reading existing ledger {path} to load known IDs...")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                rec = json.loads(line)
                iid = rec.get("id") or rec.get("dpla_id")
                if iid:
                    known.add(iid)
            except Exception:
                pass
    log(f"Loaded {len(known)} existing IDs from ledger.")
    return known


def harvest_shard(shard, api_key, known_ids, out_f):
    provider_enc = urllib.parse.quote(shard["provider"])
    label = shard["label"]
    extra_params = shard["params"]
    page_size = 500
    page = 1
    query_new = 0
    total_found = 0

    while page <= 100:
        url = f"https://api.dp.la/v2/items?dataProvider={provider_enc}{extra_params}&api_key={api_key}&page_size={page_size}&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": "CDA-Sovereign-Harvester/2.0"})

        data = None
        backoff = 10
        for attempt in range(8):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    break
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    jitter = (attempt * 3) % 7
                    wait_s = backoff + jitter
                    log(f"    [429] Rate limited on {label}, backing off {wait_s}s (attempt {attempt+1}/8)")
                    time.sleep(wait_s)
                    backoff = min(backoff * 2, 300)
                else:
                    log(f"    HTTP {he.code} on page {page} of {label}: {he}")
                    time.sleep(3)
            except Exception as e:
                log(f"    Network error on page {page} of {label}: {e}, waiting {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
        else:
            log(f"    Failed page {page} after 8 attempts, skipping remainder of {label}.")
            break

        docs = data.get("docs", [])
        total_found = data.get("count", 0)
        if not docs:
            break

        for d in docs:
            iid = d.get("id")
            if not iid or iid in known_ids:
                continue

            known_ids.add(iid)
            query_new += 1

            rec = {
                "id": iid,
                "provider": "dpla",
                "title": (d.get("sourceResource", {}).get("title") or ""),
                "creator": (d.get("sourceResource", {}).get("creator") or []),
                "date": (d.get("sourceResource", {}).get("date") or {}),
                "description": (d.get("sourceResource", {}).get("description") or ""),
                "subject": (d.get("sourceResource", {}).get("subject") or []),
                "type": (d.get("sourceResource", {}).get("type") or ""),
                "format": (d.get("sourceResource", {}).get("format") or ""),
                "spatial": (d.get("sourceResource", {}).get("spatial") or []),
                "dataProvider": (d.get("dataProvider") or ""),
                "isShownAt": (d.get("isShownAt") or ""),
                "query_matched": label,
                "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        out_f.flush()

        if len(docs) < page_size or (page * page_size) >= total_found:
            break

        page += 1
        time.sleep(0.5)

    return query_new, total_found


def main():
    api_key = get_api_key()
    known_ids = load_known_ids(LEDGER_PATH)
    start_count = len(known_ids)

    log(f"Starting DPLA Wave 3 Institutional Harvest ({len(SHARDS)} shards)...")
    total_new = 0

    with open(LEDGER_PATH, "a", encoding="utf-8") as out_f:
        for idx, shard in enumerate(SHARDS, 1):
            log(f"[{idx}/{len(SHARDS)}] Harvesting {shard['label']}...")
            q_new, total_hits = harvest_shard(shard, api_key, known_ids, out_f)
            total_new += q_new
            log(f"    {total_hits} total hits  (+{q_new} net-new, {len(known_ids)} total unique in ledger)")
            time.sleep(5.0)  # Inter-shard cooldown

    log("=" * 60)
    log("  DPLA WAVE 3 HARVEST COMPLETE")
    log(f"  shards run:           {len(SHARDS)}")
    log(f"  previously known:     {start_count}")
    log(f"  newly discovered:     {total_new}")
    log(f"  total unique:         {len(known_ids)}")
    log(f"  ledger:               {LEDGER_PATH}")
    log("=" * 60)


if __name__ == "__main__":
    main()
