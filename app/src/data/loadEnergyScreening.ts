import { ENERGY_SCENARIOS, type EnergyScreeningModel } from "./energyScreening";

const ENERGY_SCREENING_URL = new URL(
  "../../public/data/grid-screening-model-v2.json",
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
  if (record.schema_version !== 2)
    throw new Error("Unsupported energy screening schema version");
  if (record.operational_use !== false)
    throw new Error("Energy screening pack must reject operational use");
  if (record.fresh_solve_ready !== false)
    throw new Error("Energy screening pack must not claim a fresh solve");
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
  if (
    record.counts.topology_resolved_branches !== 139 ||
    record.counts.topology_blocked_branches !== 17 ||
    record.counts.resolved_endpoint_identities !== 292 ||
    record.counts.unresolved_endpoint_identities !== 20 ||
    record.counts.geometry_resolved_ambiguous_endpoints !== 75 ||
    record.counts.geometry_resolved_tap_buses !== 27 ||
    record.counts.resolved_graph_components !== 1
  )
    throw new Error("Energy topology resolution receipt is invalid");
  if (record.missing_solver_inputs?.length !== 4)
    throw new Error("Energy solver-input boundary is incomplete");
  const branchIds = new Set(record.branches.map((branch) => branch.branch_id));
  if (branchIds.size !== 156)
    throw new Error("Energy screening branch IDs must be unique");
  if (
    record.branches.some(
      (branch) =>
        branch.corridor_line_id !== branch.branch_id ||
        !["resolved", "blocked-missing"].includes(branch.topology_state) ||
        ENERGY_SCENARIOS.some(
          (scenario) => !Number.isFinite(branch.loading_pct[scenario]),
        ),
    )
  )
    throw new Error("Energy branch geometry joins or loadings are invalid");
  if (
    record.branches.filter((branch) => branch.topology_state === "resolved")
      .length !== 139 ||
    record.branches.some(
      (branch) =>
        branch.topology_state === "resolved" &&
        (!branch.from_bus_id ||
          !branch.to_bus_id ||
          branch.from_bus_id === branch.to_bus_id),
    )
  )
    throw new Error("Energy topology-ready branch identities are invalid");
  return record as EnergyScreeningModel;
}
