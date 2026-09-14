#!/usr/bin/env python3
"""Loopback-only Esri adapter for the Treasure Valley simulator.

The browser never receives the Esri credential. Licensed Esri requests use an
Authorization header, while the optional imagery surface is streamed from the
public World Imagery export service and is never written to the repository.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


HOST = "127.0.0.1"
DEFAULT_PORT = 8767
ALLOWED_ORIGINS = {
    "http://127.0.0.1:8001",
    "http://localhost:8001",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
}
STYLE_URL = (
    "https://basemapstyles-api.arcgis.com/arcgis/rest/services/styles/v2/"
    "styles/arcgis/imagery?f=json"
)
GEOCODE_URL = (
    "https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/"
    "findAddressCandidates"
)
PUBLIC_IMAGERY_URL = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
    "MapServer/export"
)
REGION_BOUNDS = "-118,43,-115,45"
REGION_IMAGE_SIZE = "1280,854"
MAX_JSON_BYTES = 512_000
MAX_IMAGE_BYTES = 3_000_000
USER_AGENT = "TreasureValleySimulator/0.2"


class GatewayError(RuntimeError):
    """Safe gateway failure that never contains an upstream URL or token."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


OPENER = urllib.request.build_opener(NoRedirect())


def read_esri_credential() -> str:
    result = subprocess.run(
        [
            "secret-tool",
            "lookup",
            "service",
            "treasure-valley-sim",
            "provider",
            "esri",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    credential = result.stdout.strip()
    if result.returncode != 0 or not credential:
        raise GatewayError("Esri credential is unavailable in Secret Service")
    return credential


def authorized_headers(credential: str, accept: str = "application/json") -> dict[str, str]:
    return {
        "Accept": accept,
        "Authorization": f"Bearer {credential}",
        "User-Agent": USER_AGENT,
    }


def cors_origin(origin: str | None) -> str | None:
    return origin if origin in ALLOWED_ORIGINS else None


def normalize_geocode_query(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not 2 <= len(normalized) <= 160:
        raise GatewayError("Place search must contain 2 to 160 characters")
    return normalized


def normalize_limit(value: str | None) -> int:
    try:
        parsed = int(value or "3")
    except ValueError as exc:
        raise GatewayError("Result limit must be an integer") from exc
    if not 1 <= parsed <= 5:
        raise GatewayError("Result limit must be between 1 and 5")
    return parsed


def _read_bounded(response, maximum: int) -> bytes:  # noqa: ANN001
    data = response.read(maximum + 1)
    if len(data) > maximum:
        raise GatewayError("Upstream response exceeded the configured size limit")
    return data


def fetch_json(url: str, headers: dict[str, str], maximum: int = MAX_JSON_BYTES) -> Any:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with OPENER.open(request, timeout=20) as response:
            if response.status != HTTPStatus.OK:
                raise GatewayError(f"Upstream service returned HTTP {response.status}")
            raw = _read_bounded(response, maximum)
    except urllib.error.HTTPError as exc:
        raise GatewayError(f"Upstream service returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GatewayError("Upstream service could not be reached") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GatewayError("Upstream service returned invalid JSON") from exc


def fetch_public_imagery() -> tuple[bytes, str]:
    query = urllib.parse.urlencode(
        {
            "bbox": REGION_BOUNDS,
            "bboxSR": "4326",
            "imageSR": "4326",
            "size": REGION_IMAGE_SIZE,
            "format": "jpg",
            "f": "image",
        }
    )
    request = urllib.request.Request(
        f"{PUBLIC_IMAGERY_URL}?{query}",
        headers={"Accept": "image/jpeg", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with OPENER.open(request, timeout=30) as response:
            content_type = response.headers.get_content_type()
            if response.status != HTTPStatus.OK or content_type not in {
                "image/jpeg",
                "image/png",
            }:
                raise GatewayError("Public imagery service returned an unsupported response")
            return _read_bounded(response, MAX_IMAGE_BYTES), content_type
    except urllib.error.HTTPError as exc:
        raise GatewayError(f"Public imagery service returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GatewayError("Public imagery service could not be reached") from exc


def probe_capabilities(credential: str) -> dict[str, bool]:
    style = fetch_json(STYLE_URL, authorized_headers(credential))
    style_ok = (
        isinstance(style, dict)
        and style.get("version") == 8
        and isinstance(style.get("sources"), dict)
        and bool(style.get("layers"))
    )
    geocode_query = urllib.parse.urlencode(
        {
            "f": "json",
            "singleLine": "Boise, Idaho",
            "maxLocations": "1",
            "searchExtent": REGION_BOUNDS,
        }
    )
    geocode = fetch_json(
        f"{GEOCODE_URL}?{geocode_query}", authorized_headers(credential)
    )
    geocode_ok = isinstance(geocode, dict) and bool(geocode.get("candidates"))
    return {
        "basemap_styles": style_ok,
        "geocoding": geocode_ok,
        "public_imagery": True,
    }


def geocode(credential: str, query: str, limit: int) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(
        {
            "f": "json",
            "singleLine": query,
            "maxLocations": str(limit),
            "searchExtent": REGION_BOUNDS,
            "outFields": "Addr_type,Match_addr",
        }
    )
    payload = fetch_json(
        f"{GEOCODE_URL}?{encoded}", authorized_headers(credential)
    )
    candidates = []
    for candidate in payload.get("candidates", [])[:limit]:
        location = candidate.get("location") or {}
        candidates.append(
            {
                "address": str(candidate.get("address", ""))[:240],
                "longitude": location.get("x"),
                "latitude": location.get("y"),
                "score": candidate.get("score"),
                "address_type": (candidate.get("attributes") or {}).get("Addr_type"),
            }
        )
    return {
        "query": query,
        "count": len(candidates),
        "candidates": candidates,
        "provider": "Esri World Geocoding Service",
    }


class GatewayServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int, credential: str, capabilities: dict[str, bool]):
        super().__init__((HOST, port), GatewayHandler)
        self.credential = credential
        self.capabilities = capabilities


class GatewayHandler(BaseHTTPRequestHandler):
    server: GatewayServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        # Do not log request targets: geocode terms may be sensitive and future
        # adapters must never leak credentials through access logs.
        return

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        allowed = cors_origin(self.headers.get("Origin"))
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
        self.end_headers()

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        origin = cors_origin(self.headers.get("Origin"))
        if not origin:
            self._json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        request_origin = self.headers.get("Origin")
        if request_origin and not cors_origin(request_origin):
            self._json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
            return
        parsed = urllib.parse.urlsplit(self.path)
        try:
            if parsed.path == "/v1/health" and not parsed.query:
                self._json(
                    HTTPStatus.OK,
                    {
                        "service": "treasure-valley-esri-gateway",
                        "version": 1,
                        "status": "ready"
                        if all(self.server.capabilities.values())
                        else "partial",
                        "credential": "verified",
                        "credential_source": "operating-system-secret-service",
                        "capabilities": self.server.capabilities,
                        "imagery_path": "/v1/imagery/treasure-valley.jpg",
                        "offline_runtime": "independent",
                        "attribution": "Powered by Esri; imagery © Esri and contributors",
                    },
                )
                return
            if parsed.path == "/v1/geocode":
                parameters = urllib.parse.parse_qs(
                    parsed.query, keep_blank_values=True, max_num_fields=4
                )
                unknown = set(parameters) - {"q", "limit"}
                if unknown:
                    raise GatewayError("Unsupported query parameter")
                query = normalize_geocode_query((parameters.get("q") or [""])[0])
                limit = normalize_limit((parameters.get("limit") or [None])[0])
                self._json(
                    HTTPStatus.OK,
                    geocode(self.server.credential, query, limit),
                )
                return
            if (
                parsed.path == "/v1/imagery/treasure-valley.jpg"
                and not parsed.query
            ):
                body, content_type = fetch_public_imagery()
                self._headers(HTTPStatus.OK, content_type, len(body))
                self.wfile.write(body)
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "route_not_found"})
        except GatewayError as exc:
            self._json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
        except (ValueError, TypeError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_request"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        raise SystemExit("Port must be between 1024 and 65535")
    credential = read_esri_credential()
    capabilities = probe_capabilities(credential)
    server = GatewayServer(args.port, credential, capabilities)
    print(
        f"Treasure Valley Esri gateway ready on http://{HOST}:{args.port} "
        f"(basemap_styles={capabilities['basemap_styles']}, "
        f"geocoding={capabilities['geocoding']}, public_imagery=True)",
        flush=True,
    )
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
