import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// 开发代理：前端 5173 → 后端 8002，避免跨域
// （生产环境由 Nginx 统一反代，见阶段4）
const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  resolve: {
    alias: [
      // element-plus 2.14 的 exports 不再暴露 ./es/components/*，
      // 而按需引入（含 ElMessage 这类命令式 API）需要深路径，这里直接指到文件系统。
      {
        find: /^element-plus\/es\/components\/(.*)$/,
        replacement: path.resolve(__dirname, 'node_modules/element-plus/es/components/$1'),
      },
    ],
  },
  plugins: [
    vue(),
    // Element Plus 按需引入：模板里的 <el-xxx /> 由 resolver 自动注册并注入对应样式，
    // 不再全量打包 950KB 的组件库（首屏 JS gzip 约 300KB → ~100KB）
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // 第三方库单独分包：业务代码更新不影响 vendor 缓存
        // element-plus 不再整包成 chunk：按需引入后组件代码分散进各视图 chunk
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
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
