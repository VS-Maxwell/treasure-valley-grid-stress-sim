# Treasure Valley Simulator Task Ledger

Updated: 2026-09-14

## Active milestone — Phase 2 historical data plane

- [x] Preserve the original legacy application and baseline commit.
- [x] Provide a stable direct-root Canvas grid while the 3D runtime is built.
- [x] Confirm the prior Firefox crash and record its evidence.
- [x] Create the master build plan and visible status surface.
- [x] Scaffold Vite, strict TypeScript, formatting, linting, and unit tests.
- [x] Define truth-state, source, scenario, simulation-state, and receipt contracts.
- [x] Implement renderer and camera interfaces independent of simulation state.
- [x] Implement the Three.js grid-and-reconstructed-terrain cockpit from the exact local grid core.
- [x] Implement explicit Explore, Follow, Compare, Stress, Inspect, and Ask actions.
- [x] Implement shared-state navigation shells for Time, Water, Energy, Nexus, Risk, Record, and Learning.
- [ ] Complete WebGL context-loss, offline, missing-data, and Canvas fallback validation. The explicit Canvas launch path passes; natural context-loss testing remains.
- [x] Add diagnostics for frame rate, draw calls, triangles, renderer mode, context loss, and data receipts.
- [x] Add deterministic `dist/` build and release-only-from-dist enforcement.
- [ ] Pass unit, contract, build, release, performance, and browser playtests. Automated gates pass; clean-load performance and screenshots remain.
- [ ] Capture visual evidence or retain the screenshot blocker with exact cause.
- [x] Promote the simulator cockpit to the default route; retain the Canvas grid only as a degraded renderer.
- [x] Acquire and byte-verify the bounded USGS TVGWFM core archive set on the T drive.
- [x] Extract the official 6-layer, 64×65 model grid and 4,055 active top cells into a browser-safe pack.
- [x] Render the ingested USGS model footprint inside the Water and Nexus scenes with an explicit non-validation label.
- [x] Reproduce all 361 USGS MODFLOW stress periods and compare heads, observation outputs, and water-budget closure against the archived baseline.
- [x] Produce 16 browser-safe six-layer head snapshots from 1986–2015 without shipping the 72 MB binary output.
- [x] Animate the six model-head surfaces from the shared year state and disclose the nearest displayed source year.
- [x] Extract 361 monthly water-budget rows and 33 simulated-observation series into a compact, receipt-backed chart table.
- [x] Render the Water panel's monthly modeled inflow/outflow chart with timeline selection and explicit non-observation boundary.
- [x] Build and validate an immutable six-artifact, 1,151,343-byte offline historical-water manifest and expose it in the Record scene.
- [x] Acquire and byte-verify 19,696 official USGS discrete groundwater-depth measurements from 3,168 locations inside the model footprint for 1986–2015.
- [ ] Define and validate the datum-aware spatial match from measured well depth to model cell/head before showing measured-versus-modeled comparisons.
- [x] Expose annual observed depth distributions only behind the explicit Compare action, with 77 null source values and the no-datum-match boundary visible.
- [x] Acquire and byte-verify elevation and vertical-datum metadata for all 3,168 measured wells: 2,920 NAVD88 and 248 NGVD29.
- [ ] Acquire well-screen evidence before assigning observed wells to model layers or computing validation residuals.
- [x] Convert eligible latest depths to NAVD88 water-level altitude, map 2,849 wells to active cells, and ship a 34,188-byte interleaved marker pack.
- [x] Render mapped observed wells only in the explicit Water → Compare state.
- [x] Acquire and independently hash six USGS 3DEP 1-arc-second GeoTIFF tiles totaling 316,921,023 bytes on the T drive.
- [x] Build a 15,251-vertex observed terrain mesh across 118°W–115°W and 43°N–45°N and retain reconstructed terrain only outside that boundary.
- [x] Preserve 32 USGS 3DEP tiles and promote an 80,601-vertex full Snake Plain overview mesh across 119°W–111°W and 42°N–46°N.
- [x] Acquire the official ESPAM 2.2 final-calibration and aquifer-property archives with byte, SHA-256, ZIP, and CRC receipts.
- [x] Cross-check and render all 11,236 official ESPAM active cells without stretching or merging the TVGWFM domain.
- [x] Map 39 archived annual ESPAM head slices from 1980–2018 onto the exact 11,236-cell official active grid and render the time-varying surface.
- [ ] Map archived ESPAM budgets and independently reproduce the published baseline before enabling new ESPAM scenarios.
- [x] Acquire and normalize 193 current USACE NID regional dam records, retaining one missing NIDID and three shared-NIDID records under distinct Corps OBJECTIDs.
- [x] Render all 193 regional dams in water/nexus/risk and distinguish 11 hydroelectric-purpose dams in Energy without claiming watershed or grid connectivity.
- [x] Preserve and render the expanded full-scene inventory of 647 NID dams, including 55 hydroelectric-purpose candidates, without rewriting the 193-dam checkpoint.
- [x] Define the normalized historical tables, charts, and relationship matrices needed for an API-independent runtime.
- [x] Build and validate the directed receiving-system graph to the Snake River at Weiser: 348 dams have complete hashed COMID paths, 297 are outside the upstream set, and two retain explicit unresolved responses; do not relabel this as proven Treasure Valley delivery.
- [x] Preserve the final 2025 EIA-860 archive and extract 77 regional hydropower plants, 167 hydro generator records, and reviewable candidates for all 55 hydro-purpose dams.
- [ ] Match hydroelectric dams to EIA generators and expand all active/planned/retired regional energy projects by technology and status.
- [ ] Promote the 94-bus/156-branch screening graph into the interactive solver and improve voltage/selection rendering without fabricating missing topology. All 156 preserved scenario results are now interactive and color-banded; a fresh typed pandapower solve and individually resolved identities for the 27 legacy TAP buses remain pending.
- [x] Extract and render all six published TVGWFM bottom arrays as source-native model geometry with a 24,960-cell IDOMAIN pack.
- [ ] Add borehole/core constraints under separate evidence labels; do not reinterpret model bottoms as observations.

