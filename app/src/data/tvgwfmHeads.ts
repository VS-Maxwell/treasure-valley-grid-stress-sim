export interface TvgwfmHeadLayerSummary {
  readonly layer: number;
  readonly active_cells: number;
  readonly min_feet: number;
  readonly max_feet: number;
  readonly mean_feet: number;
}

export interface TvgwfmHeadSlice {
  readonly stress_period: number;
  readonly period_end_date: string;
  readonly year: number;
  readonly layers: readonly TvgwfmHeadLayerSummary[];
}

export interface TvgwfmHeadManifest {
  readonly schema_version: 1;
  readonly id: "tvgwfm-heads-biennial-v1";
  readonly truth_state: "modeled-screening";
  readonly layout: {
    readonly encoding: "little-endian-uint16";
    readonly order: "slice-layer-row-column";
    readonly rows: number;
    readonly columns: number;
    readonly layers: number;
    readonly slices: number;
    readonly value_count: number;
    readonly bytes: number;
    readonly offset_feet: number;
    readonly scale_feet: number;
    readonly inactive_value: number;
  };
  readonly slices: readonly TvgwfmHeadSlice[];
  readonly binary: {
    readonly file: string;
    readonly sha256: string;
  };
  readonly limitations: readonly string[];
}

export interface TvgwfmHeads {
  readonly manifest: TvgwfmHeadManifest;
  readonly values: Uint16Array;
}
