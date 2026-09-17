# Lemhi archive

This directory holds scripts and full sends for the CDA Dule Lensed project,
also referred to as Dianne's one-year grant project. It is the first source
collection being organized in this repository.

## Folder convention

Every item is filed by source location first and year second:

```text
projects/lemhi/sources/<source-location>/<year>/scripts/
projects/lemhi/sources/<source-location>/<year>/full-sends/
```

- `source-location` is the place, organization, drive, or other origin the
  material came from. Use a stable lowercase name with hyphens.
- `<year>` is the four-digit year associated with the material. Use `unknown`
  when the year is not known instead of guessing.
- `scripts/` contains source code, job scripts, notebooks, and related tooling.
- `full-sends/` contains complete delivery bundles or transmission packages.

The first intake location is `lemhi-idaho/2026`. Empty `.gitkeep` files mark
the two intake areas until the first materials are added.

## Intake rules

Keep original filenames when they carry provenance. Add a short README or
receipt beside a delivery when the source, date, contents, or integrity hash
would otherwise be unclear. Do not commit credentials, private keys, or
protected records without the required authority and access review.