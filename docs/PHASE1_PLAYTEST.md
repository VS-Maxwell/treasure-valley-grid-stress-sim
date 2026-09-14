# Phase 1 Browser Playtest Receipt

Date: 2026-09-14
Build URL: `http://127.0.0.1:8001/dist/?build=phase1-1`
Renderer: Three.js r186 through the production Vite bundle

## Boot and rendering

- Production application booted directly into the working cockpit.
- Renderer state reported `three-webgl`.
- Exact local pack reported 244 corridors.
- Scene used 9 draw calls in the tested view.
- The UI reported 10 rendered frames per second in the controlled in-app browser while the workstation was under unrelated heavy CPU load.
- The loading surface became inert and accessibility-hidden after boot.
- No current-bundle warning or error was recorded after replacing deprecated `THREE.Clock` with `THREE.Timer`.

The automated browser screenshot interface timed out repeatedly. Therefore the visual-composition gate remains blocked even though live DOM, canvas dimensions, renderer identity, controls, and scene state were inspected.

## Primary verbs

| Verb | Evidence |
|---|---|
| Explore | selected Time and invoked the explicit camera-home method |
| Follow | advanced from Time to Energy on the defined Energy → Water → Nexus → Risk path |
| Compare | enabled and disabled the baseline versus Heat + Drought 2050 divider |
| Stress | selected Nexus, year 2050, modeled-screening truth, and the heat-drought scenario |
| Evidence | opened a drawer with the full grid SHA-256, representation boundary, terrain label, and release boundary |
| Ask | opened the offline boundary; inference remained disabled pending Phase 8 tests |

## Scene and time checks

- Time, Water, Energy, Nexus, Risk, Record, and Learning are reachable DOM tabs backed by one shared state store.
- Risk explicitly displays `UNVALIDATED PREVIEW` and withholds unreceipted RAVEN results.
- The timeline preserved the exact 2026 starting year after changing the range step from 25 to 1.
- Play advanced from 2050 into the reconstructed deep-time range and changed the truth state to `RECONSTRUCTED`.
- Pause stopped timeline advancement.

## Responsive and degraded mode

- At 390 × 844, the canvas filled the viewport, all seven tabs and six primary actions remained accessible, and the contextual narrative collapsed to protect the playfield.
- Returning to 1280 × 720 restored the full status and context surfaces.
- `?renderer=canvas` booted deterministically with `Degraded Canvas mode`, the same 244-corridor pack, shared controls, and no WebGL canvas.
- A naturally triggered `webglcontextlost` event still needs a browser-level test; the event handler is implemented but the browser test interface cannot force the extension safely.

## Open findings

1. Screenshot capture is blocked by the browser-control surface.
2. The controlled browser reported 10 FPS; a clean system-load performance pass is required before promotion.
3. The Three.js engine chunk is 572 KB minified and 142 KB gzip. It is dynamically loaded, but the production build warns that the chunk exceeds 500 KB.
4. Actual USGS terrain, provider imagery, time-dynamic 3D assets, scientific model outputs, and RAVEN results are not part of this Phase 1 receipt.
