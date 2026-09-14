export interface MeasuredGroundwaterSitesManifest {
  readonly schema_version: 1;
  readonly id: "usgs-groundwater-sites-tvgwfm-v1";
  readonly truth_state: "observed";
  readonly horizontal_method: string;
  readonly vertical_method: string;
  readonly field_receipt_sha256: string;
  readonly location_receipt_sha256: string;
  readonly grid_sha256: string;
  readonly site_count: number;
  readonly numeric_reading_count: number;
  readonly source_null_reading_count: number;
  readonly exclusions: Readonly<Record<string, number>>;
  readonly binary: {
    readonly file: string;
    readonly sha256: string;
    readonly bytes: number;
    readonly encoding: "little-endian-float32";
    readonly order: "site-longitude-latitude-water-level-altitude-navd88-feet";
    readonly stride: 3;
  };
  readonly limitations: readonly string[];
}

export interface MeasuredGroundwaterSites {
  readonly manifest: MeasuredGroundwaterSitesManifest;
  readonly values: Float32Array;
}
