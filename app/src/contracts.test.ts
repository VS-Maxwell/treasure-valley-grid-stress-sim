import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { SCENE_IDS, truthStateForYear } from "./contracts";

const schemaRoot = resolve(import.meta.dirname, "../../schemas");

describe("public contracts", () => {
  it("defines all seven product scenes", () => {
    expect(SCENE_IDS).toEqual([
      "time",
      "water",
      "energy",
      "nexus",
      "risk",
      "record",
      "learning",
    ]);
  });

  it("keeps time-dependent truth states explicit", () => {
    expect(truthStateForYear(-14_000)).toBe("reconstructed");
    expect(truthStateForYear(2026)).toBe("observed");
    expect(truthStateForYear(2050)).toBe("modeled-screening");
  });

  it("ships parseable JSON schemas with unique identifiers", () => {
    const names = [
      "truth-state.schema.json",
      "source-record.schema.json",
      "scenario.schema.json",
      "run-receipt.schema.json",
      "simulation-state.schema.json",
    ];
    const ids = names.map((name) => {
      const schema = JSON.parse(
        readFileSync(resolve(schemaRoot, name), "utf8"),
      ) as { $id?: string };
      expect(schema.$id).toBeTruthy();
      return schema.$id;
    });
    expect(new Set(ids).size).toBe(names.length);
  });
});
