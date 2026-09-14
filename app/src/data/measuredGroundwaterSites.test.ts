import { describe, expect, it } from "vitest";

import { validateMeasuredGroundwaterSitesManifest } from "./loadMeasuredGroundwaterSites";

describe("validateMeasuredGroundwaterSitesManifest", () => {
  it("rejects an unreceipted or dimensionally incorrect site pack", () => {
    expect(() =>
      validateMeasuredGroundwaterSitesManifest({
        schema_version: 1,
        id: "usgs-groundwater-sites-tvgwfm-v1",
        truth_state: "observed",
        site_count: 2849,
        numeric_reading_count: 19117,
        binary: { encoding: "little-endian-float32", stride: 3, bytes: 1 },
      }),
    ).toThrow("invalid");
  });
});
