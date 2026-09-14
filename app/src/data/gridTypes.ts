export type Position = readonly [number, number];

export interface LineGeometry {
  readonly type: "LineString";
  readonly coordinates: readonly Position[];
}

export interface MultiLineGeometry {
  readonly type: "MultiLineString";
  readonly coordinates: readonly (readonly Position[])[];
}

export interface PointGeometry {
  readonly type: "Point";
  readonly coordinates: Position;
}

export interface TransmissionProperties {
  readonly line_id: string;
  readonly voltage_kv: number;
  readonly status: string;
  readonly owner: string;
  readonly sub_from: string;
  readonly sub_to: string;
}

export interface SubstationProperties {
  readonly name: string;
  readonly max_voltage_kv: number;
  readonly min_voltage_kv: number;
  readonly lines: number;
}

export interface PlantProperties {
  readonly plant_code: string;
  readonly plant_name: string;
  readonly capacity_mw: number;
  readonly fuel: string;
}

export interface Feature<G, P> {
  readonly type: "Feature";
  readonly geometry: G;
  readonly properties: P;
}

export interface FeatureCollection<F> {
  readonly type: "FeatureCollection";
  readonly features: readonly F[];
}

export interface GridCore {
  readonly schema_version: number;
  readonly source: string;
  readonly source_sha256: string;
  readonly trans: FeatureCollection<
    Feature<LineGeometry | MultiLineGeometry, TransmissionProperties>
  >;
  readonly subs: FeatureCollection<
    Feature<PointGeometry, SubstationProperties>
  >;
  readonly plants: FeatureCollection<Feature<PointGeometry, PlantProperties>>;
}

export function lineParts(
  geometry: LineGeometry | MultiLineGeometry,
): readonly (readonly Position[])[] {
  return geometry.type === "LineString"
    ? [geometry.coordinates]
    : geometry.coordinates;
}
