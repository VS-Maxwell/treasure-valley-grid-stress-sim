export const ESRI_GATEWAY_ORIGIN = "http://127.0.0.1:8767";
const IMAGERY_PATH = "/v1/imagery/treasure-valley.jpg";

interface GatewayHealth {
  readonly service: "treasure-valley-esri-gateway";
  readonly version: 1;
  readonly status: "ready" | "partial";
  readonly credential: "verified";
  readonly capabilities: {
    readonly basemap_styles: boolean;
    readonly geocoding: boolean;
    readonly public_imagery: boolean;
  };
  readonly imagery_path: typeof IMAGERY_PATH;
  readonly offline_runtime: "independent";
  readonly attribution: string;
}

export interface EsriGatewayState {
  readonly connected: boolean;
  readonly basemapStyles: boolean;
  readonly geocoding: boolean;
  readonly publicImagery: boolean;
  readonly imageryUrl: string | null;
  readonly attribution: string | null;
  readonly detail: string;
}

function isGatewayHealth(value: unknown): value is GatewayHealth {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<GatewayHealth>;
  const capabilities = candidate.capabilities as
    Partial<GatewayHealth["capabilities"]> | undefined;
  return (
    candidate.service === "treasure-valley-esri-gateway" &&
    candidate.version === 1 &&
    candidate.credential === "verified" &&
    candidate.offline_runtime === "independent" &&
    candidate.imagery_path === IMAGERY_PATH &&
    typeof candidate.attribution === "string" &&
    typeof capabilities?.basemap_styles === "boolean" &&
    typeof capabilities.geocoding === "boolean" &&
    typeof capabilities.public_imagery === "boolean"
  );
}

export async function probeEsriGateway(
  fetcher: typeof fetch = fetch,
  timeoutMilliseconds = 1_500,
): Promise<EsriGatewayState> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMilliseconds);
  try {
    const response = await fetcher(`${ESRI_GATEWAY_ORIGIN}/v1/health`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (!response.ok) throw new Error("Gateway health request failed");
    const payload: unknown = await response.json();
    if (!isGatewayHealth(payload)) throw new Error("Invalid gateway contract");
    return {
      connected: true,
      basemapStyles: payload.capabilities.basemap_styles,
      geocoding: payload.capabilities.geocoding,
      publicImagery: payload.capabilities.public_imagery,
      imageryUrl: payload.capabilities.public_imagery
        ? `${ESRI_GATEWAY_ORIGIN}${IMAGERY_PATH}`
        : null,
      attribution: payload.attribution,
      detail:
        "Credential isolated in the local gateway; offline packs remain independent.",
    };
  } catch {
    return {
      connected: false,
      basemapStyles: false,
      geocoding: false,
      publicImagery: false,
      imageryUrl: null,
      attribution: null,
      detail:
        "Optional Esri gateway is offline; receipt-backed local terrain remains active.",
    };
  } finally {
    clearTimeout(timeout);
  }
}
