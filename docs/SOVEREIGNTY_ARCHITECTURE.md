# Sovereignty architecture

Updated: 2026-09-14

## Decision

Neither the web renderer nor an optional Unreal/ArcGIS renderer receives authority over the archive. They are replaceable presentation clients over approved, versioned data products. Software choice does not confer permission to acquire, disclose, transform, train on, or publish protected material.

## Two-renderer boundary

- The HTML/Three.js application remains the universal, inspectable and offline-capable reference client.
- A future Unreal Engine plus ArcGIS Maps SDK project may provide the cinematic desktop/XR client.
- Both clients consume the same immutable scientific manifests and browser-safe packs.
- Unreal Engine source, Esri plugin binaries, licensed provider tiles and credentials are not relicensed under the project's open-source code license.
- A renderer may be removed or replaced without changing custody, source receipts, review state or community authority.

## Data tiers

| Tier | Examples | Online-provider rule | Distribution rule |
|---|---|---|---|
| Public context | Public terrain, rivers, roads, published infrastructure | May use approved Esri/USGS services with attribution | Only where provider terms permit |
| Public scientific | Published model grids and outputs | Acquisition jobs retain source IDs and original bytes | Ship only receipted derivatives with limitations |
| Community-controlled | Approved lessons, interpretations and selected archive derivatives | Local by default; online use requires recorded authority | Access-gated and revocable |
| Protected | Oral histories, cultural locations, restricted archives, embeddings and local-AI prompts | Never sent to Epic, Esri or another cloud by default | Never bundled in a public build |

## Non-negotiable controls

1. Credentials remain in operating-system or server secret storage and never enter Git, browser JavaScript, screenshots or receipts.
2. Protected retrieval, transcription and inference run on sovereign-controlled systems unless a specific authority record permits another processor.
3. Every archival derivative retains original-object identity, custody, access class, source offsets, transformation receipt and human review state.
4. Online map requests are treated as disclosures of their requested geography and timing. Sensitive locations use local packages or generalized public geometry.
5. Community authority controls access, correction, retention, derivative use, publication and shutdown.
6. A model output cannot authorize its own acceptance, publication, training use or access change.
7. The public application must remain operational with every keyed provider gateway disabled.

## Release gate

No Unreal or web release containing community-controlled material is publishable until its exact manifest has an authority decision, provider-terms review, access test, credential scan, offline test and independent restore test. Public infrastructure layers may proceed separately; they do not weaken the protected-data gate.
