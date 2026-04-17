import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
        AutoImport({
            dts: false,
            resolvers: [
                ElementPlusResolver({
                    importStyle: 'css',
                    directives: true
                })
            ]
        }),
        Components({
            dts: false,
            resolvers: [
                ElementPlusResolver({
                    importStyle: 'css'
                })
            ]
        })
    ],
    build: {
        rollupOptions: {
            output: {
                manualChunks(id) {
                    if (!id.includes('node_modules')) return undefined

                    if (id.includes('echarts')) {
                        return 'charts-vendor'
                    }
                    if (id.includes('@element-plus/icons-vue')) {
                        return 'ep-icons'
                    }
                    if (id.includes('element-plus/es')) {
                        return 'ep-shared'
                    }
                    if (id.includes('vant')) return 'mobile-vendor'
                    if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) return 'framework-vendor'
                    if (id.includes('axios') || id.includes('dayjs')) return 'utils-vendor'

                    return 'vendor'
                }
            }
        }
    },
    test: {
        server: {
            deps: {
                inline: ['element-plus']
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
