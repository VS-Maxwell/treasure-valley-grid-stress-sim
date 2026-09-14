# Offline lake handoff audit

Updated: 2026-09-14

## Decision

The package at `/home/madame-butterfly/forge/treasure_valley_offline_lake/` is a useful schema and interface prototype. It is not accepted scientific data and must not replace the receipt-backed simulator packs.

## Confirmed artifacts

- The executed notebook exists, contains 9 executed code cells and contains no saved error output.
- The package contains 63 Parquet files totaling 1,640 rows.
- The package contains 12 files under `raw_vault/`, 36 JSON receipt files and 5 browser-pack files.
- The four browser-pack hashes listed in the walkthrough match the current filenames.

These facts prove that files were generated. They do not prove that the records came from the named authorities or that the models were scientifically validated.

## Blocking findings

1. Fifty-one of the 63 Parquet tables omit one or more of the required common `record_id`, `source_id`, `receipt_id`, `truth_state`, `review_state`, and `limitations` fields.
2. `tvgwfm_parser.py` synthesizes a 12 × 16 surface with `numpy.linspace`, a sloped formula and sinusoidal thickness. The verified USGS TVGWFM discretization is 6 × 64 × 65 with 24,960 bottom values. The handoff's 1,152 cells are not the published model grid.
3. `grid_topology.py` says it “synthesizes” the network. It creates sequential buses, formula-derived impedance, 63 hard-coded cross-ties and trigonometric display values while writing a “Newton-Raphson Converged” string. This is not the preserved 94-bus/156-branch line-ID model and not a reproduced solver run.
4. `lake_manager.py` generates random RAVEN-like draws and hard-codes a risk probability of 0.082, an NSE value of 0.892, and a reviewer signature. No accepted RAVEN execution or independent reviewer record supports those claims.
5. Several connectors explicitly fall back to synthetic or local example data after acquisition errors. Hashing those bytes proves preservation of the generated fallback, not provider provenance.
6. The terrain tile uses the SHA-256 of an empty object while individual terrain samples are hard-coded.
7. A local path or a reported `rclone` target is not proof that Google Drive contains a complete, independently readable copy. No Drive readback receipt was supplied with the handoff.

## Safe reuse

- Reuse module organization and selected schema names after review.
- Import no scientific row without a provider object, full byte receipt, source-to-row transform receipt, correct truth state, and table-specific validation.
- Replace the synthetic aquifer and grid tables with the already verified TVGWFM and exact legacy line-ID packs.
- Keep all risk values blocked until an actual pinned RAVEN run, inputs, seed, output hashes and reviewer acceptance exist.
- Keep the Coeur d'Alene package separate and unaccepted until its Tribal authority, source, scientific and custody checks are performed independently.
