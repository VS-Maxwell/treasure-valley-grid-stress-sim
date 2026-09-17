declare module "@mkkellogg/gaussian-splats-3d" {
  import type * as THREE from "three";

  export interface SplatSceneOptions {
    readonly showLoadingUI?: boolean;
    readonly splatAlphaRemovalThreshold?: number;
    readonly position?: readonly [number, number, number];
    readonly rotation?: readonly [number, number, number, number];
    readonly scale?: readonly [number, number, number];
    readonly onProgress?: (percent: number) => void;
  }

  export interface DropInViewerOptions {
    readonly gpuAcceleratedSort?: boolean;
    readonly sharedMemoryForWorkers?: boolean;
    readonly ignoreDevicePixelRatio?: boolean;
  }

  export class DropInViewer extends THREE.Group {
    constructor(options?: DropInViewerOptions);
    addSplatScene(path: string, options?: SplatSceneOptions): Promise<unknown>;
    dispose(): void;
  }
}
