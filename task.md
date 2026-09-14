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
- [ ] Produce browser-safe time slices from the reproduced heads and budgets without shipping the 72 MB binary output.

## Later phases

- [ ] Phase 2 historical data plane and offline packs.
- [ ] Phase 3 terrain, provider layers, 3D assets, time, and cinematic.
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
- [ ] Google Drive checkpoint connectivity needs a successful bounded recheck.
- [ ] Queen must be confirmed live before preservation transfer.
- [ ] Scientific datasets, authority decisions, and expert acceptance remain phase gates.

## Checkpoints

- 2026-09-14 11:24 PDT — execution plan and task ledger created; Phase 1 scaffold starting.
- 2026-09-14 11:42 PDT — Phase 1 Three.js build, 10 tests, production bundle, responsive controls, primary verbs, and explicit Canvas fallback pass; screenshot and clean-load performance gates remain.
