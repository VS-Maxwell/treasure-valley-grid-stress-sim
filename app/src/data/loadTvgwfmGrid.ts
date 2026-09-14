import type { TvgwfmGrid } from "./tvgwfmTypes";

const TVGWFM_GRID_URL = new URL(
  "../../public/data/tvgwfm-grid.json",
  import.meta.url,
).href;

export async function loadTvgwfmGrid(
  signal?: AbortSignal,
): Promise<TvgwfmGrid> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const response = await fetch(TVGWFM_GRID_URL, request);
  if (!response.ok)
    throw new Error(`TVGWFM grid request failed with ${response.status}`);
  return validateTvgwfmGrid(await response.json());
}

export function validateTvgwfmGrid(candidate: unknown): TvgwfmGrid {
  if (!candidate || typeof candidate !== "object")
    throw new Error("TVGWFM grid pack is not an object");
  const record = candidate as Partial<TvgwfmGrid>;
  const grid = record.grid;
  if (
    record.schema_version !== 1 ||
    record.id !== "usgs-tvgwfm-grid-v1" ||
    record.truth_state !== "ingested" ||
    record.rights !== "CC0-1.0"
  )
    throw new Error("TVGWFM grid identity or truth boundary is invalid");
  if (
    !record.source_archive?.sha256.match(/^[a-f0-9]{64}$/u) ||
    record.source_archive.bytes !== 6_744_282
  )
    throw new Error("TVGWFM source receipt is invalid");
  if (!grid || grid.layers !== 6 || grid.rows !== 64 || grid.columns !== 65)
    throw new Error("TVGWFM grid dimensions do not match the official archive");
  if (
    grid.cell_widths.length !== grid.columns ||
    grid.cell_heights.length !== grid.rows ||
    grid.top_elevation_feet.length !== grid.rows * grid.columns
  )
    throw new Error("TVGWFM grid arrays are incomplete");
  if (
    grid.active_top_cells !==
    grid.top_elevation_feet.filter((value) => value > 0).length
  )
    throw new Error("TVGWFM active-cell receipt does not match the surface");
  return record as TvgwfmGrid;
}
