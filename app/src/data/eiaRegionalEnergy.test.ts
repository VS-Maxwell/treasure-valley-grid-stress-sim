import { describe, expect, it } from "vitest";

import { validateEiaRegionalEnergyManifest } from "./loadEiaRegionalEnergy";

const manifest = {
  schema_version: 1,
  id: "eia860-2025-snake-plain-regional-energy-points-v1",
  truth_state: "ingested",
  plant_count: 190,
  plants_with_generators: 190,
  generator_count: 335,
  generator_lifecycle_counts: {
    operable: 287,
    proposed: 18,
    retired: 14,
    canceled: 15,
    "indefinitely-postponed": 1,
  },
  generator_technology_counts: {
    hydropower: 167,
    solar: 36,
    wind: 48,
    storage: 14,
    "natural-gas": 32,
    geothermal: 6,
    biomass: 17,
    petroleum: 2,
    nuclear: 12,
    other: 1,
  },
  technology_codes: {
    hydropower: 0,
    solar: 1,
    wind: 2,
    storage: 3,
    "natural-gas": 4,
    geothermal: 5,
    biomass: 6,
    petroleum: 7,
    nuclear: 8,
    other: 9,
  },
  lifecycle_codes: {
    operable: 0,
    proposed: 1,
    retired: 2,
    canceled: 3,
    "indefinitely-postponed": 4,
  },
  binary: { stride: 5, bytes: 6700, sha256: "a".repeat(64) },
};

describe("EIA regional energy manifest", () => {
  it("accepts all final-2025 regional generator lifecycles", () => {
    expect(() => validateEiaRegionalEnergyManifest(manifest)).not.toThrow();
  });

  it("rejects lifecycle counts that omit canceled records", () => {
    expect(() =>
      validateEiaRegionalEnergyManifest({
        ...manifest,
        generator_lifecycle_counts: {
          ...manifest.generator_lifecycle_counts,
          canceled: 0,
        },
      }),
    ).toThrow(/invalid/u);
  });
});
