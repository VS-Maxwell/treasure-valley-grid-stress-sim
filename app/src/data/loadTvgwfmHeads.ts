import type { TvgwfmHeadManifest, TvgwfmHeads } from "./tvgwfmHeads";

const MANIFEST_URL = new URL(
  "../../public/data/tvgwfm-heads-manifest.json",
  import.meta.url,
).href;
const BINARY_URL = new URL(
  "../../public/data/tvgwfm-heads-q10.bin",
  import.meta.url,
).href;

export async function loadTvgwfmHeads(
  signal?: AbortSignal,
): Promise<TvgwfmHeads> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const [manifestResponse, binaryResponse] = await Promise.all([
    fetch(MANIFEST_URL, request),
    fetch(BINARY_URL, request),
  ]);
  if (!manifestResponse.ok)
    throw new Error(
      `TVGWFM head manifest request failed with ${manifestResponse.status}`,
    );
  if (!binaryResponse.ok)
    throw new Error(
      `TVGWFM head binary request failed with ${binaryResponse.status}`,
    );
  const manifest = validateTvgwfmHeadManifest(await manifestResponse.json());
  const binary = await binaryResponse.arrayBuffer();
  if (binary.byteLength !== manifest.layout.bytes)
    throw new Error(
      "TVGWFM head binary byte count does not match its manifest",
    );
  const values = new Uint16Array(binary);
  if (values.length !== manifest.layout.value_count)
    throw new Error(
      "TVGWFM head binary value count does not match its manifest",
    );
  return { manifest, values };
}

export function validateTvgwfmHeadManifest(
  candidate: unknown,
): TvgwfmHeadManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("TVGWFM head manifest is not an object");
  const record = candidate as Partial<TvgwfmHeadManifest>;
  const layout = record.layout;
  if (
    record.schema_version !== 1 ||
    record.id !== "tvgwfm-heads-biennial-v1" ||
    record.truth_state !== "modeled-screening"
  )
    throw new Error("TVGWFM head manifest identity is invalid");
  if (
    !layout ||
    layout.encoding !== "little-endian-uint16" ||
    layout.order !== "slice-layer-row-column" ||
    layout.rows !== 64 ||
    layout.columns !== 65 ||
    layout.layers !== 6 ||
    layout.slices !== 16 ||
    layout.value_count !== 399_360 ||
    layout.bytes !== 798_720 ||
    layout.inactive_value !== 65_535
  )
    throw new Error("TVGWFM head manifest layout is invalid");
  if (
    record.slices?.length !== layout.slices ||
    record.slices[0]?.year !== 1986 ||
    record.slices.at(-1)?.year !== 2015
  )
    throw new Error("TVGWFM head manifest time axis is invalid");
  if (!record.binary?.sha256.match(/^[a-f0-9]{64}$/u))
    throw new Error("TVGWFM head binary receipt is invalid");
  return record as TvgwfmHeadManifest;
}

export function nearestHeadSlice(manifest: TvgwfmHeadManifest, year: number) {
  return manifest.slices.reduce(
    (best, slice, index) =>
      Math.abs(slice.year - year) < Math.abs(manifest.slices[best]!.year - year)
        ? index
        : best,
    0,
  );
}
