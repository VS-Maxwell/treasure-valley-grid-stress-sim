# Treasure Valley 4D Earth-State Simulator — Master Build Plan

Status: working engineering baseline, 2026-09-14

Baseline commit: `d856e3cf998031990ef53b55f1ec59b8548e545b`

Working branch: `codex/visible-master-build`

## 1. Outcome

Build one place-bound, four-dimensional Earth-water-energy-society simulator for the Treasure Valley and Western Snake River Plain. It must combine an immediately understandable map/game cockpit, defensible scientific model chains, RAVEN uncertainty and risk, historical and future time, realistic terrain and drone-derived scenes, and an offline-capable desktop edition.

The same source tree produces:

- a lightweight public browser demonstration;
- a full browser application backed by local or hosted data packs;
- a Tauri desktop application for large offline packs and protected archives;
- reproducible scientific and RAVEN command-line runs;
- a kiosk/showcase mode for presentations; and
- an educator mode with guided lessons and evidence inspection.

## 2. Delivery Horizon

These are engineering ranges, not promises that missing scientific data can be invented.

| Delivery | Elapsed target | What is demonstrably complete |
|---|---:|---|
| Visible development foundation | Days 1–3 | Live status view, clean baseline, plan, gates, secrets policy |
| Modular walking skeleton | Weeks 1–2 | Vite/TypeScript cockpit, shared state, diagnostics, legacy fallback |
| Impressive 4D visual vertical slice | Weeks 3–8 | Terrain, time, Energy/Water/Nexus, first cinematic, evidence UI |
| Offline historical data foundation | Weeks 5–12 | STAC catalog, DuckDB/Parquet, COG/PMTiles, provenance receipts |
| Coupled Scenario H research prototype | Weeks 9–18 | Heat+drought through water, agriculture, pumping, grid, and exposure |
| RAVEN uncertainty and risk release | Weeks 16–24 | Reproducible ensemble, seeds, sensitivity, confidence and risk cards |
| Desktop/offline and teaching release | Weeks 21–30 | Signed-candidate Tauri build, local packs, AI guide, lesson mode |
| Research-grade keystone system | Months 7–10 | Independent validation of the principal coupled domains |
| 34-domain program | Months 10–18+ | Domains expanded in waves; each remains gated by evidence and review |

Visual impact can arrive quickly. Research-grade validation is governed by data quality, model calibration, expert review, and authority—not GPU speed.

## 3. Fixed Architecture

### 3.1 Shared state and contracts

All scientific state is renderer-independent. Each field pack declares:

- domain and variable identifiers;
- units and sign conventions;
- horizontal and vertical coordinate reference systems;
- spatial and temporal resolution;
- observation/model/reconstruction truth state;
- source, version, retrieval time, and full SHA-256;
- model code, parameters, seed, and execution receipt;
- uncertainty and confidence;
- sensitivity/access classification; and
- downstream consumers.

The coupling engine rejects unit, time-base, coordinate, authority, and truth-state mismatches instead of silently converting them.

### 3.2 Application layers

| Layer | Selected approach | Responsibility |
|---|---|---|
| Product shell | Vite + TypeScript | Routing, state, input, loading, accessibility, diagnostics |
| Geospatial renderer | CesiumJS adapter | Globe/terrain, time-dynamic 3D Tiles, large geospatial layers |
| Cinematic/scene renderer | Three.js adapter | Controlled scenes, effects, authored sequences, splat pilots |
| UI | Standards-based DOM/CSS | Low-chrome HUD, drawers, charts, evidence and keyboard access |
| Core | Rust crates | Contracts, units, scenario state, spatial indexes, receipts |
| Scientific adapters | Typed Python | MODFLOW, climate, crop, grid, air, ecology and conversion workflows |
| Analytics | DuckDB + Arrow | Local queries across historical Parquet/GeoParquet packs |
| Multidimensional arrays | Zarr/NetCDF | Climate, groundwater and ensemble grids |
| Risk | INL RAVEN | Sampling, uncertainty, sensitivity, surrogates and risk workflows |
| Desktop | Tauri 2 | Offline packs and narrowly scoped, validated OS access |

