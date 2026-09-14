import { lineParts, type GridCore, type Position } from "./gridTypes";

export interface GeoBounds {
  readonly west: number;
  readonly east: number;
  readonly south: number;
  readonly north: number;
}

export interface WorldPoint {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

export function measureGridBounds(grid: GridCore): GeoBounds {
  const bounds = {
    west: Infinity,
    east: -Infinity,
    south: Infinity,
    north: -Infinity,
  };
  for (const feature of grid.trans.features) {
    for (const line of lineParts(feature.geometry)) {
      for (const [longitude, latitude] of line) {
        bounds.west = Math.min(bounds.west, longitude);
        bounds.east = Math.max(bounds.east, longitude);
        bounds.south = Math.min(bounds.south, latitude);
        bounds.north = Math.max(bounds.north, latitude);
      }
    }
  }
  if (
    !Number.isFinite(bounds.west) ||
    bounds.west === bounds.east ||
    bounds.south === bounds.north
  ) {
    throw new Error("Grid pack has invalid geographic bounds");
  }
  return bounds;
}

export function previewElevation(x: number, z: number): number {
  const basin = -4.5 * Math.exp(-((x / 64) ** 2 + (z / 45) ** 2));
  const westernRidges = 8 * Math.max(0, (-x - 55) / 80) ** 1.7;
  const easternRidges = 11 * Math.max(0, (x - 52) / 80) ** 1.55;
  const texture =
    Math.sin(x * 0.075) * Math.cos(z * 0.11) * 1.1 +
    Math.sin((x + z) * 0.16) * 0.45;
  return basin + westernRidges + easternRidges + texture;
}

export function projectPosition(
  position: Position,
  bounds: GeoBounds,
): WorldPoint {
  const nx = (position[0] - bounds.west) / (bounds.east - bounds.west) - 0.5;
  const nz = (position[1] - bounds.south) / (bounds.north - bounds.south) - 0.5;
  const x = nx * 230;
  const z = -nz * 150;
  return { x, y: previewElevation(x, z) + 0.65, z };
}
