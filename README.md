# Treasure Valley Earth-State Simulator

An open, place-bound simulator for exploring how time, water, energy, climate, land, infrastructure, and risk interact across Idaho’s Treasure Valley and the Western Snake River Plain.

The project is under active construction. It is not yet a research-grade coupled model.

## What runs now

Two interfaces are preserved while the modular application is built:

- `/` — a bounded Canvas stability view with 244 transmission corridors and 94 mapped substations.
- `/dist/` after `npm run build` — the Phase 1 Three.js cockpit with shared simulation state, seven system scenes, time controls, comparison and stress actions, evidence labels, runtime diagnostics, responsive layouts, and deterministic Canvas fallback.

The current Three.js regional terrain is a receipt-backed USGS 3DEP surface, and its six aquifer-bottom surfaces are exact visualization transforms of the published TVGWFM discretization arrays. The dim terrain outside the verified six-tile region remains reconstructed context. Model bottoms are not borehole observations, and animated heads are reproduced model output rather than a new validated forecast. The geographic grid pack is an exact extraction from the preserved legacy application and carries a SHA-256 receipt.

## Build and validate

Requirements: Node.js 22.12 or newer.

```bash
npm install
npm run validate
npm run dev
```

`npm run validate` runs formatting, linting, unit tests, strict TypeScript, the Vite production build, and the distribution safety check. Only `dist/` is eligible for future hosting; the repository root is not a release artifact.

To exercise the degraded renderer deliberately, add `?renderer=canvas` to the built application URL.

## Current scientific boundary

The app distinguishes the 244 visible corridor features from the larger 94-bus/156-branch screening representation and the 12 selected buses used by the legacy interactive solver. Transformers remain idealized because authoritative impedance and tap parameters are not embedded.

No current screen is a validated operational grid, groundwater, climate, public-health, or risk forecast. RAVEN values cannot ship until a pinned version, distributions, inputs, seed, outputs, and acceptance receipt reproduce them. Planned pandapower and MODFLOW adapters must reproduce accepted baselines before forecasts are enabled.

The interface uses explicit truth states: observed, ingested, reconstructed, modeled-screening, validated-model, synthetic, and blocked-missing. Absence of Tribal representation in a public dataset is treated as a documentary or governance gap—not evidence of absent Tribal presence, activity, knowledge, or rights.

## Architecture

- Vite + strict TypeScript product shell
- renderer-independent serializable simulation state
- Three.js 3D adapter with merged grid geometry and instanced assets
- bounded Canvas degraded-mode adapter
- DOM HUD and accessibility surfaces
- JSON Schemas for state, scenarios, sources, truth labels, and run receipts
- future CesiumJS, Rust, Python, DuckDB, STAC, RAVEN, Tauri, and offline-AI modules gated in `docs/MASTER_BUILD_PLAN.md`

The preserved `legacy.html` remains source evidence and a regression reference. It is not the default boot path.

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
