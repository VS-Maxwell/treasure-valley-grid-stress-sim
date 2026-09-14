import { describe, expect, it, vi } from "vitest";

import { INITIAL_STATE } from "../contracts";
import { SimulationStore } from "./SimulationStore";

describe("SimulationStore", () => {
  it("starts with renderer-independent serializable state", () => {
    const store = new SimulationStore();
    expect(store.state).toEqual(INITIAL_STATE);
    expect(JSON.parse(JSON.stringify(store.state))).toEqual(INITIAL_STATE);
  });

  it("clamps time and keeps truth state explicit", () => {
    const store = new SimulationStore();
    store.selectScene("time");
    store.setYear(-20_000);
    expect(store.state.year).toBe(-15_000);
    expect(store.state.truthState).toBe("reconstructed");
    store.setYear(2080);
    expect(store.state.year).toBe(2080);
    expect(store.state.truthState).toBe("modeled-screening");
  });

  it("labels active representations instead of treating every past year as observed", () => {
    const store = new SimulationStore();
    store.selectScene("water");
    store.setYear(2000);
    expect(store.state.truthState).toBe("modeled-screening");
    store.selectScene("risk");
    expect(store.state.truthState).toBe("blocked-missing");
    store.selectScene("energy");
    expect(store.state.truthState).toBe("modeled-screening");
  });

  it("builds the heat and drought comparison state through Stress", () => {
    const store = new SimulationStore();
    store.stress();
    expect(store.state).toMatchObject({
      scene: "nexus",
      year: 2050,
      compare: true,
      climateScenario: "heat-drought-2050",
      truthState: "modeled-screening",
    });
  });

  it("promotes all branches through selectable screening scenarios", () => {
    const store = new SimulationStore();
    store.selectScene("water");
    store.setEnergyScenario("all50");
    expect(store.state).toMatchObject({
      scene: "energy",
      energyScenario: "all50",
      truthState: "modeled-screening",
    });
  });

  it("notifies subscribers only when state changes", () => {
    const store = new SimulationStore();
    const subscriber = vi.fn();
    store.subscribe(subscriber);
    store.selectScene("energy");
    store.selectScene("water");
    expect(subscriber).toHaveBeenCalledTimes(2);
    expect(store.state.scene).toBe("water");
  });
});
