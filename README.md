# Treasure Valley Grid-Stress Simulator (3D)

An interactive 3D web demonstrator of how **data-center load growth and climate stress (drought, heat)**
stress the **Idaho Power transmission grid** in the Treasure Valley. Built for energy-engineering and
I-CREWS (NSF EPSCoR) audiences.

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

## Tech / licensing
Open stack only — MapLibre GL JS, deck.gl, OpenFreeMap (ODbL), AWS Terrarium DEM, USGS NAIP/3DEP
(public domain), Esri World Imagery (public endpoint), WebLLM. **No API keys or secrets are embedded.**

## Attribution
Van Maxwell · University of Idaho — I-CREWS. Screening model + 3D demonstrator, 2026.
