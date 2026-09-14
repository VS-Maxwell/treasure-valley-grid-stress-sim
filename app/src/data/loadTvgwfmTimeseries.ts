import type { TvgwfmBudgetRow, TvgwfmTimeseries } from "./tvgwfmTimeseries";

const TIMESERIES_URL = new URL(
  "../../public/data/tvgwfm-timeseries.json",
  import.meta.url,
).href;

export async function loadTvgwfmTimeseries(
  signal?: AbortSignal,
): Promise<TvgwfmTimeseries> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const response = await fetch(TIMESERIES_URL, request);
  if (!response.ok)
    throw new Error(
      `TVGWFM time-series request failed with ${response.status}`,
    );
  return validateTvgwfmTimeseries(await response.json());
}

export function validateTvgwfmTimeseries(candidate: unknown): TvgwfmTimeseries {
  if (!candidate || typeof candidate !== "object")
    throw new Error("TVGWFM time-series pack is not an object");
  const record = candidate as Partial<TvgwfmTimeseries>;
  if (
    record.schema_version !== 1 ||
    record.id !== "tvgwfm-historical-tables-v1" ||
    record.truth_state !== "modeled-screening"
  )
    throw new Error("TVGWFM time-series identity is invalid");
  if (record.budget?.rows.length !== 361)
    throw new Error("TVGWFM time-series must contain 361 budget rows");
  const groups = Object.values(record.observations ?? {});
  if (
    groups.length !== 4 ||
    groups.some((group) => group.row_count !== 361) ||
    groups.reduce((total, group) => total + group.series_count, 0) !== 33
  )
    throw new Error(
      "TVGWFM simulated-observation table dimensions are invalid",
    );
  if (
    !record.source?.model_listing_sha256.match(/^[a-f0-9]{64}$/u) ||
    !record.source.baseline_receipt_sha256.match(/^[a-f0-9]{64}$/u)
  )
    throw new Error("TVGWFM time-series source receipts are invalid");
  return record as TvgwfmTimeseries;
}

export function nearestBudgetRow(
  rows: readonly TvgwfmBudgetRow[],
  year: number,
): number {
  const target = Date.UTC(Math.max(1986, Math.min(2015, year)), 6, 1);
  return rows.reduce(
    (best, row, index) =>
      Math.abs(Date.parse(row.period_end_date) - target) <
      Math.abs(Date.parse(rows[best]!.period_end_date) - target)
        ? index
        : best,
    0,
  );
}
