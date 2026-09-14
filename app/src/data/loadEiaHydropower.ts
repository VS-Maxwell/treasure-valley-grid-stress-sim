import type { EiaHydropower, EiaHydropowerManifest } from "./eiaHydropower";

const MANIFEST_URL = new URL(
  "../../public/data/eia-hydropower-manifest-v1.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/eia-hydropower-f32-v1.bin",
  import.meta.url,
).href;

async function fetchChecked(url: string): Promise<Response> {
  const response = await fetch(url);
  if (!response.ok)
    throw new Error(`EIA hydropower request failed (${response.status})`);
  return response;
}

export function validateEiaHydropowerManifest(
  candidate: unknown,
): asserts candidate is EiaHydropowerManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("EIA hydropower manifest is invalid");
  const manifest = candidate as Partial<EiaHydropowerManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "eia860-2025-snake-plain-hydropower-points-v1" ||
    manifest.truth_state !== "ingested" ||
    manifest.plant_count !== 77 ||
    manifest.generator_count !== 167 ||
    manifest.operable_plant_count !== 76 ||
    manifest.dam_link_review_state !== "pending-human-review" ||
    manifest.binary?.stride !== 4 ||
    manifest.binary.bytes !== 1_232 ||
    !/^[a-f0-9]{64}$/u.test(manifest.binary.sha256 ?? "")
  )
    throw new Error("EIA hydropower manifest is invalid");
}

export async function loadEiaHydropower(): Promise<EiaHydropower> {
  const manifest = (await (await fetchChecked(MANIFEST_URL)).json()) as unknown;
  validateEiaHydropowerManifest(manifest);
  const bytes = await (await fetchChecked(BINARY_URL)).arrayBuffer();
  if (bytes.byteLength !== manifest.binary.bytes)
    throw new Error("EIA hydropower binary byte count is invalid");
  const values = new Float32Array(bytes);
  if (values.length !== manifest.plant_count * manifest.binary.stride)
    throw new Error("EIA hydropower binary dimensions are invalid");
  return { manifest, values };
}
