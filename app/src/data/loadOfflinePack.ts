import type { OfflinePackManifest } from "./offlinePack";

const OFFLINE_PACK_URL = new URL(
  "../../public/data/offline-pack-manifest.json",
  import.meta.url,
).href;

export async function loadOfflinePack(
  signal?: AbortSignal,
): Promise<OfflinePackManifest> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const response = await fetch(OFFLINE_PACK_URL, request);
  if (!response.ok)
    throw new Error(`Offline pack request failed with ${response.status}`);
  return validateOfflinePack(await response.json());
}

export function validateOfflinePack(candidate: unknown): OfflinePackManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("Offline pack manifest is not an object");
  const manifest = candidate as Partial<OfflinePackManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "treasure-valley-historical-water-pack-v1" ||
    manifest.source_doi !== "10.5066/P9U6OOPH" ||
    manifest.network_required !== false
  )
    throw new Error("Offline pack identity is invalid");
  if (
    !manifest.artifacts ||
    manifest.artifacts.length !== manifest.artifact_count ||
    manifest.artifacts.length !== 5
  )
    throw new Error("Offline pack artifact count is invalid");
  const total = manifest.artifacts.reduce(
    (sum, artifact) => sum + artifact.bytes,
    0,
  );
  if (total !== manifest.total_bytes)
    throw new Error("Offline pack byte total is invalid");
  if (
    manifest.artifacts.some(
      (artifact) =>
        artifact.bytes <= 0 || !/^[a-f0-9]{64}$/u.test(artifact.sha256),
    )
  )
    throw new Error("Offline pack artifact receipt is invalid");
  return manifest as OfflinePackManifest;
}
