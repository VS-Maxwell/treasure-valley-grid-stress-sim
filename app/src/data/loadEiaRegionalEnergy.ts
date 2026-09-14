import type {
  EiaGeneratorLifecycle,
  EiaRegionalEnergy,
  EiaRegionalEnergyManifest,
  EiaTechnologyCategory,
} from "./eiaRegionalEnergy";

const MANIFEST_URL = new URL(
  "../../public/data/eia-regional-energy-manifest-v1.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/eia-regional-energy-f32-v1.bin",
  import.meta.url,
).href;

const TECHNOLOGIES: readonly EiaTechnologyCategory[] = [
  "hydropower",
  "solar",
  "wind",
  "storage",
  "natural-gas",
  "geothermal",
  "biomass",
  "petroleum",
  "nuclear",
  "other",
];
const LIFECYCLES: readonly EiaGeneratorLifecycle[] = [
  "operable",
  "proposed",
  "retired",
  "canceled",
  "indefinitely-postponed",
];

async function fetchChecked(url: string): Promise<Response> {
  const response = await fetch(url);
  if (!response.ok)
    throw new Error(`EIA regional energy request failed (${response.status})`);
  return response;
}

export function validateEiaRegionalEnergyManifest(
  candidate: unknown,
): asserts candidate is EiaRegionalEnergyManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("EIA regional energy manifest is invalid");
  const manifest = candidate as Partial<EiaRegionalEnergyManifest>;
  const lifecycleTotal = LIFECYCLES.reduce(
    (total, key) => total + (manifest.generator_lifecycle_counts?.[key] ?? 0),
    0,
  );
  const technologyTotal = TECHNOLOGIES.reduce(
    (total, key) => total + (manifest.generator_technology_counts?.[key] ?? 0),
    0,
  );
  const technologyCodes = TECHNOLOGIES.every(
    (key, index) => manifest.technology_codes?.[key] === index,
  );
  const lifecycleCodes = LIFECYCLES.every(
    (key, index) => manifest.lifecycle_codes?.[key] === index,
  );
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "eia860-2025-snake-plain-regional-energy-points-v1" ||
    manifest.truth_state !== "ingested" ||
    manifest.plant_count !== 190 ||
    manifest.plants_with_generators !== 190 ||
    manifest.generator_count !== 335 ||
    lifecycleTotal !== 335 ||
    technologyTotal !== 335 ||
    manifest.generator_lifecycle_counts?.operable !== 287 ||
    manifest.generator_lifecycle_counts.proposed !== 18 ||
    manifest.generator_lifecycle_counts.retired !== 14 ||
    manifest.generator_lifecycle_counts.canceled !== 15 ||
    manifest.generator_lifecycle_counts["indefinitely-postponed"] !== 1 ||
    !technologyCodes ||
    !lifecycleCodes ||
    manifest.binary?.stride !== 5 ||
    manifest.binary.bytes !== 6_700 ||
    !/^[a-f0-9]{64}$/u.test(manifest.binary.sha256 ?? "")
  )
    throw new Error("EIA regional energy manifest is invalid");
}

export async function loadEiaRegionalEnergy(): Promise<EiaRegionalEnergy> {
  const manifest = (await (await fetchChecked(MANIFEST_URL)).json()) as unknown;
  validateEiaRegionalEnergyManifest(manifest);
  const bytes = await (await fetchChecked(BINARY_URL)).arrayBuffer();
  if (bytes.byteLength !== manifest.binary.bytes)
    throw new Error("EIA regional energy binary byte count is invalid");
  const values = new Float32Array(bytes);
  if (values.length !== manifest.generator_count * manifest.binary.stride)
    throw new Error("EIA regional energy binary dimensions are invalid");
  return { manifest, values };
}