CesiumJS and Three.js are renderer adapters, not sources of scientific truth. A common camera/time/state contract prevents the two views from becoming separate products.

### 3.3 Data formats

- STAC: catalog and spatial/temporal discovery.
- Parquet/GeoParquet: tabular and vector history.
- DuckDB: local SQL without a mandatory server.
- COG: raster observations and derived surfaces.
- Zarr/NetCDF: chunked time-depth-field arrays.
- PMTiles: downloadable vector/raster map packs.
- 3D Tiles: streamed terrain, buildings, photogrammetry and point clouds.
- GLB/glTF 2.0: authored runtime assets.
- Compressed splat bundles: explicit-action pilot scenes only.
- JSON Schema: scenario, handoff, provenance and receipt contracts.

## 4. User Experience

The app opens directly into the working map cockpit. In under three seconds the user should understand that it is a time-aware model of how the valley's systems affect one another.

Persistent UI is limited to:

- a compact scene/time control;
- one status/risk strip; and
- a contextual interaction prompt.

Everything else lives in collapsible surfaces: layers, evidence, charts, archive, scenarios, uncertainty, lessons, model details and development status.

Primary verbs are Explore, Follow, Compare, Stress, Inspect Evidence, and Ask. The central playfield and lower-middle view remain clear.

### 4.1 Main scenes

1. **Time** — deep history, observed history, present state, and climate futures.
2. **Water** — rivers, canals, aquifer layers, recharge, pumping and quality.
3. **Energy** — generation, transmission, substations, irrigation loads and large loads.
4. **Nexus** — visible handoffs among climate, agriculture, water and electricity.
5. **Risk** — RAVEN distributions, sensitivity, thresholds and unequal exposure.
6. **Record** — sources, transformations, model receipts and permitted archives.
7. **Learning** — guided tours, lesson plans and age-appropriate explanations.

### 4.2 Cinematic opening

The optional tour begins in the live cockpit, not behind an entry screen. Its sequence is:

1. Western Snake River Plain formation.
2. Lake Idaho and drainage evolution.
3. Canyon incision and the Bonneville Flood.
4. Dams, canals, irrigation and aquifer recharge.
5. Urban, agricultural and industrial growth.
6. Present connected system.
7. User-selectable climate futures.

Deep-time geometry is a labeled reconstruction. Drone captures are observed 3D epochs. Only multiple dated captures support observed 4D change; modeled motion between captures remains labeled as simulation.

## 5. Scientific Program

The governing source describes 317 processes across 17 spheres and 34 executable domains, with three canonical model slots per domain where feasible. The build therefore maintains 102 possible model slots without claiming all are implemented or validated.

The 34 domains are:

1. Atmosphere
2. Climate
3. Land surface/snow
4. Riverflow/surface hydrology
5. Aquifer/groundwater
6. Lake hydrodynamics
7. Water quality/contaminant transport
8. Ecology/habitat
9. AI surrogate/reduced order
10. Risk/decision/prediction
11. Game engine/3D record
12. Geology/lithology/structure
13. Tectonics/seismic hazard
14. Geomorphology/landscape evolution
15. Slope stability/mass wasting
16. Sediment/turbidity/bed dynamics
17. Toxicity/fate/bioaccumulation
18. Biogeochemistry/methane/anoxia
19. Urban growth/land use
20. Public health/exposure
21. Wildfire/post-fire hydrology
22. Cryosphere/snowpack
23. Wind/boundary layer
24. Energy generation/hydropower
25. Grid/power flow/resilience
26. Infrastructure fragility/lifelines
27. Dam safety/reservoir operations
28. Economics/regional impact
29. Mining/legacy and active mines
30. Air quality
31. Data backend/ground truth
32. Forestry/timber/carbon
33. Transportation/evacuation
34. Agriculture/irrigation/consumptive use

### 5.1 Implementation waves

