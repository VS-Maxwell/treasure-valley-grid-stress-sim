import type { TvgwfmBottoms, TvgwfmBottomsManifest } from "./tvgwfmBottoms";

const MANIFEST_URL = new URL(
  "../../public/data/tvgwfm-bottoms-manifest.json",
  import.meta.url,
).href;
const BOTTOMS_URL = new URL(
  "../../public/data/tvgwfm-bottoms-f32.bin",
  import.meta.url,
).href;
const IDOMAIN_URL = new URL(
  "../../public/data/tvgwfm-idomain-i8.bin",
  import.meta.url,
).href;

export async function loadTvgwfmBottoms(
  signal?: AbortSignal,
): Promise<TvgwfmBottoms> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const [manifestResponse, bottomsResponse, idomainResponse] =
    await Promise.all([
      fetch(MANIFEST_URL, request),
      fetch(BOTTOMS_URL, request),
      fetch(IDOMAIN_URL, request),
    ]);
  if (!manifestResponse.ok || !bottomsResponse.ok || !idomainResponse.ok)
    throw new Error("TVGWFM layer-bottom pack request failed");
  const manifest = validateTvgwfmBottomsManifest(await manifestResponse.json());
  const [bottomBuffer, idomainBuffer] = await Promise.all([
    bottomsResponse.arrayBuffer(),
    idomainResponse.arrayBuffer(),
  ]);
  if (bottomBuffer.byteLength !== manifest.bottoms_binary.bytes)
    throw new Error("TVGWFM bottom binary byte count is invalid");
  if (idomainBuffer.byteLength !== manifest.idomain_binary.bytes)
    throw new Error("TVGWFM IDOMAIN binary byte count is invalid");
  const bottoms = new Float32Array(bottomBuffer);
  const idomain = new Int8Array(idomainBuffer);
  const expected = manifest.layout.layers * manifest.layout.cell_count;
  if (bottoms.length !== expected || idomain.length !== expected)
    throw new Error("TVGWFM bottom pack value count is invalid");
  return { manifest, bottoms, idomain };
}

export function validateTvgwfmBottomsManifest(
  candidate: unknown,
): TvgwfmBottomsManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("TVGWFM layer-bottom manifest is not an object");
  const manifest = candidate as Partial<TvgwfmBottomsManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "usgs-tvgwfm-layer-bottoms-v1" ||
    manifest.truth_state !== "ingested" ||
    manifest.doi !== "10.5066/P9U6OOPH" ||
    manifest.layout?.layers !== 6 ||
    manifest.layout.rows !== 64 ||
    manifest.layout.columns !== 65 ||
    manifest.layout.cell_count !== 4160 ||
    manifest.layout.vertical_datum !== "NAVD88" ||
    manifest.bottoms_binary?.bytes !== 99_840 ||
    manifest.idomain_binary?.bytes !== 24_960 ||
    manifest.layer_statistics?.length !== 6 ||
    !/^[a-f0-9]{64}$/u.test(manifest.bottoms_binary.sha256 ?? "") ||
    !/^[a-f0-9]{64}$/u.test(manifest.idomain_binary.sha256 ?? "")
  )
    throw new Error("TVGWFM layer-bottom manifest is invalid");
  return manifest as TvgwfmBottomsManifest;
}
