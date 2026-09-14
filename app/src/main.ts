import "./styles.css";

import { RuntimeDiagnostics } from "./diagnostics/RuntimeDiagnostics";
import { loadGridCore } from "./data/loadGridCore";
import { InputController } from "./input/InputController";
import { CanvasFallbackRenderer } from "./render/CanvasFallbackRenderer";
import type {
  RendererAdapter,
  RendererMetrics,
} from "./render/RendererAdapter";
import { SimulationStore } from "./simulation/SimulationStore";
import { HudController } from "./ui/HudController";

declare global {
  interface Window {
    TV_SIM_DIAGNOSTICS: () => ReturnType<RuntimeDiagnostics["snapshot"]>;
  }
}

function required<T extends HTMLElement>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Required element is missing: ${selector}`);
  return element;
}

async function boot(): Promise<void> {
  const diagnostics = new RuntimeDiagnostics();
  window.TV_SIM_DIAGNOSTICS = () => diagnostics.snapshot();
  const grid = await loadGridCore();
  diagnostics.setDataReceipt(
    grid.source_sha256,
    grid.trans.features.length,
    grid.subs.features.length,
  );

  const store = new SimulationStore();
  let renderer: RendererAdapter | null = null;
  let timelineTimer: number | null = null;

  const syncTimeline = (playing: boolean): void => {
    if (timelineTimer !== null) window.clearInterval(timelineTimer);
    timelineTimer = playing
      ? window.setInterval(() => store.tick(25), 300)
      : null;
  };

  const actions = {
    explore: (): void => {
      store.explore();
      renderer?.focusHome();
    },
    follow: (): void => store.follow(),
    compare: (): void => store.toggleCompare(),
    stress: (): void => store.stress(),
    inspect: (): void => store.openDrawer("evidence"),
    ask: (): void => store.openDrawer("ask"),
  };

  const hud = new HudController(store, grid, actions);
  hud.connect();

  const recordMetrics = (metrics: RendererMetrics): void => {
    diagnostics.recordMetrics(metrics);
    hud.setMetrics(metrics);
  };

  const activateFallback = (reason: string, contextLost = false): void => {
    renderer?.dispose();
    if (contextLost) diagnostics.recordContextLoss();
    const fallback = new CanvasFallbackRenderer(
      required("#fallback-canvas"),
      grid,
      {
        onContextLost: () => undefined,
        onMetrics: recordMetrics,
      },
    );
    renderer = fallback;
    diagnostics.setRenderer(fallback.kind);
    fallback.mount();
    fallback.applyState(store.state);
    fallback.start();
    hud.setLoadingDetail(reason);
    hud.setReady(fallback.kind);
  };

  const input = new InputController({
    selectScene: (scene) => store.selectScene(scene),
    ...actions,
    playTime: () => store.togglePlaying(),
    close: () => store.closeDrawer(),
  });
  input.connect();

  store.subscribe((state, previous) => {
    hud.render(state);
    renderer?.applyState(state);
    if (state.playing !== previous.playing) syncTimeline(state.playing);
  });

  const forceCanvas =
    new URLSearchParams(window.location.search).get("renderer") === "canvas";
  if (forceCanvas) {
    activateFallback(
      "Canvas mode was selected explicitly for degraded operation testing.",
    );
  } else
    try {
      hud.setLoadingDetail(
        "Creating the Three.js terrain and merged grid layers…",
      );
      const { ThreeCockpitRenderer } =
        await import("./render/ThreeCockpitRenderer");
      const three = new ThreeCockpitRenderer(required("#playfield"), grid, {
        onContextLost: () =>
          activateFallback(
            "WebGL context was lost; switched to the bounded Canvas view.",
            true,
          ),
        onMetrics: recordMetrics,
      });
      renderer = three;
      diagnostics.setRenderer(three.kind);
      three.mount();
      three.applyState(store.state);
      three.start();
      hud.setReady(three.kind);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unknown WebGL startup failure";
      activateFallback(
        `3D renderer unavailable (${message}); using the bounded Canvas view.`,
      );
    }

  window.addEventListener("beforeunload", () => {
    if (timelineTimer !== null) window.clearInterval(timelineTimer);
    input.disconnect();
    renderer?.dispose();
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      renderer?.stop();
      syncTimeline(false);
    } else {
      renderer?.start();
      syncTimeline(store.state.playing);
    }
  });
}

void boot().catch((error: unknown) => {
  const message =
    error instanceof Error ? error.message : "Unknown startup error";
  const fatal = document.querySelector<HTMLElement>("#fatal");
  const loading = document.querySelector<HTMLElement>("#loading");
  if (fatal) {
    fatal.hidden = false;
    fatal.textContent = `Simulator startup failed: ${message}`;
  }
  loading?.classList.add("ready");
  console.error("Treasure Valley simulator startup failed", error);
});
