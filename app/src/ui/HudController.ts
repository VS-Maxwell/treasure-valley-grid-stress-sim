import { SCENE_CONTENT } from "../simulation/sceneContent";
import type { GridCore } from "../data/gridTypes";
import { nearestHeadSlice } from "../data/loadTvgwfmHeads";
import { nearestBudgetRow } from "../data/loadTvgwfmTimeseries";
import { nearestMeasuredYear } from "../data/loadMeasuredGroundwater";
import type { MeasuredGroundwater } from "../data/measuredGroundwater";
import type { OfflinePackManifest } from "../data/offlinePack";
import type { TvgwfmHeads } from "../data/tvgwfmHeads";
import type { TvgwfmTimeseries } from "../data/tvgwfmTimeseries";
import type { RendererMetrics } from "../render/RendererAdapter";
import type { SceneId, SimulationState } from "../contracts";
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
  readonly #actions: HudActions;
  readonly #app = required<HTMLElement>("#app");
  readonly #loading = required<HTMLElement>("#loading");
  readonly #loadingDetail = required<HTMLElement>("#loading-detail");
  readonly #rendererState = required<HTMLElement>("#renderer-state");
  readonly #corridorCount = required<HTMLElement>("#corridor-count");
  readonly #fps = required<HTMLElement>("#fps-value");
  readonly #truth = required<HTMLElement>("#truth-state");
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

  constructor(
    store: SimulationStore,
    grid: GridCore,
    tvgwfmHeads: TvgwfmHeads,
    tvgwfmTimeseries: TvgwfmTimeseries,
    measuredGroundwater: MeasuredGroundwater,
    offlinePack: OfflinePackManifest,
    actions: HudActions,
  ) {
    this.#store = store;
    this.#grid = grid;
    this.#tvgwfmHeads = tvgwfmHeads;
    this.#tvgwfmTimeseries = tvgwfmTimeseries;
    this.#measuredGroundwater = measuredGroundwater;
    this.#offlinePack = offlinePack;
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
    this.#renderContext(state.scene, state.year, state.compare);
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

  showFatal(message: string): void {
    this.#app.dataset.renderer = "failed";
    this.#fatal.hidden = false;
    this.#fatal.textContent = message;
    this.#loading.classList.add("ready");
  }

  #renderContext(scene: SceneId, year: number, compare: boolean): void {
    const content = SCENE_CONTENT[scene];
    const selectedHeadSlice =
      scene === "water"
        ? this.#tvgwfmHeads.manifest.slices[
            nearestHeadSlice(this.#tvgwfmHeads.manifest, year)
          ]
        : undefined;
    this.#contextEyebrow.textContent = content.eyebrow;
    this.#contextTitle.textContent = content.title;
    this.#contextCopy.textContent = selectedHeadSlice
      ? `${content.copy} Displayed head slice: ${selectedHeadSlice.year}.`
      : content.copy;
    const metrics = selectedHeadSlice
      ? [
          ...content.metrics,
          { value: String(selectedHeadSlice.year), label: "head slice" },
        ]
      : content.metrics;
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
    } else if (scene === "record") {
      this.#renderOfflinePack();
    } else {
      this.#contextChart.hidden = true;
      this.#contextChart.replaceChildren();
    }
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
    this.#drawerTitle.textContent =
      "Receipt-backed geometry, reconstructed surface";
    this.#drawerContent.replaceChildren(
      this.#heading("Grid source"),
      this.#paragraph(this.#grid.source),
      this.#code(this.#grid.source_sha256),
      this.#heading("Representation boundary"),
      this.#paragraph(
        "244 corridors and 94 substations are visible geographic features. The scientific screening graph separately contains 94 buses and 156 usable branches; the interactive solver has 12 selected buses.",
      ),
      this.#heading("Terrain truth state"),
      this.#paragraph(
        "The broad terrain remains a reconstructed visual preview. The blue Treasure Valley footprint is an ingested transform of the CC0 USGS TVGWFM grid: 6 layers, 64 rows, 65 columns, and 4,055 active top cells.",
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
