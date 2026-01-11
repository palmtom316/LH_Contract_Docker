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

app.mount('#app')
