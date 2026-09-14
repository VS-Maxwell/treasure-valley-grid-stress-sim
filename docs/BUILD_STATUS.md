# Build Status

Updated: 2026-09-14

## Confirmed baseline

- Local checkout: Toshiba T drive
- Branch: `codex/visible-master-build`
- Baseline: `d856e3cf998031990ef53b55f1ec59b8548e545b`
- Local preview: `http://127.0.0.1:8001/`
- Existing simulator: static wrapper plus compiled `legacy.html`
- Screening representation: 94 buses and 156 branches
- Interactive representation: 12 selected buses

## Validation state

- Direct-entry simulator: **PASSED** — the legacy intro gate is suppressed by the wrapper.
- Visible grid builder: **REPAIRED AND UI-TESTED** — 244 embedded map corridors are progressively revealed through 32 bounded Canvas redraw states. The earlier implementation repeatedly serialized the multi-megabyte GeoJSON source and was removed.
- Wrapper parser: **REPAIRED AFTER LIVE BROWSER TEST** — a literal closing script tag prematurely terminated the wrapper; the injected tag is now parser-safe and covered by validation.
- Wrapper memory path: **REPAIRED AFTER HANG REPRODUCTION** — the 4.2 MB legacy document now loads directly in the iframe rather than being fetched, duplicated as a JavaScript string, and assigned through `srcdoc`.
- First-playable boot: **CRASH-SAFE GRID CORE ADDED** — the default view now loads only the exact 244-corridor, 94-substation grid core. The preserved full legacy model is no longer allowed to block the first screen.
- First-playable renderer: **CANVAS SAFE MODE** — the default grid has no remote tile, WebGL, or perpetual render-loop dependency. Drag, wheel zoom, replay, and refresh are available; the full MapLibre model remains preserved for modular repair.
- Representation boundary: **CONFIRMED** — the geographic map has 244 drawable corridor features; the power-flow screening graph separately reports 94 buses and 156 solver branches.
- Primary JavaScript parse: **PASSED** — `node --check grid-canvas.js` and `node --check grid-live.js`.
- 5060 worker cross-check: **PASSED** — the current crash-safe files matched local SHA-256 receipts and passed 20 structural, scope, and provenance checks on Palimpsest.
- 5060 Node check: **BLOCKED** — Node is not installed on Palimpsest; the primary host performed the parser check.
- Transmission verifier: **PASSED** — all 16 expert-model markers are verified in `legacy.html`.
- Release validator: **PASSED** — required files, secret boundary, truth labels, crash-safe default, and model-scope disclosures passed.
- Browser UI playtest: **PASSED** — observed `DRAWING NETWORK`, `GRID READY 244/244`, progress 100%, and `VIEW REFRESHED` through the visible browser controls.
- Screenshot capture: **BLOCKED** — the browser surface could not return an image, so the visual evidence is the live deliverable tab plus accessibility-state receipts.
- 5060 GPU worker: **BLOCKED** — NVIDIA driver/library mismatch prevents telemetry.
- Lemonade local multimodal routing: **BLOCKED** — provided installer does not support CachyOS.

Open blockers remain visible until resolved.
