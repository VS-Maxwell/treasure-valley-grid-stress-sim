import { describe, expect, it } from "vitest";

import { validateRegionalDamsManifest } from "./loadRegionalDams";

describe("validateRegionalDamsManifest", () => {
  it("rejects unreceipted or dimensionally incorrect dam points", () => {
    expect(() =>
      validateRegionalDamsManifest({
        schema_version: 1,
        id: "usace-nid-snake-plain-dam-points-v2",
        truth_state: "observed",
        dam_count: 647,
        hydroelectric_purpose_count: 55,
        connectivity_state: "unresolved-pending-upstream-watershed-graph",
        binary: {
          encoding: "little-endian-float32",
          stride: 3,
          bytes: 1,
          sha256: "a".repeat(64),
        },
      }),
    ).toThrow("invalid");
  });
});
