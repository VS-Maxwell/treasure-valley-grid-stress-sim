import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import { resolve, relative, join } from "node:path";

const root = resolve(import.meta.dirname, "../public-demo-dist");
const files = [];
async function walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isSymbolicLink()) throw new Error("symlink in public output");
    if (entry.isDirectory()) await walk(path);
    else if (entry.isFile()) files.push(relative(root, path).replaceAll("\\", "/"));
    else throw new Error("non-file entry in public output");
  }
}
await walk(root);
files.sort();
const expected = [
  "index.html",
  "assets/eia-regional-energy-f32-v1-*.bin",
  "assets/index-*.css",
  "assets/index-*.js",
  "assets/usgs-3dep-snake-plain-terrain-f32-v4-*.bin",
];
if (files.length !== expected.length) throw new Error("unexpected public output file count");
for (const pattern of expected) {
  const regex = new RegExp("^" + pattern.replaceAll(".", "\\.").replaceAll("*", "[A-Za-z0-9_-]+") + "$");
  if (files.filter((name) => regex.test(name)).length !== 1) {
    throw new Error("missing or duplicate public artifact: " + pattern);
  }
}
const hashes = {
  "eia-regional-energy-f32-v1": "6c3785d65876dc2e15a342dfd710fc64c0e49fd8af6646a2aeac369fcf7e876b",
  "usgs-3dep-snake-plain-terrain-f32-v4": "dfae5691cde8ef59e499aa6c0b6fa454b9663ed934a641b2247ce1caa990635c",
};
for (const [prefix, digest] of Object.entries(hashes)) {
  const name = files.find((file) => file.startsWith("assets/" + prefix + "-"));
  if (!name) throw new Error("missing approved binary: " + prefix);
  const bytes = await readFile(join(root, name));
  if (createHash("sha256").update(bytes).digest("hex") !== digest) {
    throw new Error("approved binary hash mismatch: " + prefix);
  }
}
const blocked = /auth-gate|bypassGate|idaho_statewide_master_meta|idaho_sovereign_tribes|CDA_GRANT_CANONICAL|grid-core|grid-screening|usace-nid|offline-pack-manifest|funding_pitch|\/\@fs\/|(?:api[_-]?key|password|secret)\s*[:=]/i;
for (const name of files.filter((file) => /\.(?:html|css|js)$/.test(file))) {
  const content = await readFile(join(root, name), "utf8");
  if (blocked.test(content)) throw new Error("blocked reference in public output: " + name);
}
const html = await readFile(join(root, "index.html"), "utf8");
if (!html.includes("PUBLIC DATA DEMO") || !html.includes('id="scene"')) {
  throw new Error("public preview identity or scene missing");
}
console.log(JSON.stringify({ check: "public-demo-dist", status: "pass", files: files.length, approved_binaries: Object.keys(hashes).length }));
