import type { SimulationState } from "../contracts";
import {
  energyLoadingColor,
  type EnergyBranch,
  type EnergyScreeningModel,
} from "../data/energyScreening";
import { measureGridBounds, projectPosition } from "../data/geo";
import { lineParts, type GridCore } from "../data/gridTypes";
import type { RendererAdapter, RendererCallbacks } from "./RendererAdapter";

export class CanvasFallbackRenderer implements RendererAdapter {
  readonly kind = "canvas-fallback" as const;
  readonly #canvas: HTMLCanvasElement;
  readonly #context: CanvasRenderingContext2D;
  readonly #grid: GridCore;
  readonly #branches: ReadonlyMap<string, EnergyBranch>;
  readonly #callbacks: RendererCallbacks;
  #state: SimulationState | null = null;
  #resizeObserver: ResizeObserver | null = null;

  constructor(
    canvas: HTMLCanvasElement,
    grid: GridCore,
    energyScreening: EnergyScreeningModel,
    callbacks: RendererCallbacks,
  ) {
    this.#canvas = canvas;
    const context = canvas.getContext("2d", { alpha: false });
    if (!context) throw new Error("Canvas fallback is unavailable");
    this.#context = context;
    this.#grid = grid;
    this.#branches = new Map(
      energyScreening.branches.map((branch) => [branch.branch_id, branch]),
    );
    this.#callbacks = callbacks;
  }

  mount(): void {
    this.#canvas.hidden = false;
    this.#resizeObserver = new ResizeObserver(() => this.#resize());
    this.#resizeObserver.observe(this.#canvas.parentElement ?? this.#canvas);
    this.#resize();
  }

  start(): void {
    this.#callbacks.onMetrics({ fps: 0, drawCalls: 5, triangles: 0 });
    this.#draw();
  }

  stop(): void {}

  applyState(state: SimulationState): void {
    this.#state = state;
    this.#draw();
  }

  focusHome(): void {
    this.#draw();
  }

  dispose(): void {
    this.#resizeObserver?.disconnect();
    this.#canvas.hidden = true;
  }

  #resize(): void {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    this.#canvas.width = Math.max(
      1,
      Math.round(this.#canvas.clientWidth * ratio),
    );
    this.#canvas.height = Math.max(
      1,
      Math.round(this.#canvas.clientHeight * ratio),
    );
    this.#context.setTransform(ratio, 0, 0, ratio, 0, 0);
    this.#draw();
  }

  #draw(): void {
    const width = this.#canvas.clientWidth;
    const height = this.#canvas.clientHeight;
    if (!width || !height) return;
    const context = this.#context;
    const gradient = context.createRadialGradient(
      width * 0.5,
      height * 0.48,
      20,
      width * 0.5,
      height * 0.48,
      width * 0.7,
    );
    gradient.addColorStop(
      0,
      this.#state?.scene === "risk" ? "#3b1724" : "#16384a",
    );
    gradient.addColorStop(1, "#061019");
    context.fillStyle = gradient;
    context.fillRect(0, 0, width, height);

    const bounds = measureGridBounds(this.#grid);
    const scale = Math.min(width / 250, height / 170) * 0.88;
    const screen = (
      longitude: number,
      latitude: number,
    ): readonly [number, number] => {
      const point = projectPosition([longitude, latitude], bounds);
      return [width / 2 + point.x * scale, height / 2 + point.z * scale];
    };

    const color =
      this.#state?.scene === "water"
        ? "#55bff7"
        : this.#state?.scene === "risk"
          ? "#ff6675"
          : "#77dcff";
    for (const feature of this.#grid.trans.features) {
      const branch = this.#branches.get(feature.properties.line_id);
      if (this.#state?.scene === "energy" && branch) {
        context.strokeStyle = `#${energyLoadingColor(
          branch.loading_pct[this.#state.energyScenario],
        )
          .toString(16)
          .padStart(6, "0")}`;
        context.globalAlpha = 0.95;
        context.lineWidth = 2;
      } else {
        context.strokeStyle = color;
        context.globalAlpha =
          this.#state?.scene === "energy" && !branch ? 0.16 : 0.8;
        context.lineWidth = 1.25;
      }
      for (const line of lineParts(feature.geometry)) {
        context.beginPath();
        line.forEach(([longitude, latitude], index) => {
          const [x, y] = screen(longitude, latitude);
          if (index === 0) context.moveTo(x, y);
          else context.lineTo(x, y);
        });
        context.stroke();
      }
    }
    context.globalAlpha = 1;
  }
}
