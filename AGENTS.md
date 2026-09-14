# Treasure Valley Simulator Working Rules

## Visible Development Is Mandatory

The owner must be able to see development as it happens. For every material task:

1. Record the task in `dev/status.json` before work begins.
2. Report the command or action in plain language without exposing secrets.
3. Record pass, fail, or blocked status immediately after validation.
4. Keep failures visible until they are fixed or explicitly accepted.
5. List changed files and the exact verification performed.
6. Never claim completion from an HTTP status, model response, build artifact, or visual impression alone.

The local development view is `http://127.0.0.1:8001/dev/`. It polls the status file every two seconds. Do not place credentials, private paths, protected records, or sensitive source content in the visible log.

## Product Invariants

- The first visible product screen is the working map cockpit. Do not add a splash screen, entry gate, blocking modal, or landing page.
- Energy, Water, Nexus, Risk, Archive, and Time are state-driven scenes over a shared simulation state. Camera movement occurs only from explicit user controls, tours, or scenario events.
- Simulation state remains independent from renderer objects.
- Text-heavy controls and accessibility surfaces use the DOM; the central 3D playfield stays clear.
- Heavy imagery, 3D Tiles, and Gaussian splats are lazy-loaded with poster and degraded-mode fallbacks.
- Observed, ingested, reconstructed, modeled-screening, validated-model, synthetic, and blocked-missing states remain visually distinct.
- Restricted or sovereignty-sensitive material is excluded unless an executed authority instrument explicitly allows its use.

## Secrets and External Services

- Never print, screenshot, commit, embed in public HTML, or place API keys in URLs or development logs.
- Retrieve only the credential required for the adapter being validated.
- Store private credentials outside this NTFS repository in the operating system's protected configuration area.
- Public browser keys must be provider-restricted by origin, service, and quota.
- A configured credential does not prove that a service is free, licensed for caching, or approved for redistribution.
- No paid call, public deployment, or remote publication occurs without an explicit cost and release gate.

## Machine Policy

- Madame-Butterfly and its RTX 4090 are the primary build, render, AI, and simulation engine.
- Palimpsest is the RTX 5060 Ti secondary worker. Celena's school use always has priority.
- Palimpsest keeps at least 16 GiB system RAM available. GPU jobs require working telemetry and retain at least 25 percent or 4 GiB VRAM, whichever is greater.
- Secondary jobs are bounded, checkpointed, low priority, and immediately pausable.
- Queen is storage and receipt custody only when live; availability is verified before every transfer.

## Validation and Release

- Test simulation, renderer, UI, assets, data contracts, licenses, and release packaging separately.
- Runtime-facing changes require a browser playtest and screenshots when a controllable browser is available.
- Preserve the original bytes and SHA-256 for every acquired research artifact.
- Code licensing does not relicense dependencies, models, imagery, data, archives, or generated third-party content.
- Maintain `THIRD_PARTY_LICENSES.csv`, `MODEL_REGISTRY.json`, `DATA_SOURCES.csv`, and `RESTRICTED_DATA_POLICY.md` before release.
- Build hosted artifacts into `dist/`; never deploy the repository root.