**Wave A — flagship coupled spine:** D1, D2, D3, D4, D5, D9, D10, D11, D22, D24, D25, D31, and D34.

**Wave B — compound hazard and exposure:** D7, D8, D16, D17, D19, D20, D21, D23, D26, D27, D30, D32, and D33.

**Wave C — solid Earth and long-term landscape:** D12, D13, D14, D15, and D29.

**Wave D — dormant, bounded, or specialized:** D6, D18, D28 and any place-bound extension. A dormant domain remains represented as dormant instead of being deleted.

### 5.2 First end-to-end scenario

Scenario H connects heat and drought to snowpack/runoff, canal supply, crop demand, recharge and pumping, aquifer state, electricity demand, grid stress, air/wildfire compound conditions, costs and community exposure. It is the first complete proof because it forces the key systems to exchange real typed state.

## 6. Step-by-Step Execution

### Phase 0 — Baseline, visibility and custody

1. Preserve release-0 commit and hash the checkout.
2. Capture existing screenshots and performance when browser automation is available.
3. Record current failing validators without suppressing them.
4. Install the live development status surface and event writer.
5. Inventory local video, notebook tables, model outputs and Drive source records.
6. Create source, model, dependency and restricted-data registries.
7. Establish T-drive data directories; keep secrets off NTFS.
8. Repair 5060 driver/library mismatch during an agreed school maintenance window.

Gate: baseline is reproducible, visible, and preserved; no source has uncertain custody.

### Phase 1 — Modular walking skeleton

1. Scaffold Vite/TypeScript without deleting the legacy app.
2. Add formatter, linter, strict TypeScript, unit tests and browser smoke tests.
3. Define state, scenario, truth-state, source and receipt schemas.
4. Create renderer interfaces and a legacy fallback adapter.
5. Create low-chrome DOM HUD and explicit camera/input state machine.
6. Add context-loss, missing-tile, offline and degraded-mode behavior.
7. Build only `dist/` for hosting.

Gate: clean clone builds deterministically; tests pass; cockpit is first screen; legacy data remains reachable.

### Phase 2 — Data plane and historical packs

1. Inventory and fingerprint every source.
2. Normalize tabular history to Parquet/GeoParquet.
3. Normalize arrays to chunked Zarr/NetCDF.
4. Convert rasters to COG and web maps to PMTiles.
5. Create a STAC catalog and DuckDB views.
6. Add units, CRS, datum, time-zone, missingness and update-frequency checks.
7. Create immutable, versioned offline packs.
8. Build provider adapters that update packs without making APIs a runtime dependency.

Gate: disconnect the network and reproduce a historical view with complete provenance.

### Phase 3 — Terrain, 3D assets and time

1. Establish a USGS/public terrain baseline.
2. Add Esri imagery as the default owner-facing rich basemap when authorized.
3. Add Google Photorealistic 3D Tiles only as an online, policy-compliant optional layer.
4. Add USGS/satellite comparison layers with provider attribution kept distinct.
5. Convert drone outputs to 3D Tiles and one small compressed splat pilot.
6. Normalize GLB units, pivots, names, materials, LOD and collision proxies.
7. Implement time controller and observed/reconstructed/modeled styling.
8. Measure draw calls, texture memory, decode stalls and frame time.

Gate: app works without the splat, splat failure falls back cleanly, and provider attribution remains visible.

### Phase 4 — Energy and grid

1. Extract the current embedded grid data from `legacy.html` into versioned packs.
2. Reproduce current results before altering algorithms.
3. Separate the 94-bus screening graph from the 12-bus interactive representation.
4. Build a typed pandapower adapter and store its exact inputs/outputs.
5. Add generation, transmission, substation, irrigation-pumping and large-load layers.
6. Add N-1, heat, drought and growth scenarios.
7. Train and validate an interactive surrogate against held-out runs.

Gate: every displayed line reports whether it is visible, electrically modeled, assumed, or blocked-missing.

### Phase 5 — Water, agriculture and aquifer

