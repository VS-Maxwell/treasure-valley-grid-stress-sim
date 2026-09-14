import type { RegionalDams, RegionalDamsManifest } from "./regionalDams";

const MANIFEST_URL = new URL(
  "../../public/data/usace-nid-snake-plain-dams-manifest-v3.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/usace-nid-snake-plain-dams-f32-v3.bin",
  import.meta.url,
).href;

export async function loadRegionalDams(
  signal?: AbortSignal,
): Promise<RegionalDams> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const [manifestResponse, binaryResponse] = await Promise.all([
    fetch(MANIFEST_URL, request),
    fetch(BINARY_URL, request),
  ]);
  if (!manifestResponse.ok || !binaryResponse.ok)
    throw new Error("Regional NID dam pack request failed");
  const manifest = validateRegionalDamsManifest(await manifestResponse.json());
  const binary = await binaryResponse.arrayBuffer();
  if (binary.byteLength !== manifest.binary.bytes)
    throw new Error("Regional NID dam binary byte count is invalid");
  const values = new Float32Array(binary);
  if (values.length !== manifest.dam_count * manifest.binary.stride)
    throw new Error("Regional NID dam binary value count is invalid");
  return { manifest, values };
}

export function validateRegionalDamsManifest(
  candidate: unknown,
): RegionalDamsManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("Regional NID dam manifest is not an object");
  const manifest = candidate as Partial<RegionalDamsManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "usace-nid-snake-plain-dam-points-v3" ||
    manifest.truth_state !== "observed-plus-network-derived" ||
    manifest.dam_count !== 647 ||
    manifest.hydroelectric_purpose_count !== 55 ||
    manifest.connected_dam_count !== 348 ||
    manifest.connected_hydroelectric_purpose_count !== 42 ||
    manifest.outside_dam_count !== 297 ||
    manifest.unresolved_dam_count !== 2 ||
    manifest.target_outlet?.nwis_site_id !== "USGS-13269000" ||
    manifest.target_outlet.outlet_comid !== 24193082 ||
    manifest.connectivity_state !==
      "directed-network-resolved-to-usgs-13269000" ||
    manifest.binary?.encoding !== "little-endian-float32" ||
    manifest.binary.stride !== 4 ||
    manifest.binary.bytes !== 10_352 ||
    !/^[a-f0-9]{64}$/u.test(manifest.binary.sha256 ?? "")
  )
    throw new Error("Regional NID dam manifest is invalid");
  return manifest as RegionalDamsManifest;
}
