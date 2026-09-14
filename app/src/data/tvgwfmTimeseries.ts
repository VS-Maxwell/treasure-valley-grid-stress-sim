export interface TvgwfmBudgetRow {
  readonly stress_period: number;
  readonly period_end_date: string;
  readonly model_time_days: number;
  readonly cumulative_in_ft3: number;
  readonly cumulative_out_ft3: number;
  readonly cumulative_delta_ft3: number;
  readonly rate_in_ft3_per_day: number;
  readonly rate_out_ft3_per_day: number;
  readonly rate_delta_ft3_per_day: number;
  readonly cumulative_discrepancy_percent: number;
  readonly rate_discrepancy_percent: number;
}

export interface TvgwfmTimeseries {
  readonly schema_version: 1;
  readonly id: "tvgwfm-historical-tables-v1";
  readonly truth_state: "modeled-screening";
  readonly source: {
    readonly model_listing: string;
    readonly model_listing_sha256: string;
    readonly baseline_receipt_sha256: string;
  };
  readonly budget: {
    readonly units: Record<string, string>;
    readonly rows: readonly TvgwfmBudgetRow[];
  };
  readonly observations: Record<
    string,
    {
      readonly row_count: number;
      readonly series_count: number;
      readonly source_sha256: string;
      readonly columns: Record<string, readonly number[]>;
    }
  >;
  readonly limitations: readonly string[];
}
