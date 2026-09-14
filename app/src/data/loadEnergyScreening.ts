import { ENERGY_SCENARIOS, type EnergyScreeningModel } from "./energyScreening";

const ENERGY_SCREENING_URL = new URL(
  "../../public/data/grid-screening-model.json",
  import.meta.url,
).href;

export async function loadEnergyScreening(
  signal?: AbortSignal,
): Promise<EnergyScreeningModel> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const response = await fetch(ENERGY_SCREENING_URL, request);
  if (!response.ok)
    throw new Error(`Energy screening request failed with ${response.status}`);
  return validateEnergyScreening((await response.json()) as unknown);
}

export function validateEnergyScreening(
  candidate: unknown,
): EnergyScreeningModel {
  if (!candidate || typeof candidate !== "object")
    throw new Error("Energy screening pack is not an object");
  const record = candidate as Partial<EnergyScreeningModel>;
  if (record.schema_version !== 1)
    throw new Error("Unsupported energy screening schema version");
  if (record.operational_use !== false)
    throw new Error("Energy screening pack must reject operational use");
  if (record.buses?.length !== 94 || record.counts?.buses !== 94)
    throw new Error("Energy screening pack must contain 94 buses");
  if (record.branches?.length !== 156 || record.counts?.branches !== 156)
    throw new Error("Energy screening pack must contain 156 branches");
  if (record.counts.map_corridors !== 244)
    throw new Error("Energy screening pack must distinguish 244 map corridors");
  if (
    !record.source_legacy_sha256?.match(/^[a-f0-9]{64}$/u) ||
    !record.source_grid_core_sha256?.match(/^[a-f0-9]{64}$/u)
  )
    throw new Error("Energy screening source receipts are invalid");
  if (
    record.scenarios?.join("|") !== ENERGY_SCENARIOS.join("|") ||
    ENERGY_SCENARIOS.some((scenario) => !record.scenario_summaries?.[scenario])
  )
    throw new Error("Energy screening scenarios are incomplete");
  const branchIds = new Set(record.branches.map((branch) => branch.branch_id));
  if (branchIds.size !== 156)
    throw new Error("Energy screening branch IDs must be unique");
  if (
    record.branches.some(
      (branch) =>
        branch.corridor_line_id !== branch.branch_id ||
        ENERGY_SCENARIOS.some(
          (scenario) => !Number.isFinite(branch.loading_pct[scenario]),
        ),
    )
  )
    throw new Error("Energy branch geometry joins or loadings are invalid");
  return record as EnergyScreeningModel;
}
