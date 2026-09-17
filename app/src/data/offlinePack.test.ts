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
  it("accepts a complete twenty-six-artifact offline pack", () => {
    const artifacts = Array.from({ length: 26 }, (_, index) =>
      artifact(String(index + 1)),
    );
    expect(
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-offline-earth-pack-v15",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 26,
        total_bytes: 260,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }).total_bytes,
    ).toBe(260);
  });

  it("rejects a manifest whose byte receipt does not balance", () => {
    const artifacts = Array.from({ length: 26 }, (_, index) =>
      artifact(String(index + 1)),
    );
    expect(() =>
      validateOfflinePack({
        schema_version: 1,
        id: "treasure-valley-offline-earth-pack-v15",
        created_at: "2026-09-14T19:25:00Z",
        source_doi: "10.5066/P9U6OOPH",
        network_required: false,
        artifact_count: 26,
        total_bytes: 259,
        artifacts,
        validation_boundary: "Build-time hashes.",
      }),
    ).toThrow("byte total");
  });
});
