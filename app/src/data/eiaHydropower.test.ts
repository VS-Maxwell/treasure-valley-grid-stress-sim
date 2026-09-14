import { describe, expect, it } from "vitest";

import { validateEiaHydropowerManifest } from "./loadEiaHydropower";

const manifest = {
  schema_version: 1,
  id: "eia860-2025-snake-plain-hydropower-points-v1",
  truth_state: "ingested",
  plant_count: 77,
  generator_count: 167,
  operable_plant_count: 76,
  dam_link_review_state: "pending-human-review",
  binary: { stride: 4, bytes: 1232, sha256: "a".repeat(64) },
};

describe("EIA hydropower manifest", () => {
  it("accepts the receipted final-2025 inventory dimensions", () => {
    expect(() => validateEiaHydropowerManifest(manifest)).not.toThrow();
  });

  it("rejects an accepted identity claim before human review", () => {
    expect(() =>
      validateEiaHydropowerManifest({
        ...manifest,
        dam_link_review_state: "accepted",
      }),
    ).toThrow(/invalid/u);
  });
});
