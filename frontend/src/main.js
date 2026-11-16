import { createApp } from 'vue'
import { createPinia } from 'pinia'
// 命令式 API（ElMessage/ElMessageBox）不走模板，必须深路径导入才能被摇树；
// 从 'element-plus' 主入口导入会打包整个 950KB 组件库
import ElMessage from 'element-plus/es/components/message'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)

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
