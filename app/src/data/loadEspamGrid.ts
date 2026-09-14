import type { EspamGrid, EspamGridManifest } from "./espamGrid";

const MANIFEST_URL = new URL(
  "../../public/data/idwr-espam22-grid-manifest-v1.json",
  import.meta.url,
).href;
const LINES_URL = new URL(
  "../../public/data/idwr-espam22-grid-lines-f32-v1.bin",
  import.meta.url,
).href;
const CELLS_URL = new URL(
  "../../public/data/idwr-espam22-grid-cells-f32-v1.bin",
  import.meta.url,
).href;

export async function loadEspamGrid(signal?: AbortSignal): Promise<EspamGrid> {
  const request: RequestInit = { cache: "force-cache" };
  if (signal) request.signal = signal;
  const [manifestResponse, linesResponse, cellsResponse] = await Promise.all([
    fetch(MANIFEST_URL, request),
    fetch(LINES_URL, request),
    fetch(CELLS_URL, request),
  ]);
  if (!manifestResponse.ok || !linesResponse.ok || !cellsResponse.ok)
    throw new Error("ESPAM grid pack request failed");
  const manifest = validateEspamGridManifest(await manifestResponse.json());
  const [lineBuffer, cellBuffer] = await Promise.all([
    linesResponse.arrayBuffer(),
    cellsResponse.arrayBuffer(),
  ]);
  if (
    lineBuffer.byteLength !== manifest.line_binary.bytes ||
    cellBuffer.byteLength !== manifest.cell_binary.bytes
  )
    throw new Error("ESPAM grid binary byte count is invalid");
  const lines = new Float32Array(lineBuffer);
  const cells = new Float32Array(cellBuffer);
  if (
    lines.length !== manifest.line_binary.record_count * 4 ||
    cells.length !== manifest.layout.active_cells * 4
  )
    throw new Error("ESPAM grid binary value count is invalid");
  return { manifest, lines, cells };
}

export function validateEspamGridManifest(
  candidate: unknown,
): EspamGridManifest {
  if (!candidate || typeof candidate !== "object")
    throw new Error("ESPAM grid manifest is not an object");
  const manifest = candidate as Partial<EspamGridManifest>;
  if (
    manifest.schema_version !== 1 ||
    manifest.id !== "idwr-espam22-grid-v1" ||
    manifest.truth_state !== "ingested" ||
    manifest.layout?.layers !== 1 ||
    manifest.layout.rows !== 104 ||
    manifest.layout.columns !== 209 ||
    manifest.layout.stress_periods !== 462 ||
    manifest.layout.active_cells !== 11_236 ||
    manifest.line_binary?.stride !== 4 ||
    manifest.line_binary.record_count !== 44_944 ||
    manifest.line_binary.bytes !== 719_104 ||
    manifest.cell_binary?.stride !== 4 ||
    manifest.cell_binary.record_count !== 11_236 ||
    manifest.cell_binary.bytes !== 179_776 ||
    !/^[a-f0-9]{64}$/u.test(manifest.line_binary.sha256 ?? "") ||
    !/^[a-f0-9]{64}$/u.test(manifest.cell_binary.sha256 ?? "")
  )
    throw new Error("ESPAM grid manifest is invalid");
  return manifest as EspamGridManifest;
}
