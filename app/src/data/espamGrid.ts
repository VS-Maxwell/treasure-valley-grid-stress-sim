import type { GeoBounds } from "./geo";

export interface EspamGridManifest {
  readonly schema_version: 1;
  readonly id: "idwr-espam22-grid-v1";
  readonly truth_state: "ingested";
  readonly provider: string;
  readonly model: string;
  readonly source_grid_receipt: string;
  readonly source_grid_receipt_sha256: string;
  readonly source_model_receipt: string;
  readonly source_model_receipt_sha256: string;
  readonly layout: {
    readonly layers: 1;
    readonly rows: 104;
    readonly columns: 209;
    readonly stress_periods: 462;
    readonly cell_width_feet: 5280;
    readonly cell_height_feet: 5280;
    readonly active_cells: 11236;
    readonly row_id_range: readonly [number, number];
    readonly column_id_range: readonly [number, number];
  };
  readonly bounds_wgs84: GeoBounds;
  readonly line_binary: {
    readonly file: string;
    readonly bytes: number;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
    readonly stride: 4;
    readonly record_count: number;
    readonly fields: readonly string[];
  };
  readonly cell_binary: {
    readonly file: string;
    readonly bytes: number;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
    readonly stride: 4;
    readonly record_count: number;
    readonly fields: readonly string[];
  };
  readonly limitations: readonly string[];
}

export interface EspamGrid {
  readonly manifest: EspamGridManifest;
  readonly lines: Float32Array;
  readonly cells: Float32Array;
}
