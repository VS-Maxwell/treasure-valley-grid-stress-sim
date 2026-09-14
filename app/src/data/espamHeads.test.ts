import { describe, expect, it } from "vitest";

import {
  nearestEspamHeadSlice,
  validateEspamHeadsManifest,
} from "./loadEspamHeads";

describe("ESPAM archived heads", () => {
  const slices = Array.from({ length: 39 }, (_, index) => ({
    year: 1980 + index,
    month: 9,
    stress_period: 6 + index * 12,
    value_offset: index * 11_236,
    value_count: 11_236,
    minimum_feet: 2_500,
    maximum_feet: 6_500,
  }));
  const manifest = {
    schema_version: 1,
    id: "idwr-espam22-archived-heads-v1",
    truth_state: "ingested",
    representation: "archived-modeled-output-not-independently-reproduced",
    source_head_record_count: 923,
    active_cell_count: 11_236,
    slice_count: 39,
    quantization: {
      scale_feet: 0.1,
      offset_feet: 2_400,
      missing_sentinel: 65_535,
    },
    binary: {
      bytes: 876_408,
      encoding: "little-endian-uint16",
      sha256: "a".repeat(64),
    },
    slices,
  };

  it("accepts the exact preserved contract and selects the nearest year", () => {
    const valid = validateEspamHeadsManifest(manifest);
    expect(nearestEspamHeadSlice(valid, 2007)).toBe(27);
  });

  it("rejects a claimed reproduced representation", () => {
    expect(() =>
      validateEspamHeadsManifest({
        ...manifest,
        representation: "validated-model",
      }),
    ).toThrow("invalid");
  });
});
