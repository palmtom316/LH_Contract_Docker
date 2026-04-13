import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

function getElementPlusChunkName(id) {
    const elementComponentMatch = id.match(/node_modules\/element-plus\/es\/components\/([^/]+)/)
    if (elementComponentMatch?.[1]) {
        return `element-${elementComponentMatch[1]}`
    }

    if (id.includes('node_modules/element-plus/')) {
        return 'element-core'
    }

    if (id.includes('node_modules/@element-plus/icons-vue/')) {
        return 'element-icons'
    }

    return null
}

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
    ],
    build: {
        rollupOptions: {
            output: {
                manualChunks(id) {
                    if (!id.includes('node_modules')) return undefined

                    const elementChunk = getElementPlusChunkName(id)
                    if (elementChunk) {
                        return elementChunk
                    }

                    if (id.includes('echarts')) {
                        return 'charts-vendor'
                    }
                    if (id.includes('vant')) return 'mobile-vendor'
                    if (id.includes('@supabase/supabase-js')) return 'supabase-vendor'
                    if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) return 'framework-vendor'
                    if (id.includes('axios') || id.includes('dayjs') || id.includes('file-saver')) return 'utils-vendor'

                    return 'vendor'
                }
            }
        }
    },
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
