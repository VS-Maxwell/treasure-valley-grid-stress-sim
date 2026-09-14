export interface EiaHydropowerManifest {
  readonly schema_version: 1;
  readonly id: "eia860-2025-snake-plain-hydropower-points-v1";
  readonly truth_state: "ingested";
  readonly normalized_table: string;
  readonly normalized_table_sha256: string;
  readonly bbox_epsg_4326: readonly [number, number, number, number];
  readonly plant_count: 77;
  readonly generator_count: 167;
  readonly operable_plant_count: 76;
  readonly reported_nameplate_capacity_mw: number;
  readonly dam_candidate_counts: {
    readonly "strong-candidate-pending-review": 41;
    readonly "candidate-pending-review": 11;
    readonly unmatched: 3;
  };
  readonly dam_link_review_state: "pending-human-review";
  readonly binary: {
    readonly file: string;
    readonly bytes: 1232;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
    readonly stride: 4;
    readonly order: "longitude-latitude-reported-nameplate-capacity-mw-operable-flag";
  };
  readonly limitations: readonly string[];
}

export interface EiaHydropower {
  readonly manifest: EiaHydropowerManifest;
  readonly values: Float32Array;
}
