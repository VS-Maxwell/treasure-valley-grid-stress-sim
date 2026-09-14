# Treasure Valley Simulator Implementation Plan

Status: active
Owner authorization: persistent goal to finish the whole simulator and all steps
Authoritative detailed plan: `docs/MASTER_BUILD_PLAN.md`

## Execution strategy

The project advances through ten gated phases. A phase is complete only when its implementation, automated checks, browser/runtime evidence, provenance, licensing, and required human/scientific review all pass. Visual prototypes never substitute for scientific validation.

| Phase | Working estimate | Deliverable | Exit evidence |
|---|---:|---|---|
| 0. Baseline and custody | 1–3 days | Preserved baseline, visible status, registries, stable fallback | hashes, current inventory, clean recovery path |
| 1. Modular walking skeleton | 1–2 weeks | Vite/TypeScript 3D cockpit, external state, HUD, diagnostics, degraded mode | deterministic build, unit tests, browser playtest |
| 2. Historical data plane | 5–12 weeks overlapping | STAC, Parquet/GeoParquet, DuckDB, COG/PMTiles, immutable packs | offline reproduction and provenance receipts |
| 3. Terrain, assets, and time | 3–8 weeks overlapping | public terrain, optional provider layers, time controller, cinematic pipeline | attribution, fallback, performance budget |
| 4. Energy and grid | 4–10 weeks | typed 94-bus and 12-bus models, pandapower runs, stress scenarios | model/visible-line classification and regression |
| 5. Water, agriculture, aquifer | 6–14 weeks | reproduced USGS baseline, six-layer aquifer, irrigation-energy coupling | conservation and published-baseline checks |
| 6. Climate and compound futures | 5–10 weeks | observed and ensemble forcing packs, heat/drought/wildfire paths | visible ensemble choices and uncertainty |
| 7. RAVEN uncertainty and risk | 6–10 weeks | pinned RAVEN workflow, reproducible ensembles and sensitivity | version/input/seed/output receipts |
| 8. Offline AI, voice, archives | 5–10 weeks | allow-listed local AI, RAG, transcription, lesson explanations | leakage, citation, prompt-injection, authority tests |
| 9. Tauri desktop | 4–8 weeks | offline desktop build with scoped IPC and packs | install, upgrade, rollback, offline tests |
| 10. Education and release | 3–8 weeks | tours, lessons, accessibility, public/internal manifests | release matrix and independent review |

## Current build decision

- Runtime: Vite + strict TypeScript.
- 3D scene: vanilla Three.js with imperative camera/render control.
- Scientific truth: renderer-independent serializable state.
- UI: low-chrome DOM overlay.
- Data: versioned, typed packs with truth-state and receipt metadata.
- Default route during migration: proven Canvas stability build.
- New 3D runtime: built and tested under `app/`, then promoted only after gates pass.
- Heavy terrain, imagery, 3D Tiles, and splats: lazy and optional, with explicit fallback.

## Immediate milestone

Build the Phase 1 walking skeleton with:

1. strict TypeScript/Vite tooling;
2. simulation, renderer, UI, input, diagnostics, and data boundaries;
3. a Three.js terrain/grid cockpit using the exact local grid core;
4. time and scene state controls;
5. WebGL context-loss fallback to the existing Canvas view;
6. tests, a deterministic `dist/`, and visible runtime evidence.

## Checkpoint and custody

- Commit each coherent, passing milestone locally.
- Update `dev/status.json` before and after material work.
- Create timestamped checkpoint bundles every 30 minutes during sustained runs.
- Copy checkpoints to Google Drive only after live connectivity is verified.
- Never place credentials or restricted archive content in checkpoints or public builds.
