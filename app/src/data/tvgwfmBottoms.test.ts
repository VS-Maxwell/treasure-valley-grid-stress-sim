import { describe, expect, it } from "vitest";

import { validateTvgwfmBottomsManifest } from "./loadTvgwfmBottoms";

describe("validateTvgwfmBottomsManifest", () => {
  it("rejects an incomplete bottom-surface pack", () => {
    expect(() =>
      validateTvgwfmBottomsManifest({
        schema_version: 1,
        id: "usgs-tvgwfm-layer-bottoms-v1",
        truth_state: "ingested",
        doi: "10.5066/P9U6OOPH",
        layout: {
          layers: 6,
          rows: 64,
          columns: 65,
          cell_count: 4160,
          vertical_datum: "NAVD88",
        },
        bottoms_binary: { bytes: 4, sha256: "a".repeat(64) },
        idomain_binary: { bytes: 24_960, sha256: "b".repeat(64) },
        layer_statistics: Array(6).fill({}),
      }),
    ).toThrow("invalid");
  });
});
