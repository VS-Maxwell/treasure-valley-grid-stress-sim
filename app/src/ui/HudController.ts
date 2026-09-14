import { SCENE_CONTENT } from "../simulation/sceneContent";
import { ENERGY_SCENARIOS } from "../data/energyScreening";
import type { EnergyScreeningModel } from "../data/energyScreening";
import type { EspamGrid } from "../data/espamGrid";
import type { EspamHeads } from "../data/espamHeads";
import { nearestEspamHeadSlice } from "../data/loadEspamHeads";
import type { GridCore } from "../data/gridTypes";
import { nearestHeadSlice } from "../data/loadTvgwfmHeads";
import { nearestBudgetRow } from "../data/loadTvgwfmTimeseries";
import { nearestMeasuredYear } from "../data/loadMeasuredGroundwater";
import type { MeasuredGroundwater } from "../data/measuredGroundwater";
import type { OfflinePackManifest } from "../data/offlinePack";
import type { RegionalTerrain } from "../data/regionalTerrain";
import type { RegionalDams } from "../data/regionalDams";
import type { TvgwfmBottoms } from "../data/tvgwfmBottoms";
import type { TvgwfmHeads } from "../data/tvgwfmHeads";
import type { TvgwfmTimeseries } from "../data/tvgwfmTimeseries";
import type { RendererMetrics } from "../render/RendererAdapter";
import type { EsriGatewayState } from "../services/esriGateway";
import type { EnergyScenario, SceneId, SimulationState } from "../contracts";
import type { SimulationStore } from "../simulation/SimulationStore";

export interface HudActions {
  readonly explore: () => void;
  readonly follow: () => void;
  readonly compare: () => void;
  readonly stress: () => void;
  readonly inspect: () => void;
  readonly ask: () => void;
}

