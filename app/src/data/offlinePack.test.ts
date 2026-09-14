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
  it("accepts a complete twenty-five-artifact offline pack", () => {
    const artifacts = Array.from({ length: 25 }, (_, index) =>
      artifact(String(index + 1)),
    );
    expect(
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-offline-earth-pack-v14",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 25,
        total_bytes: 250,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }).total_bytes,
    ).toBe(250);
  });

  it("rejects a manifest whose byte receipt does not balance", () => {
    const artifacts = Array.from({ length: 25 }, (_, index) =>
      artifact(String(index + 1)),
    );
    expect(() =>
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-offline-earth-pack-v14",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 25,
        total_bytes: 249,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }),
    ).toThrow("byte total");
  });
});
