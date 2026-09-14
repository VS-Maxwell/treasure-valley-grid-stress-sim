# Antigravity bounded handoff: connected dams and regional energy inventory

Updated: 2026-09-14

## Purpose

Support the active Treasure Valley simulator build without editing the live renderer branch. Produce a source-preserving, reviewable data bundle for dams that hydrologically feed the region and the energy projects connected to the regional grid.

## Isolation rule

- Read the primary checkout at `/run/media/madame-butterfly/Toshiba/Treasure_Valley_Model/github_treasure_valley_sim`.
- Do not modify `codex/visible-master-build` or its working tree.
- Work in a separate Git worktree on branch `antigravity/dam-energy-evidence`.
- Write large original data only beneath `/run/media/madame-butterfly/Toshiba/Treasure_Valley_Model/data/raw/antigravity/`.
- Do not read, print, copy, or commit API keys. This task must use public government sources that do not require credentials.

## Read first

1. `AGENTS.md`
2. `docs/MASTER_BUILD_PLAN.md`
3. `docs/BUILD_STATUS.md`
4. `DATA_SOURCES.csv`
5. `RESTRICTED_DATA_POLICY.md`
6. `receipts/usgs-3dep-terrain-20260914.json`

## Bounded task A: dam and watershed topology

1. Acquire the current public National Inventory of Dams features from the official USACE FeatureServer. Preserve the unmodified GeoJSON response, request URL and retrieval time.
2. Acquire an official USGS hydrography/catchment source sufficient to establish directed upstream connectivity into the Treasure Valley water-supply system. Preserve original bytes and provider metadata.
3. Define the target receiving system explicitly. Do not equate "inside a rectangle" with "feeds the region."
4. Classify every candidate dam as one of:
   - upstream supply-connected;
   - in-valley control/storage;
   - downstream/backwater-connected;
   - nearby but not hydrologically connected;
   - unresolved.
5. Retain the graph path or catchment evidence supporting every non-unresolved classification.
6. Include dam purpose, storage, operational status, hazard potential and location when those fields are public. Do not represent the NID as real-time emergency information.

Primary dam endpoint:

`https://geospatial.sec.usace.army.mil/dls/rest/services/NID/National_Inventory_of_Dams_Public_Service/FeatureServer/0`

## Bounded task B: water-energy linkage

1. Acquire the latest public EIA generator/plant inventory needed to identify hydro, solar, wind, storage, geothermal and thermal projects in the regional system.
2. Match hydropower plants to dams using normalized name plus spatial distance. Preserve both match signals.
3. Match generation to the simulator's existing 94 substations and 244 drawable corridors only as candidate links unless an authoritative electrical topology source confirms the connection.
4. Label every match as `confirmed`, `candidate`, `ambiguous`, or `unmatched`. Never promote proximity alone to confirmed electrical connectivity.
5. Keep active, planned, retired and canceled projects distinct.

## Required outputs

Place only compact outputs in the Antigravity branch:

- `handoffs/antigravity/dam-energy/receipt.json`
- `handoffs/antigravity/dam-energy/dams.geojson`
- `handoffs/antigravity/dam-energy/watershed-edges.json`
- `handoffs/antigravity/dam-energy/energy-projects.geojson`
- `handoffs/antigravity/dam-energy/dam-energy-links.json`
- `handoffs/antigravity/dam-energy/validation-report.md`

The receipt must include provider IDs/URLs, retrieval timestamps, local original paths, full SHA-256 hashes, byte counts, feature counts, coordinate reference systems and license/terms notes.

## Acceptance gates

- Every compact feature traces to a preserved original object.
- Counts and byte totals balance.
- Coordinates are finite and within declared source bounds.
- Duplicate provider IDs fail validation.
- Upstream classification has a stored graph path or remains unresolved.
- Hydropower matches retain distance and name evidence.
- No API key, token, private archive content or machine secret is present.
- Public redistribution remains blocked wherever provider terms are unclear.
- Antigravity reports `prepared for Codex review`, not `accepted`, `integrated` or `complete`.

## Paste-ready instruction for Antigravity

> Use `/run/media/madame-butterfly/Toshiba/Treasure_Valley_Model/github_treasure_valley_sim/docs/ANTIGRAVITY_HANDOFF.md` as the controlling task. Create a separate worktree and branch; do not edit the live Codex worktree. Complete the dam/watershed evidence bundle first, then the energy inventory and candidate links. Preserve original bytes on the T drive, expose progress in receipts, run your validators, and stop at `prepared for Codex review`. Never access or expose API keys.