function required<T extends HTMLElement>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Required UI element is missing: ${selector}`);
  return element;
}

function formatYear(year: number): string {
  if (year < 0) return `${Math.abs(year).toLocaleString()} BCE`;
  return `${year.toLocaleString()} CE`;
}

function timeKind(year: number): string {
  if (year < 1800) return "Reconstructed deep time";
  if (year <= 2026) return "Observed / ingested history";
  return "Modeled climate future";
}

export class HudController {
  readonly #store: SimulationStore;
  readonly #grid: GridCore;
  readonly #tvgwfmHeads: TvgwfmHeads;
  readonly #tvgwfmTimeseries: TvgwfmTimeseries;
  readonly #measuredGroundwater: MeasuredGroundwater;
  readonly #offlinePack: OfflinePackManifest;
  readonly #regionalTerrain: RegionalTerrain | null;
  readonly #terrainLoadError: string | null;
  readonly #regionalDams: RegionalDams | null;
  readonly #damLoadError: string | null;
  readonly #tvgwfmBottoms: TvgwfmBottoms | null;
  readonly #bottomLoadError: string | null;
  readonly #espamGrid: EspamGrid | null;
  readonly #espamLoadError: string | null;
  readonly #espamHeads: EspamHeads | null;
  readonly #espamHeadLoadError: string | null;
  readonly #energyScreening: EnergyScreeningModel;
  readonly #actions: HudActions;
  readonly #app = required<HTMLElement>("#app");
  readonly #loading = required<HTMLElement>("#loading");
  readonly #loadingDetail = required<HTMLElement>("#loading-detail");
  readonly #rendererState = required<HTMLElement>("#renderer-state");
  readonly #corridorCount = required<HTMLElement>("#corridor-count");
  readonly #fps = required<HTMLElement>("#fps-value");
  readonly #truth = required<HTMLElement>("#truth-state");
  readonly #providerState = required<HTMLElement>("#provider-state");
  readonly #mapAttribution = required<HTMLElement>("#map-attribution");
  readonly #yearRange = required<HTMLInputElement>("#year-range");
  readonly #yearLabel = required<HTMLElement>("#year-label");
  readonly #timeKind = required<HTMLElement>("#time-kind");
  readonly #timePlay = required<HTMLButtonElement>("#time-play");
  readonly #contextEyebrow = required<HTMLElement>("#context-eyebrow");
  readonly #contextTitle = required<HTMLElement>("#context-title");
  readonly #contextCopy = required<HTMLElement>("#context-copy");
  readonly #contextMetrics = required<HTMLElement>("#context-metrics");
  readonly #contextChart = required<HTMLElement>("#context-chart");
  readonly #drawer = required<HTMLElement>("#drawer");
  readonly #drawerEyebrow = required<HTMLElement>("#drawer-eyebrow");
  readonly #drawerTitle = required<HTMLElement>("#drawer-title");
  readonly #drawerContent = required<HTMLElement>("#drawer-content");
  readonly #comparison = required<HTMLElement>("#comparison");
  readonly #fatal = required<HTMLElement>("#fatal");
  #esriGateway: EsriGatewayState | null = null;
  #esriImageryActive = false;

  constructor(
    store: SimulationStore,
    grid: GridCore,
    tvgwfmHeads: TvgwfmHeads,
    tvgwfmTimeseries: TvgwfmTimeseries,
    measuredGroundwater: MeasuredGroundwater,
    offlinePack: OfflinePackManifest,
    regionalTerrain: RegionalTerrain | null,
    terrainLoadError: string | null,
    regionalDams: RegionalDams | null,
    damLoadError: string | null,
    tvgwfmBottoms: TvgwfmBottoms | null,
    bottomLoadError: string | null,
    espamGrid: EspamGrid | null,
    espamLoadError: string | null,
    espamHeads: EspamHeads | null,
    espamHeadLoadError: string | null,
    energyScreening: EnergyScreeningModel,
    actions: HudActions,
  ) {
    this.#store = store;
    this.#grid = grid;
    this.#tvgwfmHeads = tvgwfmHeads;
    this.#tvgwfmTimeseries = tvgwfmTimeseries;
    this.#measuredGroundwater = measuredGroundwater;
    this.#offlinePack = offlinePack;
    this.#regionalTerrain = regionalTerrain;
    this.#terrainLoadError = terrainLoadError;
    this.#regionalDams = regionalDams;
    this.#damLoadError = damLoadError;
    this.#tvgwfmBottoms = tvgwfmBottoms;
    this.#bottomLoadError = bottomLoadError;
    this.#espamGrid = espamGrid;
    this.#espamLoadError = espamLoadError;
    this.#espamHeads = espamHeads;
    this.#espamHeadLoadError = espamHeadLoadError;
    this.#energyScreening = energyScreening;
    this.#actions = actions;
  }

  connect(): void {
    document
      .querySelectorAll<HTMLButtonElement>("[data-scene]")
      .forEach((button) => {
        button.addEventListener("click", () =>
          this.#store.selectScene(button.dataset.scene as SceneId),
        );
      });
    document
      .querySelectorAll<HTMLButtonElement>("[data-action]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          const action = button.dataset.action as keyof HudActions;
          this.#actions[action]();
        });
      });
    this.#yearRange.addEventListener("input", () =>
      this.#store.setYear(Number(this.#yearRange.value)),
    );
    this.#timePlay.addEventListener("click", () => this.#store.togglePlaying());
    required<HTMLButtonElement>("#drawer-close").addEventListener("click", () =>
      this.#store.closeDrawer(),
    );
  }

  render(state: SimulationState): void {
    document
      .querySelectorAll<HTMLButtonElement>("[data-scene]")
      .forEach((button) => {
        button.setAttribute(
          "aria-selected",
          String(button.dataset.scene === state.scene),
        );
      });
    document
      .querySelectorAll<HTMLButtonElement>("[data-action='compare']")
      .forEach((button) => {
        button.dataset.active = String(state.compare);
      });
    this.#truth.textContent = state.truthState.toUpperCase();
    this.#yearRange.value = String(state.year);
    this.#yearLabel.textContent = formatYear(state.year);
    this.#timeKind.textContent = timeKind(state.year);
    this.#timePlay.textContent = state.playing ? "Ⅱ" : "▶";
    this.#timePlay.setAttribute(
      "aria-label",
      state.playing ? "Pause timeline" : "Play timeline",
    );
    this.#comparison.hidden = !state.compare;
    this.#renderContext(
      state.scene,
      state.year,
      state.compare,
      state.energyScenario,
    );
    this.#renderDrawer(state);
  }

  setLoadingDetail(message: string): void {
    this.#loadingDetail.textContent = message;
  }

  setReady(renderer: "three-webgl" | "canvas-fallback"): void {
    this.#app.dataset.renderer = renderer;
    this.#rendererState.textContent =
      renderer === "three-webgl" ? "3D cockpit" : "Degraded Canvas mode";
    this.#corridorCount.textContent = String(this.#grid.trans.features.length);
    this.#loading.classList.add("ready");
    this.#loading.setAttribute("aria-hidden", "true");
  }

  setMetrics(metrics: RendererMetrics): void {
    this.#fps.textContent = metrics.fps > 0 ? String(metrics.fps) : "—";
    this.#rendererState.textContent = `${this.#app.dataset.renderer === "three-webgl" ? "3D cockpit" : "Canvas fallback"} · ${metrics.drawCalls} calls`;
  }

  setEsriGateway(state: EsriGatewayState, imageryActive: boolean): void {
    this.#esriGateway = state;
    this.#esriImageryActive = imageryActive;
    this.#providerState.dataset.state = state.connected ? "ready" : "offline";
    this.#providerState.textContent = imageryActive
      ? "ESRI IMAGERY · LIVE"
      : state.connected
        ? "ESRI SERVICES · READY"
        : "ESRI OPTIONAL · OFFLINE";
    this.#providerState.title = state.connected
      ? `${state.basemapStyles ? "Basemap style verified" : "Basemap style unavailable"}; ${state.geocoding ? "geocoding verified" : "geocoding unavailable"}; ${state.detail}`
      : state.detail;
    this.#mapAttribution.hidden = !imageryActive;
    this.#mapAttribution.textContent = imageryActive
      ? (state.attribution ?? "Powered by Esri")
      : "";
    if (this.#store.state.drawer !== "closed")
      this.#renderDrawer(this.#store.state);
  }

  showFatal(message: string): void {
    this.#app.dataset.renderer = "failed";
    this.#fatal.hidden = false;
    this.#fatal.textContent = message;
    this.#loading.classList.add("ready");
  }

  #renderContext(
    scene: SceneId,
    year: number,
    compare: boolean,
    energyScenario: EnergyScenario,
  ): void {
    const content = SCENE_CONTENT[scene];
    const selectedHeadSlice =
      scene === "water"
        ? this.#tvgwfmHeads.manifest.slices[
            nearestHeadSlice(this.#tvgwfmHeads.manifest, year)
          ]
        : undefined;
    const selectedEspamSlice =
      scene === "water" && this.#espamHeads
        ? this.#espamHeads.manifest.slices[
            nearestEspamHeadSlice(this.#espamHeads.manifest, year)
          ]
        : undefined;
    this.#contextEyebrow.textContent = content.eyebrow;
    this.#contextTitle.textContent = content.title;
    this.#contextCopy.textContent = selectedHeadSlice
      ? `${content.copy} Displayed head slice: ${selectedHeadSlice.year}.`
      : content.copy;
    let metrics = selectedHeadSlice
      ? [
          ...content.metrics,
          { value: String(selectedHeadSlice.year), label: "head slice" },
        ]
      : content.metrics;
    if (scene === "water" && compare)
      metrics = [
        ...metrics,
        { value: "2,849", label: "mapped observed wells" },
      ];
    if (scene === "water" && this.#tvgwfmBottoms)
      metrics = [
        ...metrics,
        {
          value: String(this.#tvgwfmBottoms.manifest.layout.layers),
          label: "bottom surfaces",
        },
      ];
    if (scene === "water" && selectedEspamSlice)
      metrics = [
        ...metrics,
        { value: "11,236", label: "ESPAM active cells" },
        { value: String(selectedEspamSlice.year), label: "ESPAM head slice" },
      ];
    if (scene === "energy" && this.#regionalDams)
      metrics = [
        ...metrics,
        {
          value: this.#regionalDams.manifest.dam_count.toLocaleString(),
          label: "regional dam records",
        },
        {
          value:
            this.#regionalDams.manifest.hydroelectric_purpose_count.toLocaleString(),
          label: "hydroelectric-purpose dams",
        },
      ];
    this.#contextMetrics.replaceChildren(
      ...metrics.map((metric) => {
        const card = document.createElement("div");
        card.className = "metric";
        const value = document.createElement("b");
        value.textContent = metric.value;
        const label = document.createElement("span");
        label.textContent = metric.label;
        card.append(value, label);
        return card;
      }),
    );
    if (scene === "water") {
      this.#renderWaterChart(
        nearestBudgetRow(this.#tvgwfmTimeseries.budget.rows, year),
        compare,
        year,
      );
    } else if (scene === "energy") {
      this.#renderEnergyControl(energyScenario);
    } else if (scene === "record") {
      this.#renderOfflinePack();
    } else {
      this.#contextChart.hidden = true;
      this.#contextChart.replaceChildren();
    }
  }

  #renderEnergyControl(scenario: EnergyScenario): void {
    const labels: Record<EnergyScenario, string> = {
      base: "Baseline",
      dc25: "Data centers +25%",
      dc50: "Data centers +50%",
      all25: "All demand +25%",
      all50: "All demand +50%",
      drought: "Drought derating",
      n1: "N-1 contingency envelope",
    };
    const label = document.createElement("label");
    label.className = "energy-scenario-label";
    label.htmlFor = "energy-scenario";
    label.textContent = "Grid screening scenario";
    const select = document.createElement("select");
    select.id = "energy-scenario";
    select.setAttribute("aria-label", "Grid screening scenario");
    select.replaceChildren(
      ...ENERGY_SCENARIOS.map((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = labels[value];
        option.selected = value === scenario;
        return option;
      }),
    );
    select.addEventListener("change", () =>
      this.#store.setEnergyScenario(select.value as EnergyScenario),
    );
    const summary = this.#energyScreening.scenario_summaries[scenario];
    const caption = document.createElement("p");
    caption.className = "context-chart-caption";
    caption.textContent = `${labels[scenario]} · ${summary.branches_at_or_above_80_pct} branches ≥80% · ${summary.branches_at_or_above_100_pct} branches ≥100% · ${summary.maximum_loading_pct.toFixed(1)}% maximum`;
    const legend = document.createElement("div");
    legend.className = "energy-legend";
    const bands = [
      ["<50", "#54b9ff"],
      ["50–79", "#63e5c5"],
      ["80–99", "#ffc247"],
      ["100–149", "#ff654b"],
      ["150%+", "#ff274f"],
    ] as const;
    legend.replaceChildren(
      ...bands.map(([text, color]) => {
        const item = document.createElement("span");
        const swatch = document.createElement("i");
        swatch.style.backgroundColor = color;
        item.append(swatch, document.createTextNode(text));
        return item;
      }),
    );
    const boundary = document.createElement("p");
    boundary.className = "context-chart-boundary";
    boundary.textContent =
      "Calibrated DC screening · assumed ratings · not operational data";
    this.#contextChart.replaceChildren(
      label,
      select,
      caption,
      legend,
      boundary,
    );
    this.#contextChart.hidden = false;
  }

  #renderOfflinePack(): void {
    const title = document.createElement("p");
    title.className = "context-chart-caption";
    title.textContent = `${this.#offlinePack.artifact_count} local artifacts · ${(this.#offlinePack.total_bytes / 1_000_000).toFixed(2)} MB`;
    const list = document.createElement("ul");
    list.className = "offline-pack-list";
    list.replaceChildren(
      ...this.#offlinePack.artifacts.map((artifact) => {
        const item = document.createElement("li");
        item.textContent = `${artifact.id} · ${(artifact.bytes / 1_000).toFixed(1)} KB`;
        return item;
      }),
    );
    const boundary = document.createElement("p");
    boundary.className = "context-chart-boundary";
    boundary.textContent = "No runtime network · hashes checked at build gate";
    this.#contextChart.replaceChildren(title, list, boundary);
    this.#contextChart.hidden = false;
  }

  #renderWaterChart(
    selectedIndex: number,
    showMeasured: boolean,
    year: number,
  ): void {
    const rows = this.#tvgwfmTimeseries.budget.rows;
    const selected = rows[selectedIndex];
    if (!selected) return;
    const width = 300;
    const height = 72;
    const inset = 4;
    const values = rows.flatMap((row) => [
      row.rate_in_ft3_per_day,
      row.rate_out_ft3_per_day,
    ]);
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    const range = Math.max(maximum - minimum, 1);
    const points = (key: "rate_in_ft3_per_day" | "rate_out_ft3_per_day") =>
      rows
        .map((row, index) => {
          const x = inset + (index / (rows.length - 1)) * (width - inset * 2);
          const y =
            height -
            inset -
            ((row[key] - minimum) / range) * (height - inset * 2);
          return `${x.toFixed(2)},${y.toFixed(2)}`;
        })
        .join(" ");
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("role", "img");
    svg.setAttribute(
      "aria-label",
      `Monthly modeled water budget. Selected ${selected.period_end_date}: inflow ${this.#formatFlow(selected.rate_in_ft3_per_day)} million, outflow ${this.#formatFlow(selected.rate_out_ft3_per_day)} million cubic feet per day.`,
    );
    const inflow = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "polyline",
    );
    inflow.setAttribute("class", "budget-inflow");
    inflow.setAttribute("points", points("rate_in_ft3_per_day"));
    const outflow = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "polyline",
    );
    outflow.setAttribute("class", "budget-outflow");
    outflow.setAttribute("points", points("rate_out_ft3_per_day"));
    const marker = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "line",
    );
    const markerX =
      inset + (selectedIndex / (rows.length - 1)) * (width - inset * 2);
    marker.setAttribute("class", "budget-marker");
    marker.setAttribute("x1", String(markerX));
    marker.setAttribute("x2", String(markerX));
    marker.setAttribute("y1", "0");
    marker.setAttribute("y2", String(height));
    svg.append(inflow, outflow, marker);

    const caption = document.createElement("p");
    caption.className = "context-chart-caption";
    caption.textContent = `${selected.period_end_date} · ${this.#formatFlow(selected.rate_in_ft3_per_day)}M in · ${this.#formatFlow(selected.rate_out_ft3_per_day)}M out ft³/day`;
    const boundary = document.createElement("p");
    boundary.className = "context-chart-boundary";
    boundary.textContent =
      "Reproduced MODFLOW output · not direct field observations";
    const content: Node[] = [svg, caption, boundary];
    if (showMeasured) {
      const selectedMeasured =
        this.#measuredGroundwater.years[
          nearestMeasuredYear(this.#measuredGroundwater, year)
        ];
      if (selectedMeasured) {
        const measured = document.createElement("p");
        measured.className = "measured-comparison";
        measured.textContent = `${selectedMeasured.year} measured depth distribution · median ${selectedMeasured.median_depth_ft.toFixed(1)} ft below land · ${selectedMeasured.measurement_count.toLocaleString()} readings at ${selectedMeasured.monitoring_location_count.toLocaleString()} locations`;
        const measuredBoundary = document.createElement("p");
        measuredBoundary.className = "context-chart-boundary";
        measuredBoundary.textContent =
          "Observed distribution only · not datum-matched to modeled head";
        content.push(measured, measuredBoundary);
      }
    }
    this.#contextChart.replaceChildren(...content);
    this.#contextChart.hidden = false;
  }

  #formatFlow(value: number): string {
    return (value / 1_000_000).toFixed(1);
  }

  #renderDrawer(state: SimulationState): void {
    const closed = state.drawer === "closed";
    this.#drawer.hidden = closed;
    this.#drawer.setAttribute("aria-hidden", String(closed));
    if (closed) return;
    if (state.drawer === "ask") {
      this.#drawerEyebrow.textContent = "ASK · OFFLINE BOUNDARY";
      this.#drawerTitle.textContent = "The local guide is not connected yet";
      this.#drawerContent.replaceChildren(
        this.#paragraph(
          "The Ask action is wired into the shared state, but model inference remains disabled until the Phase 8 allow-list, citation, authority, and leakage tests pass.",
        ),
        this.#heading("What you can inspect now"),
        this.#paragraph(
          "Use the seven system tabs, time control, comparison, and evidence view. None of those controls can modify accepted scientific data.",
        ),
      );
      return;
    }
    this.#drawerEyebrow.textContent = "EVIDENCE · CURRENT BUILD";
    this.#drawerTitle.textContent = this.#regionalTerrain
      ? "Receipt-backed geometry and Snake Plain USGS terrain"
      : "Receipt-backed geometry, reconstructed surface";
    this.#drawerContent.replaceChildren(
      this.#heading("Grid source"),
      this.#paragraph(this.#grid.source),
      this.#code(this.#grid.source_sha256),
      this.#heading("Representation boundary"),
      this.#paragraph(
        `244 corridors and 94 substations are visible geographic features. All ${this.#energyScreening.counts.branches} preserved DC-screening branches now respond to seven scenarios. Exactly ${this.#energyScreening.counts.branches_with_unique_endpoint_labels} branch endpoints resolve through unique labels; ${this.#energyScreening.counts.branches_with_ambiguous_endpoint_labels} retain ambiguous legacy labels rather than receiving invented bus identities.`,
      ),
      this.#heading("Terrain truth state"),
      this.#paragraph(
        this.#regionalTerrain
          ? `Observed USGS 3DEP terrain is active across the full Snake Plain overview envelope from 119°W to 111°W and 42°N to 46°N: ${this.#regionalTerrain.manifest.mesh.vertex_count.toLocaleString()} browser vertices, ${this.#regionalTerrain.manifest.statistics.minimum_meters.toLocaleString()}–${this.#regionalTerrain.manifest.statistics.maximum_meters.toLocaleString()} meters NAVD88. This terrain context does not expand the calibrated TVGWFM aquifer domain; ESPAM and framework-only areas remain separate evidence layers.`
          : `The broad terrain remains a reconstructed visual preview. USGS 3DEP failed to load${this.#terrainLoadError ? `: ${this.#terrainLoadError}` : "."}`,
      ),
      this.#heading("Esri online overlay"),
      this.#paragraph(
        this.#esriGateway?.connected
          ? `${this.#esriGateway.basemapStyles ? "The EDU-authorized basemap style" : "The basemap style"} and ${this.#esriGateway.geocoding ? "geocoding capability are verified" : "geocoding is unavailable"} through a loopback-only gateway. ${this.#esriImageryActive ? "Live public Esri World Imagery is draped on the observed USGS terrain." : "The live image did not load, so the observed USGS elevation-color surface remains visible."} The credential is never sent to browser code, and the historical simulator remains usable from local packs with the gateway off.`
          : "The optional localhost Esri gateway is offline. The simulator is using its receipt-backed local terrain and data packs without an online-service dependency.",
      ),
      this.#heading("Aquifer topology"),
      this.#paragraph(
        this.#tvgwfmBottoms
          ? `All ${this.#tvgwfmBottoms.manifest.layout.layers} published TVGWFM model-bottom arrays are loaded as source-native ${this.#tvgwfmBottoms.manifest.layout.rows} × ${this.#tvgwfmBottoms.manifest.layout.columns} surfaces in feet ${this.#tvgwfmBottoms.manifest.layout.vertical_datum}. These are model discretization geometry, not core or borehole observations; field evidence will test and interpret them without being silently substituted.`
          : `The six TVGWFM model-bottom surfaces are unavailable${this.#bottomLoadError ? `: ${this.#bottomLoadError}` : "."}`,
      ),
      this.#heading("Eastern Snake Plain model"),
      this.#paragraph(
        this.#espamGrid && this.#espamHeads
          ? `The official ESPAM 2.2 active domain is loaded independently: ${this.#espamGrid.manifest.layout.active_cells.toLocaleString()} active cells in a one-layer 104 × 209 MODFLOW-USG grid with ${this.#espamGrid.manifest.layout.stress_periods} stress periods and 5,280-foot cells. The current IDWR model-grid service is cross-checked against the preserved final-calibration archive. A timeline-driven 4D surface renders 39 archived September head slices from 1980–2018 (${this.#espamHeads.manifest.statistics.minimum_feet.toLocaleString()}–${this.#espamHeads.manifest.statistics.maximum_feet.toLocaleString()} feet). Those values are archived modeled output, not an independently reproduced run, and they are not silently merged with the six-layer TVGWFM.`
          : this.#espamGrid
            ? `The official ESPAM 2.2 active grid is loaded, but the archived head surface is unavailable${this.#espamHeadLoadError ? `: ${this.#espamHeadLoadError}` : "."}`
            : `The ESPAM 2.2 active grid is unavailable${this.#espamLoadError ? `: ${this.#espamLoadError}` : "."}`,
      ),
      this.#heading("Dam and hydropower inventory"),
      this.#paragraph(
        this.#regionalDams
          ? `${this.#regionalDams.manifest.dam_count.toLocaleString()} current USACE NID records are loaded in the six-tile region; ${this.#regionalDams.manifest.hydroelectric_purpose_count.toLocaleString()} list hydroelectric generation among their purposes. All remain connectivity-unresolved until the upstream watershed graph is receipted; generation capacity and electrical links require EIA matching.`
          : `The USACE dam layer is unavailable${this.#damLoadError ? `: ${this.#damLoadError}` : "."}`,
      ),
      this.#heading("USGS water-model source"),
      this.#paragraph(
        "DOI 10.5066/P9U6OOPH · original model.zip bytes and upstream MD5 verified · local SHA-256 bdefb11eaf7b75ab63dc0b23b0de4f65fe9d68798c0ff229420322bf8abb0dd6",
      ),
      this.#heading("Baseline reproduction"),
      this.#paragraph(
        "MODFLOW 6.1.1 completed all 361 stress periods normally. Final budget discrepancy rounds to 0.00%; four observation tables match at published precision; maximum head difference versus the archived output is 3.14e-11 feet. New-scenario suitability still requires domain review.",
      ),
      this.#heading("Release boundary"),
      this.#paragraph(
        "RAVEN values, climate futures, and protected archives remain blocked until their own input, authority, reproducibility, and acceptance receipts exist.",
      ),
    );
  }

  #heading(text: string): HTMLHeadingElement {
    const element = document.createElement("h3");
    element.textContent = text;
    return element;
  }

  #paragraph(text: string): HTMLParagraphElement {
    const element = document.createElement("p");
    element.textContent = text;
    return element;
  }

  #code(text: string): HTMLElement {
    const paragraph = document.createElement("p");
    const code = document.createElement("code");
    code.textContent = text;
    paragraph.append(code);
    return paragraph;
  }
}
