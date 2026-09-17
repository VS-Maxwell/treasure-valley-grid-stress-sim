import type * as THREE from "three";
import { DropInViewer } from "@mkkellogg/gaussian-splats-3d";

export type GaussianSplatStatus =
  "not-configured" | "loading" | "ready" | "failed";

export class GaussianSplatLayer {
  readonly #viewer: DropInViewer;
  #status: GaussianSplatStatus = "not-configured";

  constructor(scene: THREE.Scene) {
    this.#viewer = new DropInViewer({
      gpuAcceleratedSort: true,
      sharedMemoryForWorkers: false,
      ignoreDevicePixelRatio: true,
    });
    this.#viewer.visible = false;
    scene.add(this.#viewer);
  }

  get status(): GaussianSplatStatus {
    return this.#status;
  }

  async load(url: string): Promise<boolean> {
    this.#status = "loading";
    try {
      await this.#viewer.addSplatScene(url, {
        showLoadingUI: false,
        splatAlphaRemovalThreshold: 5,
        onProgress: () => undefined,
      });
      this.#viewer.visible = true;
      this.#status = "ready";
      return true;
    } catch (error) {
      this.#status = "failed";
      console.warn("Gaussian splat scene unavailable", error);
      return false;
    }
  }

  setVisible(visible: boolean): void {
    this.#viewer.visible = visible && this.#status === "ready";
  }

  dispose(): void {
    this.#viewer.dispose();
    this.#viewer.removeFromParent();
  }
}
