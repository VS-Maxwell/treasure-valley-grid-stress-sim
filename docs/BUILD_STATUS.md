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

- Overall simulator: **INCOMPLETE / ACTIVE BUILD** — the current default enters the modular 3D cockpit directly; a verified regional terrain/dam increment is active, while coupled science, full upstream coverage, climate, RAVEN, local AI, and desktop packaging still have open gates.
- Firefox stability: **UNDER INVESTIGATION** — Firefox produced a confirmed `SIGSEGV` in `libxul.so` after an earlier renderer grew into tens of gigabytes. The lightweight Canvas path passes structural checks and is visible, but it has not yet completed the required sustained clean-tab stability gate.
- Direct-entry simulator: **PASSED** — `/` redirects immediately into the built cockpit at `/dist/`; there is no intro gate or iframe. The bounded Canvas grid remains available as an automatic or explicit degraded renderer.
- Visible grid builder: **REPAIR CANDIDATE** — 244 embedded map corridors are progressively revealed through 32 bounded Canvas redraw states. The earlier implementation repeatedly serialized the multi-megabyte GeoJSON source and was removed; sustained browser validation is still pending.
- Retired wrapper parser: **ROOT CAUSE REMOVED** — the earlier wrapper both mishandled a closing script tag and duplicated the legacy document through `srcdoc`; the default route no longer uses that wrapper.
- First-playable boot: **LIGHTWEIGHT GRID CORE ADDED** — the default view now loads only the exact 244-corridor, 94-substation grid core. The preserved full legacy model is no longer allowed to block the first screen. “Crash-safe” remains a target, not a completed claim.
- Degraded renderer: **CANVAS SAFE MODE** — `?renderer=canvas` has no remote tile, WebGL, or perpetual render-loop dependency and retains all 244 corridors.
- Representation boundary: **CONFIRMED** — the geographic map has 244 drawable corridor features; the power-flow screening graph separately reports 94 buses and 156 solver branches.
- Primary JavaScript parse: **PASSED** — `node --check grid-canvas.js` and `node --check grid-live.js`.
- 5060 worker cross-check: **PASSED** — the current crash-safe files matched local SHA-256 receipts and passed 20 structural, scope, and provenance checks on Palimpsest.
- 5060 Node check: **BLOCKED** — Node is not installed on Palimpsest; the primary host performed the parser check.
- Transmission verifier: **PASSED** — all 16 expert-model markers are verified in `legacy.html`.
- Release validator: **PASSED** — required files, secret boundary, truth labels, bounded default route, and model-scope disclosures passed.
- Browser UI function check: **PASSED** — observed `DRAWING NETWORK`, `GRID READY 244/244`, progress 100%, and `VIEW REFRESHED` through the visible browser controls.
- Sustained browser stability gate: **PARTIAL** — a 75-second controlled-browser run completed automatic build, replay, cancellation/refresh, and held 244/244 with no new coredump. A fresh Firefox reload is still required before Firefox-specific stability can pass.
- Screenshot capture: **BLOCKED** — the browser surface could not return an image, so the visual evidence is the live deliverable tab plus accessibility-state receipts.
- 5060 GPU worker: **BLOCKED** — NVIDIA driver/library mismatch prevents telemetry.
- Lemonade local multimodal routing: **BLOCKED** — provided installer does not support CachyOS.

## Phase 1 modular application

