import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [react(), tsconfigPaths()],
	server: {
		port: 5173,
		proxy: {
			// Local dev: forward API calls to FastAPI running on localhost
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false,
			},
			// Docker dev: if frontend resolves 'web' service, forward '/v1' to backend '/api/v1'
			'/v1': {
				target: 'http://web:8000',
				changeOrigin: true,
				secure: false,
				rewrite: (path) => `/api${path}`,
			},
		},
	},
}) 