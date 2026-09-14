import { describe, expect, it } from "vitest";

import { validateEspamGridManifest } from "./loadEspamGrid";

describe("validateEspamGridManifest", () => {
  it("accepts only the exact receipted ESPAM 2.2 grid contract", () => {
    const manifest = {
      schema_version: 1,
      id: "idwr-espam22-grid-v1",
      truth_state: "ingested",
      layout: {
        layers: 1,
        rows: 104,
        columns: 209,
        stress_periods: 462,
        active_cells: 11_236,
      },
      line_binary: {
        stride: 4,
        record_count: 44_944,
        bytes: 719_104,
        sha256: "a".repeat(64),
      },
      cell_binary: {
        stride: 4,
        record_count: 11_236,
        bytes: 179_776,
        sha256: "b".repeat(64),
      },
    };
    expect(validateEspamGridManifest(manifest).layout.active_cells).toBe(
      11_236,
    );
    expect(() =>
      validateEspamGridManifest({
        ...manifest,
        layout: { ...manifest.layout, layers: 6 },
      }),
    ).toThrow("invalid");
  });
});
