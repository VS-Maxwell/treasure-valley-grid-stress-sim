import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import "./style.css";
import terrain from "../data/usgs-3dep-snake-plain-terrain-manifest-v4.json";
import water from "../data/tvgwfm-heads-manifest.json";
import baseline from "../data/tvgwfm-baseline-summary.json";
import energy from "../data/eia-regional-energy-manifest-v1.json";
import terrainUrl from "../data/usgs-3dep-snake-plain-terrain-f32-v4.bin?url";
import energyUrl from "../data/eia-regional-energy-f32-v1.bin?url";

const element = (id) => document.getElementById(id);
const canvas = element("scene");
const scene = new THREE.Scene();
scene.background = new THREE.Color("#213f53");
scene.fog = new THREE.Fog("#213f53", 10, 26);
const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
camera.up.set(0, 0, 1);
camera.position.set(0, -5.5, 5.5);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.minDistance = 4;
controls.maxDistance = 22;
controls.target.set(0, 0, 0);
scene.add(new THREE.HemisphereLight(0xd5f7ff, 0x17334b, 2.2));
const sun = new THREE.DirectionalLight(0xffffff, 2.1);
sun.position.set(-3, -2, 8);
scene.add(sun);
let terrainMesh;
let energyMarkers;
let activeLayer = "terrain";
let activeYear = 0;
let error = false;