1. Acquire the official USGS Treasure Valley MODFLOW 6 archive and preserve original bytes.
2. Run the published historical baseline before changing it.
3. Extract six-layer heads, budgets, recharge, rivers, wells and canal components.
4. Add irrigation and crop-consumptive-use adapters.
5. Couple surface delivery, recharge, pumping and electricity demand.
6. Keep the Treasure Valley model separate from ESPAM; create an explicit regional seam.
7. Add uncertainty and resolution warnings to every map level.

Gate: published baseline reproduction and conservation checks pass before forecasts are shown.

### Phase 6 — Climate and compound scenarios

1. Build observed-weather and climate-projection adapters.
2. Select models, SSPs, periods, downscaling and bias treatment explicitly.
3. Generate historical and future forcing packs.
4. Connect heat/drought to snow, river/canal availability, crop demand and grid load.
5. Add wildfire smoke and air-quality compound scenarios after core coupling passes.

Gate: ensembles and scenario choices are visible; one climate realization is never presented as the future.

### Phase 7 — RAVEN risk

1. Pin the RAVEN version and audit its bundled/contrib licenses.
2. Define uncertain parameters and distributions from cited sources.
3. Wrap each external model with bounded inputs, timeouts and receipts.
4. Run small deterministic test ensembles.
5. Scale independent samples across the 4090 host and 5060 worker.
6. Compute sensitivity, response surfaces, threshold exceedance and uncertainty.
7. Render risk cards linked to run IDs, seeds and source states.

Gate: same version, inputs and seed reproduce the accepted result; unreceipted RAVEN values cannot ship.

### Phase 8 — AI, voice and archives

1. Build a local model gateway with an allow-listed model registry.
2. Add offline retrieval over authorized public/project collections.
3. Add transcription with source-audio linkage and confidence intervals.
4. Add scenario-language parsing that produces a reviewable structured scenario.
5. Add explanations and lesson plans with citations.
6. Keep restricted archives behind explicit collection and authority gates.
7. Red-team prompt injection, false citation, data leakage and invented-state failures.

Gate: AI cannot alter accepted scientific state, publish content, or cross a restricted boundary.

### Phase 9 — Tauri desktop application

1. Reuse the web application; do not fork the UI.
2. Define the entire typed IPC contract before adding filesystem access.
3. Give the renderer no arbitrary shell or path access.
4. Scope file permissions to approved data-pack and export directories.
5. Implement offline startup and explicit sync status.
6. Measure cold start, idle memory, installer size and background CPU.
7. Establish signing, update-manifest verification, staged rollout and rollback.

Gate: fresh install, upgrade, rollback and offline tests pass on real target operating systems.

### Phase 10 — Education, accessibility and publication

1. Create short guided paths for water, energy, nexus, risk and evidence.
2. Add educator-controlled lessons and downloadable worksheets.
3. Test keyboard, screen-reader labels, contrast, reduced motion and mobile layouts.
4. Generate public, internal and restricted release manifests.
5. Run license, secret, asset-size, source, scientific and browser validators.
6. Stage the release; preserve hashes and restore-test it.

Gate: only the public/sanitized `dist/` is eligible for hosting.

## 7. Visible Development System

The development page polls `dev/status.json` every two seconds and shows:

- current phase and task;
- queued/active/passed/failed/blocked state;
- progress estimate;
- last validation result;
- changed files;
- 4090/5060/Queen availability;
- credential configuration without secret values;
- recent bounded event history; and
- known blockers.

Every future engineering command is accompanied by a status event. Secret-bearing commands are summarized rather than copied verbatim. Scientific outputs link to immutable run receipts.

## 8. Compute Plan

### Madame-Butterfly / RTX 4090

- Primary TypeScript/Rust/Python builds and tests.
- High-resolution 3D asset work, photogrammetry and splat processing.
- Coupled scientific runs and surrogate training.
- Local code/reasoning review.
- Coordinator for RAVEN ensembles.

### Palimpsest / RTX 5060 Ti

