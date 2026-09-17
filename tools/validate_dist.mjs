import { readFile, readdir, stat } from "node:fs/promises";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../dist/", import.meta.url));
const failures = [];

async function filesUnder(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await filesUnder(path)));
    else files.push(path);
  }
  return files;
}

let files = [];
try {
  files = await filesUnder(root);
} catch (error) {
  failures.push(
    `dist is missing or unreadable: ${error instanceof Error ? error.message : String(error)}`,
  );
}

const names = files.map((file) => relative(root, file));
for (const requiredExtension of [".html", ".js", ".css", ".json"]) {
  if (!names.some((name) => extname(name) === requiredExtension))
    failures.push(`dist has no ${requiredExtension} artifact`);
}
if (names.some((name) => name === ".env" || name.endsWith("/.env")))
  failures.push("dist contains an .env file");
if (names.some((name) => name.endsWith(".ts") && !name.endsWith(".d.ts")))
  failures.push("dist contains TypeScript source");

let totalBytes = 0;
for (const file of files) totalBytes += (await stat(file)).size;
// Hosted dist stays lean; source maps remain available through the Vite dev
// server while terrain and data layers are integrated. Raw provider data remain out.
const fullPlainDevelopmentBudget = 8 * 1024 * 1024;
if (totalBytes > fullPlainDevelopmentBudget)
  failures.push(
    `dist exceeds the 8 MiB full-plain development budget: ${totalBytes} bytes`,
  );

const textFiles = files.filter((file) =>
  [".html", ".js", ".css"].includes(extname(file)),
);
const combined = (
  await Promise.all(textFiles.map((file) => readFile(file, "utf8")))
).join("\n");
if (!combined.includes("Treasure Valley"))
  failures.push("dist does not identify the Treasure Valley product");
if (combined.includes("127.0.0.1:8080/log"))
  failures.push("dist contains the retired development logger");
if (/INL RAVEN Probabilistic Risk Output/iu.test(combined))
  failures.push("dist attributes unreceipted values to RAVEN");
if (/(?:api[_-]?key|secret|token)\s*[:=]\s*["'][^"']{12,}["']/iu.test(combined))
  failures.push("dist may contain an embedded credential");

if (failures.length) {
  console.error(`Distribution validation failed:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}

console.log(
  `Distribution validation passed: ${files.length} files, ${totalBytes} bytes, no source or obvious secret leakage.`,
);
