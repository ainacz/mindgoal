import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    port: 5173,
    host: true,
    // Пускаем любой хост: туннель для отладки в Telegram каждый раз даёт
    // новый домен, а Vite по умолчанию чужие хосты блокирует.
    allowedHosts: true,
    // Бэкенд ходит через тот же origin — значит туннель нужен один,
    // а не два, и CORS в отладке вообще не участвует.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
