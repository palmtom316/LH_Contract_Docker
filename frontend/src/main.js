import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Vant UI for mobile views
import 'vant/lib/index.css'
import { Locale } from 'vant'
import zhCN from 'vant/lib/locale/lang/zh-CN'

import App from './App.vue'
import router from './router'
import './assets/main.scss'

// Configure Vant Chinese locale
Locale.use('zh-CN', zhCN)

const app = createApp(App)

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// Global error handler for uncaught exceptions
app.config.errorHandler = (err, vm, info) => {
    console.error('[Global Error]', err)
    console.error('Component:', vm?.$options?.name || 'Unknown')
    console.error('Info:', info)

    // In production, you could send this to a logging service
    // Example: logErrorToService({ error: err.message, component: vm?.$options?.name, info })
}

// Global warning handler (development only)
if (import.meta.env.DEV) {
    app.config.warnHandler = (msg, vm, trace) => {
        console.warn('[Vue Warning]', msg)
        if (trace) console.warn('Trace:', trace)
    }
}

app.mount('#app')
