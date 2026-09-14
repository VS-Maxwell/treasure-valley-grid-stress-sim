import type { GridCore } from "./gridTypes";

const GRID_CORE_URL = new URL("../../../data/grid-core.json", import.meta.url)
  .href;

export async function loadGridCore(signal?: AbortSignal): Promise<GridCore> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const response = await fetch(GRID_CORE_URL, request);
  if (!response.ok)
    throw new Error(`Grid pack request failed with ${response.status}`);
  const candidate: unknown = await response.json();
  return validateGridCore(candidate);
}

export function validateGridCore(candidate: unknown): GridCore {
  if (!candidate || typeof candidate !== "object")
    throw new Error("Grid pack is not an object");
  const record = candidate as Partial<GridCore>;
  if (record.schema_version !== 1)
    throw new Error("Unsupported grid pack schema version");
  if (!record.source_sha256 || !/^[a-f0-9]{64}$/u.test(record.source_sha256)) {
    throw new Error("Grid pack source receipt is missing or invalid");
  }
  if (record.trans?.features.length !== 244)
    throw new Error("Grid pack must contain 244 transmission corridors");
  if (record.subs?.features.length !== 94)
    throw new Error("Grid pack must contain 94 substations");
  if (record.plants?.features.length !== 14)
    throw new Error("Grid pack must contain 14 plants");
  return record as GridCore;
}