function resize() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
function frame() {
  if (error) return;
  controls.update();
  resize();
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
async function verifiedFloats(url, expected) {
  const response = await fetch(url);
  if (!response.ok) throw new Error("A public source pack could not be loaded.");
  const bytes = await response.arrayBuffer();
  const hash = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
    .map((value) => value.toString(16).padStart(2, "0")).join("");
  if (hash !== expected) throw new Error("A public source pack failed its SHA-256 receipt.");
  return new Float32Array(bytes);
}
function terrainPosition(lon, lat, heights) {
  const bounds = terrain.mesh.bounds_wgs84;
  const x = ((lon - bounds.west) / (bounds.east - bounds.west)) * 8 - 4;
  const y = ((lat - bounds.south) / (bounds.north - bounds.south)) * 4 - 2;
  const col = Math.max(0, Math.min(terrain.mesh.columns - 1, Math.round((lon - bounds.west) / 8 * (terrain.mesh.columns - 1))));
  const row = Math.max(0, Math.min(terrain.mesh.rows - 1, Math.round((bounds.north - lat) / 4 * (terrain.mesh.rows - 1))));
  const elevation = heights[row * terrain.mesh.columns + col];
  const z = (elevation - terrain.statistics.mean_meters) / 3000 + 0.05;
  return [x, y, z];
}
function drawTerrain(heights) {
  const columns = terrain.mesh.columns;
  const rows = terrain.mesh.rows;
  if (heights.length !== rows * columns) throw new Error("Terrain dimensions do not match the source manifest.");
  const geometry = new THREE.PlaneGeometry(8, 4, columns - 1, rows - 1);
  const positions = geometry.getAttribute("position");
  const colors = new Float32Array(heights.length * 3);
  const low = new THREE.Color("#123d67");
  const high = new THREE.Color("#3d82ba");
  const color = new THREE.Color();
  for (let i = 0; i < heights.length; i++) {
    const value = heights[i];
    positions.setZ(i, (value - terrain.statistics.mean_meters) / 3000);
    const t = Math.max(0, Math.min(1, (value - 200) / 3200));
    color.copy(low).lerp(high, t);
    colors.set([color.r, color.g, color.b], i * 3);
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.computeVertexNormals();
  terrainMesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: 0.95, side: THREE.DoubleSide,
  }));
  scene.add(terrainMesh);
}
function drawEnergy(values, heights) {
  const stride = energy.binary.stride;
  if (values.length !== energy.generator_count * stride) throw new Error("Energy point count does not match the EIA manifest.");
  const geometry = new THREE.SphereGeometry(0.028, 7, 5);
  const material = new THREE.MeshBasicMaterial({ color: 0xffffff });
  energyMarkers = new THREE.InstancedMesh(geometry, material, energy.generator_count);
  const marker = new THREE.Object3D();
  const blue = new THREE.Color("#54e6ff");
  const amber = new THREE.Color("#ffc363");
  for (let i = 0; i < energy.generator_count; i++) {
    const at = i * stride;
    const [x, y, z] = terrainPosition(values[at], values[at + 1], heights);
    const capacity = Math.max(0, values[at + 2]);
    marker.position.set(x, y, z + 0.08);
    marker.scale.setScalar(Math.min(3.5, 0.7 + Math.sqrt(capacity) / 12));
    marker.updateMatrix();
    energyMarkers.setMatrixAt(i, marker.matrix);
    energyMarkers.setColorAt(i, values[at + 4] === 0 ? blue : amber);
  }
  energyMarkers.instanceMatrix.needsUpdate = true;
  scene.add(energyMarkers);
  energyMarkers.visible = false;
}
function readout() {
  const truth = element("truth");
  const title = element("readout-title");
  const copy = element("readout-copy");
  const metric = element("metric");
  const source = element("source");
  const yearInput = element("year");
  yearInput.disabled = activeLayer !== "water";
  energyMarkers.visible = activeLayer === "energy";
  if (activeLayer === "terrain") {
    truth.textContent = "OBSERVED";
    title.textContent = "USGS Snake Plain elevation";
    copy.textContent = "Terrain samples from 32 USGS 3DEP tiles across 119°W–111°W and 42°N–46°N. Relief is exaggerated for visibility.";
    metric.textContent = terrain.mesh.vertex_count.toLocaleString() + " source vertices";
    source.textContent = "Source: USGS 3D Elevation Program. Elevation is in meters NAVD88; no new forecast is computed.";
  } else if (activeLayer === "water") {
    const slice = water.slices[activeYear];
    const top = slice.layers[0];
    truth.textContent = "MODELED SCREENING";
    title.textContent = "TVGWFM historical groundwater";
    copy.textContent = "Published USGS model baseline, numerically reproduced. Year and layer-one head statistics change with the selected archived slice.";
    metric.textContent = Math.round(top.mean_feet).toLocaleString() + " ft mean model head";
    source.textContent = "USGS TVGWFM · DOI " + baseline.doi + " · " + baseline.stress_periods + " stress periods. " + baseline.acceptance_boundary;
    element("year-label").textContent = String(slice.year);
  } else {
    truth.textContent = "INGESTED";
    title.textContent = "EIA reported energy records";
    copy.textContent = "The dots are final 2025 EIA-860 generator locations. Blue indicates operable; amber marks other reported lifecycle states. No grid connections are inferred.";
    metric.textContent = energy.generator_count.toLocaleString() + " generators";
    source.textContent = "Source: U.S. Energy Information Administration Form EIA-860. Reported capacity and lifecycle are records, not simulated output.";
  }
  for (const button of document.querySelectorAll("[data-layer]")) {
    button.setAttribute("aria-pressed", String(button.dataset.layer === activeLayer));
  }
}
async function start() {
  const heights = await verifiedFloats(terrainUrl, terrain.binary.sha256);
  const energyValues = await verifiedFloats(energyUrl, energy.binary.sha256);
  drawTerrain(heights);
  drawEnergy(energyValues, heights);
  const yearInput = element("year");
  yearInput.max = String(water.slices.length - 1);
  yearInput.addEventListener("input", () => {
    activeYear = Number(yearInput.value);
    readout();
  });
  for (const button of document.querySelectorAll("[data-layer]")) {
    button.addEventListener("click", () => {
      activeLayer = button.dataset.layer;
      readout();
    });
  }
  readout();
  frame();
}
start().catch((cause) => {
  error = true;
  const panel = element("error");
  panel.hidden = false;
  panel.textContent = cause instanceof Error ? cause.message : "The public preview could not load.";
});
