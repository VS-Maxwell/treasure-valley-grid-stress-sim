import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { measureGridBounds, projectPosition } from "./geo";
import { validateGridCore } from "./loadGridCore";

const sourcePath = resolve(import.meta.dirname, "../../../data/grid-core.json");
const grid = validateGridCore(
  JSON.parse(readFileSync(sourcePath, "utf8")) as unknown,
);

describe("receipt-backed grid core", () => {
  it("retains the exact source counts and receipt", () => {
    expect(grid.trans.features).toHaveLength(244);
    expect(grid.subs.features).toHaveLength(94);
    expect(grid.plants.features).toHaveLength(14);
    expect(grid.source_sha256).toMatch(/^[a-f0-9]{64}$/u);
  });

  it("has finite geographic bounds and projection", () => {
    const bounds = measureGridBounds(grid);
    expect(bounds.west).toBeLessThan(bounds.east);
    expect(bounds.south).toBeLessThan(bounds.north);
    const projected = projectPosition([bounds.west, bounds.south], bounds);
    expect(Object.values(projected).every(Number.isFinite)).toBe(true);
  });

  it("rejects an incomplete pack", () => {
    const invalid = { ...grid, trans: { ...grid.trans, features: [] } };
    expect(() => validateGridCore(invalid)).toThrow(
      /244 transmission corridors/u,
    );
  });
});
