// vite.config.ts
import { defineConfig } from "vite";
import { TanStackRouterVite } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from "vite-tsconfig-paths";
import { resolve } from "node:path";
var vite_config_default = defineConfig({
  plugins: [
    TanStackRouterVite({
      autoCodeSplitting: true,
      generatedRouteTree: "./src/routeTree.gen.ts"
    }),
    react(),
    tailwindcss(),
    tsConfigPaths()
  ],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src")
    }
  },
  ssr: {
    noExternal: ["@tanstack/react-start"]
  },
  build: {
    target: "esnext"
  }
});
export {
  vite_config_default as default
};
