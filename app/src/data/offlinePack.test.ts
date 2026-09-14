import { describe, expect, it } from "vitest";

import { validateOfflinePack } from "./loadOfflinePack";

const artifact = (id: string) => ({
  id,
  path: `data/${id}.json`,
  bytes: 10,
  sha256: "a".repeat(64),
  media_type: "application/json",
  truth_state: "modeled-screening",
});

describe("validateOfflinePack", () => {
  it("accepts a complete twenty-three-artifact offline pack", () => {
    const artifacts = Array.from({ length: 23 }, (_, index) =>
      artifact(String(index + 1)),
    );
    expect(
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-offline-earth-pack-v13",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 23,
        total_bytes: 230,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }).total_bytes,
    ).toBe(230);
  });

  it("rejects a manifest whose byte receipt does not balance", () => {
    const artifacts = Array.from({ length: 23 }, (_, index) =>
      artifact(String(index + 1)),
    );
    expect(() =>
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-offline-earth-pack-v13",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 23,
        total_bytes: 229,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }),
    ).toThrow("byte total");
  });
});
