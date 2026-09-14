import type { SimulationState } from "../contracts";

export interface RendererMetrics {
  readonly fps: number;
  readonly drawCalls: number;
  readonly triangles: number;
}

export interface RendererAdapter {
  readonly kind: "three-webgl" | "canvas-fallback";
  mount(): void;
  start(): void;
  stop(): void;
  applyState(state: SimulationState): void;
  loadImageryOverlay?(url: string): Promise<boolean>;
  focusHome(): void;
  dispose(): void;
}

export interface RendererCallbacks {
  readonly onContextLost: () => void;
  readonly onMetrics: (metrics: RendererMetrics) => void;
}
