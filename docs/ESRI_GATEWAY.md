# Secure Esri gateway

Updated: 2026-09-14

## Confirmed capability

The locally stored Esri EDU credential was validated without printing or copying it into the repository. The ArcGIS basemap style endpoint and World Geocoding Service both returned valid bounded responses when the credential was supplied in an `Authorization: Bearer` header. The earlier basemap HTTP 403 was caused by using `POST` against a `GET` endpoint, not by an invalid credential.

The credential is never placed in a URL. Esri imagery tile requests do not support the same header-only pattern, so this adapter does not forward privileged tile URLs to the browser. It streams the public Esri World Imagery export for the fixed 119°W–111°W, 42°N–46°N Snake Plain scene envelope and applies the required on-screen attribution. The service response is not saved into the offline pack.

## Run

```bash
npm run esri:gateway
```

The server binds only `127.0.0.1:8767`. The simulator probes it for at most 1.5 seconds and otherwise continues with the receipt-backed local USGS terrain.

## Exposed routes

- `GET /v1/health` — fixed, secret-free capability contract.
- `GET /v1/geocode?q=...&limit=1..5` — bounded Treasure Valley place search; returns only address, point, score, and address type.
- `GET /v1/imagery/treasure-valley.jpg` — live fixed-bounds public Esri World Imagery export; no arbitrary upstream target or bounds.

## Security and product boundaries

- The credential is read once from the operating-system Secret Service with `secret-tool`; it is not accepted through HTTP, environment files, or command-line arguments.
- Licensed service calls use an authorization header. No token is logged, placed in a URL, committed, embedded in browser code, or returned in a response.
- Only explicit simulator origins on loopback receive access. A request with any other browser `Origin` is rejected with HTTP 403.
- Redirects are disabled, payload sizes and timeouts are bounded, request targets are not access-logged, and no arbitrary proxy route exists.
- The live image is an optional presentation overlay. USGS 3DEP remains the elevation geometry and authoritative local terrain source.
- A successful provider response does not create an archival receipt, redistribution permission, scientific validation, or an offline record.
- Public hosting remains closed until provider terms, quota, origin restrictions, and release attribution are reviewed.
