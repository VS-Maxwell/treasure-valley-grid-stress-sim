import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import type { SimulationState } from "../contracts";
import {
  energyLoadingColor,
  type EnergyBranch,
  type EnergyScreeningModel,
} from "../data/energyScreening";
import type { EspamGrid } from "../data/espamGrid";
import { espamHeadFeet, type EspamHeads } from "../data/espamHeads";
import { nearestEspamHeadSlice } from "../data/loadEspamHeads";
import {
  measureGridBounds,
  previewElevation,
  projectPosition,
} from "../data/geo";
import type { GeoBounds, WorldPoint } from "../data/geo";
import { lineParts, type GridCore } from "../data/gridTypes";
import type { TvgwfmGrid } from "../data/tvgwfmTypes";
import { nearestHeadSlice } from "../data/loadTvgwfmHeads";
import type { TvgwfmHeads } from "../data/tvgwfmHeads";
import type { MeasuredGroundwaterSites } from "../data/measuredGroundwaterSites";
import type { RegionalDams } from "../data/regionalDams";
import type { TvgwfmBottoms } from "../data/tvgwfmBottoms";
import {
  terrainWorldHeight,
  terrainWorldHeightAt,
  type RegionalTerrain,
} from "../data/regionalTerrain";
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
  readonly #gridBounds: GeoBounds;
  readonly #tvgwfm: TvgwfmGrid;
  readonly #tvgwfmHeads: TvgwfmHeads;
  readonly #measuredGroundwaterSites: MeasuredGroundwaterSites;
  readonly #regionalTerrain: RegionalTerrain | null;
  readonly #regionalDams: RegionalDams | null;
  readonly #tvgwfmBottoms: TvgwfmBottoms | null;
  readonly #espamGrid: EspamGrid | null;
  readonly #espamHeads: EspamHeads | null;
  readonly #energyScreening: EnergyScreeningModel;
  readonly #callbacks: RendererCallbacks;
  readonly #scene = new THREE.Scene();
  readonly #camera = new THREE.PerspectiveCamera(47, 1, 0.1, 1200);
  readonly #renderer: THREE.WebGLRenderer;
  readonly #controls: OrbitControls;
  readonly #timer = new THREE.Timer();
  readonly #gridMaterials = new Map<VoltageClass, THREE.LineBasicMaterial>();
  readonly #screeningVertexBranches: EnergyBranch[] = [];
  #screeningBranchLines: THREE.LineSegments | null = null;
  #activeEnergyScenario = "base";
  readonly #terrainMaterial: THREE.MeshStandardMaterial;
  readonly #contextTerrainMaterial: THREE.MeshStandardMaterial;
  readonly #waterMaterial: THREE.MeshPhysicalMaterial;
  readonly #headMeshes: THREE.Mesh<
    THREE.BufferGeometry,
    THREE.MeshStandardMaterial
  >[] = [];
  readonly #headGroundY: number[] = [];
  readonly #aquiferBottomMeshes: THREE.Mesh<
    THREE.BufferGeometry,
    THREE.MeshStandardMaterial
  >[] = [];
  #measuredWellPoints: THREE.Points | null = null;
  #damPoints: THREE.Points | null = null;
  #hydroDamPoints: THREE.Points | null = null;
  #espamGridLines: THREE.LineSegments | null = null;
  #espamHeadSurface: THREE.Mesh<
    THREE.BufferGeometry,
    THREE.MeshPhysicalMaterial
  > | null = null;
  #imageryTexture: THREE.Texture | null = null;
  #imageryRequest = 0;
  readonly #sun = new THREE.DirectionalLight(0xfff0d1, 3.2);
  #frameHandle = 0;
  #frameCount = 0;
  #metricSeconds = 0;
  #lastRenderTime = 0;
  #settleFrames = 0;
  #headSliceIndex = -1;
  #espamHeadSliceIndex = -1;
  #running = false;
  #resizeObserver: ResizeObserver | null = null;

  constructor(
    container: HTMLElement,
    grid: GridCore,
    tvgwfm: TvgwfmGrid,
    tvgwfmHeads: TvgwfmHeads,
    measuredGroundwaterSites: MeasuredGroundwaterSites,
    regionalTerrain: RegionalTerrain | null,
    regionalDams: RegionalDams | null,
    tvgwfmBottoms: TvgwfmBottoms | null,
    espamGrid: EspamGrid | null,
    espamHeads: EspamHeads | null,
    energyScreening: EnergyScreeningModel,
    callbacks: RendererCallbacks,
  ) {
    this.#container = container;
    this.#grid = grid;
    this.#gridBounds =
      regionalTerrain?.manifest.mesh.bounds_wgs84 ?? measureGridBounds(grid);
    this.#tvgwfm = tvgwfm;
    this.#tvgwfmHeads = tvgwfmHeads;
    this.#measuredGroundwaterSites = measuredGroundwaterSites;
    this.#regionalTerrain = regionalTerrain;
    this.#regionalDams = regionalDams;
    this.#tvgwfmBottoms = tvgwfmBottoms;
    this.#espamGrid = espamGrid;
    this.#espamHeads = espamHeads;
    this.#energyScreening = energyScreening;
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
    this.#contextTerrainMaterial = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 1,
      metalness: 0,
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

  async loadImageryOverlay(url: string): Promise<boolean> {
    if (!this.#regionalTerrain) return false;
    const request = ++this.#imageryRequest;
    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin("anonymous");
    return new Promise((resolve) => {
      const timeout = window.setTimeout(() => {
        if (this.#imageryRequest === request) this.#imageryRequest += 1;
        resolve(false);
      }, 8_000);
      loader.load(
        url,
        (texture) => {
          window.clearTimeout(timeout);
          if (this.#imageryRequest !== request) {
            texture.dispose();
            return;
          }
          texture.colorSpace = THREE.SRGBColorSpace;
          texture.wrapS = THREE.ClampToEdgeWrapping;
          texture.wrapT = THREE.ClampToEdgeWrapping;
          this.#imageryTexture?.dispose();
          this.#imageryTexture = texture;
          this.#terrainMaterial.map = texture;
          this.#terrainMaterial.vertexColors = false;
          this.#terrainMaterial.needsUpdate = true;
          this.#requestRender(4);
          resolve(true);
        },
        undefined,
        () => {
          window.clearTimeout(timeout);
          if (this.#imageryRequest === request) this.#imageryRequest += 1;
          resolve(false);
        },
      );
    });
  }

  applyState(state: SimulationState): void {
    const gridOpacity =
      state.scene === "water"
        ? 0.28
        : state.scene === "time"
          ? 0.52
          : state.scene === "energy"
            ? 0.18
            : 0.94;
    this.#gridMaterials.forEach((material, key) => {
      material.opacity =
        key === "bulk" ? Math.min(1, gridOpacity + 0.08) : gridOpacity;
      material.color.setHex(
        state.scene === "risk" ? 0xff5366 : (VOLTAGE_COLORS[key] ?? 0x6fcaff),
      );
    });
    this.#waterMaterial.opacity =
      state.scene === "water" ? 0.82 : state.scene === "nexus" ? 0.5 : 0.16;
    const showHeads = state.scene === "water" || state.scene === "nexus";
    this.#headMeshes.forEach((mesh, index) => {
      mesh.visible = showHeads;
      mesh.material.opacity =
        state.scene === "water" ? 0.5 - index * 0.045 : 0.2;
    });
    const showBottoms =
      state.scene === "water" ||
      state.scene === "nexus" ||
      state.scene === "record";
    this.#aquiferBottomMeshes.forEach((mesh, index) => {
      mesh.visible = showBottoms;
      mesh.material.opacity =
        state.scene === "water"
          ? 0.26 - index * 0.018
          : state.scene === "record"
            ? 0.2
            : 0.12;
      mesh.material.wireframe = state.scene === "record";
    });
    if (this.#measuredWellPoints)
      this.#measuredWellPoints.visible =
        state.scene === "water" && state.compare;
    if (this.#damPoints)
      this.#damPoints.visible =
        state.scene === "water" ||
        state.scene === "nexus" ||
        state.scene === "risk";
    if (this.#hydroDamPoints)
      this.#hydroDamPoints.visible =
        state.scene === "energy" ||
        state.scene === "water" ||
        state.scene === "nexus" ||
        state.scene === "risk";
    if (this.#espamGridLines)
      this.#espamGridLines.visible =
        state.scene === "water" ||
        state.scene === "nexus" ||
        state.scene === "record";
    if (this.#espamHeadSurface) {
      this.#espamHeadSurface.visible =
        state.scene === "water" || state.scene === "nexus";
      this.#espamHeadSurface.material.opacity =
        state.scene === "water" ? 0.58 : 0.32;
    }
    if (this.#screeningBranchLines) {
      this.#screeningBranchLines.visible = state.scene === "energy";
      if (this.#activeEnergyScenario !== state.energyScenario) {
        this.#activeEnergyScenario = state.energyScenario;
        const colors = this.#screeningBranchLines.geometry.getAttribute(
          "color",
        ) as THREE.BufferAttribute;
        this.#screeningVertexBranches.forEach((branch, index) => {
          const color = new THREE.Color(
            energyLoadingColor(branch.loading_pct[state.energyScenario]),
          );
          colors.setXYZ(index, color.r, color.g, color.b);
        });
        colors.needsUpdate = true;
      }
    }
    this.#updateHeadSurfaces(state.year);
    this.#updateEspamHeadSurface(state.year);
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
    this.#imageryRequest += 1;
    this.#resizeObserver?.disconnect();
    this.#renderer.domElement.removeEventListener(
      "webglcontextlost",
      this.#onContextLost,
    );
    this.#controls.removeEventListener("change", this.#onControlsChange);
    this.#controls.dispose();
    this.#timer.dispose();
    this.#imageryTexture?.dispose();
    this.#imageryTexture = null;
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
      const elevation =
        previewElevation(x, z) - (this.#regionalTerrain ? 7 : 0);
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
    const terrain = new THREE.Mesh(
      terrainGeometry,
      this.#regionalTerrain
        ? this.#contextTerrainMaterial
        : this.#terrainMaterial,
    );
    terrain.name = this.#regionalTerrain
      ? "reconstructed-context-outside-3dep"
      : "reconstructed-preview-terrain";
    this.#scene.add(terrain);

    this.#addRegionalTerrainSurface();
    this.#addEspamGrid();
    this.#addEspamHeadSurface();

    this.#addTvgwfmSurface();
    this.#addAquiferBottomSurfaces();
    this.#addTvgwfmHeadSurfaces();
    this.#addMeasuredGroundwaterSites();
    this.#addRegionalDams();

    this.#addGridLines();
    this.#addScreeningBranches();
    this.#addSubstations();
    this.#addPlants();
    this.#addAtmosphereMarkers();
  }

  #projectPosition(position: readonly [number, number]): WorldPoint {
    const point = projectPosition(position, this.#gridBounds);
    const terrainY = this.#regionalTerrain
      ? terrainWorldHeightAt(this.#regionalTerrain, position)
      : null;
    return terrainY === null ? point : { ...point, y: terrainY + 0.65 };
  }

  #addRegionalTerrainSurface(): void {
    if (!this.#regionalTerrain) return;
    const terrain = this.#regionalTerrain;
    const { rows, columns, bounds_wgs84: bounds } = terrain.manifest.mesh;
    const vertices: number[] = [];
    const colors: number[] = [];
    const uvs: number[] = [];
    const indices: number[] = [];
    const low = new THREE.Color(0x21483b);
    const mid = new THREE.Color(0x627254);
    const high = new THREE.Color(0xb6aa8b);
    for (let row = 0; row < rows; row += 1) {
      const v = row / (rows - 1);
      const latitude = THREE.MathUtils.lerp(bounds.north, bounds.south, v);
      for (let column = 0; column < columns; column += 1) {
        const u = column / (columns - 1);
        const longitude = THREE.MathUtils.lerp(bounds.west, bounds.east, u);
        const point = projectPosition([longitude, latitude], this.#gridBounds);
        const elevation = terrain.elevations[row * columns + column]!;
        const worldY = terrainWorldHeight(terrain, elevation);
        vertices.push(point.x, worldY, point.z);
        uvs.push(u, 1 - v);
        const normalized = THREE.MathUtils.clamp(
          (elevation - terrain.manifest.statistics.minimum_meters) /
            (terrain.manifest.statistics.maximum_meters -
              terrain.manifest.statistics.minimum_meters),
          0,
          1,
        );
        const color =
          normalized < 0.55
            ? low.clone().lerp(mid, normalized / 0.55)
            : mid.clone().lerp(high, (normalized - 0.55) / 0.45);
        colors.push(color.r, color.g, color.b);
      }
    }
    for (let row = 0; row < rows - 1; row += 1) {
      for (let column = 0; column < columns - 1; column += 1) {
        const a = row * columns + column;
        const b = a + 1;
        const c = a + columns;
        const d = c + 1;
        indices.push(a, c, b, b, c, d);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(vertices, 3),
    );
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const surface = new THREE.Mesh(geometry, this.#terrainMaterial);
    surface.name = "usgs-3dep-snake-plain-terrain-observed";
    this.#scene.add(surface);
  }

  #addEspamGrid(): void {
    if (!this.#espamGrid) return;
    const values = this.#espamGrid.lines;
    const positions: number[] = [];
    for (let index = 0; index < values.length; index += 4) {
      const start = this.#projectPosition([values[index]!, values[index + 1]!]);
      const end = this.#projectPosition([
        values[index + 2]!,
        values[index + 3]!,
      ]);
      positions.push(
        start.x,
        start.y + 0.24,
        start.z,
        end.x,
        end.y + 0.24,
        end.z,
      );
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    this.#espamGridLines = new THREE.LineSegments(
      geometry,
      new THREE.LineBasicMaterial({
        color: 0x35d7c8,
        transparent: true,
        opacity: 0.2,
        depthWrite: false,
      }),
    );
    this.#espamGridLines.name = "idwr-espam22-active-grid-11236";
    this.#scene.add(this.#espamGridLines);
  }

  #addEspamHeadSurface(): void {
    if (!this.#espamGrid || !this.#espamHeads || !this.#regionalTerrain) return;
    const edges = this.#espamGrid.lines;
    const vertices: number[] = [];
    const colors: number[] = [];
    const indices: number[] = [];
    const low = new THREE.Color(0x126b9a);
    const high = new THREE.Color(0x6ff7ff);
    const firstSlice = this.#espamHeads.manifest.slices[0]!;
    for (
      let cell = 0;
      cell < this.#espamGrid.manifest.layout.active_cells;
      cell += 1
    ) {
      const edge = cell * 16;
      const corners: readonly (readonly [number, number])[] = [
        [edges[edge]!, edges[edge + 1]!],
        [edges[edge + 2]!, edges[edge + 3]!],
        [edges[edge + 6]!, edges[edge + 7]!],
        [edges[edge + 10]!, edges[edge + 11]!],
      ];
      const packed = this.#espamHeads.values[firstSlice.value_offset + cell]!;
      const headFeet = espamHeadFeet(this.#espamHeads, packed);
      const normalized = THREE.MathUtils.clamp(
        (headFeet - this.#espamHeads.manifest.statistics.minimum_feet) /
          (this.#espamHeads.manifest.statistics.maximum_feet -
            this.#espamHeads.manifest.statistics.minimum_feet),
        0,
        1,
      );
      const color = low.clone().lerp(high, normalized);
      for (const corner of corners) {
        const point = projectPosition(corner, this.#gridBounds);
        vertices.push(
          point.x,
          terrainWorldHeight(this.#regionalTerrain, headFeet * 0.3048) + 0.36,
          point.z,
        );
        colors.push(color.r, color.g, color.b);
      }
      const base = cell * 4;
      indices.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(vertices, 3),
    );
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    this.#espamHeadSurface = new THREE.Mesh(
      geometry,
      new THREE.MeshPhysicalMaterial({
        vertexColors: true,
        emissive: 0x06344d,
        emissiveIntensity: 0.38,
        roughness: 0.24,
        metalness: 0.04,
        transparent: true,
        opacity: 0.58,
        depthWrite: false,
        side: THREE.DoubleSide,
      }),
    );
    this.#espamHeadSurface.name =
      "idwr-espam22-archived-head-surface-1980-2018";
    this.#scene.add(this.#espamHeadSurface);
  }

  #updateEspamHeadSurface(year: number): void {
    if (!this.#espamHeadSurface || !this.#espamHeads || !this.#regionalTerrain)
      return;
    const sliceIndex = nearestEspamHeadSlice(this.#espamHeads.manifest, year);
    if (sliceIndex === this.#espamHeadSliceIndex) return;
    this.#espamHeadSliceIndex = sliceIndex;
    const slice = this.#espamHeads.manifest.slices[sliceIndex]!;
    const positions = this.#espamHeadSurface.geometry.getAttribute(
      "position",
    ) as THREE.BufferAttribute;
    const colors = this.#espamHeadSurface.geometry.getAttribute(
      "color",
    ) as THREE.BufferAttribute;
    const low = new THREE.Color(0x126b9a);
    const high = new THREE.Color(0x6ff7ff);
    for (
      let cell = 0;
      cell < this.#espamHeads.manifest.active_cell_count;
      cell += 1
    ) {
      const headFeet = espamHeadFeet(
        this.#espamHeads,
        this.#espamHeads.values[slice.value_offset + cell]!,
      );
      const y =
        terrainWorldHeight(this.#regionalTerrain, headFeet * 0.3048) + 0.36;
      const normalized = THREE.MathUtils.clamp(
        (headFeet - this.#espamHeads.manifest.statistics.minimum_feet) /
          (this.#espamHeads.manifest.statistics.maximum_feet -
            this.#espamHeads.manifest.statistics.minimum_feet),
        0,
        1,
      );
      const color = low.clone().lerp(high, normalized);
      for (let corner = 0; corner < 4; corner += 1) {
        const vertex = cell * 4 + corner;
        positions.setY(vertex, y);
        colors.setXYZ(vertex, color.r, color.g, color.b);
      }
    }
    positions.needsUpdate = true;
    colors.needsUpdate = true;
    this.#espamHeadSurface.geometry.computeVertexNormals();
  }

  #addMeasuredGroundwaterSites(): void {
    const values = this.#measuredGroundwaterSites.values;
    const positions: number[] = [];
    const colors: number[] = [];
    const low = new THREE.Color(0x3ee8ff);
    const high = new THREE.Color(0xffd166);
    for (let index = 0; index < values.length; index += 3) {
      const point = this.#projectPosition([values[index]!, values[index + 1]!]);
      positions.push(point.x, point.y + 2.1, point.z);
      const altitude = values[index + 2]!;
      const mix = THREE.MathUtils.clamp((altitude - 2050) / 1300, 0, 1);
      const color = low.clone().lerp(high, mix);
      colors.push(color.r, color.g, color.b);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    const material = new THREE.PointsMaterial({
      size: 1.15,
      sizeAttenuation: true,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
    });
    this.#measuredWellPoints = new THREE.Points(geometry, material);
    this.#measuredWellPoints.name = "usgs-observed-groundwater-sites";
    this.#measuredWellPoints.visible = false;
    this.#scene.add(this.#measuredWellPoints);
  }

  #addRegionalDams(): void {
    if (!this.#regionalDams) return;
    const allPositions: number[] = [];
    const hydroPositions: number[] = [];
    const values = this.#regionalDams.values;
    for (let index = 0; index < values.length; index += 3) {
      const point = this.#projectPosition([values[index]!, values[index + 1]!]);
      allPositions.push(point.x, point.y + 1.05, point.z);
      if (values[index + 2] === 1)
        hydroPositions.push(point.x, point.y + 1.45, point.z);
    }
    const allGeometry = new THREE.BufferGeometry();
    allGeometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(allPositions, 3),
    );
    this.#damPoints = new THREE.Points(
      allGeometry,
      new THREE.PointsMaterial({
        color: 0x5bdcff,
        size: 0.72,
        sizeAttenuation: true,
        transparent: true,
        opacity: 0.76,
        depthWrite: false,
      }),
    );
    this.#damPoints.name = "usace-nid-snake-plain-dams-647";
    this.#damPoints.visible = false;
    this.#scene.add(this.#damPoints);

    const hydroGeometry = new THREE.BufferGeometry();
    hydroGeometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(hydroPositions, 3),
    );
    this.#hydroDamPoints = new THREE.Points(
      hydroGeometry,
      new THREE.PointsMaterial({
        color: 0xffd166,
        size: 1.8,
        sizeAttenuation: true,
        transparent: true,
        opacity: 0.96,
        depthWrite: false,
      }),
    );
    this.#hydroDamPoints.name = "usace-nid-hydroelectric-purpose-dams-55";
    this.#hydroDamPoints.visible = false;
    this.#scene.add(this.#hydroDamPoints);
  }

  #addTvgwfmSurface(): void {
    const model = this.#tvgwfm.grid;
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
        const point = this.#projectPosition([longitude, latitude]);
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

  #addAquiferBottomSurfaces(): void {
    if (!this.#tvgwfmBottoms) return;
    const pack = this.#tvgwfmBottoms;
    const { rows, columns, layers, cell_count: cells } = pack.manifest.layout;
    const corners = this.#tvgwfm.grid.corners_wgs84;
    const colors = [0x45d8ff, 0x45bdf5, 0x4d9dea, 0x557dd7, 0x685fc0, 0x7d4aa8];
    const mix = (start: number, end: number, amount: number): number =>
      start + (end - start) * amount;

    for (let layer = 0; layer < layers; layer += 1) {
      const vertices: number[] = [];
      const indices: number[] = [];
      const offset = layer * cells;
      for (let row = 0; row < rows; row += 1) {
        const v = row / (rows - 1);
        const left: readonly [number, number] = [
          mix(corners.upper_left[0], corners.lower_left[0], v),
          mix(corners.upper_left[1], corners.lower_left[1], v),
        ];
        const right: readonly [number, number] = [
          mix(corners.upper_right[0], corners.lower_right[0], v),
          mix(corners.upper_right[1], corners.lower_right[1], v),
        ];
        for (let column = 0; column < columns; column += 1) {
          const u = column / (columns - 1);
          const position: readonly [number, number] = [
            mix(left[0], right[0], u),
            mix(left[1], right[1], u),
          ];
          const point = projectPosition(position, this.#gridBounds);
          const bottomFeet = pack.bottoms[offset + row * columns + column]!;
          const worldY = this.#regionalTerrain
            ? terrainWorldHeight(this.#regionalTerrain, bottomFeet * 0.3048)
            : point.y - 1.5 - layer * 1.2;
          vertices.push(point.x, worldY, point.z);
        }
      }
      const active = (row: number, column: number): boolean =>
        pack.idomain[offset + row * columns + column] !== 0;
      for (let row = 0; row < rows - 1; row += 1) {
        for (let column = 0; column < columns - 1; column += 1) {
          const a = row * columns + column;
          const b = a + 1;
          const c = a + columns;
          const d = c + 1;
          if (
            active(row, column) &&
            active(row + 1, column) &&
            active(row, column + 1)
          )
            indices.push(a, c, b);
          if (
            active(row, column + 1) &&
            active(row + 1, column) &&
            active(row + 1, column + 1)
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
      const material = new THREE.MeshStandardMaterial({
        color: colors[layer]!,
        emissive: colors[layer]!,
        emissiveIntensity: 0.12,
        roughness: 0.58,
        metalness: 0.04,
        transparent: true,
        opacity: 0.26 - layer * 0.018,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.name = `tvgwfm-aquifer-bottom-layer-${layer + 1}`;
      this.#aquiferBottomMeshes.push(mesh);
      this.#scene.add(mesh);
    }
  }

  #addTvgwfmHeadSurfaces(): void {
    const {
      rows,
      columns,
      layers,
      inactive_value: inactive,
    } = this.#tvgwfmHeads.manifest.layout;
    const corners = this.#tvgwfm.grid.corners_wgs84;
    const cells = rows * columns;
    const mix = (start: number, end: number, amount: number): number =>
      start + (end - start) * amount;

    for (let layer = 0; layer < layers; layer += 1) {
      const vertices: number[] = [];
      const indices: number[] = [];
      const firstLayerOffset = layer * cells;
      for (let row = 0; row < rows; row += 1) {
        const v = row / (rows - 1);
        const left: readonly [number, number] = [
          mix(corners.upper_left[0], corners.lower_left[0], v),
          mix(corners.upper_left[1], corners.lower_left[1], v),
        ];
        const right: readonly [number, number] = [
          mix(corners.upper_right[0], corners.lower_right[0], v),
          mix(corners.upper_right[1], corners.lower_right[1], v),
        ];
        for (let column = 0; column < columns; column += 1) {
          const u = column / (columns - 1);
          const point = this.#projectPosition([
            mix(left[0], right[0], u),
            mix(left[1], right[1], u),
          ]);
          if (layer === 0) this.#headGroundY.push(point.y);
          const packed =
            this.#tvgwfmHeads.values[firstLayerOffset + row * columns + column];
          vertices.push(
            point.x,
            packed === inactive
              ? -200
              : this.#headWorldY(packed!, point.y, layer),
            point.z,
          );
        }
      }
      const active = (row: number, column: number): boolean =>
        this.#tvgwfmHeads.values[firstLayerOffset + row * columns + column] !==
        inactive;
      for (let row = 0; row < rows - 1; row += 1) {
        for (let column = 0; column < columns - 1; column += 1) {
          const a = row * columns + column;
          const b = a + 1;
          const c = a + columns;
          const d = c + 1;
          if (
            active(row, column) &&
            active(row, column + 1) &&
            active(row + 1, column)
          )
            indices.push(a, c, b);
          if (
            active(row, column + 1) &&
            active(row + 1, column) &&
            active(row + 1, column + 1)
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
      const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color().setHSL(0.54 + layer * 0.018, 0.78, 0.57),
        emissive: new THREE.Color().setHSL(0.56, 0.62, 0.12),
        emissiveIntensity: 0.5,
        transparent: true,
        opacity: 0.5 - layer * 0.045,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.name = `tvgwfm-head-layer-${layer + 1}`;
      this.#headMeshes.push(mesh);
      this.#scene.add(mesh);
    }
  }

  #updateHeadSurfaces(year: number): void {
    const manifest = this.#tvgwfmHeads.manifest;
    const slice = nearestHeadSlice(manifest, year);
    if (slice === this.#headSliceIndex) return;
    this.#headSliceIndex = slice;
    const { rows, columns, layers, inactive_value: inactive } = manifest.layout;
    const cells = rows * columns;
    for (let layer = 0; layer < layers; layer += 1) {
      const positions = this.#headMeshes[layer]?.geometry.getAttribute(
        "position",
      ) as THREE.BufferAttribute | undefined;
      if (!positions) continue;
      const offset = (slice * layers + layer) * cells;
      for (let cell = 0; cell < cells; cell += 1) {
        const packed = this.#tvgwfmHeads.values[offset + cell];
        positions.setY(
          cell,
          packed === inactive
            ? -200
            : this.#headWorldY(
                packed!,
                this.#headGroundY[cell] ??
                  previewElevation(positions.getX(cell), positions.getZ(cell)),
                layer,
              ),
        );
      }
      positions.needsUpdate = true;
      this.#headMeshes[layer]!.geometry.computeVertexNormals();
    }
  }

  #headWorldY(packed: number, groundY: number, layer: number): number {
    const layout = this.#tvgwfmHeads.manifest.layout;
    const headFeet = layout.offset_feet + packed * layout.scale_feet;
    // A documented vertical exaggeration keeps six regional head surfaces
    // legible in the cockpit; source values remain unchanged in the data pack.
    return groundY + (headFeet - 2_400) / 180 - layer * 0.82 + 2.3;
  }

  #addGridLines(): void {
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
          const start = this.#projectPosition(line[index - 1]!);
          const end = this.#projectPosition(line[index]!);
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

  #addScreeningBranches(): void {
    const vertices: number[] = [];
    const colors: number[] = [];
    for (const branch of this.#energyScreening.branches) {
      const feature = this.#grid.trans.features[branch.corridor_feature_index];
      if (feature?.properties.line_id !== branch.corridor_line_id)
        throw new Error(
          `Energy branch corridor join failed: ${branch.branch_id}`,
        );
      const color = new THREE.Color(
        energyLoadingColor(branch.loading_pct.base),
      );
      for (const line of lineParts(feature.geometry)) {
        for (let index = 1; index < line.length; index += 1) {
          const start = this.#projectPosition(line[index - 1]!);
          const end = this.#projectPosition(line[index]!);
          vertices.push(
            start.x,
            start.y + 0.34,
            start.z,
            end.x,
            end.y + 0.34,
            end.z,
          );
          colors.push(color.r, color.g, color.b, color.r, color.g, color.b);
          this.#screeningVertexBranches.push(branch, branch);
        }
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(vertices, 3),
    );
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    const material = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 1,
    });
    const lines = new THREE.LineSegments(geometry, material);
    lines.name = "screening-branches-156-interactive";
    this.#screeningBranchLines = lines;
    this.#scene.add(lines);
  }

  #addSubstations(): void {
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
      const point = this.#projectPosition(feature.geometry.coordinates);
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
      const point = this.#projectPosition(feature.geometry.coordinates);
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
