#!/usr/bin/env python3
"""
Master CDA Catalog Ledger Unifier & Deduplicator.
Combines DPLA, Internet Archive, and OpenAlex harvest ledgers into a single,
cleanly structured, deduplicated master catalog ledger.
"""

import sys
import os
import json
import hashlib
import time

RUN_DIR = os.path.expanduser("~/cda_archive_run")
OUTPUT_MASTER = os.path.join(RUN_DIR, "master_cda_catalog_ledger.jsonl")

SOURCES = [
    {"path": os.path.join(RUN_DIR, "dpla_catalog_ledger.jsonl"), "provider": "dpla"},
    {"path": os.path.join(RUN_DIR, "catalog_ledger_expanded.jsonl"), "provider": "internet_archive"},
    {"path": os.path.join(RUN_DIR, "catalog_ledger.jsonl"), "provider": "internet_archive"},
    {"path": os.path.join(RUN_DIR, "ia_regional_ledger.jsonl"), "provider": "internet_archive"},
    {"path": os.path.join(RUN_DIR, "openalex_catalog_ledger.jsonl"), "provider": "openalex"},
]

CDA_KEYWORDS = [
    "coeur d'alene", "schitsu'umsh", "spokane river", "st. joe", "cataldo",
    "bunker hill", "silver valley", "post falls", "rathdrum", "kootenai",
    "benewah", "shoshone", "pend oreille", "priest lake", "hayden lake",
    "allotment", "dawes", "treaty", "sovereignty", "submerged lands"
]


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] {msg}", flush=True)


def compute_relevance(text):
    if not text:
        return 10
    t_lower = text.lower()
    score = 10
    for kw in CDA_KEYWORDS:
        if kw in t_lower:
            score += 20
    return min(score, 100)


def normalize_record(raw, provider):
    if provider == "dpla":
        iid = raw.get("id")
        title = raw.get("title") or ""
        if isinstance(title, list):
            title = " / ".join(str(x) for x in title)
        creator = raw.get("creator") or []
        if isinstance(creator, str):
            creator = [creator]
        date_obj = raw.get("date") or {}
        date_str = ""
        if isinstance(date_obj, dict):
            date_str = str(date_obj.get("displayDate") or date_obj.get("begin") or "")
        elif isinstance(date_obj, str):
            date_str = date_obj
        desc = raw.get("description") or ""
        if isinstance(desc, list):
            desc = " ".join(str(x) for x in desc)
        subj = raw.get("subject") or []
        if isinstance(subj, list):
            subj_list = [s.get("name") if isinstance(s, dict) else str(s) for s in subj]
        else:
            subj_list = [str(subj)]
        url = raw.get("isShownAt") or f"https://dp.la/item/{iid}"

        return {
            "global_id": f"dpla:{iid}",
            "provider": "dpla",
            "provider_id": iid,
            "title": str(title).strip(),
            "creator": subj_list[:5],
            "date": date_str,
            "description": str(desc)[:1000].strip(),
            "subjects": subj_list[:10],
            "source_url": url,
            "cda_relevance": compute_relevance(f"{title} {desc} {' '.join(subj_list)}"),
        }

    elif provider == "internet_archive":
        ident = raw.get("identifier") or raw.get("id")
        title = raw.get("title") or ""
        creator = raw.get("creator") or ""
        desc = raw.get("description") or ""
        subj = raw.get("subject") or []
        if isinstance(subj, str):
            subj = [subj]
        date_str = str(raw.get("date") or raw.get("year") or "")
        url = f"https://archive.org/details/{ident}"

        return {
            "global_id": f"ia:{ident}",
            "provider": "internet_archive",
            "provider_id": ident,
            "title": str(title).strip(),
            "creator": [str(creator)] if creator else [],
            "date": date_str,
            "description": str(desc)[:1000].strip(),
            "subjects": [str(s) for s in subj][:10],
            "source_url": url,
            "cda_relevance": compute_relevance(f"{title} {desc} {' '.join(str(s) for s in subj)}"),
        }

    elif provider == "openalex":
        oid = raw.get("id")
        title = raw.get("title") or ""
        authors = [a.get("author_name") for a in raw.get("authorships", []) if a.get("author_name")]
        date_str = str(raw.get("publication_year") or raw.get("publication_date") or "")
        concepts = raw.get("concepts") or []
        doi = raw.get("doi")
        url = doi if doi else (raw.get("oa_url") or oid)

        return {
            "global_id": f"openalex:{oid.split('/')[-1] if oid else ''}",
            "provider": "openalex",
            "provider_id": oid,
            "title": str(title).strip(),
            "creator": authors[:5],
            "date": date_str,
            "description": f"Published in: {raw.get('host_venue')}. Type: {raw.get('type')}. Citations: {raw.get('cited_by_count')}",
            "subjects": concepts[:10],
            "source_url": url,
            "cda_relevance": compute_relevance(f"{title} {' '.join(concepts)}"),
        }

    return None


def main():
    seen_ids = set()
    seen_titles = set()
    total_in = 0
    total_out = 0
    provider_counts = {}

    log(f"Starting Master Catalog Unification -> {OUTPUT_MASTER}")

    with open(OUTPUT_MASTER, "w", encoding="utf-8") as out_f:
        for src in SOURCES:
            path = src["path"]
            provider = src["provider"]
            if not os.path.exists(path):
                log(f"Skipping absent ledger: {path}")
                continue

            log(f"Processing {provider} ledger: {path}...")
            count = 0
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    total_in += 1
                    count += 1
                    try:
                        raw = json.loads(line)
                        norm = normalize_record(raw, provider)
                        if not norm:
                            continue

                        gid = norm["global_id"]
                        if gid in seen_ids:
                            continue

                        # Deduplicate by normalized title hash if same year
                        title_clean = "".join(c for c in norm["title"].lower() if c.isalnum())
                        if title_clean and len(title_clean) > 15:
                            thash = f"{title_clean[:60]}_{norm['date'][:4]}"
                            if thash in seen_titles:
                                continue
                            seen_titles.add(thash)

                        seen_ids.add(gid)
                        out_f.write(json.dumps(norm, ensure_ascii=False) + "\n")
                        total_out += 1
                        provider_counts[provider] = provider_counts.get(provider, 0) + 1

                    except Exception:
                        pass

            log(f"    Read {count} records from {os.path.basename(path)}")

    log("=" * 60)
    log("MASTER CDA CATALOG UNIFICATION COMPLETE")
    log(f"Total records processed: {total_in}")
    log(f"Total unique master records: {total_out}")
    for p, c in provider_counts.items():
        log(f"  - {p}: {c:,} records")
    log(f"Master ledger: {OUTPUT_MASTER}")
    log("=" * 60)


if __name__ == "__main__":
    main()
