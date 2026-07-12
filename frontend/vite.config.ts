import { defineConfig } from "vite";
import { resolve } from "path";

// Single self-contained ES module bundle (Lit included, no externals) with a
// stable filename, since the integration references it by a fixed path
// (see __init__.py's PANEL_MODULE_FILENAME). Built output is committed into
// custom_components/dash480/panel_dist/ — HACS installs never run this.
export default defineConfig({
  build: {
    outDir: resolve(__dirname, "../custom_components/dash480/panel_dist"),
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/dash480-panel.ts"),
      formats: ["es"],
      fileName: () => "dash480-panel.js",
    },
  },
});
