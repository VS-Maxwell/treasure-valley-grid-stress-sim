import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  root: "public-demo",
  base: "./",
  publicDir: false,
  preview: {
    allowedHosts: ["bless-scott-boating-cross.trycloudflare.com"],
  },
  build: {
    outDir: "../public-demo-dist",
    emptyOutDir: true,
    sourcemap: false,
    rollupOptions: {
      input: resolve(import.meta.dirname, "public-demo/index.html"),
    },
  },
});
