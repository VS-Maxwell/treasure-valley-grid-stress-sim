import type { RegionalDams, RegionalDamsManifest } from "./regionalDams";

const MANIFEST_URL = new URL(
  "../../public/data/usace-nid-snake-plain-dams-manifest-v2.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/usace-nid-snake-plain-dams-f32-v2.bin",
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
    manifest.id !== "usace-nid-snake-plain-dam-points-v2" ||
    manifest.truth_state !== "observed" ||
    manifest.dam_count !== 647 ||
    manifest.hydroelectric_purpose_count !== 55 ||
    manifest.connectivity_state !==
      "unresolved-pending-upstream-watershed-graph" ||
    manifest.binary?.encoding !== "little-endian-float32" ||
    manifest.binary.stride !== 3 ||
    manifest.binary.bytes !== 7_764 ||
    !/^[a-f0-9]{64}$/u.test(manifest.binary.sha256 ?? "")
  )
    throw new Error("Regional NID dam manifest is invalid");
  return manifest as RegionalDamsManifest;
}