- Vite 8 + TypeScript 6 scaffold: **PASSED**.
- Renderer-independent state and JSON contracts: **PASSED** — seven scenes, time, comparison, climate scenario, drawers, and seven explicit truth states.
- Three.js cockpit: **PASSED FUNCTIONAL PLAYTEST** — exact 244-corridor pack, 94 instanced substations, 14 instanced plants, observed regional terrain, six source-model aquifer bottoms, explicit camera controls, and bounded rendering in the tested scene.
- User verbs: **PASSED** — Explore, Follow, Compare, Stress, Evidence, and Ask all changed the shared state through visible controls.
- Timeline: **PASSED** — exact 2026 start, play/pause, deep-time wrap, and time-dependent truth labeling.
- Responsive layout: **PASSED STRUCTURAL PLAYTEST** — 390 × 844 retained seven scene tabs and six primary actions while collapsing secondary narrative.
- Deterministic Canvas mode: **PASSED** — `?renderer=canvas` booted the same state and 244-corridor pack without WebGL.
- Natural WebGL context-loss test: **OPEN** — handler is implemented; browser automation cannot yet force and visually receipt the transition.
- Automated toolchain: **PASSED** — format, lint, strict typing, 28 unit tests, source/registry checks, production build, and distribution scan.
- Distribution: **PASSED WITH SIZE WARNING** — 8 files and 3,961,886 bytes; Three.js is lazy-loaded but its 573 KB minified engine chunk exceeds Vite's 500 KB advisory threshold.
- Browser performance: **NOT ACCEPTED** — controlled browser reported 10 FPS while unrelated CPU inference consumed substantial host resources; repeat under a clean or bounded load before promotion.
- Drive connectivity: **PASSED** — bounded `rclone about gdrive:` returned quota data without reading file names or secrets; the shared client-ID retirement warning remains.

## Phase 2 verified data plane increment

- USGS TVGWFM source: **ORIGINAL BYTES VERIFIED** — 10 bounded core files totaling 71,707,343 bytes are preserved on the T drive; all upstream ScienceBase MD5 values, local SHA-256 hashes, and six ZIP integrity checks pass.
- Large development archive: **DEFERRED EXPLICITLY** — `model_development_scripts.zip` is 15,881,621,281 bytes and was not pulled blindly. The USGS README says it supports redevelopment, while `model.zip` is the runnable published model.
- Browser pack: **GENERATED AND VERIFIED** — an exact extraction from `model/mf6-tv_hist.dis` contains 6 layers, 64 rows, 65 columns, 4,055 active top cells, official georeference corners, and the source-archive SHA-256.
- USGS baseline: **NUMERICALLY REPRODUCED** — native MODFLOW 6.1.1 completed all 361 stress periods in 81.189 seconds with normal termination and a final rounded 0.00% budget discrepancy. Four observation CSVs match the archived values exactly at published text precision. Across 3,293,764 finite head values, the maximum absolute difference is 3.14e-11 feet and RMSE is 7.63e-12 feet.
- Water scene: **SOURCE AND BASELINE RECEIPTED** — the 3D cockpit renders the USGS model footprint and top-surface mesh and discloses the reproduction result. New climate, pumping, recharge, or coupling scenarios remain blocked until domain review defines scientifically defensible changes.
- Historical head pack: **GENERATED AND ACTIVE** — 399,360 six-layer values across 16 snapshots representing 1986–2015 are stored as an 798,720-byte little-endian `uint16` table at 0.1-foot display precision. The renderer selects the nearest source year from shared timeline state and animates all six head surfaces; the original 72 MB double-precision output remains preserved outside the web bundle.
- Monthly model tables: **GENERATED AND ACTIVE** — the browser pack contains all 361 reproduced water-budget rows and 33 simulated-equivalent series from four archived comparison groups. The Water panel plots monthly modeled inflow and outflow, follows the shared timeline, and explicitly distinguishes the curves from direct field observations.
- Offline historical pack: **HASHED AND ACTIVE** — six browser artifacts totaling 1,151,343 source bytes have path, byte-count, SHA-256, media-type, and truth-state records. Release validation re-hashes every file; the Record scene exposes the local pack inventory and correctly states that the browser itself performs structural checks rather than independent hashing.
- Measured groundwater baseline: **ORIGINAL API PAGES VERIFIED** — the current USGS field-measurements OGC endpoint returned 19,696 approved-or-qualified discrete parameter-72019 readings at 3,168 locations inside the TVGWFM footprint for 1986–2015. Two original GeoJSON pages totaling 22,544,359 bytes are preserved on the T drive with SHA-256 receipts. They remain separate from simulated-equivalent outputs until datum-aware cell matching is specified and tested.
- Measured comparison overlay: **OBSERVED DISTRIBUTION ACTIVE WITH BOUNDARY** — 19,619 numeric readings form 30 annual depth-distribution rows; 77 provider-null values are counted and excluded. Water → Compare reveals the nearest annual median, reading count, and changing location count while stating that depth below land surface is not datum-matched modeled head.
- Well metadata: **ORIGINAL API PAGES VERIFIED** — all 3,168 measured locations have provider elevations; 2,920 use the model's NAVD88 vertical datum and 248 use NGVD29. Thirty-two original monitoring-location GeoJSON pages totaling 6,905,294 bytes are preserved and re-hashed. NGVD29 records remain excluded until an explicit vertical transformation is implemented.
- Mapped well markers: **OBSERVED SCREENING LAYER ACTIVE** — 2,849 NAVD88 wells covering 19,117 numeric readings map to active TVGWFM cells. The browser loads a 34,188-byte float32 point pack and renders the markers only under Water → Compare. The layer does not assign well screens to model layers and does not claim validation residuals.
- Eastern Snake Plain: **SOURCE LOCATED, NOT ACQUIRED** — IDWR publishes ESPAM model files separately. The simulator will keep ESPAM and TVGWFM as distinct calibrated domains joined only through a documented coupling seam.

