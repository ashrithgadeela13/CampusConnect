import {defineConfig} from "vite";import react from "@vitejs/plugin-react";import {fileURLToPath} from "node:url";
export default defineConfig({resolve:{alias:{"@":fileURLToPath(new URL(".",import.meta.url))}},publicDir:"web-assets",plugins:[react()],build:{outDir:"public",emptyOutDir:true,chunkSizeWarningLimit:800}});
