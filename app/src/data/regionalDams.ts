export interface RegionalDamsManifest {
  readonly schema_version: 1;
  readonly id: "usace-nid-regional-dam-points-v1";
  readonly truth_state: "observed";
  readonly source_receipt: string;
  readonly source_receipt_sha256: string;
  readonly normalized_table: string;
  readonly normalized_table_sha256: string;
  readonly bbox_epsg_4326: readonly [number, number, number, number];
  readonly dam_count: number;
  readonly hydroelectric_purpose_count: number;
  readonly connectivity_state: "unresolved-pending-upstream-watershed-graph";
  readonly binary: {
    readonly file: string;
    readonly bytes: number;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
    readonly stride: 3;
    readonly order: "longitude-latitude-hydroelectric-purpose-flag";
  };
  readonly limitations: readonly string[];
}

export interface RegionalDams {
  readonly manifest: RegionalDamsManifest;
  readonly values: Float32Array;
}
