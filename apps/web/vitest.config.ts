import { defineConfig } from "vitest/config";
export default defineConfig({
  esbuild: { jsx: "automatic" },
  test: {
    environment: "jsdom",
    exclude: ["e2e/**", "node_modules/**"],
    setupFiles: ["./test-setup.ts"],
  },
  resolve: { alias: { "@": new URL(".", import.meta.url).pathname } },
});
