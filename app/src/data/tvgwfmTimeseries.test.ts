import { describe, expect, it } from "vitest";

import { nearestBudgetRow } from "./loadTvgwfmTimeseries";
import type { TvgwfmBudgetRow } from "./tvgwfmTimeseries";

const row = (date: string): TvgwfmBudgetRow => ({
  stress_period: 1,
  period_end_date: date,
  model_time_days: 0,
  cumulative_in_ft3: 0,
  cumulative_out_ft3: 0,
  cumulative_delta_ft3: 0,
  rate_in_ft3_per_day: 0,
  rate_out_ft3_per_day: 0,
  rate_delta_ft3_per_day: 0,
  cumulative_discrepancy_percent: 0,
  rate_discrepancy_percent: 0,
});

describe("nearestBudgetRow", () => {
  const rows = [row("1986-01-01"), row("2000-07-01"), row("2016-01-01")];

  it("selects a historical row close to the requested year", () => {
    expect(nearestBudgetRow(rows, 2000)).toBe(1);
  });

  it("clamps future requests to the historical baseline", () => {
    expect(nearestBudgetRow(rows, 2050)).toBe(2);
  });
});
