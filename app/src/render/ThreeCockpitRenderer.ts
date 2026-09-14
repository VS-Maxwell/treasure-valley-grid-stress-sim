import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import type { SimulationState } from "../contracts";
import {
  measureGridBounds,
  previewElevation,
  projectPosition,
} from "../data/geo";
import { lineParts, type GridCore } from "../data/gridTypes";
import type { TvgwfmGrid } from "../data/tvgwfmTypes";
import type { RendererAdapter, RendererCallbacks } from "./RendererAdapter";

const TERRAIN_WIDTH = 230;
const TERRAIN_DEPTH = 150;
const TARGET_FRAME_INTERVAL = 1000 / 30;
const VOLTAGE_COLORS = {
  low: 0x6fcaff,
  medium: 0xffdf73,
  high: 0xff9148,
  bulk: 0xff4658,
} as const;

type VoltageClass = keyof typeof VOLTAGE_COLORS;

function voltageClass(voltage: number): VoltageClass {
  if (voltage >= 500) return "bulk";
  if (voltage >= 230) return "high";
  if (voltage >= 138) return "medium";
  return "low";
}

export class ThreeCockpitRenderer implements RendererAdapter {
  readonly kind = "three-webgl" as const;
  readonly #container: HTMLElement;
  readonly #grid: GridCore;
  readonly #tvgwfm: TvgwfmGrid;
  readonly #callbacks: RendererCallbacks;
  readonly #scene = new THREE.Scene();
  readonly #camera = new THREE.PerspectiveCamera(47, 1, 0.1, 1200);
  readonly #renderer: THREE.WebGLRenderer;
  readonly #controls: OrbitControls;
  readonly #timer = new THREE.Timer();
  readonly #gridMaterials = new Map<VoltageClass, THREE.LineBasicMaterial>();
  readonly #terrainMaterial: THREE.MeshStandardMaterial;
  readonly #waterMaterial: THREE.MeshPhysicalMaterial;
  readonly #sun = new THREE.DirectionalLight(0xfff0d1, 3.2);
  #frameHandle = 0;
  #frameCount = 0;
  #metricSeconds = 0;
  #lastRenderTime = 0;
  #settleFrames = 0;
  #running = false;
  #resizeObserver: ResizeObserver | null = null;

