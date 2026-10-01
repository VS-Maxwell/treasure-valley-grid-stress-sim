export interface IdahoCounty {
  readonly fid: number;
  readonly fips: string;
  readonly name: string;
  readonly seat: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly acres: number;
  readonly tribal_homeland: string;
  readonly tax_roll_usd: number;
  readonly extraction_usd: number;
  readonly reparations_quantum_usd: number;
  readonly utm_x_m: number;
  readonly utm_y_m: number;
}

export interface IdahoStreamGauge {
  readonly fid: number;
  readonly site_no: string;
  readonly station_name: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly utm_x_m: number;
  readonly utm_y_m: number;
}

export interface IdahoDam {
  readonly fid: number;
  readonly dam_name: string;
  readonly river: string;
  readonly operator: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly height_ft: number;
  readonly capacity_mw: number;
  readonly storage_acre_ft: number;
  readonly utm_x_m: number;
  readonly utm_y_m: number;
}

export interface IdahoClimateStation {
  readonly fid: number;
  readonly station_id: string;
  readonly station_name: string;
  readonly climate_division: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly elevation_m: number;
  readonly record_start_yr: number;
  readonly mean_annual_temp_c: number;
  readonly mean_annual_precip_mm: number;
  readonly utm_x_m: number;
  readonly utm_y_m: number;
}

export interface IdahoTribe {
  readonly fid: number;
  readonly tribe_name: string;
  readonly capital: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly homeland_acres: number;
  readonly current_res_acres: number;
  readonly treaties: string;
  readonly sovereign_nexus: string;
  readonly utm_x_m: number;
  readonly utm_y_m: number;
}

export interface IdahoSuperfundSite {
  readonly fid: number;
  readonly site_name: string;
  readonly county: string;
  readonly primary_contaminant: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly remedial_status: string;
  readonly hazard_rank: string;
  readonly utm_x_m: number;
  readonly utm_y_m: number;
}

export interface StatewideMasterData {
  readonly idaho_44_counties: readonly IdahoCounty[];
  readonly idaho_all_usgs_stream_gauges: readonly IdahoStreamGauge[];
  readonly idaho_major_dams: readonly IdahoDam[];
  readonly idaho_noaa_deep_time_weather: readonly IdahoClimateStation[];
  readonly idaho_sovereign_tribes: readonly IdahoTribe[];
  readonly idaho_superfund_toxic_sites: readonly IdahoSuperfundSite[];
}

const STATEWIDE_URL = new URL(
  "../../../data/idaho_statewide_master_meta.json",
  import.meta.url,
).href;

export async function loadStatewideMaster(
  signal?: AbortSignal,
): Promise<StatewideMasterData> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const response = await fetch(STATEWIDE_URL, request);
  if (!response.ok) {
    throw new Error(
      `Statewide master pack request failed with ${response.status}`,
    );
  }
  const candidate = (await response.json()) as StatewideMasterData;
  return candidate;
}
