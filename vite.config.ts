import { resolve } from "node:path";

import { defineConfig } from "vitest/config";

export default defineConfig({
  root: "app",
  base: "./",
  server: {
    allowedHosts: true,
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    fs: {
      deny: ["**/idaho_statewide_master_meta.json"],
    },
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    target: "es2022",
    // Keep hosted dist lean; Vite's dev server remains the source-map workflow.
    sourcemap: false,
    assetsInlineLimit: 0,
    rollupOptions: {
      input: resolve(import.meta.dirname, "app/index.html"),
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
    coverage: {
      reporter: ["text", "json-summary"],
    },
  },
});
