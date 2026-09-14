import type { TruthState } from "../contracts";

export interface OfflinePackArtifact {
  readonly id: string;
  readonly path: string;
  readonly bytes: number;
  readonly sha256: string;
  readonly media_type: string;
  readonly truth_state: TruthState;
}

export interface OfflinePackManifest {
  readonly schema_version: 1;
  readonly id: "treasure-valley-offline-earth-pack-v6";
  readonly created_at: string;
  readonly source_doi: "10.5066/P9U6OOPH";
  readonly network_required: false;
  readonly artifact_count: number;
  readonly total_bytes: number;
  readonly artifacts: readonly OfflinePackArtifact[];
  readonly validation_boundary: string;
}
