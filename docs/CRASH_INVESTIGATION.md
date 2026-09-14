# Crash Investigation

Updated: 2026-09-14 11:20 PDT

## Confirmed failure

- Firefox content process PID 305544 received `SIGSEGV` at 10:47:18 PDT.
- The fault was inside Firefox `libxul.so`; the system retained a truncated 2.2 GB coredump.
- The earlier simulator implementation repeatedly replaced a multi-megabyte GeoJSON source during animation.
- Two stale content processes from that session grew to roughly 19.8 GB and 27 GB RSS before they were terminated.
- The HTTP preview server stayed available and continued returning `200 OK`.

These facts establish a real browser crash and runaway renderer memory. They do not establish that the application was the only possible cause of the Firefox `libxul` fault.

## Repair now promoted on the default route

- `/` redirects directly to the built modular cockpit at `/dist/`.
- No intro gate, iframe, `srcdoc`, automatic watchdog drawer, MapLibre startup, or remote tile request runs on the default route.
- The local 397 KB grid core retains all 244 transmission corridors and 94 substations with a source SHA-256 receipt.
- Grid construction performs at most 32 visible redraw states and does not replace the underlying dataset.
- WebGL context loss is wired to dispose the 3D renderer and activate the bounded Canvas view.

## Current verification

- Controlled browser: automatic build reached 244/244.
- Replay: reached 244/244.
- Mid-build refresh: canceled the old generation and returned 244/244.
- Duration: 75 seconds.
- Firefox process total during the observation window: approximately 1,373,924 KB to 1,375,648 KB, a rise of about 1.7 MB.
- System available memory stayed near 67 GB.
- New coredumps after 11:17 PDT: none.
- Structural grid checks: 22 passed.
- Transmission expert markers: 16 passed.
- Release validation and JavaScript parse checks: passed.

## Open gates

- Reload the new direct-root build in a fresh Firefox content process and repeat the sustained test.
- Obtain a visual screenshot receipt; the browser screenshot interface currently times out even though DOM and control-state inspection works.
- Reintroduce terrain, timelines, water, climate, RAVEN, and the full 4D cockpit as separately budgeted modules. The preserved `legacy.html` is not the default boot path.
