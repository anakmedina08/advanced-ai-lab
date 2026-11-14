import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Frontend desacoplado: habla con la API FastAPI por HTTP/SSE (VITE_API_URL), sin proxy,
// para que la frontera frontend/backend se vea en la pestaña Network del navegador.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  test: {
    environment: "jsdom",
    globals: false,
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["src/setupTests.ts"],
  },
});
