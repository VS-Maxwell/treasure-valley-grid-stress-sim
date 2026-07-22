# Treasure Valley Earth-State Watchdog

An interactive public-interest screening tool for exploring how grid topology, large-load growth,
heat, drought, water demand, land conversion, and infrastructure decisions interact across the
Treasure Valley.

**Live demo:** once GitHub Pages is enabled, this loads at the repository's Pages URL
(`https://<user>.github.io/<repo>/`). It is a single self-contained HTML file — just open `index.html`.

## What it shows
- Real **3DEP terrain** of the Treasure Valley (MapLibre GL + deck.gl).
- The **transmission network recolored green → red** by per-line loading, from a pandapower DC
  screening model, across 7 scenarios (base, named-DC +25/+50%, all-load +25/+50%, N-1, drought).
- **Data-center loads** (Meta/Kuna ~130 MW, Micron/Boise ~350 MW) as columns scaled by MW.
- **USGS NAIP aerial imagery** (0.6 m, public domain) draped on the terrain.
- An **on-device AI panel** (WebLLM, runs in your browser via WebGPU — no server, no key).
- Animated power-flow, a cinematic fly-through tour, and a glassy heads-up display.

## Data & honesty
This is a **screening tool on public data with assumed line ratings** — loadings are relative stress
indicators for prioritization, **not validated thermal limits**. Each layer carries a truth-state badge
in the UI. Sources: EIA-930/860, HIFLD topology, U.S. Census, USGS 3DEP + NAIP, pandapower DC power flow.
Companion white paper documents every figure.

The app distinguishes the larger 94-bus/156-line screening representation from the 12 selected buses
used by the interactive solver. Transformers are idealized because authoritative impedance and tap
parameters are not embedded. RAVEN-style probabilities, LOLE, and EUE remain unvalidated scenario
assumptions until linked input/output receipts are recovered. Visible infrastructure is not necessarily
electrically modeled.

Absence of Tribal representation in a public dataset is treated as a documentary or governance gap,
not as evidence of absent Tribal presence, activity, knowledge, or rights.

## Tech / licensing
Open stack — MapLibre GL JS, deck.gl, OpenFreeMap (ODbL), AWS Terrarium DEM, USGS NAIP/3DEP
(public domain), Esri World Imagery (public endpoint), and WebLLM. Local refresh credentials belong
only in an ignored `.env`; `.env.example` contains blank placeholders.

Project-owned source code is available under `Apache-2.0 OR MIT`. Third-party software and data
retain their own licenses and terms; see `LICENSE`, `LICENSE-APACHE`, `LICENSE-MIT`, and `NOTICE`.

## Attribution
Van Maxwell · University of Idaho — I-CREWS. Screening model + 3D demonstrator, 2026.
