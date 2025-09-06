import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";
import { lingui } from "@lingui/vite-plugin";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");
    const frontendApi = env.VITE_FRONTEND_API_URL || env.FRONTEND_API_URL || "";
    const apiBaseUrl = env.VITE_API_BASE_URL || env.API_BASE_URL || "";
    const googleClientId = env.VITE_GOOGLE_CLIENT_ID || env.GOOGLE_CLIENT_ID || "";
    const frontendUrl = env.VITE_FRONTEND_URL || env.FRONTEND_URL || "";
    return {
        plugins: [
            lingui(),
            react({
                babel: {
                    plugins: ["macros"],
                },
            }),
        ],
        resolve: {
            alias: {
                "@": path.resolve(__dirname, "src"),
            },
        },
        css: {
            preprocessorOptions: {
                scss: {
                    additionalData: `@use "@/styles/tokens" as *;`,
                },
            },
        },
        define: {
            "import.meta.env.VITE_FRONTEND_API_URL": JSON.stringify(frontendApi),
            "import.meta.env.VITE_API_BASE_URL": JSON.stringify(apiBaseUrl),
            "import.meta.env.VITE_GOOGLE_CLIENT_ID": JSON.stringify(googleClientId),
            "import.meta.env.VITE_FRONTEND_URL": JSON.stringify(frontendUrl),
            "import.meta.env.API_BASE_URL": JSON.stringify(apiBaseUrl),
            "import.meta.env.GOOGLE_CLIENT_ID": JSON.stringify(googleClientId),
            "import.meta.env.FRONTEND_URL": JSON.stringify(frontendUrl),
        },
        server: {
            port: 3000,
            host: true,
            proxy: {
                "/api": {
                    target: apiBaseUrl || "http://127.0.0.1:8000",
                    changeOrigin: true,
                    secure: false,
                },
            },
        },
        preview: {
            port: 3000,
            host: true,
        },
    };
});
