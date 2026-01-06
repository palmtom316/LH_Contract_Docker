import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    server: {
        host: '0.0.0.0',
        port: 3000,
        allowedHosts: [
            'localhost',
            '127.0.0.1',
            'cm.lhdl.cc',
            '.lhdl.cc'  // Allow all subdomains just in case
        ],
        hmr: {
            host: 'localhost',
            port: 3000
        },
        proxy: {
            '/api': {
                target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            },
            '/uploads': {
                target: process.env.API_PROXY_TARGET || 'http://localhost:8000',
                changeOrigin: true,
                secure: false
            }
        }
    }
})
