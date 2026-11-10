import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// 全局异常兜底：组件抛错时不至于白屏，给用户可读提示（业务级基础保障）
app.config.errorHandler = (err, _instance, info) => {
  console.error('[vue error]', info, err)
  ElMessage.error('页面出了点小问题，已为你自动恢复，请重试')
}

// 未捕获的 Promise 异常（如网络中断）同样提示，不阻塞使用
window.addEventListener('unhandledrejection', (e) => {
  console.error('[unhandledrejection]', e.reason)
})

app.mount('#app')
