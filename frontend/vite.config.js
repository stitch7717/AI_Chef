import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发代理：前端 5173 → 后端 8002，避免跨域
// （生产环境由 Nginx 统一反代，见阶段4）
export default defineConfig({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // 第三方库单独分包：业务代码更新不影响 vendor 缓存
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
    },
  },
})
