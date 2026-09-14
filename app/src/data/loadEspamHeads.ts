import type { EspamHeads, EspamHeadsManifest } from "./espamHeads";

const MANIFEST_URL = new URL(
  "../../public/data/idwr-espam22-heads-manifest-v1.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/idwr-espam22-heads-q10-v1.bin",
  import.meta.url,
).href;

export async function loadEspamHeads(
  signal?: AbortSignal,
): Promise<EspamHeads> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const [manifestResponse, binaryResponse] = await Promise.all([
    fetch(MANIFEST_URL, request),
    fetch(BINARY_URL, request),
  ]);
  if (!manifestResponse.ok || !binaryResponse.ok)
    throw new Error("ESPAM archived-head pack request failed");
  const manifest = validateEspamHeadsManifest(await manifestResponse.json());
  const buffer = await binaryResponse.arrayBuffer();
  if (buffer.byteLength !== manifest.binary.bytes)
    throw new Error("ESPAM archived-head binary byte count is invalid");
  const values = new Uint16Array(buffer);
  if (values.length !== manifest.slice_count * manifest.active_cell_count)
    throw new Error("ESPAM archived-head value count is invalid");
  return { manifest, values };
}

export function validateEspamHeadsManifest(
  candidate: unknown,
): EspamHeadsManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("ESPAM archived-head manifest is not an object");
  const manifest = candidate as Partial<EspamHeadsManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "idwr-espam22-archived-heads-v1" ||
    manifest.truth_state !== "ingested" ||
    manifest.representation !==
      "archived-modeled-output-not-independently-reproduced" ||
    manifest.active_cell_count !== 11_236 ||
    manifest.slice_count !== 39 ||
    manifest.source_head_record_count !== 923 ||
    manifest.quantization?.scale_feet !== 0.1 ||
    manifest.quantization.missing_sentinel !== 65_535 ||
    manifest.binary?.bytes !== 876_408 ||
    manifest.binary.encoding !== "little-endian-uint16" ||
    manifest.slices?.length !== 39 ||
    manifest.slices[0]?.year !== 1980 ||
    manifest.slices.at(-1)?.year !== 2018 ||
    !/^[a-f0-9]{64}$/u.test(manifest.binary.sha256 ?? "")
  )
    throw new Error("ESPAM archived-head manifest is invalid");
  return manifest as EspamHeadsManifest;
}

export function nearestEspamHeadSlice(
  manifest: EspamHeadsManifest,
  year: number,
): number {
  return manifest.slices.reduce(
    (best, slice, index) =>
      Math.abs(slice.year - year) < Math.abs(manifest.slices[best]!.year - year)
        ? index
        : best,
    0,
  );
}