- School work always preempts project work.
- Keep 16 GiB RAM available at all times.
- Keep at least 25 percent or 4 GiB VRAM available, whichever is greater.
- Daytime: low-priority CPU table validation, tests and metadata only when idle.
- After-hours idle: bounded RAVEN samples, tile/asset compression, local Qwen review and surrogate batches.
- Jobs checkpoint at short intervals and stop when telemetry, thermal, memory or interactive-use gates fail.
- GPU use remains disabled until its NVIDIA driver/library mismatch is repaired and VRAM can be measured.

### Storage

- Repository and bulk working data: mounted Toshiba T drive.
- Secrets: protected Linux configuration directory, never the NTFS project tree.
- Temporary hot cache: capped and monitored.
- Queen: preservation and independent read-back when online.
- Google Drive: controlled source/review channel, not the runtime data lake.

## 9. API Policy

Credential discovery has identified the Drive key register without opening secret values. Each provider is activated separately only after its adapter, license, quota and redaction tests exist.

- Esri keys: restrict privileges and service scope; preserve required attribution.
- Google Map Tiles: online visualization only. Do not prefetch, extract, analyze, or build offline packs from Google content.
- Microsoft: identify the provider before use. Retired free Bing Maps keys are not a durable dependency; prefer Azure Maps where licensed or the Planetary Computer STAC/data-token path where appropriate.
- USGS, EIA, Census, NOAA and other public sources: snapshot with retrieval receipts and keep API refresh separate from runtime.

## 10. Licensing and Distribution Boundaries

Project-owned code keeps the existing `Apache-2.0 OR MIT` expression unless the owner changes it. Third-party components retain their licenses. Model weights and datasets are never relicensed as project code.

Required release records:

- `THIRD_PARTY_LICENSES.csv`
- `MODEL_REGISTRY.json`
- `DATA_SOURCES.csv`
- `RESTRICTED_DATA_POLICY.md`
- `NOTICE`
- SBOM for each application build
- source and binary release checklists

Google, Esri and other service-delivered imagery is not placed inside the open-source asset bundle unless its terms explicitly permit redistribution. Sovereignty-sensitive material stays outside all public releases.

## 11. Verification Matrix

| Area | Automated evidence | Human/visual evidence |
|---|---|---|
| Contracts | JSON Schema, Rust and Python type tests | Scientific variable review |
| Simulation | unit, conservation, regression and reproducibility tests | Expert reasonableness review |
| Coupling | unit/time/CRS/lineage integration tests | Scenario-chain review |
| Renderer | load, context-loss, asset-budget and performance tests | Screenshots and structured playtest |
| UI | DOM, input-state, accessibility and responsive tests | Playfield/HUD review |
| Assets | glTF validation, texture/LOD budgets and hashes | Scale, pivot and visual inspection |
| RAVEN | version/seed/input/output receipt checks | Distribution and risk interpretation |
| Desktop | IPC schema, capability and offline tests | Install/upgrade/rollback on real OSes |
| Security | secret scanning, CSP and dependency audit | Threat-model review |
| Licensing | SPDX, registry, NOTICE and bundle scan | Release-counsel/owner review as needed |

## 12. Current Confirmed Blockers

1. Screenshot capture times out in the available browser-control surface, so visual composition is not yet receipted.
2. The controlled 3D browser reported 10 FPS while the workstation was under unrelated heavy CPU load; clean-load performance is not yet accepted.
3. A natural WebGL context-loss transition has not been forced in browser automation; deterministic Canvas launch passes.
4. Modular source history described in `GIT_LESSONS.md` is not present on the remote.
5. Palimpsest has NVIDIA driver 610.57.04 loaded with NVML library 615.71; GPU telemetry fails.
6. Google Drive checkpoint access did not complete in the first bounded check and its shared client ID is being retired.
7. Lemonade's requested automatic installer supports apt-based Linux only and did not configure this CachyOS workspace.
8. Queen is not currently confirmed online for preservation.
9. Third-party dependency/data/model licensing inventory is incomplete.
