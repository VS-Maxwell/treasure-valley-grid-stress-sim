import { describe, expect, it } from "vitest";

import { validateRegionalDamsManifest } from "./loadRegionalDams";

describe("validateRegionalDamsManifest", () => {
  it("rejects unreceipted or dimensionally incorrect dam points", () => {
    expect(() =>
      validateRegionalDamsManifest({
        schema_version: 1,
        id: "usace-nid-snake-plain-dam-points-v3",
        truth_state: "observed-plus-network-derived",
        dam_count: 647,
        hydroelectric_purpose_count: 55,
        connected_dam_count: 348,
        connected_hydroelectric_purpose_count: 42,
        outside_dam_count: 297,
        unresolved_dam_count: 2,
        target_outlet: {
          nwis_site_id: "USGS-13269000",
          outlet_comid: 24193082,
          name: "Snake River at Weiser ID",
        },
        connectivity_state: "directed-network-resolved-to-usgs-13269000",
        binary: {
          encoding: "little-endian-float32",
          stride: 4,
          bytes: 1,
          sha256: "a".repeat(64),
        },
      }),
    ).toThrow("invalid");
  });
});
