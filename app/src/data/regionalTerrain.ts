import type { GeoBounds } from "./geo";
import type { Position } from "./gridTypes";

export interface RegionalTerrainManifest {
  readonly schema_version: 1;
  readonly id: "usgs-3dep-snake-plain-terrain-v4";
  readonly truth_state: "observed";
  readonly provider: string;
  readonly product: string;
  readonly source_receipt: string;
  readonly source_receipt_sha256: string;
  readonly horizontal_datum: "NAD83";
  readonly vertical_datum: "NAVD88";
  readonly elevation_unit: "meters";
  readonly mesh: {
    readonly rows: number;
    readonly columns: number;
    readonly vertex_count: number;
    readonly bounds_wgs84: GeoBounds;
  };
  readonly statistics: {
    readonly minimum_meters: number;
    readonly maximum_meters: number;
    readonly mean_meters: number;
  };
  readonly binary: {
    readonly file: string;
    readonly bytes: number;
    readonly sha256: string;
    readonly encoding: "little-endian-float32";
    readonly order: "row-major-northwest-to-southeast-elevation-meters";
  };
  readonly render_transform: {
    readonly vertical_exaggeration: number;
    readonly world_height_span: number;
    readonly note: string;
  };
  readonly limitations: readonly string[];
}

export interface RegionalTerrain {
  readonly manifest: RegionalTerrainManifest;
  readonly elevations: Float32Array;
}

export function terrainWorldHeight(
  terrain: RegionalTerrain,
  elevationMeters: number,
): number {
  const { minimum_meters: minimum, maximum_meters: maximum } =
    terrain.manifest.statistics;
  const normalized = (elevationMeters - minimum) / (maximum - minimum);
  return normalized * terrain.manifest.render_transform.world_height_span - 4.5;
}

export function terrainWorldHeightAt(
  terrain: RegionalTerrain,
  position: Position,
): number | null {
  const { bounds_wgs84: bounds, columns, rows } = terrain.manifest.mesh;
  const [longitude, latitude] = position;
  if (
    longitude < bounds.west ||
    longitude > bounds.east ||
    latitude < bounds.south ||
    latitude > bounds.north
  )
    return null;
  const x =
    ((longitude - bounds.west) / (bounds.east - bounds.west)) * (columns - 1);
  const y =
    ((bounds.north - latitude) / (bounds.north - bounds.south)) * (rows - 1);
  const left = Math.floor(x);
  const top = Math.floor(y);
  const right = Math.min(left + 1, columns - 1);
  const bottom = Math.min(top + 1, rows - 1);
  const fx = x - left;
  const fy = y - top;
  const elevation = (row: number, column: number): number =>
    terrain.elevations[row * columns + column]!;
  const upper = elevation(top, left) * (1 - fx) + elevation(top, right) * fx;
  const lower =
    elevation(bottom, left) * (1 - fx) + elevation(bottom, right) * fx;
  return terrainWorldHeight(terrain, upper * (1 - fy) + lower * fy);
}
