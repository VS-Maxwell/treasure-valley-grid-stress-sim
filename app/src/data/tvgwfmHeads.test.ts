import { describe, expect, it } from "vitest";

import {
  nearestHeadSlice,
  validateTvgwfmHeadManifest,
} from "./loadTvgwfmHeads";

function manifest() {
  const slices = Array.from({ length: 16 }, (_, index) => ({
    stress_period: index + 1,
    period_end_date: `${1987 + index * 2}-01-01`,
    year: index === 15 ? 2015 : 1986 + index * 2,
    layers: [],
  }));
  return {
    schema_version: 1,
    id: "tvgwfm-heads-biennial-v1",
    truth_state: "modeled-screening",
    layout: {
      encoding: "little-endian-uint16",
      order: "slice-layer-row-column",
      rows: 64,
      columns: 65,
      layers: 6,
      slices: 16,
      value_count: 399_360,
      bytes: 798_720,
      offset_feet: 1800,
      scale_feet: 0.1,
      inactive_value: 65_535,
    },
    slices,
    binary: { file: "heads.bin", sha256: "b".repeat(64) },
    limitations: ["test"],
  };
}

describe("TVGWFM head time-series contracts", () => {
  it("accepts the bounded browser layout", () => {
    expect(validateTvgwfmHeadManifest(manifest()).layout.bytes).toBe(798_720);
  });

  it("chooses the nearest available historical slice", () => {
    const parsed = validateTvgwfmHeadManifest(manifest());
    expect(parsed.slices[nearestHeadSlice(parsed, 2009)]?.year).toBe(2008);
    expect(parsed.slices[nearestHeadSlice(parsed, 2026)]?.year).toBe(2015);
  });

  it("rejects an unbounded binary layout", () => {
    const broken = manifest();
    broken.layout.bytes = 20_000_000;
    expect(() => validateTvgwfmHeadManifest(broken)).toThrow(/layout/u);
  });
});
