export interface MeasuredGroundwaterYear {
  readonly year: number;
  readonly measurement_count: number;
  readonly monitoring_location_count: number;
  readonly minimum_depth_ft: number;
  readonly p25_depth_ft: number;
  readonly median_depth_ft: number;
  readonly p75_depth_ft: number;
  readonly maximum_depth_ft: number;
  readonly approval_status_counts: Readonly<Record<string, number>>;
}

export interface MeasuredGroundwater {
  readonly schema_version: 1;
  readonly id: "usgs-groundwater-depth-annual-1986-2015-v1";
  readonly truth_state: "observed";
  readonly parameter_code: "72019";
  readonly unit: "feet below land surface";
  readonly aggregation: string;
  readonly source_receipt: string;
  readonly source_receipt_sha256: string;
  readonly source_measurement_count: number;
  readonly numeric_measurement_count: number;
  readonly excluded_null_value_count: number;
  readonly year_count: number;
  readonly years: readonly MeasuredGroundwaterYear[];
  readonly limitations: readonly string[];
}
