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

- Overall simulator: **INCOMPLETE / ACTIVE BUILD** — the current default enters the modular 3D cockpit directly; full-plain terrain and both TVGWFM and ESPAM model domains are present, while cross-domain coupling, ESPAM baseline reproduction, climate, RAVEN, local AI, and desktop packaging still have open gates.
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
- Automated toolchain: **PASSED** — format, lint, strict typing, 39 TypeScript tests across 17 files, five Python gateway-security tests, source/registry checks, production build, and distribution scan.
- Distribution: **PASSED WITH SIZE WARNING** — the inspectable development bundle remains below the explicit 8 MiB full-plain ceiling; Three.js is lazy-loaded but its approximately 585 KB minified engine chunk exceeds Vite's 500 KB advisory threshold.
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
- Eastern Snake Plain: **OFFICIAL MODEL, GRID, AND ARCHIVED HEADS INTEGRATED** — IDWR ESPAM 2.2 final-calibration and aquifer-property archives are verified, the official active grid is visible, and 39 archived September head slices from 1980–2018 animate over its exact 11,236 active cells. Independent numerical reproduction remains open. ESPAM and TVGWFM stay distinct and may be joined only through a documented coupling seam.

## Phase 3 regional terrain and dam increment

- USGS 3DEP originals: **FULL-PLAIN SOURCE ENVELOPE VERIFIED** — 32 newest 1-arc-second GeoTIFF tiles from the National Map products query total 1,639,886,219 bytes across 119°W–111°W and 42°N–46°N. Every provider byte count, local SHA-256 hash, float32 TIFF decoding, NAD83 horizontal metadata and NAVD88-meter vertical contract passes. The earlier six-, eight-, and twenty-tile acquisitions remain immutable lineage checkpoints.
- Full-plain terrain mesh: **OBSERVED SURFACE ACTIVE** — 80,601 float32 elevations sampled from the 32 verified tiles cover the scene envelope. Source values span 103.900–3,570.421 meters NAVD88; the renderer applies a documented visual scale while preserving source meters in the pack. This outer surface does not assert aquifer-model coverage.
- ESPAM 2.2 originals: **ORIGINAL BYTES AND FORMAT VERIFIED** — IDWR's final-calibration archive plus published transmissivity and specific-yield packages total 494,832,320 bytes. All three expected byte counts, SHA-256 hashes, ZIP central directories, and member CRCs pass. The final-calibration archive has 320 members; acquisition is not yet numerical reproduction.
- ESPAM 2.2 grid: **OFFICIAL ACTIVE DOMAIN INTEGRATED** — six preserved IDWR GeoJSON pages contain exactly 11,236 active cells, matching the archived IBOUND count. The browser renders 44,944 cell edges over the one-layer 104 × 209, 462-stress-period, 5,280-foot-cell model. It remains distinct from six-layer TVGWFM.
- Aquifer geometry: **SIX SOURCE SURFACES ACTIVE** — the published TVGWFM DIS source's six 64 × 65 bottom arrays and IDOMAIN values are packed in layer-row-column order and rendered as translucent subsurface surfaces. The 24,960 bottom values retain feet NAVD88 and every layer retains 1,861 active cells. These are model discretization geometry, not borehole/core observations; independent field evidence remains a separate constraint and validation layer.
- USACE Snake Plain dams: **FULL-SCENE ORIGINAL RESPONSE AND DIRECTED CLASSIFICATION VERIFIED** — 647 NID records fall inside the 119°W–111°W, 42°N–46°N scene envelope and 55 list hydroelectric generation among their purposes. One record without NIDID and ten additional records sharing an NIDID are retained under distinct Corps OBJECTIDs. The app renders all 647 dams in water-facing scenes and preserves the earlier 193-dam layer as an immutable checkpoint.
- Dam connectivity boundary: **DIRECTED RECEIVING-SYSTEM GRAPH VERIFIED** — USGS-13269000 resolves to NHDPlus COMID 24193082 at the Snake River at Weiser. The preserved NLDI upstream set contains 50,486 unique COMIDs; 50,938 in-set NHDPlusV2 edges route every member to the outlet. Of 647 dams, 348 have a complete hashed COMID path to that outlet, 297 are not in its upstream set, and two retain explicit no-indexed-catchment responses. This is surface-water connectivity to the Weiser outlet, not proof of operational delivery to Treasure Valley.
- EIA hydropower inventory: **FINAL 2025 SOURCE VERIFIED / LINKS PENDING REVIEW** — the 23,622,347-byte final Form EIA-860 archive released September 10, 2026 retains 13 CRC-valid members. Inside the full scene, 190 plants and 335 generator records include 77 hydropower plants and 167 hydro generator records. Nearest-distance and normalized-name evidence produce 41 strong candidates, 11 broader candidates, and three unmatched hydro-purpose dams; all 55 links remain explicitly pending human review.
- EIA regional energy lifecycle: **COMPLETE SOURCE INVENTORY ACTIVE** — all 335 regional generator records at 190 plants are packed and rendered by ten technology classes. Lifecycle remains explicit: 287 operable, 18 proposed, 14 retired, 15 canceled, and one indefinitely postponed. Reported nameplate capacity is not presented as current output, availability, or proof of grid interconnection.
- Dam-energy boundary: **CANDIDATES ONLY** — NID purpose and EIA proximity do not establish identity or electrical connection. Candidate review must accept each dam-to-plant crosswalk; bus/branch topology evidence remains separately required.
- Historical/offline design: **SPECIFIED** — `docs/HISTORICAL_TABLE_PLAN.md` defines the source, terrain, geology, aquifer, water, dam, energy, climate, pollutant, scenario, risk, archive, education and AI tables plus the required charts and relationship matrices. Live APIs are acquisition/refresh paths, not required historical-runtime dependencies.
- Offline earth pack v6: **HASHED AND ACTIVE** — 15 local artifacts totaling 1,380,208 source bytes include water-model history, measured-well markers, regional terrain, regional dam points, six aquifer-bottom arrays and IDOMAIN. Immutable earlier manifests remain preserved.
- Energy screening pack: **EXTRACTED AND INTERACTIVE** — all 94 legacy screening buses and 156 modeled branches are retained with seven scenario loading tables. Every modeled branch joins a visible corridor by exact `line_id`; 75 branches have unique endpoint labels and 81 preserve ambiguous legacy labels rather than receiving invented bus identities. The Energy scene recolors all 156 branches and labels the values calibrated DC screening, not operational utility data.
- Offline earth pack v12: **HASHED CHECKPOINT PRESERVED** — 21 local artifacts totaling 3,660,748 source bytes first promoted the directed receiving-system dam flags; v13 supersedes it without rewriting it.
- Offline earth pack v13: **HASHED CHECKPOINT PRESERVED** — 23 local artifacts totaling 3,663,317 source bytes first added the final-2025 EIA hydropower inventory; v14 supersedes it without rewriting it.
- Offline earth pack v14: **HASHED AND ACTIVE** — 25 local artifacts totaling 3,672,183 source bytes add all 335 final-2025 EIA generator lifecycle points while preserving immutable v13 and all earlier packs. Hydropower identities remain candidate-only and no EIA point is silently joined to a model bus or branch.
- Esri secure adapter: **LOCAL GATEWAY ACTIVE / RELEASE GATED** — the complete authorized EDU credential is stored in the operating-system Secret Service and was validated against Esri basemap-style and geocoding endpoints without entering a URL, browser bundle, repository file, or log. The gateway binds only `127.0.0.1:8767`, exposes fixed allow-listed routes, rejects non-simulator browser origins, and streams a fixed-region public World Imagery export without storing it. The UI distinguishes `ESRI IMAGERY · LIVE`, service-ready, and offline states. Provider terms, quota, and public-origin restrictions remain a release gate; local historical packs remain the runtime baseline.
- Esri browser playtest: **PASSED WITH SCREENSHOT LIMITATION** — the visible Three.js tab reported `ESRI IMAGERY · LIVE`, displayed `Powered by Esri; imagery © Esri and contributors`, retained the 244-corridor/94-bus/156-branch energy controls, and produced no browser warnings or errors. Browser screenshot capture still failed, so accessibility-state evidence is retained and visual-image evidence remains open.
- Distribution budget: **FULL-PLAIN DEVELOPMENT CEILING** — retained browser source maps keep programming inspectable. The explicit development ceiling is 8 MiB after adding the full-plain terrain and ESPAM grid; raw GeoTIFFs, original ESPAM archives, and original API pages are not copied to `dist/`.

Open blockers remain visible until resolved.
