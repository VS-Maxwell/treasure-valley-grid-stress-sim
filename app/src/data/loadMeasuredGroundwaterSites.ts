import type {
  MeasuredGroundwaterSites,
  MeasuredGroundwaterSitesManifest,
} from "./measuredGroundwaterSites";

const MANIFEST_URL = new URL(
  "../../public/data/usgs-groundwater-sites-manifest.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/usgs-groundwater-sites-f32.bin",
  import.meta.url,
).href;

export async function loadMeasuredGroundwaterSites(
  signal?: AbortSignal,
): Promise<MeasuredGroundwaterSites> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const [manifestResponse, binaryResponse] = await Promise.all([
    fetch(MANIFEST_URL, request),
    fetch(BINARY_URL, request),
  ]);
  if (!manifestResponse.ok || !binaryResponse.ok)
    throw new Error("Measured groundwater site pack request failed");
  const manifest = validateMeasuredGroundwaterSitesManifest(
    await manifestResponse.json(),
  );
  const binary = await binaryResponse.arrayBuffer();
  if (binary.byteLength !== manifest.binary.bytes)
    throw new Error("Measured groundwater site binary byte count is invalid");
  const values = new Float32Array(binary);
  if (values.length !== manifest.site_count * manifest.binary.stride)
    throw new Error("Measured groundwater site binary value count is invalid");
  return { manifest, values };
}

export function validateMeasuredGroundwaterSitesManifest(
  candidate: unknown,
): MeasuredGroundwaterSitesManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("Measured groundwater site manifest is not an object");
  const manifest = candidate as Partial<MeasuredGroundwaterSitesManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "usgs-groundwater-sites-tvgwfm-v1" ||
    manifest.truth_state !== "observed" ||
    manifest.site_count !== 2849 ||
    manifest.numeric_reading_count !== 19117 ||
    manifest.binary?.encoding !== "little-endian-float32" ||
    manifest.binary.stride !== 3 ||
    manifest.binary.bytes !== 34188 ||
    !manifest.binary.sha256.match(/^[a-f0-9]{64}$/u)
  )
    throw new Error("Measured groundwater site manifest is invalid");
  return manifest as MeasuredGroundwaterSitesManifest;
}
