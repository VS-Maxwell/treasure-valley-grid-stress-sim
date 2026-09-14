import type { Position } from "./gridTypes";

export interface TvgwfmGrid {
  readonly schema_version: 1;
  readonly id: "usgs-tvgwfm-grid-v1";
  readonly title: string;
  readonly provider: string;
  readonly doi: string;
  readonly rights: "CC0-1.0";
  readonly truth_state: "ingested";
  readonly source_archive: {
    readonly name: string;
    readonly sha256: string;
    readonly bytes: number;
  };
  readonly grid: {
    readonly layers: number;
    readonly rows: number;
    readonly columns: number;
    readonly length_units: "feet";
    readonly x_origin: number;
    readonly y_origin: number;
    readonly rotation_degrees: number;
    readonly cell_widths: readonly number[];
    readonly cell_heights: readonly number[];
    readonly corners_wgs84: {
      readonly upper_left: Position;
      readonly upper_right: Position;
      readonly lower_right: Position;
      readonly lower_left: Position;
    };
    readonly top_elevation_feet: readonly number[];
    readonly active_top_cells: number;
    readonly top_min_feet: number;
    readonly top_max_feet: number;
  };
  readonly limitations: readonly string[];
}
