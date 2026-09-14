# Restricted Data Policy

## Scope

This repository and any public `dist/` contain project-owned code and explicitly approved public or synthetic demonstration data only. The `Apache-2.0 OR MIT` project license applies only to work the owner has authority to license. It does not apply to third-party datasets, imagery, model weights, archives, transcripts, personal information, institutional records, or sovereignty-sensitive material.

## Excluded material

The following material is excluded from source control, public builds, screenshots, logs, checkpoints, training corpora, and model prompts unless a specific executed authority instrument permits the exact use:

- Tribal, cultural, ceremonial, archaeological, burial, NAGPRA, Graves Act, or location-sensitive records;
- protected or restricted archival collections;
- personally identifying, student, employment, medical, financial, credential, or security information;
- infrastructure details whose release is restricted by law, agreement, or safety review;
- unpublished research supplied under confidentiality or limited-use terms; and
- provider content whose terms prohibit caching, extraction, analysis, redistribution, or offline packaging.

Absence of Tribal representation in a public source is a documentary or governance gap—not evidence of absent Tribal presence, activity, knowledge, rights, or authority.

## Access classes

1. `public` — verified for the specific public use and redistribution path.
2. `internal` — available to authorized project members; excluded from public builds.
3. `restricted` — available only through an explicit collection-level authority gate and logged decision.
4. `service-restricted` — accessed from a provider at runtime under its terms; never assumed redistributable.

Moving material between classes requires a recorded owner or authority decision, source terms, permitted uses, review date, and reviewer identity. A model, script, successful API call, or repository location cannot make that decision.

## AI and transcription boundary

Local AI may search or explain only allow-listed collections. It cannot publish, accept scientific state, approve archival recovery, infer missing authority, or combine restricted and public collections. Transcription retains source-audio linkage, time segments, confidence, model identity, and human-review state. Model outputs remain generated interpretations until reviewed.

## Release gate

The public release process fails closed when any bundled item has unknown provenance, unknown terms, a blocked redistribution state, a missing hash where one is required, or a restricted classification. Public, internal, and restricted manifests are generated separately. Only the public manifest may enter a hosted bundle.
