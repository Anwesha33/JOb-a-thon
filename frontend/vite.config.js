import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api to the FastAPI backend so the frontend can use
// same-origin relative URLs.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Force IPv4 — `localhost` can resolve to ::1 and miss a backend bound
      // only to 127.0.0.1.
      "/api": "http://127.0.0.1:8000",
    },
  },
});
