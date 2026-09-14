import type { RendererMetrics } from "../render/RendererAdapter";

export interface RuntimeSnapshot {
  readonly startedAt: string;
  readonly renderer: "loading" | "three-webgl" | "canvas-fallback" | "failed";
  readonly sourceSha256: string | null;
  readonly corridorCount: number;
  readonly substationCount: number;
  readonly contextLosses: number;
  readonly latestMetrics: RendererMetrics | null;
  readonly samples: readonly RendererMetrics[];
}

export class RuntimeDiagnostics {
  readonly #startedAt = new Date().toISOString();
  readonly #samples: RendererMetrics[] = [];
  #renderer: RuntimeSnapshot["renderer"] = "loading";
  #sourceSha256: string | null = null;
  #corridorCount = 0;
  #substationCount = 0;
  #contextLosses = 0;

  setDataReceipt(
    sourceSha256: string,
    corridors: number,
    substations: number,
  ): void {
    this.#sourceSha256 = sourceSha256;
    this.#corridorCount = corridors;
    this.#substationCount = substations;
  }

  setRenderer(renderer: RuntimeSnapshot["renderer"]): void {
    this.#renderer = renderer;
  }

  recordContextLoss(): void {
    this.#contextLosses += 1;
  }

  recordMetrics(metrics: RendererMetrics): void {
    this.#samples.push(metrics);
    if (this.#samples.length > 120) this.#samples.shift();
  }

  snapshot(): RuntimeSnapshot {
    return {
      startedAt: this.#startedAt,
      renderer: this.#renderer,
      sourceSha256: this.#sourceSha256,
      corridorCount: this.#corridorCount,
      substationCount: this.#substationCount,
      contextLosses: this.#contextLosses,
      latestMetrics: this.#samples.at(-1) ?? null,
      samples: [...this.#samples],
    };
  }
}
