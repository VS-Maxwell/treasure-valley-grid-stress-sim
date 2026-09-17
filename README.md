# Treasure Valley Earth-State Simulator

An open, place-bound simulator for exploring how time, water, energy, climate, land, infrastructure, and risk interact across Idaho’s Treasure Valley and the Western Snake River Plain.

The project is under active construction. It is not yet a research-grade coupled model.

## CDA Dule Lensed project

This repository also contains the source archive for the CDA Dule Lensed project,
supporting Dianne's one-year grant. The first archive is the Lemhi collection.
Lemhi materials are organized by the location they came from and then by year:

```text
projects/lemhi/sources/<source-location>/<year>/scripts/
projects/lemhi/sources/<source-location>/<year>/full-sends/
```

See [the Lemhi archive guide](projects/lemhi/README.md) for naming, provenance,
and intake rules.

## What runs now

The built application is the only public entry point:

- `/dist/` after `npm run build` — the Phase 1 Three.js cockpit with shared simulation state, seven system scenes, time controls, comparison and stress actions, evidence labels, runtime diagnostics, responsive layouts, and deterministic Canvas fallback.

The earlier single-file compiled `index.html` plus `watchdog.js`/`watchdog.css` overlay and the `legacy.html` iframe host have been retired. That combination was the confirmed source of the GitHub Pages entry screen freeze (see `docs/CRASH_INVESTIGATION.md`): the old build never ran through Vite and the multi-megabyte `legacy.html` was loaded into a hidden iframe via `srcdoc`, which previously produced a `SIGSEGV` in Firefox. GitHub Pages now deploys only the CI-built `dist/` bundle produced from `app/`.

The current Three.js terrain is a receipt-backed USGS 3DEP surface spanning the full Snake Plain overview envelope (119°W–111°W, 42°N–46°N). The western six TVGWFM aquifer-bottom surfaces remain exact visualization transforms of that published model's discretization arrays. The separate official ESPAM 2.2 wireframe maps 11,236 active eastern cells from IDWR's one-layer 104×209 grid. Terrain coverage is not presented as groundwater-model coverage: TVGWFM, ESPAM, and framework-only areas remain distinct. Model bottoms are not borehole observations, and animated TVGWFM heads are reproduced model output rather than a new validated forecast.

## Build and validate

Requirements: Node.js 22.12 or newer.

```bash
npm install
npm run validate
npm run dev
```

`npm run validate` runs formatting, linting, unit tests, strict TypeScript, the Vite production build, and the distribution safety check. Only `dist/` is eligible for future hosting; the repository root is not a release artifact.

The receipt-backed terrain and historical tables run without network access. To add the optional live Esri layer on this workstation, start the credential-isolating loopback service in a second terminal:

```bash
npm run esri:gateway
```

The gateway binds only `127.0.0.1:8767`, reads the authorized credential from the operating-system Secret Service, and never sends it to browser JavaScript. The cockpit shows `ESRI IMAGERY · LIVE` only after both the gateway contract and the image load succeed. See `docs/ESRI_GATEWAY.md`.

The browser build also has an optional Gaussian-splat pilot hook. Keep the
scene asset outside the repository and load it through the query string:

```text
http://127.0.0.1:5173/?splat=/data/treasure-valley-pilot.ksplat
```

The status strip reports whether the splat is optional, loading, live, or
unavailable. The existing receipt-backed terrain and government-data tables
remain the default when no splat asset is configured.

To exercise the degraded renderer deliberately, add `?renderer=canvas` to the built application URL.

## Current scientific boundary

The app distinguishes the 244 visible corridor features from the larger 94-bus/156-branch screening representation and the 12 selected buses used by the legacy interactive solver. Transformers remain idealized because authoritative impedance and tap parameters are not embedded.

No current screen is a validated operational grid, groundwater, climate, public-health, or risk forecast. RAVEN values cannot ship until a pinned version, distributions, inputs, seed, outputs, and acceptance receipt reproduce them. Planned pandapower and MODFLOW adapters must reproduce accepted baselines before forecasts are enabled.

The interface uses explicit truth states: observed, ingested, reconstructed, modeled-screening, validated-model, synthetic, and blocked-missing. Absence of Tribal representation in a public dataset is treated as a documentary or governance gap—not evidence of absent Tribal presence, activity, knowledge, or rights.

The HTML client and any future Unreal/ArcGIS client are replaceable renderers, not authorities over community data. See `docs/SOVEREIGNTY_ARCHITECTURE.md` for the protected-data, credential, offline and publication gates.

## Architecture

- Vite + strict TypeScript product shell
- renderer-independent serializable simulation state
- Three.js 3D adapter with merged grid geometry and instanced assets
- bounded Canvas degraded-mode adapter
- loopback-only optional Esri adapter with fixed provider routes and offline fallback
- DOM HUD and accessibility surfaces
- JSON Schemas for state, scenarios, sources, truth labels, and run receipts
- future CesiumJS, Rust, Python, DuckDB, STAC, RAVEN, Tauri, and offline-AI modules gated in `docs/MASTER_BUILD_PLAN.md`

`legacy.html` and the retired watchdog overlay remain available in git history (see the `codex/visible-master-build` history before the entry-screen fix) as source evidence; they are no longer present in the working tree or in any published build.

## Status and plans

- `implementation_plan.md` — long-run delivery sequence
- `task.md` — live checklist
- `docs/MASTER_BUILD_PLAN.md` — full scientific and engineering plan
- `docs/BUILD_STATUS.md` — evidence-backed status
- `docs/CRASH_INVESTIGATION.md` — Firefox crash findings and repair boundary
- `docs/PHASE1_PLAYTEST.md` — current browser test receipt
- `/dev/` — live local build status when the repository server is running

## Licensing

Project-owned source code is available under `Apache-2.0 OR MIT`. Third-party software, models, data, imagery, and archives retain their own licenses and terms. No provider credential belongs in source, logs, screenshots, URLs, or the public distribution.

## Attribution

Van Maxwell · University of Idaho — I-CREWS. Earth-state simulation research and 3D demonstrator, 2026.
