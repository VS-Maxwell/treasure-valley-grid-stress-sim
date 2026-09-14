export interface TvgwfmBottomsManifest {
  readonly schema_version: 1;
  readonly id: "usgs-tvgwfm-layer-bottoms-v1";
  readonly truth_state: "ingested";
  readonly provider: string;
  readonly doi: "10.5066/P9U6OOPH";
  readonly source_archive: {
    readonly file: "model.zip";
    readonly sha256: string;
    readonly member: "model/mf6-tv_hist.dis";
  };
  readonly layout: {
    readonly layers: 6;
    readonly rows: 64;
    readonly columns: 65;
    readonly cell_count: 4160;
    readonly order: "layer-row-column";
    readonly length_unit: "feet";
    readonly vertical_datum: "NAVD88";
  };
  readonly bottoms_binary: {
    readonly file: string;
    readonly bytes: 99840;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
  };
  readonly idomain_binary: {
    readonly file: string;
    readonly bytes: 24960;
    readonly sha256: string;
    readonly encoding: "signed-int8";
  };
  readonly layer_statistics: readonly {
    readonly layer: number;
    readonly active_cells: number;
    readonly minimum_bottom_feet: number;
    readonly maximum_bottom_feet: number;
    readonly mean_bottom_feet: number;
  }[];
  readonly limitations: readonly string[];
}

export interface TvgwfmBottoms {
  readonly manifest: TvgwfmBottomsManifest;
  readonly bottoms: Float32Array;
  readonly idomain: Int8Array;
}
