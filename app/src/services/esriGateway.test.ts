import { describe, expect, it, vi } from "vitest";

import { ESRI_GATEWAY_ORIGIN, probeEsriGateway } from "./esriGateway";

describe("Esri gateway contract", () => {
  it("accepts the fixed loopback service contract", async () => {
    const fetcher = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            service: "treasure-valley-esri-gateway",
            version: 1,
            status: "ready",
            credential: "verified",
            capabilities: {
              basemap_styles: true,
              geocoding: true,
              public_imagery: true,
            },
            imagery_path: "/v1/imagery/treasure-valley.jpg",
            offline_runtime: "independent",
            attribution: "Powered by Esri; imagery © Esri and contributors",
          }),
          { status: 200 },
        ),
    );
    const state = await probeEsriGateway(fetcher as typeof fetch, 100);
    expect(state.connected).toBe(true);
    expect(state.geocoding).toBe(true);
    expect(state.imageryUrl).toBe(
      `${ESRI_GATEWAY_ORIGIN}/v1/imagery/treasure-valley.jpg`,
    );
  });

  it("fails closed on a malformed or unavailable gateway", async () => {
    const fetcher = vi.fn(
      async () =>
        new Response(JSON.stringify({ credential: "maybe" }), { status: 200 }),
    );
    const state = await probeEsriGateway(fetcher as typeof fetch, 100);
    expect(state.connected).toBe(false);
    expect(state.imageryUrl).toBeNull();
  });
});
