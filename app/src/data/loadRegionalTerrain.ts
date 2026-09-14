import type {
  RegionalTerrain,
  RegionalTerrainManifest,
} from "./regionalTerrain";

const MANIFEST_URL = new URL(
  "../../public/data/usgs-3dep-regional-terrain-manifest.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/usgs-3dep-regional-terrain-f32.bin",
  import.meta.url,
).href;

export async function loadRegionalTerrain(
  signal?: AbortSignal,
): Promise<RegionalTerrain> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const [manifestResponse, binaryResponse] = await Promise.all([
    fetch(MANIFEST_URL, request),
    fetch(BINARY_URL, request),
  ]);
  if (!manifestResponse.ok || !binaryResponse.ok)
    throw new Error("Regional terrain pack request failed");
  const manifest = validateRegionalTerrainManifest(
    await manifestResponse.json(),
  );
  const binary = await binaryResponse.arrayBuffer();
  if (binary.byteLength !== manifest.binary.bytes)
    throw new Error("Regional terrain binary byte count is invalid");
  const elevations = new Float32Array(binary);
  if (elevations.length !== manifest.mesh.vertex_count)
    throw new Error("Regional terrain binary value count is invalid");
  return { manifest, elevations };
}

export function validateRegionalTerrainManifest(
  candidate: unknown,
): RegionalTerrainManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("Regional terrain manifest is not an object");
  const manifest = candidate as Partial<RegionalTerrainManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "usgs-3dep-regional-terrain-v1" ||
    manifest.truth_state !== "observed" ||
    manifest.horizontal_datum !== "NAD83" ||
    manifest.vertical_datum !== "NAVD88" ||
    manifest.elevation_unit !== "meters" ||
    manifest.mesh?.rows !== 101 ||
    manifest.mesh.columns !== 151 ||
    manifest.mesh.vertex_count !== 15_251 ||
    manifest.binary?.encoding !== "little-endian-float32" ||
    manifest.binary.bytes !== 61_004 ||
    !/^[a-f0-9]{64}$/u.test(manifest.binary.sha256 ?? "") ||
    !/^[a-f0-9]{64}$/u.test(manifest.source_receipt_sha256 ?? "")
  )
    throw new Error("Regional terrain manifest is invalid");
  return manifest as RegionalTerrainManifest;
}
