export interface RegionalDamsManifest {
  readonly schema_version: 1;
  readonly id: "usace-nid-snake-plain-dam-points-v3";
  readonly truth_state: "observed-plus-network-derived";
  readonly normalized_table: string;
  readonly normalized_table_sha256: string;
  readonly network_receipt: string;
  readonly network_receipt_sha256: string;
  readonly target_outlet: {
    readonly nwis_site_id: "USGS-13269000";
    readonly outlet_comid: 24193082;
    readonly name: "Snake River at Weiser ID";
  };
  readonly bbox_epsg_4326: readonly [number, number, number, number];
  readonly dam_count: number;
  readonly hydroelectric_purpose_count: number;
  readonly connected_dam_count: number;
  readonly connected_hydroelectric_purpose_count: number;
  readonly outside_dam_count: number;
  readonly unresolved_dam_count: number;
  readonly connectivity_state: "directed-network-resolved-to-usgs-13269000";
  readonly binary: {
    readonly file: string;
    readonly bytes: number;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
    readonly stride: 4;
    readonly order: "longitude-latitude-hydroelectric-purpose-flag-connectivity-code";
    readonly connectivity_codes: Readonly<Record<string, string>>;
  };
  readonly limitations: readonly string[];
}

export interface RegionalDams {
  readonly manifest: RegionalDamsManifest;
  readonly values: Float32Array;
}