## Later phases

- [ ] Phase 2 historical data plane and offline packs.
- [ ] Phase 3 terrain, provider layers, 3D assets, time, and cinematic. Regional 3DEP and first NID dam increment are active; expanded watershed terrain, imagery and cinematic remain.
- [ ] Phase 4 energy and grid science.
- [ ] Phase 5 water, agriculture, and aquifer science.
- [ ] Phase 6 climate ensembles and compound scenarios.
- [ ] Phase 7 RAVEN uncertainty and risk.
- [ ] Phase 8 local AI, transcription, archive gates, and lessons.
- [ ] Phase 9 Tauri desktop and offline deployment.
- [ ] Phase 10 education, accessibility, manifests, publication, and preservation.

## Current blockers

- [ ] Fresh Firefox-specific stability validation for the direct-root build.
- [ ] Browser screenshot interface times out.
- [ ] Palimpsest RTX 5060 Ti GPU disabled until driver/library telemetry works.
- [x] Google Drive API register connectivity rechecked without exposing credentials; its Esri row contains only a truncated prefix and states that the full key is in email.
- [x] Store the complete authorized Esri EDU credential in the operating-system Secret Service and validate basemap styles plus geocoding without exposing it.
- [x] Activate a loopback-only Esri gateway with allow-listed health, bounded geocoding, and fixed-region public imagery routes; retain offline fallback.
- [ ] Confirm Esri provider terms, quota, allowed public origins, and attribution before any hosted release; local activation is not publication approval.
- [ ] Quarantine and rebuild the `/home/madame-butterfly/forge/treasure_valley_offline_lake/` handoff: its 63 files exist, but synthetic aquifer, grid, solver and risk rows plus missing shared lineage fields prevent scientific import.
- [ ] Queen must be confirmed live before preservation transfer.
- [ ] Scientific datasets, authority decisions, and expert acceptance remain phase gates.

## Checkpoints

- 2026-09-14 11:24 PDT — execution plan and task ledger created; Phase 1 scaffold starting.
- 2026-09-14 11:42 PDT — Phase 1 Three.js build, 10 tests, production bundle, responsive controls, primary verbs, and explicit Canvas fallback pass; screenshot and clean-load performance gates remain.
