import type { EnergyScenario } from "../contracts";

export const ENERGY_SCENARIOS = [
  "base",
  "dc25",
  "dc50",
  "all25",
  "all50",
  "drought",
  "n1",
] as const;

export interface EnergyBus {
  readonly bus_id: string;
  readonly label: string;
  readonly display_label: string;
  readonly label_is_unique: boolean;
  readonly source_feature_index: number;
  readonly longitude: number;
  readonly latitude: number;
  readonly minimum_voltage_kv: number;
  readonly maximum_voltage_kv: number;
  readonly mapped_corridor_count: number;
  readonly truth_state: "ingested";
}

export interface EnergyBranch {
  readonly branch_id: string;
  readonly corridor_line_id: string;
  readonly corridor_feature_index: number;
  readonly display_name: string;
  readonly from_bus_label: string;
  readonly to_bus_label: string;
  readonly from_bus_candidates: readonly string[];
  readonly to_bus_candidates: readonly string[];
  readonly endpoint_identity_state: "unique-label" | "ambiguous-label";
  readonly voltage_kv: number;
  readonly loading_pct: Readonly<Record<EnergyScenario, number>>;
  readonly n1: {
    readonly converged: boolean;
    readonly maximum_loading_pct: number;
    readonly overload_count: number;
  };
  readonly truth_state: "modeled-screening";
}

export interface EnergyScenarioSummary {
  readonly maximum_loading_pct: number;
  readonly median_loading_pct: number;
  readonly branches_at_or_above_80_pct: number;
  readonly branches_at_or_above_100_pct: number;
}

export interface EnergyScreeningModel {
  readonly schema_version: 1;
  readonly id: string;
  readonly source: string;
  readonly source_legacy_sha256: string;
  readonly source_grid_core_sha256: string;
  readonly truth_state: "modeled-screening";
  readonly operational_use: false;
  readonly counts: {
    readonly buses: number;
    readonly branches: number;
    readonly map_corridors: number;
    readonly branches_with_unique_endpoint_labels: number;
    readonly branches_with_ambiguous_endpoint_labels: number;
  };
  readonly scenarios: readonly EnergyScenario[];
  readonly scenario_summaries: Readonly<
    Record<EnergyScenario, EnergyScenarioSummary>
  >;
  readonly buses: readonly EnergyBus[];
  readonly branches: readonly EnergyBranch[];
  readonly limitations: readonly string[];
}

export function energyLoadingColor(loadingPct: number): number {
  if (loadingPct >= 150) return 0xff274f;
  if (loadingPct >= 100) return 0xff654b;
  if (loadingPct >= 80) return 0xffc247;
  if (loadingPct >= 50) return 0x63e5c5;
  return 0x54b9ff;
}
