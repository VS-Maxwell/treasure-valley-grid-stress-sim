export type EiaTechnologyCategory =
  | "hydropower"
  | "solar"
  | "wind"
  | "storage"
  | "natural-gas"
  | "geothermal"
  | "biomass"
  | "petroleum"
  | "nuclear"
  | "other";

export type EiaGeneratorLifecycle =
  "operable" | "proposed" | "retired" | "canceled" | "indefinitely-postponed";

export interface EiaRegionalEnergyManifest {
  readonly schema_version: 1;
  readonly id: "eia860-2025-snake-plain-regional-energy-points-v1";
  readonly truth_state: "ingested";
  readonly normalized_table: string;
  readonly normalized_table_sha256: string;
  readonly bbox_epsg_4326: readonly [number, number, number, number];
  readonly plant_count: 190;
  readonly plants_with_generators: 190;
  readonly generator_count: 335;
  readonly generator_lifecycle_counts: Readonly<
    Record<EiaGeneratorLifecycle, number>
  >;
  readonly generator_technology_counts: Readonly<
    Record<EiaTechnologyCategory, number>
  >;
  readonly reported_nameplate_capacity_mw_by_lifecycle: Readonly<
    Record<EiaGeneratorLifecycle, number>
  >;
  readonly technology_codes: Readonly<Record<EiaTechnologyCategory, number>>;
  readonly lifecycle_codes: Readonly<Record<EiaGeneratorLifecycle, number>>;
  readonly binary: {
    readonly file: string;
    readonly bytes: 6700;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
    readonly stride: 5;
    readonly order: "longitude-latitude-reported-nameplate-capacity-mw-technology-code-lifecycle-code";
  };
  readonly limitations: readonly string[];
}

export interface EiaRegionalEnergy {
  readonly manifest: EiaRegionalEnergyManifest;
  readonly values: Float32Array;
}