## Phase 3 regional terrain and dam increment

- USGS 3DEP originals: **ORIGINAL BYTES AND FORMAT VERIFIED** — six newest 1-arc-second GeoTIFF tiles from the National Map products query total 316,921,023 bytes. All six provider byte counts, local SHA-256 hashes, float32 TIFF decoding, NAD83 horizontal metadata and NAVD88-meter vertical contract pass. Originals remain on the T drive and are excluded from the browser bundle.
- Regional terrain mesh: **OBSERVED SURFACE ACTIVE** — 15,251 float32 elevations sampled from the six verified tiles cover 118°W–115°W and 43°N–45°N. Source values span 519.753–3,120.670 meters NAVD88; the renderer applies a documented visual scale while preserving source meters in the pack. Reconstructed terrain is now only dim outer context beyond the verified region.
- Aquifer geometry: **SIX SOURCE SURFACES ACTIVE** — the published TVGWFM DIS source's six 64 × 65 bottom arrays and IDOMAIN values are packed in layer-row-column order and rendered as translucent subsurface surfaces. The 24,960 bottom values retain feet NAVD88 and every layer retains 1,861 active cells. These are model discretization geometry, not borehole/core observations; independent field evidence remains a separate constraint and validation layer.
- USACE regional dams: **ORIGINAL RESPONSE AND NORMALIZED TABLE VERIFIED** — 193 NID records fall inside the six-tile region and 11 list hydroelectric generation among their purposes. One record without NIDID and three additional records sharing an NIDID are retained under distinct Corps OBJECTIDs. The app renders all dams in water-facing scenes and the 11 hydroelectric-purpose candidates in Energy.
- Dam connectivity boundary: **UNRESOLVED** — bounding-box inclusion does not prove that a dam feeds Treasure Valley. A directed USGS hydrography/catchment graph must support each upstream classification before the simulator labels it supply-connected.
- Dam-energy boundary: **UNMATCHED** — NID purpose does not establish generator capacity or electrical connection. EIA plant/generator matching and topology evidence remain required.
- Historical/offline design: **SPECIFIED** — `docs/HISTORICAL_TABLE_PLAN.md` defines the source, terrain, geology, aquifer, water, dam, energy, climate, pollutant, scenario, risk, archive, education and AI tables plus the required charts and relationship matrices. Live APIs are acquisition/refresh paths, not required historical-runtime dependencies.
- Offline earth pack v6: **HASHED AND ACTIVE** — 15 local artifacts totaling 1,380,208 source bytes include water-model history, measured-well markers, regional terrain, regional dam points, six aquifer-bottom arrays and IDOMAIN. Immutable earlier manifests remain preserved.
- Esri credential discovery: **REGISTER LOCATED, COMPLETE KEY NOT PRESENT** — the connected Drive API directory confirms an active U of Idaho ArcGIS developer item and privileges, but the stored key field is deliberately truncated and says the full key is in email. The simulator will not use that prefix or place a credential in browser JavaScript; activation remains blocked until a complete authorized value is available to the local proxy/desktop secret store.
- Distribution budget: **PHASE 3 CEILING** — retained browser source maps keep programming inspectable. The development distribution ceiling is 6 MiB; raw GeoTIFF and original dam responses are not copied to `dist/`.

Open blockers remain visible until resolved.
