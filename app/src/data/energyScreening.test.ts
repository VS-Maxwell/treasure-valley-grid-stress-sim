import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { ENERGY_SCENARIOS } from "./energyScreening";
import { validateEnergyScreening } from "./loadEnergyScreening";

const sourcePath = resolve(
  import.meta.dirname,
  "../../public/data/grid-screening-model-v2.json",
);
const model = validateEnergyScreening(
  JSON.parse(readFileSync(sourcePath, "utf8")) as unknown,
);

describe("94-bus energy screening pack", () => {
  it("keeps solver branches separate from map corridors", () => {
    expect(model.buses).toHaveLength(94);
    expect(model.branches).toHaveLength(156);
    expect(model.counts.map_corridors).toBe(244);
    expect(model.operational_use).toBe(false);
  });

  it("retains every scenario loading for every exact line id", () => {
    expect(
      model.branches.every((branch) =>
        ENERGY_SCENARIOS.every((scenario) =>
          Number.isFinite(branch.loading_pct[scenario]),
        ),
      ),
    ).toBe(true);
    expect(new Set(model.branches.map((branch) => branch.branch_id)).size).toBe(
      156,
    );
  });

  it("resolves only endpoint identities supported by geometry", () => {
    expect(model.counts.branches_with_unique_endpoint_labels).toBe(75);
    expect(model.counts.branches_with_ambiguous_endpoint_labels).toBe(81);
    expect(
      model.branches.filter(
        (branch) => branch.endpoint_identity_state === "ambiguous-label",
      ),
    ).toHaveLength(81);
    expect(model.counts.topology_resolved_branches).toBe(139);
    expect(model.counts.topology_blocked_branches).toBe(17);
    expect(model.counts.resolved_endpoint_identities).toBe(292);
    expect(model.counts.unresolved_endpoint_identities).toBe(20);
    expect(model.counts.geometry_resolved_tap_buses).toBe(27);
    expect(model.counts.resolved_graph_components).toBe(1);
    expect(model.fresh_solve_ready).toBe(false);
  });
});
