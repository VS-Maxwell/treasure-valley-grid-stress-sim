export const SCENE_IDS = [
  "time",
  "water",
  "energy",
  "nexus",
  "risk",
  "record",
  "learning",
] as const;

export type SceneId = (typeof SCENE_IDS)[number];

export type TruthState =
  | "observed"
  | "ingested"
  | "reconstructed"
  | "modeled-screening"
  | "validated-model"
  | "synthetic"
  | "blocked-missing";

export type ClimateScenario = "historical" | "baseline" | "heat-drought-2050";
export type EnergyScenario =
  "base" | "dc25" | "dc50" | "all25" | "all50" | "drought" | "n1";

export interface SimulationState {
  readonly scene: SceneId;
  readonly year: number;
  readonly playing: boolean;
  readonly compare: boolean;
  readonly drawer: "closed" | "evidence" | "ask";
  readonly climateScenario: ClimateScenario;
  readonly energyScenario: EnergyScenario;
  readonly truthState: TruthState;
}

export interface SourceRecord {
  readonly id: string;
  readonly title: string;
  readonly provider: string;
  readonly retrievedAt: string;
  readonly sha256: string;
  readonly truthState: TruthState;
  readonly access: "public" | "internal" | "restricted";
}

export interface ScenarioDefinition {
  readonly id: string;
  readonly title: string;
  readonly startYear: number;
  readonly endYear: number;
  readonly climateScenario: ClimateScenario;
  readonly assumptions: readonly string[];
  readonly truthState: TruthState;
}

export interface RunReceipt {
  readonly runId: string;
  readonly createdAt: string;
  readonly engine: string;
  readonly engineVersion: string;
  readonly inputSha256: string;
  readonly outputSha256: string;
  readonly seed: number;
  readonly accepted: boolean;
}

export const INITIAL_STATE: SimulationState = {
  scene: "energy",
  year: 2026,
  playing: false,
  compare: false,
  drawer: "closed",
  climateScenario: "baseline",
  energyScenario: "base",
  truthState: "ingested",
};

export function clampYear(year: number): number {
  return Math.max(-15_000, Math.min(2100, Math.round(year)));
}

export function truthStateForYear(year: number): TruthState {
  if (year < 1800) return "reconstructed";
  if (year > 2026) return "modeled-screening";
  return "observed";
}

export function truthStateForView(scene: SceneId, year: number): TruthState {
  switch (scene) {
    case "time":
      return truthStateForYear(year);
    case "energy":
    case "record":
      return "ingested";
    case "water":
    case "nexus":
      return "modeled-screening";
    case "risk":
    case "learning":
      return "blocked-missing";
  }
}

export function isSceneId(value: string): value is SceneId {
  return (SCENE_IDS as readonly string[]).includes(value);
}
