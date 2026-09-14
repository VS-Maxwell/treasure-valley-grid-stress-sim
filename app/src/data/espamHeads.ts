export interface EspamHeadSlice {
  readonly year: number;
  readonly month: 9;
  readonly stress_period: number;
  readonly value_offset: number;
  readonly value_count: 11236;
  readonly minimum_feet: number;
  readonly maximum_feet: number;
}

export interface EspamHeadsManifest {
  readonly schema_version: 1;
  readonly id: "idwr-espam22-archived-heads-v1";
  readonly truth_state: "ingested";
  readonly representation: "archived-modeled-output-not-independently-reproduced";
  readonly model: string;
  readonly source_model_receipt: string;
  readonly source_model_receipt_sha256: string;
  readonly source_grid_receipt: string;
  readonly source_grid_receipt_sha256: string;
  readonly source_archive_member: "ESPAM_modflow/bigtrn.hds";
  readonly source_head_record_count: 923;
  readonly cell_order: "idwr-espam22-grid-cells-f32-v1";
  readonly active_cell_count: 11236;
  readonly slice_count: 39;
  readonly slices: readonly EspamHeadSlice[];
  readonly quantization: {
    readonly source_unit: "feet";
    readonly scale_feet: 0.1;
    readonly offset_feet: number;
    readonly missing_sentinel: 65535;
  };
  readonly statistics: {
    readonly minimum_feet: number;
    readonly maximum_feet: number;
  };
  readonly binary: {
    readonly file: "idwr-espam22-heads-q10-v1.bin";
    readonly bytes: 876408;
    readonly sha256: string;
    readonly encoding: "little-endian-uint16";
    readonly order: "slice-then-active-cell-service-order";
  };
  readonly limitations: readonly string[];
}

export interface EspamHeads {
  readonly manifest: EspamHeadsManifest;
  readonly values: Uint16Array;
}

export function espamHeadFeet(heads: EspamHeads, packed: number): number {
  return (
    heads.manifest.quantization.offset_feet +
    packed * heads.manifest.quantization.scale_feet
  );
}
