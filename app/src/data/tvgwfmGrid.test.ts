import { describe, expect, it } from "vitest";

import { validateTvgwfmGrid } from "./loadTvgwfmGrid";

function candidate() {
  return {
    schema_version: 1,
    id: "usgs-tvgwfm-grid-v1",
    title: "test",
    provider: "USGS",
    doi: "10.5066/P9U6OOPH",
    rights: "CC0-1.0",
    truth_state: "ingested",
    source_archive: {
      name: "model.zip",
      sha256: "a".repeat(64),
      bytes: 6_744_282,
    },
    grid: {
      layers: 6,
      rows: 64,
      columns: 65,
      length_units: "feet",
      x_origin: 1,
      y_origin: 2,
      rotation_degrees: -2,
      cell_widths: Array(65).fill(5280),
      cell_heights: Array(64).fill(5280),
      corners_wgs84: {
        upper_left: [-117, 44],
        upper_right: [-116, 44],
        lower_right: [-116, 43],
        lower_left: [-117, 43],
      },
      top_elevation_feet: Array(64 * 65).fill(2200),
      active_top_cells: 64 * 65,
      top_min_feet: 2200,
      top_max_feet: 2200,
    },
    limitations: ["test"],
  };
}

describe("validateTvgwfmGrid", () => {
  it("accepts the official grid dimensions and source receipt", () => {
    expect(validateTvgwfmGrid(candidate()).grid.layers).toBe(6);
  });

  it("rejects an incomplete top array", () => {
    const broken = candidate();
    broken.grid.top_elevation_feet.pop();
    expect(() => validateTvgwfmGrid(broken)).toThrow(/incomplete/u);
  });

  it("rejects a mismatched active-cell receipt", () => {
    const broken = candidate();
    broken.grid.active_top_cells = 10;
    expect(() => validateTvgwfmGrid(broken)).toThrow(/active-cell/u);
  });
});