  constructor(
    container: HTMLElement,
    grid: GridCore,
    tvgwfm: TvgwfmGrid,
    callbacks: RendererCallbacks,
  ) {
    this.#container = container;
    this.#grid = grid;
    this.#tvgwfm = tvgwfm;
    this.#callbacks = callbacks;
    this.#renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
    });
    this.#renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.#renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.#renderer.toneMappingExposure = 1.05;
    this.#renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    this.#renderer.domElement.setAttribute(
      "aria-label",
      "Three-dimensional Treasure Valley system view",
    );
    this.#renderer.domElement.addEventListener(
      "webglcontextlost",
      this.#onContextLost,
      false,
    );
    this.#timer.connect(document);

    this.#controls = new OrbitControls(this.#camera, this.#renderer.domElement);
    this.#controls.enableDamping = true;
    this.#controls.dampingFactor = 0.06;
    this.#controls.minDistance = 34;
    this.#controls.maxDistance = 310;
    this.#controls.maxPolarAngle = Math.PI * 0.47;
    this.#controls.target.set(0, -1, 0);
    this.#controls.addEventListener("change", this.#onControlsChange);

    this.#terrainMaterial = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.94,
      metalness: 0.02,
      side: THREE.DoubleSide,
    });
    this.#waterMaterial = new THREE.MeshPhysicalMaterial({
      color: 0x20a7dc,
      roughness: 0.36,
      metalness: 0.03,
      transparent: true,
      opacity: 0.16,
      depthWrite: false,
      wireframe: true,
    });
    this.#buildScene();
    this.focusHome();
  }

  mount(): void {
    this.#container.prepend(this.#renderer.domElement);
    this.#resizeObserver = new ResizeObserver(() => this.#resize());
    this.#resizeObserver.observe(this.#container);
    this.#resize();
  }

  start(): void {
    if (this.#running) return;
    this.#running = true;
    this.#timer.reset();
    this.#lastRenderTime = 0;
    this.#requestRender(2);
  }

  stop(): void {
    this.#running = false;
    cancelAnimationFrame(this.#frameHandle);
    this.#frameHandle = 0;
  }

  applyState(state: SimulationState): void {
    const gridOpacity =
      state.scene === "water" ? 0.28 : state.scene === "time" ? 0.52 : 0.94;
    this.#gridMaterials.forEach((material, key) => {
      material.opacity =
        key === "bulk" ? Math.min(1, gridOpacity + 0.08) : gridOpacity;
      material.color.setHex(
        state.scene === "risk" ? 0xff5366 : (VOLTAGE_COLORS[key] ?? 0x6fcaff),
      );
    });
    this.#waterMaterial.opacity =
      state.scene === "water" ? 0.82 : state.scene === "nexus" ? 0.5 : 0.16;
    this.#terrainMaterial.wireframe = state.scene === "record";
    const future = Math.max(0, (state.year - 2026) / 74);
    this.#scene.background = new THREE.Color().setRGB(
      0.018 + future * 0.11,
      0.06 + future * 0.025,
      0.095 - future * 0.025,
    );
    this.#scene.fog = new THREE.Fog(this.#scene.background, 120, 390);
    const dayAngle = ((state.year + 15_000) / 17_100) * Math.PI * 2;
    this.#sun.position.set(
      Math.cos(dayAngle) * 110,
      90,
      Math.sin(dayAngle) * 90,
    );
    this.#sun.color.set(
      state.climateScenario === "heat-drought-2050" ? 0xffc08a : 0xfff0d1,
    );
    this.#requestRender(2);
  }

  focusHome(): void {
    this.#camera.position.set(112, 92, 132);
    this.#controls.target.set(0, -2, 0);
    this.#controls.update();
    this.#requestRender(10);
  }

  dispose(): void {
    this.stop();
    this.#resizeObserver?.disconnect();
    this.#renderer.domElement.removeEventListener(
      "webglcontextlost",
      this.#onContextLost,
    );
    this.#controls.removeEventListener("change", this.#onControlsChange);
    this.#controls.dispose();
    this.#timer.dispose();
    this.#scene.traverse((object) => {
      if (
        object instanceof THREE.Mesh ||
        object instanceof THREE.LineSegments ||
        object instanceof THREE.Points
      ) {
        object.geometry.dispose();
        const materials = Array.isArray(object.material)
          ? object.material
          : [object.material];
        materials.forEach((material) => material.dispose());
      }
    });
    this.#renderer.dispose();
    this.#renderer.domElement.remove();
  }

  #buildScene(): void {
    this.#scene.background = new THREE.Color(0x06121d);
    this.#scene.fog = new THREE.Fog(0x06121d, 120, 390);
    this.#scene.add(new THREE.HemisphereLight(0x9edcff, 0x18210f, 1.75));
    this.#sun.position.set(85, 110, 70);
    this.#sun.castShadow = false;
    this.#scene.add(this.#sun);

    const terrainGeometry = new THREE.PlaneGeometry(
      TERRAIN_WIDTH,
      TERRAIN_DEPTH,
      96,
      64,
    );
    terrainGeometry.rotateX(-Math.PI / 2);
    const positions = terrainGeometry.getAttribute("position");
    const colors: number[] = [];
    const low = new THREE.Color(0x17352f);
    const mid = new THREE.Color(0x496044);
    const high = new THREE.Color(0x8a806a);
    for (let index = 0; index < positions.count; index += 1) {
      const x = positions.getX(index);
      const z = positions.getZ(index);
      const elevation = previewElevation(x, z);
      positions.setY(index, elevation);
      const normalized = THREE.MathUtils.clamp((elevation + 5) / 19, 0, 1);
      const color =
        normalized < 0.55
          ? low.clone().lerp(mid, normalized / 0.55)
          : mid.clone().lerp(high, (normalized - 0.55) / 0.45);
      colors.push(color.r, color.g, color.b);
    }
    terrainGeometry.setAttribute(
      "color",
      new THREE.Float32BufferAttribute(colors, 3),
    );
    terrainGeometry.computeVertexNormals();
    const terrain = new THREE.Mesh(terrainGeometry, this.#terrainMaterial);
    terrain.name = "reconstructed-preview-terrain";
    this.#scene.add(terrain);

    this.#addTvgwfmSurface();

    this.#addGridLines();
    this.#addSubstations();
    this.#addPlants();
    this.#addAtmosphereMarkers();
  }

  #addTvgwfmSurface(): void {
    const model = this.#tvgwfm.grid;
    const bounds = measureGridBounds(this.#grid);
    const corners = model.corners_wgs84;
    const vertices: number[] = [];
    const indices: number[] = [];
    const elevations = model.top_elevation_feet;
    const elevationSpan = model.top_max_feet - model.top_min_feet;

    const mix = (start: number, end: number, amount: number): number =>
      start + (end - start) * amount;
    for (let row = 0; row < model.rows; row += 1) {
      const v = row / (model.rows - 1);
      const left: readonly [number, number] = [
        mix(corners.upper_left[0], corners.lower_left[0], v),
        mix(corners.upper_left[1], corners.lower_left[1], v),
      ];
      const right: readonly [number, number] = [
        mix(corners.upper_right[0], corners.lower_right[0], v),
        mix(corners.upper_right[1], corners.lower_right[1], v),
      ];
      for (let column = 0; column < model.columns; column += 1) {
        const u = column / (model.columns - 1);
        const longitude = mix(left[0], right[0], u);
        const latitude = mix(left[1], right[1], u);
        const point = projectPosition([longitude, latitude], bounds);
        const elevation = elevations[row * model.columns + column] ?? 0;
        const relief =
          elevation > 0
            ? ((elevation - model.top_min_feet) / elevationSpan) * 3.2
            : 0;
        vertices.push(point.x, point.y + 0.9 + relief, point.z);
      }
    }

    const isActive = (row: number, column: number): boolean =>
      (elevations[row * model.columns + column] ?? 0) > 0;
    for (let row = 0; row < model.rows - 1; row += 1) {
      for (let column = 0; column < model.columns - 1; column += 1) {
        const a = row * model.columns + column;
        const b = a + 1;
        const c = a + model.columns;
        const d = c + 1;
        if (
          isActive(row, column) &&
          isActive(row, column + 1) &&
          isActive(row + 1, column)
        )
          indices.push(a, c, b);
        if (
          isActive(row, column + 1) &&
          isActive(row + 1, column) &&
          isActive(row + 1, column + 1)
        )
          indices.push(b, c, d);
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(vertices, 3),
    );
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const surface = new THREE.Mesh(geometry, this.#waterMaterial);
    surface.name = "usgs-tvgwfm-ingested-top-surface";
    this.#scene.add(surface);
  }

  #addGridLines(): void {
    const bounds = measureGridBounds(this.#grid);
    const groups = new Map<keyof typeof VOLTAGE_COLORS, number[]>();
    Object.keys(VOLTAGE_COLORS).forEach((key) =>
      groups.set(key as keyof typeof VOLTAGE_COLORS, []),
    );
    for (const feature of this.#grid.trans.features) {
      const target = groups.get(
        voltageClass(Number(feature.properties.voltage_kv)),
      )!;
      for (const line of lineParts(feature.geometry)) {
        for (let index = 1; index < line.length; index += 1) {
          const start = projectPosition(line[index - 1]!, bounds);
          const end = projectPosition(line[index]!, bounds);
          target.push(start.x, start.y, start.z, end.x, end.y, end.z);
        }
      }
    }
    groups.forEach((vertices, key) => {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(vertices, 3),
      );
      const material = new THREE.LineBasicMaterial({
        color: VOLTAGE_COLORS[key],
        transparent: true,
        opacity: 0.94,
      });
      this.#gridMaterials.set(key, material);
      const lines = new THREE.LineSegments(geometry, material);
      lines.name = `transmission-${key}`;
      this.#scene.add(lines);
    });
  }

  #addSubstations(): void {
    const bounds = measureGridBounds(this.#grid);
    const geometry = new THREE.SphereGeometry(0.72, 8, 6);
    const material = new THREE.MeshStandardMaterial({
      color: 0xe7faff,
      emissive: 0x194d67,
      emissiveIntensity: 1.4,
    });
    const mesh = new THREE.InstancedMesh(
      geometry,
      material,
      this.#grid.subs.features.length,
    );
    const transform = new THREE.Object3D();
    this.#grid.subs.features.forEach((feature, index) => {
      const point = projectPosition(feature.geometry.coordinates, bounds);
      transform.position.set(point.x, point.y + 0.5, point.z);
      const scale = THREE.MathUtils.clamp(
        feature.properties.max_voltage_kv / 230,
        0.65,
        1.6,
      );
      transform.scale.setScalar(scale);
      transform.updateMatrix();
      mesh.setMatrixAt(index, transform.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.name = "substations-94";
    this.#scene.add(mesh);
  }

  #addPlants(): void {
    const bounds = measureGridBounds(this.#grid);
    const geometry = new THREE.ConeGeometry(0.8, 2.8, 7);
    const material = new THREE.MeshStandardMaterial({
      color: 0xffd57a,
      emissive: 0x5b3e0a,
      emissiveIntensity: 0.8,
    });
    const mesh = new THREE.InstancedMesh(
      geometry,
      material,
      this.#grid.plants.features.length,
    );
    const transform = new THREE.Object3D();
    this.#grid.plants.features.forEach((feature, index) => {
      const point = projectPosition(feature.geometry.coordinates, bounds);
      transform.position.set(point.x, point.y + 1.3, point.z);
      const scale = THREE.MathUtils.clamp(
        Math.sqrt(feature.properties.capacity_mw || 1) / 20,
        0.65,
        2.2,
      );
      transform.scale.setScalar(scale);
      transform.updateMatrix();
      mesh.setMatrixAt(index, transform.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.name = "generation-plants-14";
    this.#scene.add(mesh);
  }

  #addAtmosphereMarkers(): void {
    const geometry = new THREE.BufferGeometry();
    const positions: number[] = [];
    for (let index = 0; index < 320; index += 1) {
      const angle = index * 2.399963;
      const radius = 80 + ((index * 37) % 130);
      positions.push(
        Math.cos(angle) * radius,
        38 + ((index * 17) % 115),
        Math.sin(angle) * radius,
      );
    }
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    const points = new THREE.Points(
      geometry,
      new THREE.PointsMaterial({
        color: 0x9adfff,
        size: 0.48,
        transparent: true,
        opacity: 0.45,
        sizeAttenuation: true,
      }),
    );
    points.name = "atmosphere-context-points";
    this.#scene.add(points);
  }

  #resize(): void {
    const width = Math.max(1, this.#container.clientWidth);
    const height = Math.max(1, this.#container.clientHeight);
    this.#camera.aspect = width / height;
    this.#camera.updateProjectionMatrix();
    this.#renderer.setSize(width, height, false);
    this.#requestRender(2);
  }

  readonly #onControlsChange = (): void => {
    this.#requestRender(3);
  };

  #requestRender(settleFrames = 1): void {
    if (!this.#running) return;
    this.#settleFrames = Math.max(this.#settleFrames, settleFrames);
    if (this.#frameHandle === 0)
      this.#frameHandle = requestAnimationFrame(this.#frame);
  }

  readonly #onContextLost = (event: Event): void => {
    event.preventDefault();
    this.stop();
    this.#callbacks.onContextLost();
  };

  readonly #frame = (now: number): void => {
    this.#frameHandle = 0;
    if (!this.#running) return;
    if (
      this.#lastRenderTime > 0 &&
      now - this.#lastRenderTime < TARGET_FRAME_INTERVAL
    ) {
      this.#frameHandle = requestAnimationFrame(this.#frame);
      return;
    }
    this.#lastRenderTime = now;
    this.#timer.update(now);
    const delta = Math.min(this.#timer.getDelta(), 0.1);
    const controlsChanged = this.#controls.update(delta);
    this.#renderer.render(this.#scene, this.#camera);
    this.#frameCount += 1;
    this.#metricSeconds += delta;
    if (this.#metricSeconds >= 1) {
      this.#callbacks.onMetrics({
        fps: Math.round(this.#frameCount / this.#metricSeconds),
        drawCalls: this.#renderer.info.render.calls,
        triangles: this.#renderer.info.render.triangles,
      });
      this.#frameCount = 0;
      this.#metricSeconds = 0;
    }
    if (controlsChanged) this.#settleFrames = Math.max(this.#settleFrames, 2);
    else this.#settleFrames = Math.max(0, this.#settleFrames - 1);
    if (this.#settleFrames > 0)
      this.#frameHandle = requestAnimationFrame(this.#frame);
  };
}
