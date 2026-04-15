import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@/styles/index.scss' // Global styles
import {
    CircleCheck,
    Delete,
    Document,
    Download,
    Edit,
    Lock,
    Money,
    More,
    Plus,
    Refresh,
    Search,
    Tickets,
    Upload,
    User,
    Wallet,
    ZoomIn,
    ZoomOut
} from '@element-plus/icons-vue'

// Vant UI for mobile views
import 'vant/lib/index.css'
import { Locale } from 'vant'
import zhCN from 'vant/lib/locale/lang/zh-CN'

import App from './App.vue'
import router from './router'
import { useUserStore } from '@/stores/user'
import { useUiStore } from '@/stores/ui'
import './assets/main.scss'

// Configure Vant Chinese locale
Locale.use('zh-CN', zhCN)

const app = createApp(App)
const pinia = createPinia()

const globalIcons = {
    CircleCheck,
    Delete,
    Document,
    Download,
    Edit,
    Lock,
    Money,
    More,
    Plus,
    Refresh,
    Search,
    Tickets,
    Upload,
    User,
    Wallet,
    ZoomIn,
    ZoomOut
}

for (const [key, component] of Object.entries(globalIcons)) {
    app.component(key, component)
}

app.use(pinia)
app.use(router)

const uiStore = useUiStore(pinia)
uiStore.initTheme()

useUserStore(pinia)

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
