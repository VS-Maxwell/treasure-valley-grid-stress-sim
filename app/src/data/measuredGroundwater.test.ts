import { describe, expect, it } from "vitest";

import { nearestMeasuredYear } from "./loadMeasuredGroundwater";
import type { MeasuredGroundwater } from "./measuredGroundwater";

const pack = {
  years: [{ year: 1986 }, { year: 2000 }, { year: 2015 }],
} as unknown as MeasuredGroundwater;

describe("nearestMeasuredYear", () => {
  it("selects the nearest annual field-measurement summary", () => {
    expect(nearestMeasuredYear(pack, 2001)).toBe(1);
  });

  it("selects the last measured year for future dates", () => {
    expect(nearestMeasuredYear(pack, 2050)).toBe(2);
  });
});
