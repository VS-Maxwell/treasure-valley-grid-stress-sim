import { describe, expect, it } from "vitest";

import { validateRegionalTerrainManifest } from "./loadRegionalTerrain";
import {
  terrainWorldHeight,
  terrainWorldHeightAt,
  type RegionalTerrain,
} from "./regionalTerrain";

const terrain: RegionalTerrain = {
  manifest: {
    schema_version: 1,
    id: "usgs-3dep-snake-plain-terrain-v4",
    truth_state: "observed",
    provider: "USGS",
    product: "1 arc-second seamless DEM",
    source_receipt: "receipt.json",
    source_receipt_sha256: "a".repeat(64),
    horizontal_datum: "NAD83",
    vertical_datum: "NAVD88",
    elevation_unit: "meters",
    mesh: {
      rows: 201,
      columns: 401,
      vertex_count: 80_601,
      bounds_wgs84: { west: -119, east: -111, south: 42, north: 46 },
    },
    statistics: {
      minimum_meters: 500,
      maximum_meters: 2_500,
      mean_meters: 1_200,
    },
    binary: {
      file: "terrain.bin",
      bytes: 322_404,
      sha256: "b".repeat(64),
      encoding: "little-endian-float32",
      order: "row-major-northwest-to-southeast-elevation-meters",
    },
    render_transform: {
      vertical_exaggeration: 2.2,
      world_height_span: 18,
      note: "visual transform",
    },
    limitations: [],
  },
  elevations: new Float32Array(80_601).fill(1_500),
};

describe("regional terrain", () => {
  it("maps source meters into the documented world-space span", () => {
    expect(terrainWorldHeight(terrain, 500)).toBe(-4.5);
    expect(terrainWorldHeight(terrain, 2_500)).toBe(13.5);
    expect(terrainWorldHeightAt(terrain, [-115, 44])).toBe(4.5);
    expect(terrainWorldHeightAt(terrain, [-120, 44])).toBeNull();
  });

  it("rejects a dimensionally incorrect manifest", () => {
    expect(() =>
      validateRegionalTerrainManifest({
        ...terrain.manifest,
        binary: { ...terrain.manifest.binary, bytes: 4 },
      }),
    ).toThrow("invalid");
  });
});
