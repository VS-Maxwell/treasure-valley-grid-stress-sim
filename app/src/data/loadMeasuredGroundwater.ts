import type { MeasuredGroundwater } from "./measuredGroundwater";

const MEASURED_URL = new URL(
  "../../public/data/usgs-groundwater-annual.json",
  import.meta.url,
).href;

export async function loadMeasuredGroundwater(
  signal?: AbortSignal,
): Promise<MeasuredGroundwater> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const response = await fetch(MEASURED_URL, request);
  if (!response.ok)
    throw new Error(
      `Measured groundwater request failed with ${response.status}`,
    );
  return validateMeasuredGroundwater(await response.json());
}

export function validateMeasuredGroundwater(
  candidate: unknown,
): MeasuredGroundwater {
  if (!candidate || typeof candidate !== "object")
    throw new Error("Measured groundwater pack is not an object");
  const pack = candidate as Partial<MeasuredGroundwater>;
  if (
    pack.schema_version !== 1 ||
    pack.id !== "usgs-groundwater-depth-annual-1986-2015-v1" ||
    pack.truth_state !== "observed" ||
    pack.parameter_code !== "72019"
  )
    throw new Error("Measured groundwater identity is invalid");
  if (!pack.years || pack.years.length !== 30 || pack.year_count !== 30)
    throw new Error("Measured groundwater pack must contain 30 annual rows");
  const count = pack.years.reduce((sum, row) => sum + row.measurement_count, 0);
  if (
    pack.source_measurement_count !== 19_696 ||
    count !== pack.numeric_measurement_count ||
    count + (pack.excluded_null_value_count ?? -1) !==
      pack.source_measurement_count
  )
    throw new Error("Measured groundwater measurement total is invalid");
  if (!pack.source_receipt_sha256?.match(/^[a-f0-9]{64}$/u))
    throw new Error("Measured groundwater source receipt is invalid");
  return pack as MeasuredGroundwater;
}

export function nearestMeasuredYear(
  pack: MeasuredGroundwater,
  year: number,
): number {
  return pack.years.reduce(
    (best, row, index) =>
      Math.abs(row.year - year) < Math.abs(pack.years[best]!.year - year)
        ? index
        : best,
    0,
  );
}
