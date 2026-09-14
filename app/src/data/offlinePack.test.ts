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
  it("accepts a complete eight-artifact offline pack", () => {
    const artifacts = [1, 2, 3, 4, 5, 6, 7, 8].map((id) =>
      artifact(String(id)),
    );
    expect(
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-historical-water-pack-v3",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 8,
        total_bytes: 80,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }).total_bytes,
    ).toBe(80);
  });

  it("rejects a manifest whose byte receipt does not balance", () => {
    const artifacts = [1, 2, 3, 4, 5, 6, 7, 8].map((id) =>
      artifact(String(id)),
    );
    expect(() =>
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-historical-water-pack-v3",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 8,
        total_bytes: 79,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }),
    ).toThrow("byte total");
  });
});
