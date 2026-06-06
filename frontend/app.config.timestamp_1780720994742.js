// app.config.ts
import { defineConfig } from "@tanstack/react-start/config";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from "vite-tsconfig-paths";
import react from "@vitejs/plugin-react";
var __filename = fileURLToPath(import.meta.url);
var __dirname = dirname(__filename);
var app_config_default = defineConfig({
  vite: {
    plugins: [
      react(),
      tailwindcss(),
      tsConfigPaths()
    ],
    resolve: {
      alias: {
        "@": resolve(__dirname, "./src")
      }
    }
  },
  tanstackStart: {
    server: { entry: "server" }
  }
});
export {
  app_config_default as default
};
